"""Benchmark harness: quantum vs classical models on identical splits."""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from .classical import fit_random_forest, fit_rbf_svm
from .config import Config
from .data import scaffold_split, stratified_split
from .features import QuantumEncoder, morgan_matrix
from .metrics import classification_metrics
from .quantum import fit_qsvm_tuned, train_vqc, vqc_scores


def _row(name, family, split, seed, nq, fmap, reps, y, score, fit_s, pred_s, params):
    return dict(model=name, family=family, split=split, seed=seed, n_qubits=nq, feature_map=fmap,
                reps=reps, **classification_metrics(y, score), fit_seconds=fit_s,
                predict_seconds=pred_s, params=json.dumps(params, default=float))


def run_split(Xfp, y, tr, te, cfg: Config, seed: int, split_name: str, full: bool = True):
    """Run every model on one train/test split. Returns (rows, scores) where scores[name] = test probabilities."""
    ytr, yte = y[tr], y[te]
    rows, scores = [], {}

    t = time.time(); rf = fit_random_forest(Xfp[tr], ytr, seed); fit_s = time.time() - t
    t = time.time(); s = rf.predict_proba(Xfp[te])[:, 1]; pred_s = time.time() - t
    name = "Random Forest (2048-bit FP)"
    rows.append(_row(name, "classical", split_name, seed, None, None, None, yte, s, fit_s, pred_s, {})); scores[name] = s

    qubit_list = cfg.qubit_ablation if full else (cfg.n_qubits,)
    for nq in qubit_list:
        enc = QuantumEncoder(nq, random_state=seed).fit(Xfp[tr])
        Xtr, Xte = enc.transform(Xfp[tr]), enc.transform(Xfp[te])

        t = time.time(); svm, bp = fit_rbf_svm(Xtr, ytr, cfg.c_grid, cfg.cv_folds, seed); fit_s = time.time() - t
        t = time.time(); s = svm.predict_proba(Xte)[:, 1]; pred_s = time.time() - t
        name = f"Classical SVM (RBF, PCA-{nq})"
        rows.append(_row(name, "classical", split_name, seed, nq, None, None, yte, s, fit_s, pred_s, bp)); scores[name] = s

        if nq == cfg.n_qubits:
            t = time.time(); rfp = fit_random_forest(Xtr, ytr, seed); fit_s = time.time() - t
            s = rfp.predict_proba(Xte)[:, 1]
            name = f"Random Forest (PCA-{nq})"
            rows.append(_row(name, "classical", split_name, seed, nq, None, None, yte, s, fit_s, 0.0, {})); scores[name] = s

        configs = cfg.feature_map_ablation if (full and nq == cfg.n_qubits) else ((cfg.feature_map, cfg.reps),)
        if not full:
            configs = ((cfg.feature_map, cfg.reps),)
        for fmap, reps in configs:
            t = time.time()
            qsvm, table = fit_qsvm_tuned(Xtr, ytr, fmap, reps, cfg.c_grid, cfg.scale_grid, cfg.cv_folds, seed)
            fit_s = time.time() - t
            t = time.time(); s = qsvm.predict_proba(Xte)[:, 1]; pred_s = time.time() - t
            name = f"Quantum Kernel SVM ({fmap}, reps={reps}, {nq}q)"
            rows.append(_row(name, "quantum", split_name, seed, nq, fmap, reps, yte, s, fit_s, pred_s, qsvm.best_params_))
            scores[name] = s
    return rows, scores


def run_vqc_benchmark(Xfp, y, tr, te, cfg: Config, seed: int):
    """VQC vs QSVM vs classical SVM, all trained on the *same small* balanced subset (VQC is expensive)."""
    rng = np.random.default_rng(seed)
    pos, neg = tr[y[tr] == 1], tr[y[tr] == 0]
    half = cfg.vqc_train_size // 2
    sub = np.concatenate([rng.choice(pos, half, replace=False), rng.choice(neg, half, replace=False)])
    rng.shuffle(sub)
    nq = cfg.vqc_qubits
    enc = QuantumEncoder(nq, random_state=seed).fit(Xfp[sub])
    Xs, Xte = enc.transform(Xfp[sub]), enc.transform(Xfp[te])
    ys, yte = y[sub], y[te]
    rows, split = [], f"small-train({len(sub)})"

    t = time.time(); vqc = train_vqc(Xs, ys, nq, cfg.vqc_maxiter, seed); fit_s = time.time() - t
    s = vqc_scores(vqc, Xte)
    rows.append(_row(f"VQC (ZZ r1 + RealAmplitudes, {nq}q)", "quantum", split, seed, nq, "zz", 1, yte, s, fit_s, 0.0,
                     dict(maxiter=cfg.vqc_maxiter, n_weights=len(vqc.weights))))

    t = time.time(); q, _ = fit_qsvm_tuned(Xs, ys, cfg.feature_map, cfg.reps, cfg.c_grid, cfg.scale_grid, cfg.cv_folds, seed); fit_s = time.time() - t
    rows.append(_row(f"Quantum Kernel SVM ({cfg.feature_map}, reps={cfg.reps}, {nq}q)", "quantum", split, seed, nq,
                     cfg.feature_map, cfg.reps, yte, q.predict_proba(Xte)[:, 1], fit_s, 0.0, q.best_params_))
    t = time.time(); svm, bp = fit_rbf_svm(Xs, ys, cfg.c_grid, cfg.cv_folds, seed); fit_s = time.time() - t
    rows.append(_row(f"Classical SVM (RBF, PCA-{nq})", "classical", split, seed, nq, None, None, yte,
                     svm.predict_proba(Xte)[:, 1], fit_s, 0.0, bp))
    return rows


def run_all(df: pd.DataFrame, cfg: Config, log=print, run_vqc: bool = True):
    """Full benchmark: repeated random splits (+ablations), one scaffold split and the VQC comparison."""
    Xfp = morgan_matrix(df["smiles"], cfg.fp_radius, cfg.fp_bits)
    y = df["label"].values
    all_rows, roc_store = [], {}

    for seed in cfg.seeds:
        log(f"[benchmark] random split, seed {seed}")
        tr, te = stratified_split(df, cfg.test_size, seed)
        rows, scores = run_split(Xfp, y, tr, te, cfg, seed, "random", full=True)
        all_rows += rows
        if seed == cfg.seeds[0]:
            roc_store = dict(y_test=y[te], scores=scores)

    log("[benchmark] scaffold split")
    tr, te = scaffold_split(df, cfg.test_size)
    rows, _ = run_split(Xfp, y, tr, te, cfg, 0, "scaffold", full=False)
    all_rows += rows
    runs = pd.DataFrame(all_rows)

    vqc_rows = []
    if run_vqc:
        for seed in cfg.seeds:
            log(f"[benchmark] VQC comparison, seed {seed}")
            tr, te = stratified_split(df, cfg.test_size, seed)
            vqc_rows += run_vqc_benchmark(Xfp, y, tr, te, cfg, seed)
    return runs, pd.DataFrame(vqc_rows), roc_store


def summarise(runs: pd.DataFrame, group=("split", "model", "family", "n_qubits", "feature_map", "reps")) -> pd.DataFrame:
    metrics = ["auc", "accuracy", "precision", "recall", "f1", "ef10", "fit_seconds"]
    g = runs.groupby(list(group), dropna=False)[metrics].agg(["mean", "std"])
    g.columns = [f"{m}_{s}" for m, s in g.columns]
    return g.reset_index().sort_values(["split", "auc_mean"], ascending=[True, False])
