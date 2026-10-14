# ⚛️ QuantumScreen: Comprehensive System Architecture, Methodology & Limitations

## Executive Overview

**QuantumScreen** is an end-to-end, hybrid quantum-classical virtual screening pipeline designed for computational drug discovery. Created as a capstone project in Quantum Computing by **G Veda Kartik** (Amrita Vishwa Vidyapeetham), the system investigates whether near-term quantum algorithms (specifically **Quantum Kernel Methods**, **Variational Quantum Classifiers (VQC)**, **Quantum Approximate Optimization Algorithm (QAOA)**, and the **Variational Quantum Eigensolver (VQE)**) provide demonstrable computational or predictive value in identifying drug candidates against **BACE-1** ($\beta$-secretase 1), a primary enzymatic drug target in Alzheimer's disease.

The project is built on **Qiskit 2.5**, **Qiskit Machine Learning 0.9**, **Qiskit Nature 0.8**, **Qiskit Algorithms 0.4**, **RDKit**, and **scikit-learn**. Crucially, QuantumScreen embraces **scientific rigor and honest benchmarking**: rather than making unsubstantiated claims of quantum supremacy, it establishes strict parity baselines against classical machine learning (RBF Support Vector Machines and Random Forests), quantifies information loss, and evaluates whether quantum techniques deliver an actual advantage over classical algorithms on noisy or simulated regimes.

---

## High-Level System Architecture & Workflow

```
                        [ Molecule SMILES Strings ]
                                    │
                                    ▼
                         [ Data Preprocessing ]
                  (RDKit canonicalisation, deduplication)
                                    │
               ┌────────────────────┴────────────────────┐
               ▼                                         ▼
      [ Stratified Split ]                      [ Scaffold Split ]
  (Random splits across 3 seeds)          (Bemis-Murcko scaffold clusters)
               │                                         │
               └────────────────────┬────────────────────┘
                                    ▼
                         [ Feature Engineering ]
                 Morgan Fingerprints (Radius 2, 2048 bits)
                                    │
                 PCA Compression (2048 bits -> 8 components)
                                    │
                   Min-Max Scaled to Angles in [0, π]
                                    │
       ┌────────────────────────────┼────────────────────────────┐
       ▼                            ▼                            ▼
[ Quantum Kernel SVM ]    [ Classical RBF-SVM ]        [ Classical Random Forest ]
Qiskit Feature Map        scikit-learn RBF kernel      Full 2048-bit & 8-PCA
Statevector Fidelity Gram  (C, γ tuned via CV)          (Uncompressed reference)
(C, scale tuned via CV)             │                            │
       │                            │                            │
       └────────────────────────────┼────────────────────────────┘
                                    ▼
                         [ Molecular Scoring ]
                Predicted Probability of Activity: P(active)
                                    │
                                    ▼
                         [ Candidate Ranking ]
         Multi-objective: 0.7·P(active) + 0.3·QED - Lipinski Penalty
                                    │
                                    ▼
                     [ Top Shortlist of Candidates ]
                                    │
                                    ▼
               [ Diversity-Aware Combinatorial Selection ]
                     Formulate as QUBO on Top Candidates:
             Max J(x) = ∑ s_i x_i - λ ∑ S_ij x_i x_j  s.t. ∑ x_i = K
            (Balancing potency score s_i against Tanimoto redundancy S_ij)
                                    │
                     Ising Hamiltonian H_C Translation
                                    │
       ┌────────────────────────────┴────────────────────────────┐
       ▼                                                         ▼
[ QAOA Circuit (Qiskit) ]                                 [ Classical Solvers ]
p layers of (RZ, RZZ) + RX mixer                         - Exact Enumeration
Optimized via classical COBYLA                            - Diversity-Aware Greedy
Feasible bitstring sampling                               - Score-only Top-K
       │                                                         │
       └────────────────────────────┬────────────────────────────┘
                                    ▼
                    [ Final Batch of Diverse Leads ]

─────────────────────────────────────────────────────────────────────────────
[ Quantum Chemistry Module (Parallel Demonstration) ]
Variational Quantum Eigensolver (VQE) with UCCSD ansatz on H2 and LiH
Validating ground-state potential energy curves against exact FCI & Hartree-Fock.
```

