# Methodology

## 1. Problem statement

> Develop a Quantum Computing-based Drug Screening System to identify promising drug candidates.

**Virtual screening** ranks a large library of molecules by how likely each is to bind a disease target, so that
only the best few need expensive laboratory testing. We target **BACE-1** (beta-secretase 1), an enzyme involved in
amyloid-beta formation in Alzheimer's disease, and use quantum machine learning to score candidates.

## 2. Dataset

MoleculeNet **BACE**: 1513 inhibitors with a binary label (active / inactive, based on a potency threshold of roughly
IC50 = 100 nM, i.e. pIC50 = 7) and the measured pIC50. All inactives have pIC50 < 7, but a small number of actives
in the published file have a lower recorded pIC50; we keep the dataset's own labels unchanged. After RDKit validation,
canonicalisation and de-duplication all 1513 molecules are kept (45.7 % active).

## 3. Molecular representation

1. **Morgan fingerprint** (radius 2, 2048 bits): a binary vector marking which circular substructures appear in the molecule.
2. **PCA** reduces 2048 dimensions to *n* components (default 8), because each feature needs one qubit and
   near-term simulation is limited to a few qubits.
3. **Angle scaling**: each component is min-max scaled to [0, pi] so it can be used as a rotation angle.
   PCA and scaler are fitted on training data only.

## 4. Quantum kernel method (the core)

A **feature map** is a parameterised circuit `U(x)` that loads a data vector `x` into a quantum state
`|phi(x)> = U(x)|0...0>`. Two molecules are compared by the **fidelity kernel**

    k(x, x') = | <phi(x) | phi(x')> |^2   (a number in [0, 1])

