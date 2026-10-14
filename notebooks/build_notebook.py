"""Builds notebooks/QuantumScreen_Walkthrough.ipynb (run from the project root)."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
md = lambda t: nb.cells.append(nbf.v4.new_markdown_cell(t))
code = lambda t: nb.cells.append(nbf.v4.new_code_cell(t))

md("""# QuantumScreen - walkthrough
**Quantum computing-based drug screening for BACE-1 (Alzheimer's target) with Qiskit.**

This notebook runs the pipeline step by step: data -> fingerprints -> qubit encoding -> quantum kernel -> SVM ->
comparison with classical models -> candidate ranking -> VQE demo. The full benchmark (repeated seeds, ablations, VQC) is
produced by `python main.py`; see `results/` and `docs/RESULTS.md`.""")

code("""import sys, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, "../src")
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score, roc_curve
from quantumscreen.config import Config
from quantumscreen.data import load_bace, stratified_split
from quantumscreen.features import morgan_matrix, drug_likeness, QuantumEncoder
from quantumscreen.quantum import (build_feature_map, compute_states, fidelity_kernel, fit_qsvm_tuned)
from quantumscreen.classical import fit_rbf_svm, fit_random_forest
from quantumscreen.ranking import rank_candidates
cfg = Config()""")

md("## 1. Data\nBACE-1 inhibitors (MoleculeNet): SMILES + active/inactive label.")
code("""df = load_bace("../data/bace.csv")
print(len(df), "molecules;", f"{df.label.mean():.1%} active")
df.head()""")

md("## 2. Drug-likeness (RDKit)\nLipinski's rule of five and QED. Most molecules in this dataset already pass the rule, so it is used as a *soft* penalty in the ranking.")
code("""props = drug_likeness(df.smiles)
print("Pass Lipinski (<=1 violation): actives %.0f%%, inactives %.0f%%" % (
    100*props.loc[df.label==1, "passes_lipinski"].mean(), 100*props.loc[df.label==0, "passes_lipinski"].mean()))
props.groupby(df.label)[["MW", "LogP", "HBD", "HBA", "QED"]].mean().round(2)""")

md("## 3. Molecules to qubits\nMorgan fingerprint (2048 bits) -> PCA (8 components) -> rotation angles in [0, pi]; one component per qubit.")
code("""Xfp = morgan_matrix(df.smiles); y = df.label.values
tr, te = stratified_split(df, cfg.test_size, seed=0)
enc = QuantumEncoder(cfg.n_qubits).fit(Xfp[tr])
Xtr, Xte = enc.transform(Xfp[tr]), enc.transform(Xfp[te])
print("variance kept by 8 PCA components: %.1f%%" % (100*enc.pca_.explained_variance_ratio_.sum()))
print(Xtr[:2].round(2))""")

md("## 4. The quantum feature map\nA ZZ feature map: Hadamards, single-qubit Z rotations by the data, and entangling ZZ rotations between neighbours.")
code("""fm = build_feature_map("zz", cfg.n_qubits, reps=1)
fm.decompose().draw("mpl", fold=40, scale=0.6)""")

md("## 5. Quantum kernel\n`k(x, x') = |<phi(x)|phi(x')>|^2` (rows/columns sorted by class). The bright diagonal is each molecule compared with itself; off-diagonal brightness marks similar molecules. Most pairs are nearly orthogonal (dark) - a known 'kernel concentration' effect of high-dimensional quantum feature spaces, and the reason a small angle scale (0.25) is selected by cross-validation.")
code("""circuit = build_feature_map(cfg.feature_map, cfg.n_qubits, cfg.reps)
idx = np.random.default_rng(0).choice(len(Xte), 150, replace=False)
S = compute_states(circuit, Xte[idx] * 0.25)
K = fidelity_kernel(S, S); order = np.argsort(y[te][idx])
plt.imshow(K[np.ix_(order, order)], cmap="viridis"); plt.colorbar(); plt.title("Quantum kernel (inactives | actives)"); plt.show()""")

md("## 6. Train quantum kernel SVM vs classical baselines\n(C, scale) are tuned by inner cross-validation on the training split only.")
code("""qsvm, cv = fit_qsvm_tuned(Xtr, y[tr], cfg.feature_map, cfg.reps, cfg.c_grid, cfg.scale_grid, cfg.cv_folds, 0)
svm, _ = fit_rbf_svm(Xtr, y[tr], cfg.c_grid, cfg.cv_folds, 0)
rf = fit_random_forest(Xfp[tr], y[tr], 0)
scores = {"Quantum kernel SVM (ZZ, 8q)": qsvm.predict_proba(Xte)[:, 1],
          "Classical RBF SVM (PCA-8)": svm.predict_proba(Xte)[:, 1],
          "Random Forest (2048-bit FP)": rf.predict_proba(Xfp[te])[:, 1]}