---

## Detailed Component Breakdown

### 1. Data Layer (`src/quantumscreen/data.py`)
- **Dataset**: MoleculeNet BACE dataset comprising 1,513 curated inhibitors of human $\beta$-secretase 1. Active vs. inactive classification is defined around an inhibitory potency threshold ($IC_{50} \approx 100\text{ nM}$, i.e., $pIC_{50} \approx 7.0$). Overall active base rate is **45.7%** (691 actives, 822 inactives).
- **Validation & Cleaning**:
  - `load_bace()` parses SMILES strings using RDKit (`Chem.MolFromSmiles`), converts them to canonical SMILES (`Chem.MolToSmiles`), strips duplicates, drops invalid structures, and converts class labels to integers.
- **Data Splitting Strategies**:
  - `stratified_split()`: Generates stratified random 80/20 train/test splits preserving label balance. Evaluated across seeds `(0, 1, 2)` to compute statistical deviations ($\text{mean} \pm \text{std}$).
  - `scaffold_split()`: Implements deterministic Bemis-Murcko molecular scaffold clustering. Molecules sharing core rings and linkers are grouped; the largest clusters are placed in training, and rarer chemotypes are relegated to testing. This tests **out-of-distribution generalisation** to novel chemical scaffolds.

### 2. Feature Extraction & Encoding (`src/quantumscreen/features.py`)
- **Morgan Molecular Fingerprints**:
  - Extracted via RDKit's `rdFingerprintGenerator` at radius 2 (equivalent to ECFP4) with 2,048 bits. Represents circular atom environments and functional groups.
- **Dimensionality Reduction (`QuantumEncoder`)**:
  - Qubits are an extremely constrained resource in quantum simulators and physical quantum hardware. Encoding 2,048 features directly would require 2,048 qubits or deep data re-uploading circuits.
  - Principal Component Analysis (PCA) reduces the 2,048-dimensional sparse fingerprint into $n$ orthogonal components (default: $n=8$ qubits).
  - **Leakage Prevention**: PCA is fitted strictly on the *training set* only (`fit()`); test sets are transformed and clipped.
  - **Angle Mapping**: Component values are min-max normalised into $[0, \pi]$ rotation angles, matching the parameterised input domain of quantum single-qubit rotation gates.
- **Drug-Likeness Profiling (`drug_likeness()`)**:
  - Computes Molecular Weight (MW), Wildman-Crippen lipophilicity ($\log P$), Hydrogen Bond Donors (HBD), Hydrogen Bond Acceptors (HBA), Topological Polar Surface Area (TPSA), and Rotatable Bonds.
  - Computes Bickerton's Quantitative Estimate of Drug-likeness (**QED** $\in [0, 1]$).
  - Evaluates Lipinski's Rule of Five violations: $\text{MW} > 500$, $\log P > 5$, $\text{HBD} > 5$, $\text{HBA} > 10$.

### 3. Quantum Machine Learning & Statevector Kernels (`src/quantumscreen/quantum.py`)
- **Quantum Feature Maps**:
  Constructs parameterised quantum circuits $U(\mathbf{x})$ that map classical vectors $\mathbf{x} \in [0, \pi]^n$ into quantum statevectors $|\phi(\mathbf{x})\rangle = U(\mathbf{x})|0^{\otimes n}\rangle$. Supports four families:
  1. `z`: First-order Pauli-Z rotations preceded by Hadamard gates. **Zero entanglement**. Serves as an unentangled classical control.
  2. `zz`: Second-order Pauli-Z expansion with nearest-neighbour (linear) CNOT entanglement:
     $$U_{\Phi}(\mathbf{x}) = \exp\left(i \sum_j x_j Z_j + \sum_{\langle j, k \rangle} (\pi - x_j)(\pi - x_k) Z_j Z_k\right)$$
  3. `zz_full`: Second-order expansion with all-to-all entanglement between all qubit pairs.
  4. `pauli_yzz`: Alternating single-qubit Y-rotations and pairwise ZZ interactions.
