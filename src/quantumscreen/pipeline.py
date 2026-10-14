"""End-to-end screening pipeline: final model training, persistence, screening and ranking."""
from __future__ import annotations

import json
import time

import joblib
import numpy as np
import pandas as pd

from .classical import fit_rbf_svm
from .config import Config
from .data import stratified_split
from .features import QuantumEncoder, drug_likeness, morgan_matrix
from .metrics import enrichment_factor, precision_at_k
from .quantum import QuantumKernelSVM, build_feature_map, fit_qsvm_tuned
from .ranking import rank_candidates


def save_model(model: QuantumKernelSVM, encoder: QuantumEncoder, path, meta: dict | None = None) -> None:
    joblib.dump(dict(encoder=encoder, svc=model.svc_, states=model.train_states_,
                     params=dict(feature_map=model.feature_map, reps=model.reps, C=model.C, scale=model.scale),
                     meta=meta or {}), path, compress=3)


def load_model(path):
    """Returns ``(encoder, model, meta)`` ready for :func:`screen_smiles`."""
    d = joblib.load(path)
    m = QuantumKernelSVM(**d["params"])
    m.train_states_, m.svc_ = d["states"], d["svc"]
    m.classes_ = m.svc_.classes_
    m.circuit_ = build_feature_map(m.feature_map, d["encoder"].n_qubits, m.reps)
    return d["encoder"], m, d["meta"]


def screen_smiles(smiles, encoder: QuantumEncoder, model: QuantumKernelSVM, cfg: Config | None = None,
                  fp_radius: int = 2, fp_bits: int = 2048) -> pd.DataFrame:
    """Score and rank new molecules (list of SMILES) with a trained model."""
    cfg = cfg or Config()
    X = encoder.transform(morgan_matrix(smiles, fp_radius, fp_bits))
    df = pd.DataFrame({"smiles": list(smiles), "label": -1})
    ranked = rank_candidates(df, model.predict_proba(X)[:, 1], cfg)
    return ranked.drop(columns=["known_label"])


def final_screen(df: pd.DataFrame, cfg: Config, log=print):
    """Hold-out virtual screen + deployment model.

    1. Train the tuned quantum model on 80 % of BACE, treat the other 20 % as an unseen
       screening library, score and rank it, and measure enrichment against the known labels.
    2. Train a second model on *all* data and save it for the Streamlit app / new molecules.
    """
    Xfp = morgan_matrix(df["smiles"], cfg.fp_radius, cfg.fp_bits)
    y = df["label"].values
    seed = cfg.seeds[0]
    tr, te = stratified_split(df, cfg.test_size, seed)

    enc = QuantumEncoder(cfg.n_qubits, random_state=seed).fit(Xfp[tr])
    Xtr, Xte = enc.transform(Xfp[tr]), enc.transform(Xfp[te])
    qsvm, _ = fit_qsvm_tuned(Xtr, y[tr], cfg.feature_map, cfg.reps, cfg.c_grid, cfg.scale_grid, cfg.cv_folds, seed)
    svm, _ = fit_rbf_svm(Xtr, y[tr], cfg.c_grid, cfg.cv_folds, seed)
    pq, pc = qsvm.predict_proba(Xte)[:, 1], svm.predict_proba(Xte)[:, 1]

    ranked = rank_candidates(df.iloc[te], pq, cfg, p_classical=pc)
    ranked.to_csv(cfg.results_dir / "ranked_candidates.csv", index=False)

    yl, k = ranked["known_label"].values, cfg.top_k
    props = drug_likeness(df["smiles"])
    summary = dict(
        library_size=int(len(te)), base_hit_rate=float(y[te].mean()),
        top_k=k,
        precision_at_k_quantum_score=precision_at_k(y[te], pq, k),
        precision_at_k_final_score=float(yl[:k].mean()),
        precision_at_k_classical=precision_at_k(y[te], pc, k),
        ef10_quantum=enrichment_factor(y[te], pq, 0.10), ef10_classical=enrichment_factor(y[te], pc, 0.10),
        ef10_final_score=enrichment_factor(yl, ranked["final_score"].values, 0.10),
        actives_passing_lipinski=float(props.loc[y == 1, "passes_lipinski"].mean()),
        inactives_passing_lipinski=float(props.loc[y == 0, "passes_lipinski"].mean()),
        quantum_best_params=qsvm.best_params_,
    )
    log(f"[screen] hold-out library of {len(te)}: precision@{k} = {summary['precision_at_k_quantum_score']:.2f} "
        f"(base rate {summary['base_hit_rate']:.2f}), EF@10% = {summary['ef10_quantum']:.2f}")

    # deployment model on all labelled data
    enc_all = QuantumEncoder(cfg.n_qubits, random_state=seed).fit(Xfp)
    final, _ = fit_qsvm_tuned(enc_all.transform(Xfp), y, cfg.feature_map, cfg.reps, cfg.c_grid, cfg.scale_grid, cfg.cv_folds, seed)
    save_model(final, enc_all, cfg.models_dir / "qsvm_final.joblib",
               meta=dict(n_molecules=int(len(df)), n_qubits=cfg.n_qubits, feature_map=cfg.feature_map, reps=cfg.reps,
                         best_params=final.best_params_, trained=time.strftime("%Y-%m-%d")))
    svm_all, _ = fit_rbf_svm(enc_all.transform(Xfp), y, cfg.c_grid, cfg.cv_folds, seed)
    joblib.dump(svm_all, cfg.models_dir / "svm_final.joblib", compress=3)  # classical baseline for the app
    (cfg.results_dir / "screening_summary.json").write_text(json.dumps(summary, indent=2, default=float))
    return ranked, summary, (enc, qsvm, Xte, y[te])