which is 1 for identical states. The resulting Gram matrix is positive semi-definite, so it can be used by a
standard support-vector machine (the idea behind Qiskit's `QSVC`). The model therefore computes similarity in a
Hilbert space of dimension 2^n, which classical kernels cannot access directly in general.

Feature maps compared (all from `qiskit.circuit.library`):

| Name | Circuit | Entanglement |
|---|---|---|
| `z` | H + Z-rotation per qubit | none (control experiment) |
| `zz` | H, `P(2x_i)` and `CX-P(2(pi-x_i)(pi-x_j))-CX` between neighbours | linear |
| `zz_full` | same as `zz` | all pairs |
| `pauli_yzz` | Pauli feature map with Y and ZZ terms | linear |

**Simulation.** Circuits are simulated exactly with `qiskit.quantum_info.Statevector`. Each sample's state is
computed once and the kernel matrix is `abs(S_A^dagger-conjugate · S_B^T)^2`. This equals the sampler-based
`FidelityQuantumKernel` for an ideal, noiseless device (checked in the tests). On real hardware the kernel entries would be
estimated from finite measurement shots and would be affected by noise.

**Training.** An SVM with a precomputed kernel is fitted; `C` and a bandwidth `scale` (multiplying the angles) are
chosen by 3-fold stratified cross-validation (ROC-AUC) on the training split only. Probabilities come from Platt scaling.

## 5. Variational Quantum Classifier (VQC)

Qiskit Machine Learning's `VQC`: ZZ feature map (1 repetition) followed by a trainable `RealAmplitudes` ansatz
(2 repetitions), optimised with COBYLA to minimise cross-entropy. The class probability is read from the measured
output distribution. Because each optimiser step evaluates every training circuit, VQC is trained on a small
balanced subset (`vqc_train_size`) and compared with the quantum-kernel SVM and the classical SVM on that same subset.

## 6. Classical baselines

* **RBF-SVM** on the same PCA angles (C and gamma tuned by the same inner CV) - the fairest like-for-like baseline.
* **Random Forest** on the same PCA features, and on the full 2048-bit fingerprint (a strong, uncompressed reference).

## 7. Evaluation protocol

| Item | Choice |
|---|---|
| Random split | 80/20 stratified, repeated for 3 seeds (mean +/- std reported) |
| Scaffold split | Bemis-Murcko scaffold split, 80/20: test molecules have chemotypes not seen in training |
| Metrics | ROC-AUC (primary), accuracy, precision, recall, F1, **enrichment factor at 10 %** (EF10) |
| Ablations | number of qubits (4, 6, 8, 10); feature map (z, zz r1, zz r2, zz_full, pauli_yzz) |

**Enrichment factor** is the standard virtual-screening metric: the hit-rate among the top-ranked 10 % divided by the
overall hit-rate. EF = 1 means the ranking is no better than random.

## 8. Candidate ranking

The held-out 20 % of molecules is treated as an unseen screening library. Each is scored

    final_score = 0.7 · P_quantum(active) + 0.3 · QED − 0.10 · max(0, Lipinski_violations − 1)

where **QED** is RDKit's quantitative estimate of drug-likeness (0-1) and Lipinski violations count breaches of the
rule of five (MW > 500, logP > 5, HBD > 5, HBA > 10). Weights are configurable in `Config`. No experimental affinity (pIC50) enters the score, so the ranking never uses information that would be unknown for a genuinely new molecule.
Because the dataset provides true labels, ranking quality is *validated* with precision@25 and EF10.

## 9. Candidate selection with QAOA

After ranking, a laboratory can advance only K of N shortlisted molecules. Choosing a batch that is individually promising *and* mutually
dissimilar (so one failed chemotype does not sink the batch) is a quadratic binary optimisation problem:

    maximise  J(x) = Σ_i s_i x_i − λ Σ_{i<j} S_ij x_i x_j      subject to  Σ_i x_i = K,   x_i ∈ {0, 1}

`s_i` is the molecule's screening score (quantum P(active), QED, Lipinski penalty - **no experimental pIC50 is used**, which would leak the answer) and `S_ij` the Tanimoto
similarity of Morgan fingerprints. Without the pairwise term the problem is solved exactly by sorting; with it, sorting is generally *not* optimal (tested).

**QUBO and Ising mapping.** The budget is embedded as a penalty, `E(x) = −J(x) + A (Σ x_i − K)²`, with `A = 2 (max s + λ max S)`. Substituting `x_i = (1 − Z_i)/2` gives
`H_C = Σ h_i Z_i + Σ_{i<j} J_ij Z_i Z_j + const` with `h_i = −a_i/2 − Σ_j b_ij/4` and `J_ij = b_ij/4`, where `a_i = −s_i + A(1 − 2K)` and `b_ij = λ S_ij + 2A`.
The code checks that the eigenvalue of `H_C` on every basis state equals the QUBO energy (error ~1e-14).

**QAOA circuit (Qiskit).** |+⟩^N, then p layers of cost unitary (`RZ(2γh_i)`, `RZZ(2γJ_ij)`) and mixer (`RX(2β)`). Energies are rescaled to unit range so that angles are comparable.
Parameters are optimised by COBYLA (3 random restarts, 60 iterations) on the exact statevector expectation `⟨H_C⟩`; the answer is the best *feasible* bitstring among 1024 samples
(greedy repair if none is feasible). The circuit is verified against exact matrix evolution in `tests/test_selection.py`.

**Classical comparators.** score-only top-K; diversity-aware greedy (sequential marginal gain); exact enumeration (feasible subsets only); random feasible subsets; random search with the same number of shots.

**Evaluation.** 8 random shortlists per size N ∈ {8, 10, 12, 14} drawn from the 40 best-ranked hold-out molecules. Metrics: objective / exact optimum; feasible probability mass; probability of the optimal subset;
and the *quality of QAOA's whole output distribution relative to random feasible subsets* (1 = no better than random). The last metric is the honest test, because with only 56-1001 feasible subsets "best of 1024 shots" is
easily matched by random search. A λ-sweep confirms that top-K is optimal only when λ = 0.

## 10. VQE module (quantum chemistry)

The Variational Quantum Eigensolver finds a molecule's ground-state energy by minimising `<psi(theta)|H|psi(theta)>`
over circuit parameters, using a **UCCSD** ansatz started from the Hartree-Fock state. Molecules are described in the
STO-3G basis (PySCF), mapped to qubits with the parity mapper (+ two-qubit reduction): **H2 → 2 qubits**,
**LiH → 4 qubits** (1s core frozen, two non-bonding orbitals removed). VQE energies are compared against exact diagonalisation
(FCI in the same active space) and Hartree-Fock across bond lengths, using chemical accuracy (1.6 mHa) as the yardstick.

This module shows how quantum computers could eventually compute binding energies; it is a *demonstration* on
tiny molecules and is not coupled numerically to the BACE classifier.

## 11. References

1. Havlicek et al., "Supervised learning with quantum-enhanced feature spaces", *Nature* 567 (2019).
2. Peruzzo et al., "A variational eigenvalue solver on a photonic quantum processor", *Nat. Commun.* 5 (2014).
3. Wu et al., "MoleculeNet: a benchmark for molecular machine learning", *Chem. Sci.* 9 (2018).
4. Subramanian et al., "Computational modeling of beta-secretase 1 (BACE-1) inhibitors using ligand based approaches", *J. Chem. Inf. Model.* 56 (2016).
5. Bickerton et al., "Quantifying the chemical beauty of drugs" (QED), *Nat. Chem.* 4 (2012).
6. Qiskit, Qiskit Machine Learning, Qiskit Nature documentation: https://qiskit.org
