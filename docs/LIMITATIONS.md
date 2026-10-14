# Limitations and future work

## Limitations (please state these in your viva)

1. **Simulation, not hardware.** Every circuit is simulated classically with exact statevectors. No quantum speed-up is
   measured or claimed. Real devices add noise and shot-noise in the kernel estimate, which typically lowers accuracy.
2. **No quantum advantage on this task.** The quantum kernel performs the same as a tuned classical RBF kernel on the
   same 8 PCA features (ROC-AUC about 0.87 vs 0.88, within one standard deviation; see `docs/RESULTS.md`). Information is lost when 2048
   fingerprint bits are compressed to 8 components: a Random Forest on the full fingerprint scores clearly higher (0.916).
   The quantum kernel is also ~2.5x slower to fit here, because it is simulated.
3. **Tiny feature space.** One qubit per PCA component limits the encoding to 4-10 qubits. Exact simulation cost grows as 2^n.
4. **Dataset scale and scope.** BACE has 1513 molecules for a single target; the results do not show that the system
   generalises to other targets or to genuinely novel chemistry (the scaffold split is a first step towards that).
5. **Ligand-based only.** Scores come from molecular similarity to known actives, not from modelling the protein-ligand
   binding physics (no docking, no free-energy calculation).
6. **Label noise.** "Active" is a pIC50 threshold on literature data merged from many assays.
7. **VQE is a demonstration.** H2 and LiH are far smaller than any drug molecule; VQE is not linked to the screening classifier.
8. **QAOA gives no advantage here.** Up to 14 qubits are simulated exactly; the search spaces (56 to 1001 feasible subsets) are trivial for classical enumeration, and random search with the same 1024 shots matches QAOA's best sample.
   QAOA's output distribution is no better than random sampling of feasible subsets. The budget is enforced by a penalty, so only about 22-52 % of QAOA's probability mass is feasible; the optimiser budget was small (3 restarts, 60 COBYLA iterations, p ≤ 3).
9. **The selection objective is a modelling choice.** The weight lambda and the Tanimoto-based redundancy term are heuristic and not validated against wet-lab outcomes.
10. **Platt-scaled probabilities** are approximate and the combined ranking weights (0.7 / 0.3 / 0.1) are heuristic.

## Future work

* Run the best circuits on real hardware (IBM Quantum) with error mitigation, and quantify the noise penalty.
* Use `qiskit-aer` noise models to study robustness; compare finite-shot kernel estimation.
* Constraint-preserving XY mixers with Dicke-state initialisation and warm-started QAOA for the selection stage; larger N with tensor-network simulators or hardware.
* Quantum-kernel *alignment* / trainable feature maps; data re-uploading classifiers.
* Replace PCA with a learned low-dimensional embedding (e.g. autoencoder) before the quantum layer.
* Add a docking/MM-GBSA stage and use VQE-computed fragment energies to re-rank the top candidates.
* Larger benchmarks (other MoleculeNet targets, DUD-E) and statistical significance testing across more seeds.