- **Exact Statevector Fidelity Kernel**:
  - The fidelity quantum kernel is defined as transition probability in $2^n$-dimensional Hilbert space:
    $$k(\mathbf{x}, \mathbf{x}') = |\langle \phi(\mathbf{x}) | \phi(\mathbf{x}') \rangle|^2$$
  - **Algorithmic Optimisation**: Standard Qiskit `FidelityQuantumKernel` evaluates $N(N-1)/2$ separate overlap circuits. QuantumScreen computes each statevector $|\phi(\mathbf{x}_i)\rangle$ once ($O(N)$ circuit evaluations) and executes matrix multiplication:
    $$K = |\mathbf{S} \mathbf{S}^\dagger|^2$$
    This is mathematically equivalent to machine precision ($\approx 10^{-12}$) and cuts execution time from hours to seconds.
- **Quantum Kernel SVM (`QuantumKernelSVM`)**:
  - Wraps scikit-learn's `SVC(kernel="precomputed")`. Uses an additional bandwidth hyperparameter `scale` ($\mathbf{x} \leftarrow \mathbf{x} \cdot \text{scale}$) that controls kernel sharpness and combats **quantum kernel concentration** (the tendency of random Haar states to become orthogonal as $n$ grows).
  - `fit_qsvm_tuned()` conducts 3-fold inner cross-validation across a grid of $(C, \text{scale})$ strictly within the training fold.
  - Predicts well-calibrated class probabilities $P(\text{active})$ via Platt scaling (logistic sigmoid fit on decision values).
- **Variational Quantum Classifier (`train_vqc()`)**:
  - Utilises Qiskit ML's `VQC` with a `ZZFeatureMap` and a parameterised `RealAmplitudes` ansatz ($RY$ rotations and circular CNOT entanglers).
  - Trained via gradient-free COBYLA optimiser on one-hot categorical cross-entropy loss.

### 4. Classical Benchmarks (`src/quantumscreen/classical.py`)
- **Classical RBF-SVM**: Support Vector Classifier with radial basis function kernel $k(\mathbf{x}, \mathbf{x}') = \exp(-\gamma \|\mathbf{x} - \mathbf{x}'\|^2)$. Tuned using the exact same inner cross-validation grid for $C$ and $\gamma$. It operates on the identical 8 PCA features to isolate the algorithmic effect of the quantum kernel from data representation differences.
- **Classical Random Forest**: Ensemble of 300 decision trees evaluated on:
  1. The compressed 8 PCA features.
  2. The full, uncompressed 2,048-bit Morgan fingerprint.

### 5. Multi-Objective Ranking (`src/quantumscreen/ranking.py`, `src/quantumscreen/pipeline.py`)
- The hold-out library is scored using a multi-parameter objective function:
  $$\text{Score}(\mathbf{x}) = w_{\text{activity}} \cdot P_{\text{quantum}}(\text{active}) + w_{\text{QED}} \cdot \text{QED} - \text{penalty} \cdot \max(0, \text{Lipinski Violations} - 1)$$
  Default weights: $w_{\text{activity}} = 0.7$, $w_{\text{QED}} = 0.3$, $\text{penalty} = 0.10$.
- **Design Rationale**:
  - Avoids hard thresholding: molecules violating 1 Lipinski rule are tolerated without penalty; molecules violating 2+ are penalised softly.
  - **No target affinity leakage**: Ground-truth experimental $pIC_{50}$ values are never used during scoring, ensuring realistic virtual screening conditions.

### 6. Combinatorial Diversity Selection via QAOA (`src/quantumscreen/selection.py`)
- **Problem Formulation**:
  Virtual screening cannot advance all top-scoring compounds. A medicinal chemistry campaign selects a diverse subset of $K$ candidates out of $N$ shortlisted compounds so that structural duplicates (which might fail simultaneously due to off-target toxicity or poor bioavailability) do not monopolise the budget.
  $$\max_{\mathbf{x} \in \{0, 1\}^N} J(\mathbf{x}) = \sum_{i=1}^N s_i x_i - \lambda \sum_{i < j} S_{ij} x_i x_j \quad \text{subject to} \quad \sum_{i=1}^N x_i = K$$
  where $s_i$ is compound $i$'s screening score, $S_{ij} \in [0, 1]$ is the pairwise Tanimoto similarity of Morgan fingerprints, and $\lambda = 0.5$ balances potency against structural redundancy.