print("best quantum params:", qsvm.best_params_)
for k, s in scores.items():
    fpr, tpr, _ = roc_curve(y[te], s); plt.plot(fpr, tpr, label=f"{k}  AUC={roc_auc_score(y[te], s):.3f}")
plt.plot([0, 1], [0, 1], "k:"); plt.legend(); plt.xlabel("FPR"); plt.ylabel("TPR"); plt.title("ROC, hold-out set"); plt.show()""")

md("## 7. Rank the hold-out library\n`final_score = 0.7*P(active) + 0.3*QED - penalty for Lipinski violations beyond one`.")
code("""ranked = rank_candidates(df.iloc[te], scores["Quantum kernel SVM (ZZ, 8q)"], cfg)
top = ranked.head(25)
print("hit-rate in top 25: %.0f%%  (library base rate %.0f%%)" % (100*top.known_label.mean(), 100*y[te].mean()))
ranked[["rank", "smiles", "known_label", "p_quantum_active", "QED", "lipinski_violations", "final_score"]].head(10)""")

md("## 8. Choose a diverse batch with QAOA\nA lab can advance only K of the shortlisted molecules. Maximise `J(x) = sum s_i x_i - lambda * sum S_ij x_i x_j` (score minus Tanimoto redundancy; no experimental affinity is used) subject to a budget of K, as a QUBO -> Ising Hamiltonian solved by QAOA, and compare with classical solvers.")
code("""from quantumscreen.selection import (SelectionProblem, tanimoto_matrix, solve_exact, solve_topk, solve_greedy_diverse, QAOASolver)
top = ranked.head(10)
prob = SelectionProblem(top.final_score.values, tanimoto_matrix(top.smiles), k=3, lam=0.5)
_, j_opt = solve_exact(prob)
res = QAOASolver(prob, p=2, restarts=3, maxiter=60, shots=1024, seed=0).run()
print(f"exact optimum J = {j_opt:.3f}")
print(f"top-K by score   : {solve_topk(prob)[1]/j_opt:.3f} of optimum")
print(f"greedy (diverse) : {solve_greedy_diverse(prob)[1]/j_opt:.3f}")
print(f"QAOA (p=2)       : {res['approx_ratio']:.3f}  | feasible probability mass {res['feasible_mass']:.2f}"
      f" | quality vs random feasible subsets {res['quality']/res['random_quality']:.3f} (1 = no better than random)")""")
md("Note the last number: QAOA's best sample is near-optimal, but its output distribution is no better than random sampling of feasible subsets (see `docs/RESULTS.md`).")

md("## 9. VQE demo (quantum chemistry)\nGround-state energy of H2 with a UCCSD ansatz on 2 qubits, compared with exact diagonalisation. Requires `qiskit-nature` and `pyscf`.")
code("""try:
    from quantumscreen.vqe import vqe_curve
    h2 = vqe_curve("H2", (0.5, 0.74, 1.0, 1.5, 2.0))
    display(h2.round(5))
except ImportError as e:
    print("VQE skipped (install requirements-vqe.txt):", e)""")

md("""## Conclusions
* The pipeline is fully reproducible and runs on a laptop CPU.
* Quantum-kernel SVM performance is **comparable to, not better than,** a tuned classical RBF SVM on the same 8 features.
* Entanglement did not help (the un-entangled `z` map scores the same as `zz`), and a Random Forest on the full fingerprint
  beats every model that sees only 8 PCA features: the bottleneck is the 2048 -> 8 compression, not the kernel.
* QAOA picks near-optimal diverse batches, but random search with the same shots does equally well.\n* VQE reproduces exact H2/LiH energies to well below chemical accuracy.""")

nbf.write(nb, "notebooks/QuantumScreen_Walkthrough.ipynb")
print("notebook written")
