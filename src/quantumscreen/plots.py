"""Figures for the report and README (matplotlib, saved as PNG)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve

QC, CC = "#6C3FC5", "#2A9D8F"   # quantum = purple, classical = teal
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10})


def _color(family):
    return QC if family == "quantum" else CC


def plot_main_comparison(runs: pd.DataFrame, path, cfg):
    d = runs[(runs.split == "random") & (runs.n_qubits.isna() | (runs.n_qubits == cfg.n_qubits))]
    is_q = d.family == "quantum"
    d = d[~is_q | ((d.feature_map == cfg.feature_map) & (d.reps == cfg.reps))]   # headline quantum model only
    g = d.groupby(["model", "family"])["auc"].agg(["mean", "std"]).reset_index().sort_values("mean")
    fig, ax = plt.subplots(figsize=(8, 3.4))
    ax.barh(g.model, g["mean"], xerr=g["std"], color=[_color(f) for f in g.family], capsize=3)
    for i, (m, s) in enumerate(zip(g["mean"], g["std"])):
        ax.text(m + s + 0.008, i, f"{m:.3f}", va="center", fontsize=9)
    ax.set_xlim(0.5, 1.0); ax.set_xlabel("ROC-AUC (mean +/- std over 3 seeds, random split)")
    ax.set_title("BACE-1 activity prediction: quantum vs classical")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def plot_roc(roc_store: dict, path, cfg):
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    headline_q = f"Quantum Kernel SVM ({cfg.feature_map}, reps={cfg.reps}, {cfg.n_qubits}q)"
    keep = [k for k in roc_store["scores"] if k == headline_q or k == f"Classical SVM (RBF, PCA-{cfg.n_qubits})"
            or "2048" in k]
    for k in keep:
        fpr, tpr, _ = roc_curve(roc_store["y_test"], roc_store["scores"][k])
        ax.plot(fpr, tpr, lw=2, color=QC if "Quantum" in k else (CC if "RBF" in k else "#999999"), label=k)
    ax.plot([0, 1], [0, 1], "k:", lw=1)
    ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate"); ax.legend(fontsize=7, loc="lower right")
    ax.set_title("ROC curves (hold-out test set, seed 0)")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def plot_qubit_ablation(runs: pd.DataFrame, path, cfg):
    d = runs[(runs.split == "random") & runs.n_qubits.notna()]
    q = d[(d.family == "quantum") & (d.feature_map == cfg.feature_map) & (d.reps == cfg.reps)]
    c = d[d.model.str.startswith("Classical SVM")]
    fig, ax = plt.subplots(figsize=(5.4, 3.8))
    for df_, lab, col in ((q, f"Quantum kernel SVM ({cfg.feature_map})", QC), (c, "Classical RBF SVM", CC)):
        g = df_.groupby("n_qubits")["auc"].agg(["mean", "std"]).reset_index()
        ax.errorbar(g.n_qubits, g["mean"], yerr=g["std"], marker="o", lw=2, capsize=3, color=col, label=lab)
    ax.set_xlabel("Number of qubits (= PCA components)"); ax.set_ylabel("ROC-AUC"); ax.legend(); ax.set_title("Effect of qubit count")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def plot_featuremap_ablation(runs: pd.DataFrame, path, cfg):
    d = runs[(runs.split == "random") & (runs.family == "quantum") & (runs.n_qubits == cfg.n_qubits)]
    g = d.groupby(["feature_map", "reps"])["auc"].agg(["mean", "std"]).reset_index()
    g["label"] = g.feature_map + " (r" + g.reps.astype(int).astype(str) + ")"
    g = g.sort_values("mean")
    fig, ax = plt.subplots(figsize=(5.8, 3.6))
    ax.barh(g.label, g["mean"], xerr=g["std"], color=QC, capsize=3)
    for i, m in enumerate(g["mean"]):
        ax.text(m + 0.012, i, f"{m:.3f}", va="center", fontsize=9)
    ax.set_xlim(0.5, 1.0); ax.set_xlabel("ROC-AUC"); ax.set_title(f"Feature-map ablation ({cfg.n_qubits} qubits)")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def plot_vqc(vqc_runs: pd.DataFrame, path):
    if vqc_runs.empty:
        return
    g = vqc_runs.groupby(["model", "family"])["auc"].agg(["mean", "std"]).reset_index().sort_values("mean")
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    ax.barh(g.model, g["mean"], xerr=g["std"], color=[_color(f) for f in g.family], capsize=3)
    for i, m in enumerate(g["mean"]):
        ax.text(m + 0.01, i, f"{m:.3f}", va="center", fontsize=9)
    ax.set_xlim(0.4, 1.0); ax.set_xlabel("ROC-AUC (small training set)"); ax.set_title("VQC vs quantum kernel vs classical (small data)")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def plot_scaffold(runs: pd.DataFrame, path, cfg):
    d = runs[runs.split.isin(["random", "scaffold"]) & (runs.n_qubits.isna() | (runs.n_qubits == cfg.n_qubits))]
    d = d[d.model.str.contains("Random Forest \\(2048|RBF|Quantum Kernel SVM \\(" + cfg.feature_map + ", reps=" + str(cfg.reps), regex=True)]
    g = d.groupby(["model", "split"])["auc"].mean().unstack("split")
    fig, ax = plt.subplots(figsize=(7.4, 3.4))
    x = np.arange(len(g)); w = 0.38
    ax.bar(x - w / 2, g["random"], w, label="random split", color="#B8A1E3")
    ax.bar(x + w / 2, g["scaffold"], w, label="scaffold split", color="#4B2A91")
    ax.set_xticks(x); ax.set_xticklabels([m.replace(" (", "\n(") for m in g.index], fontsize=8)
    ax.set_ylim(0.5, 1.0); ax.set_ylabel("ROC-AUC"); ax.legend(); ax.set_title("Random vs scaffold split (generalisation to new chemotypes)")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def plot_vqe(h2: pd.DataFrame, lih: pd.DataFrame, path):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    for ax, d, name in ((axes[0], h2, "H2"), (axes[1], lih, "LiH")):
        ax.plot(d.bond_length_A, d.E_hf, "--", color="#999999", label="Hartree-Fock")
        ax.plot(d.bond_length_A, d.E_exact, "-", color="black", lw=2, label="Exact (FCI)")
        ax.plot(d.bond_length_A, d.E_vqe, "o", color=QC, ms=6, label="VQE (UCCSD)")
        ax.set_title(f"{name} potential-energy curve ({int(d.n_qubits.iloc[0])} qubits)")
        ax.set_xlabel("Bond length (Angstrom)"); ax.set_ylabel("Energy (Hartree)"); ax.legend()
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def plot_kernel_heatmap(K: np.ndarray, y: np.ndarray, path):
    order = np.argsort(y, kind="stable")
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    im = ax.imshow(K[np.ix_(order, order)], cmap="viridis", vmin=0, vmax=1)
    n0 = int((y == 0).sum())
    ax.axhline(n0 - 0.5, color="white", lw=1); ax.axvline(n0 - 0.5, color="white", lw=1)
    ax.set_title("Quantum kernel matrix (inactives | actives)"); ax.set_xticks([]); ax.set_yticks([])
    fig.colorbar(im, ax=ax, fraction=0.046); fig.tight_layout(); fig.savefig(path); plt.close(fig)


def plot_top_candidates(ranked: pd.DataFrame, path, k=15):
    t = ranked.head(k).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    cols = [QC if lab == 1 else "#E76F51" for lab in t.known_label]
    ax.barh(t["rank"].astype(str), t.final_score, color=cols)
    ax.set_xlabel("Final score (quantum P(active) + QED - Lipinski penalty)"); ax.set_ylabel("Rank")
    ax.set_title(f"Top {k} ranked candidates  (purple = known active, orange = known inactive)")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def plot_selection(runs: pd.DataFrame, lam_table: pd.DataFrame, path, p_show: int = 3):
    """QAOA vs classical selection: solution quality vs N, and whether QAOA beats random sampling."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 3.9))
    ax = axes[0]
    style = {"Top-K by score": ("#E76F51", "s", "-"), "Greedy (diversity-aware)": (CC, "o", "-"),
             "Random feasible subset": ("#999999", "x", "--")}
    for m, (col, mk, ls) in style.items():
        g = runs[runs.method == m].groupby("N")["ratio"].mean()
        ax.plot(g.index, g.values, color=col, marker=mk, ls=ls, lw=2, label=m)
    q = runs[(runs.method.str.startswith("QAOA")) & (runs.p == p_show)]
    ax.plot(q.groupby("N")["ratio"].mean().index, q.groupby("N")["ratio"].mean().values, color=QC, marker="o", lw=2.5, label=f"QAOA p={p_show} (best of 1024 shots)")
    ax.plot(q.groupby("N")["random_search_ratio"].mean().index, q.groupby("N")["random_search_ratio"].mean().values, color="#4B2A91", marker="^", ls=":", lw=2, label="Random search (1024 shots)")
    ax.set_xlabel("Candidates N (= qubits)"); ax.set_ylabel("Objective / exact optimum"); ax.set_ylim(0.4, 1.03)
    ax.set_title("Solution quality (mean of pools)"); ax.legend(fontsize=7, loc="lower left")

    ax = axes[1]
    for p in sorted(runs[runs.p > 0].p.unique()):
        g = runs[(runs.p == p) & runs.method.str.startswith("QAOA")].assign(rel=lambda d: d.quality / d.random_quality).groupby("N")["rel"].mean()
        ax.plot(g.index, g.values, marker="o", lw=2, label=f"p={p}")
    ax.axhline(1.0, color="k", ls=":", lw=1)
    ax.set_xlabel("Candidates N (= qubits)"); ax.set_ylabel("QAOA output quality / random-feasible quality")
    ax.set_ylim(0.9, 1.1); ax.set_title("Does QAOA beat random sampling? (1 = no)"); ax.legend(fontsize=8)

    ax = axes[2]
    g = lam_table.groupby("lam").agg(r=("topk_ratio", "mean"), opt=("topk_is_optimal", "mean")).reset_index()
    ax.bar(g.lam.astype(str), g.r, color="#E76F51")
    for i, (r, o) in enumerate(zip(g.r, g.opt)):
        ax.text(i, r + 0.01, f"{r:.2f}\n(opt in {o:.0%})", ha="center", fontsize=8)
    ax.set_ylim(0.5, 1.12); ax.set_xlabel("Diversity weight lambda"); ax.set_ylabel("Top-K objective / exact optimum")
    ax.set_title("Top-K is optimal only at lambda = 0")
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def plot_selected_molecules(real: pd.DataFrame, meta: dict, path, methods=None, figsize=None, font=9, size=(320, 240)):
    """Grid of the molecules chosen by each selection method (one row per method)."""
    from rdkit import Chem
    from rdkit.Chem import Draw
    methods = methods or ["top-K by score", "diversity-aware exact", "QAOA"]
    k = int(real[methods[0]].sum())
    fig, axes = plt.subplots(len(methods), k, figsize=figsize or (2.6 * k, 2.5 * len(methods)), squeeze=False)
    for r, m in enumerate(methods):
        sel = real[real[m] == 1].head(k)
        for c in range(k):
            ax = axes[r, c]; ax.axis("off")
            if c < len(sel):
                row = sel.iloc[c]
                ax.imshow(Draw.MolToImage(Chem.MolFromSmiles(row.smiles), size=size))
                ax.set_title(f"rank {int(row['rank'])}  s={row.final_score:.2f}", fontsize=font + 1)
        axes[r, 0].text(-0.05, 0.5, f"{m}\nJ={meta[m]['objective']:.2f}\nmean sim={meta[m]['mean_pairwise_similarity']:.2f}",
                        transform=axes[r, 0].transAxes, ha="right", va="center", fontsize=font + 2, fontweight="bold")
    fig.subplots_adjust(left=0.2, wspace=0.05, hspace=0.2); fig.savefig(path, bbox_inches="tight"); plt.close(fig)