- **QUBO & Ising Hamiltonian Mapping**:
  - The cardinality constraint $\sum x_i = K$ is embedded via quadratic penalty $A (\sum x_i - K)^2$, where $A = 2 (\max s + \lambda \max S)$ guarantees that violating the budget is never advantageous.
  - Variables are transformed to Pauli-Z operators via $x_i = \frac{I - Z_i}{2}$, producing the Ising Hamiltonian:
    $$H_C = \sum_{i=1}^N h_i Z_i + \sum_{i < j} J_{ij} Z_i Z_j + \text{const}$$
- **QAOA Circuit & Optimisation (`QAOASolver`)**:
  - State prepared in uniform superposition $|+\rangle^{\otimes N}$.
  - Alternates $p$ layers of cost operator $e^{-i \gamma_l H_C}$ and transverse-field mixer $e^{-i \beta_l \sum X_i}$.
  - Variational parameters $\boldsymbol{\gamma}, \boldsymbol{\beta}$ are optimised using classical COBYLA (3 restarts, 60 iterations).
  - 1,024 shots are sampled from the final statevector; the best feasible bitstring is selected (with a greedy repair heuristic fallback).
- **Comparative Solvers**:
  - `solve_topk()`: Greedily selects top $K$ by potency score $s_i$ (ignores diversity; optimal only when $\lambda = 0$).
  - `solve_greedy_diverse()`: Classical sequential greedy selection maximising marginal gain.
  - `solve_exact()`: Exact classical combinatorial enumeration across all $\binom{N}{K}$ feasible states.
  - `random_baseline()` & Random Search: Random feasible subset sampling.

### 7. Quantum Chemistry with VQE (`src/quantumscreen/vqe.py`)
- **Purpose**: Demonstrates the molecular simulation foundation of quantum drug discovery (ab initio potential energy surfaces and binding thermodynamics).
- **Implementation**:
  - Uses PySCF to compute one- and two-electron integrals in the STO-3G minimal basis set.
  - Mapped to qubits using Jordan-Wigner / Parity mapping with 2-qubit reduction:
    - **$H_2$**: 2 qubits, 3 variational parameters.
    - **$LiH$**: 4 qubits, 8 variational parameters (with frozen $1s$ core and removed virtual orbitals).
  - Ansatz: Unitary Coupled Cluster with Single and Double excitations (**UCCSD**) starting from the Hartree-Fock state $|HF\rangle$.
  - Optimised with SLSQP against exact Full Configuration Interaction (FCI).

### 8. Interactive UI & Deployment (`app.py`)
- Built with **Streamlit** across 4 tabs:
  1. *Single molecule*: Input or choose a SMILES string, view 2D chemical structure, real-time quantum vs classical probability of activity, Lipinski properties, and QED.
  2. *Batch screening*: Paste SMILES or upload CSV; run batch quantum scoring and download ranked leads.
  3. *Benchmark results*: Interactive visualization of ROC curves, qubit ablations, feature maps, and QAOA distributions.
  4. *About*: Documentation and methodology notes.

---

## Experimental Results & Benchmark Analysis

All results are obtained over repeated random splits (3 seeds) and scaffold splits on 1,513 BACE molecules:

### 1. Classification Performance

| Model Architecture | Input Features | ROC-AUC | EF@10% | Fit Time (s) |
|---|---|---|---|---|
| **Classical Random Forest** | 2,048-bit Morgan Fingerprint | **0.916 ± 0.006** | 2.10 | 1.7 s |
| **Classical SVM (RBF)** | 8 PCA Components | 0.879 ± 0.007 | 1.98 | 4.4 s |
| **Quantum Kernel SVM (ZZ, reps=2)** | 8 Qubits (8 PCA Components) | **0.873 ± 0.011** | **2.07** | 11.1 s |
| **Random Forest** | 8 PCA Components | 0.877 ± 0.015 | 2.07 | 0.8 s |
| **Variational Quantum Classifier (VQC)** | 6 Qubits (200 sample subset) | 0.625 ± 0.056 | — | 119.0 s |

