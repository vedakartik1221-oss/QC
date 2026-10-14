#!/usr/bin/env python
"""QuantumScreen command-line entry point.

Examples
--------
    python main.py                     # full pipeline (about 20-30 min on a laptop CPU)
    python main.py --quick             # fast smoke run (about 2-3 min)
    python main.py --stage vqe         # only the VQE module
    python main.py --stage benchmark   # only the benchmark + figures
    python main.py --no-vqc            # skip the (slow) variational classifier
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import numpy as np
import pandas as pd

from quantumscreen import plots
from quantumscreen.benchmark import run_all, summarise
from quantumscreen.config import Config
from quantumscreen.data import load_bace, stratified_split
from quantumscreen.features import QuantumEncoder, morgan_matrix
from quantumscreen.pipeline import final_screen
from quantumscreen.quantum import build_feature_map, compute_states, fidelity_kernel


def main():
    ap = argparse.ArgumentParser(description="QuantumScreen: hybrid quantum drug screening on BACE-1")
    ap.add_argument("--stage", choices=["all", "benchmark", "screen", "select", "vqe", "figures"], default="all")
    ap.add_argument("--data", type=Path, default=None, help="path to bace.csv (columns: mol, Class)")
    ap.add_argument("--qubits", type=int, default=None)
    ap.add_argument("--max-molecules", type=int, default=None)
    ap.add_argument("--seeds", type=int, nargs="+", default=None)
    ap.add_argument("--no-vqc", action="store_true", help="skip the variational quantum classifier")
    ap.add_argument("--no-vqe", action="store_true", help="skip the VQE module (needs PySCF)")
    ap.add_argument("--quick", action="store_true", help="small, fast configuration for smoke-testing")
    args = ap.parse_args()

    cfg = Config()
    if args.data: cfg.data_path = args.data
    if args.qubits: cfg.n_qubits = args.qubits
    if args.max_molecules: cfg.max_molecules = args.max_molecules
    if args.seeds: cfg.seeds = tuple(args.seeds)
    if args.quick:
        cfg.max_molecules, cfg.seeds = 400, (0,)
        cfg.qubit_ablation, cfg.feature_map_ablation = (4, 8), (("zz", 2), ("z", 2))
        cfg.c_grid, cfg.scale_grid = (1.0, 10.0), (0.25, 0.5)
        cfg.vqc_train_size, cfg.vqc_maxiter = 60, 20
        cfg.sel_sizes, cfg.sel_p, cfg.sel_pools, cfg.sel_restarts, cfg.sel_maxiter = (8, 10), (1, 2), 2, 2, 30
        cfg.h2_bond_lengths, cfg.lih_bond_lengths = (0.5, 0.74, 1.5), (1.0, 1.6, 3.0)
        cfg.results_dir = cfg.results_dir.parent / "results_quick"
        cfg.models_dir = cfg.models_dir.parent / "models_quick"   # never overwrite the real models
    cfg.ensure_dirs()
    fig_dir = cfg.results_dir / "figures"
    t0 = time.time()
    log = lambda m: print(f"[{time.time() - t0:7.1f}s] {m}", flush=True)

    df = load_bace(cfg.data_path, cfg.max_molecules)
    log(f"loaded {len(df)} molecules ({df.label.mean():.1%} active)")

    if args.stage in ("all", "benchmark", "figures"):
        if args.stage == "figures":
            runs = pd.read_csv(cfg.results_dir / "benchmark_runs.csv")
            vqc_runs = pd.read_csv(cfg.results_dir / "vqc_runs.csv")
            from quantumscreen.benchmark import run_split
            Xfp = morgan_matrix(df["smiles"], cfg.fp_radius, cfg.fp_bits)
            tr, te = stratified_split(df, cfg.test_size, cfg.seeds[0])
            _, scores = run_split(Xfp, df["label"].values, tr, te, cfg, cfg.seeds[0], "random", full=False)
            roc_store = dict(y_test=df["label"].values[te], scores=scores)
        else:
            runs, vqc_runs, roc_store = run_all(df, cfg, log, run_vqc=not args.no_vqc)
            runs.to_csv(cfg.results_dir / "benchmark_runs.csv", index=False)
            vqc_runs.to_csv(cfg.results_dir / "vqc_runs.csv", index=False)
            summarise(runs).to_csv(cfg.results_dir / "benchmark_summary.csv", index=False)
            if len(vqc_runs):
                summarise(vqc_runs, ("split", "model", "family")).to_csv(cfg.results_dir / "vqc_summary.csv", index=False)
        plots.plot_main_comparison(runs, fig_dir / "01_model_comparison.png", cfg)
        plots.plot_qubit_ablation(runs, fig_dir / "03_qubit_ablation.png", cfg)
        plots.plot_featuremap_ablation(runs, fig_dir / "04_featuremap_ablation.png", cfg)
        plots.plot_scaffold(runs, fig_dir / "05_scaffold_split.png", cfg)
        plots.plot_vqc(vqc_runs, fig_dir / "06_vqc_comparison.png")
        if roc_store is not None:
            plots.plot_roc(roc_store, fig_dir / "02_roc_curves.png", cfg)
        log("benchmark + figures done")

    if args.stage in ("all", "screen"):
        ranked, summary, (enc, qsvm, Xte, yte) = final_screen(df, cfg, log)
        plots.plot_top_candidates(ranked, fig_dir / "07_top_candidates.png")
        sub = np.arange(min(150, len(Xte)))
        S = compute_states(build_feature_map(cfg.feature_map, cfg.n_qubits, cfg.reps), Xte[sub] * qsvm.scale)
        plots.plot_kernel_heatmap(fidelity_kernel(S, S), yte[sub], fig_dir / "08_kernel_matrix.png")
        log("screening + ranking done")

    if args.stage in ("all", "select"):
        from quantumscreen import selection
        ranked_path = cfg.results_dir / "ranked_candidates.csv"
        if not ranked_path.exists():
            final_screen(df, cfg, log)
        ranked = pd.read_csv(ranked_path)
        runs_s, lam_t = selection.run_selection_study(ranked, cfg, log)
        runs_s.to_csv(cfg.results_dir / "selection_runs.csv", index=False)
        lam_t.to_csv(cfg.results_dir / "selection_lambda.csv", index=False)
        summ = runs_s.groupby(["method", "p", "N"]).agg(ratio=("ratio", "mean"), ratio_std=("ratio", "std"), quality=("quality", "mean"),
                                                        random_quality=("random_quality", "mean"), feasible_mass=("feasible_mass", "mean"),
                                                        p_optimal=("p_optimal", "mean"), random_search_ratio=("random_search_ratio", "mean"),
                                                        runtime=("runtime", "mean")).reset_index()
        summ.to_csv(cfg.results_dir / "selection_summary.csv", index=False)
        real, meta, prob, res = selection.real_case(ranked, cfg, n=max(cfg.sel_sizes[:3]), p=max(cfg.sel_p))
        real.to_csv(cfg.results_dir / "selected_diverse_candidates.csv", index=False)
        (cfg.results_dir / "selection_real_case.json").write_text(json.dumps(meta, indent=2))
        plots.plot_selection(runs_s, lam_t, fig_dir / "11_qaoa_selection.png", p_show=max(cfg.sel_p))
        plots.plot_selected_molecules(real, meta, fig_dir / "12_selected_molecules.png")
        log("QAOA selection done")

    if args.stage in ("all", "vqe") and not args.no_vqe:
        try:
            from quantumscreen.vqe import vqe_curve
        except ImportError as e:   # qiskit-nature / PySCF are optional extras
            log(f"VQE skipped ({e}). To enable it: pip install -r requirements-vqe.txt "
                "(PySCF has no Windows wheels: use WSL2 or Colab). Or pass --no-vqe to silence this.")
        else:
            h2 = vqe_curve("H2", cfg.h2_bond_lengths); lih = vqe_curve("LiH", cfg.lih_bond_lengths)
            h2.to_csv(cfg.results_dir / "vqe_h2.csv", index=False); lih.to_csv(cfg.results_dir / "vqe_lih.csv", index=False)
            plots.plot_vqe(h2, lih, fig_dir / "09_vqe_curves.png")
            log(f"VQE done: max error H2 {h2.error_mHa.max():.4f} mHa, LiH {lih.error_mHa.max():.4f} mHa")
    log("all done")


if __name__ == "__main__":
    main()