### 2. Key Experimental Insights
1. **No Quantum Advantage in Classification**:
   - The quantum-kernel SVM (0.873) is statistically indistinguishable from the classical RBF-SVM on the same 8 features (0.879, $p > 0.05$).
   - The primary performance bottleneck is **information loss during PCA compression** (8 components retain only $\sim 36\%$ of molecular variance), evidenced by the uncompressed classical Random Forest scoring 0.916.
2. **Entanglement Does Not Improve Accuracy**:
   - An unentangled `z` feature map (pure single-qubit rotations) achieves an AUC of **0.877**, outperforming or matching the entangling `zz` (0.873) and `pauli_yzz` (0.869) circuits. Quantum entanglement provides no performance lift on this chemical dataset.
3. **Qubit Ablation Plateaus at 8 Qubits**:
   - Performance increases from 4 qubits (0.837) to 8 qubits (0.873) but plateaus at 10 qubits (0.867), while circuit simulation costs double with each added qubit.
4. **Scaffold Generalisation Drop**:
   - On the Bemis-Murcko scaffold split (unseen chemotypes), all models drop drastically: Random Forest drops from 0.916 to 0.781; Quantum Kernel drops to 0.677; Classical SVM drops to 0.667.
5. **VQC Inefficiency**:
   - The VQC is $\approx 90\times$ slower to train than the kernel method and achieves an AUC of only 0.625 due to barren plateau effects, small parameter budgets, and gradient-free optimisation overhead.
6. **Virtual Screening Enrichment on Hold-Out Test Set**:
   - On an unseen hold-out library (303 molecules, 45.5% active base rate), the quantum model placed **24 of its top 25 picks** in the active class (Precision@25 = 0.96, EF@10% = 2.12; theoretical maximum EF@10% = 2.20).
7. **Combinatorial Candidate Selection (QAOA)**:
   - Score-only selection produces near-duplicate hydantoin molecules (pairwise Tanimoto similarity = 0.46, objective = 1.96).
   - Diversity-aware selection (exact and QAOA) achieves an objective of **2.88** and lowers redundant similarity to **0.14**.
   - **However, QAOA provides no quantum advantage**: At $N \le 14$ ($K \le 4$), random search with the same 1,024 shots achieves 100% of the optimum. QAOA's output distribution has an average quality equal to random feasible sampling ($1.001\times$), because the penalty formulation concentrates only $22\% - 52\%$ of probability mass on feasible states.
8. **VQE Chemistry Validation**:
   - VQE ground-state energy curves for $H_2$ and $LiH$ matched exact Full Configuration Interaction (FCI) to within $< 0.001\text{ mHa}$, well inside standard chemical accuracy ($1.6\text{ mHa} \approx 1\text{ kcal/mol}$).

---

## Critical Limitations of the Project

When defending or reviewing this project, the following ten fundamental limitations must be highlighted:

### 1. Classical Simulation vs. Real Physical Quantum Hardware
- All quantum circuits are simulated on classical CPUs using exact, noiseless linear algebra (`Statevector`).
- On real Noisy Intermediate-Scale Quantum (NISQ) hardware:
  - Finite shot noise ($M$ measurements) degrades kernel estimation precision: error scales as $O(1/\sqrt{M})$.
  - Qubit decoherence ($T_1, T_2$ decay) and two-qubit gate errors ($CX$ infidelity) wash out interference patterns, causing fidelity kernels to flatten toward uniform matrices.

### 2. Lack of Quantum Advantage
- Neither the classification module (QSVM) nor the combinatorial selection module (QAOA) outperforms classical counterparts:
  - **QSVM vs Classical SVM**: Indistinguishable on the same features; classical Random Forest on full fingerprints is superior.
  - **QAOA vs Classical Solvers**: Classical diversity-greedy matches QAOA in microseconds, and uniform random sampling over feasible subsets performs just as well.

### 3. Severe Feature Space Bottleneck (PCA Compression)
- Drug molecules possess rich, high-dimensional chemical graphs. Compressing 2,048 bits into 8 orthogonal PCA components retains only $\sim 36\%$ of structural variance.
- Important pharmacophoric subgraphs, stereochemistry, and spatial charge distributions are discarded before the quantum model ever sees the data.

### 4. Single-Target Scope & Dataset Bias
- The project is validated solely on BACE-1 (1,513 molecules).
- It does not demonstrate cross-target generalisability (e.g., GPCRs, kinases, ion channels) or performance on expansive ultra-large chemical spaces (e.g., Enamine REAL library with billions of molecules).

### 5. Ligand-Based Approximation (Absence of 3D Biophysics)
- The screening is purely ligand-based (2D similarity to known inhibitors).
- It models no 3D protein-ligand interactions: no protein conformational dynamics, no crystallographic binding pocket geometry, no molecular docking, and no molecular mechanics (MM-GBSA / free energy perturbation).

### 6. Bioactivity Label Noise & Assay Amalgamation
- The binary label ($1 / 0$) is derived from literature $IC_{50}$ thresholds collated across diverse experimental protocols and assay technologies.
- Variations in assay conditions (pH, substrate concentration, enzymatic constructs) introduce intrinsic label noise into the training signal.

### 7. Toy Molecule Scope for VQE
- VQE is demonstrated on $H_2$ and $LiH$ (2 to 4 qubits).
- Actual drug-like molecules contain 30–70 heavy atoms and hundreds of electrons, requiring hundreds of error-corrected logical qubits and billions of quantum gates—far beyond current NISQ capabilities.
- The VQE module operates as an independent demonstration and is not coupled to the BACE screening pipeline.

### 8. QAOA Penalty Formulation & Constraint Violations
- Cardinality ($\sum x_i = K$) is enforced via an unconstrained penalty term in the QUBO rather than a constraint-preserving mixer.
- As a result, $48\% - 78\%$ of the probability mass sampled from the QAOA statevector corresponds to infeasible bitstrings (where the count of selected molecules is not equal to $K$), requiring classical post-hoc repair.

### 9. Heuristic Scoring & Diversity Weights
- The multi-objective formula ($0.7 \cdot P(\text{active}) + 0.3 \cdot \text{QED} - \text{penalty}$) and the selection diversity trade-off $\lambda = 0.5$ are heuristic hyperparameters.
- They have not been calibrated or validated against wet-lab experimental outcomes or crystallographic hit rates.

### 10. Platt Scaling Inaccuracies
- Support Vector Machine decision margins are mapped to pseudo-probabilities via Platt scaling (univariate logistic regression).
- In precomputed quantum kernel spaces with kernel concentration, Platt scaling can generate miscalibrated confidence scores near decision boundaries.

---

## Future Directions & Roadmap

1. **Execution on IBM Quantum Hardware**:
   - Run the 8-qubit circuits on physical superconducting processors (e.g., IBM Heron / Eagle) using Qiskit Runtime primitives.
   - Implement error mitigation (Zero-Noise Extrapolation, Readout Error Mitigation, Pauli Twirling) to quantify the fidelity penalty.
2. **Constraint-Preserving QAOA with XY Mixers**:
   - Replace the transverse-field $X$ mixer and penalty Hamiltonian with an $XY$ mixer initialized in a Dicke state $|D_K^N\rangle$. This confines the quantum evolution strictly to the feasible subspace $\sum x_i = K$, eliminating wasted probability mass.
3. **Trainable Quantum Kernels & Metric Learning**:
   - Implement parameterized Quantum Kernel Alignment (QKA) to optimize feature map parameters directly on molecular data rather than using fixed heuristic ZZ gates.
4. **Non-Linear Dimensionality Reduction**:
   - Replace linear PCA with a non-linear variational autoencoder (VAE) or graph neural network (GNN) molecular embedding to preserve structural motifs in a compact latent vector.
5. **Integration with Structure-Based Docking**:
   - Interface QuantumScreen with AutoDock Vina or OpenMM, using VQE or quantum-inspired tensor networks to estimate fragment-binding enthalpies.
