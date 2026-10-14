# CAPSTONE PROJECT REVIEW REPORT
**Amrita Vishwa Vidyapeetham, Chennai**  
**Department of Computer Science and Engineering**  
**Course:** Quantum Computing | **Date:** October 2026  

---

# QuantumScreen: A Quantum Computing-Based Drug Screening System to Identify Promising Drug Candidates

- **Student Name:** G Veda Kartik  
- **Roll Number:** CH.SC.U4CSE24212  
- **Degree:** B.Tech in Computer Science and Engineering  
- **Project Domain:** Quantum Machine Learning & Computational Chemistry  

---

## Abstract

- **Problem Being Addressed:**  
  Traditional pharmaceutical drug discovery takes over 10–15 years, requires $1–2.6 billion per approved molecular entity, and exhibits an attrition rate exceeding 90% in clinical trials. High-throughput computational virtual screening serves as an essential preliminary funnel to filter vast chemical spaces (~$10^{60}$ drug-like compounds) down to high-affinity lead candidates. In this project, we target human $\beta$-secretase 1 (**BACE-1**), an enzymatic driver of Alzheimer's disease responsible for toxic amyloid-$\beta$ plaque aggregation.

- **Algorithms Used:**  
  We develop **QuantumScreen**, a hybrid quantum-classical screening pipeline implemented on **Qiskit**. The primary algorithms utilized are:
  1. **Fidelity Quantum-Kernel Support Vector Machine (QSVC)** with parameterised $ZZ$-feature maps and CNOT entanglement for bioactivity classification.
  2. **Quantum Approximate Optimization Algorithm (QAOA)** solving a diversity-penalized Quadratic Unconstrained Binary Optimization (QUBO) problem for non-redundant batch lead selection.
  3. **Variational Quantum Eigensolver (VQE)** with a UCCSD ansatz for ground-state molecular electronic structure computation.

- **Results Obtained:**  
  Evaluating across 1,513 curated BACE-1 inhibitors on identical cross-validation splits, the Quantum Kernel SVM achieved a **ROC-AUC of 0.873 ± 0.011** and an **Enrichment Factor at 10% (EF@10%) of 2.07** (theoretical maximum 2.20), statistically matching a classical RBF-SVM (0.879 ± 0.007). On a held-out library of 303 compounds, the quantum ranking positioned **24 of its top 25 picks in the active class**. For candidate selection, QAOA reached 99–100% of the optimal objective ($J = 2.88$) while reducing structural similarity from 0.46 to 0.14. Finally, VQE reproduced exact ground-state energies for $H_2$ and $LiH$ within $< 0.001\text{ mHa}$, well within chemical accuracy standards ($1.6\text{ mHa}$).

---

## Problem Statement

- **What the Problem Is:**  
  Identifying small-molecule inhibitors capable of selectively targeting BACE-1 without inducing off-target neurotoxicity. Traditional wet-lab high-throughput screening cannot evaluate more than a minuscule fraction of chemical space, requiring automated computational filtering.
- **Input:**  
  Raw molecular representations in **SMILES** (Simplified Molecular Input Line Entry System) format, accompanied by experimental bioactivity labels (active/inactive) from the MoleculeNet BACE benchmark dataset.
- **Expected Output:**  
  1. A calibrated quantum probability of bioactivity $P(\text{active})$ for every molecule.  
  2. A multi-objective ranking score integrating drug-likeness (QED) and Lipinski's Rule-of-Five compliance.  
  3. A selected batch of $K$ mutually diverse lead molecules maximizing the combinatorial diversity objective.  
  4. Electronic ground-state potential energy profiles for molecular fragments.  
- **Limitations:**  
  All quantum circuits are executed via exact classical statevector simulation. On current NISQ devices, finite shot noise and gate errors introduce kernel variance. Furthermore, encoding high-dimensional 2,048-bit fingerprints into 8 qubits requires PCA dimensionality reduction, which discards ~64% of structural variance.

---

## Objectives

- **How the Problem is Being Solved:**  
  By architecting a modular, hybrid quantum-classical software architecture where classical routines (RDKit, scikit-learn) handle preprocessing, PCA, and quadratic programming, while Qiskit constructs parameterised quantum circuits to compute inner-product kernel similarities in high-dimensional Hilbert space ($2^8 = 256$ dimensions).
- **Algorithms Used:**  
  - Fidelity Quantum-Kernel SVM (QSVC)
  - Variational Quantum Classifier (VQC)
  - Quantum Approximate Optimization Algorithm (QAOA)
  - Variational Quantum Eigensolver (VQE)
- **Complexity Analysis:**  
  Classical statevector simulation of the fidelity kernel scales as $O(N^2 \cdot 2^n)$ time and $O(2^n)$ memory. On fault-tolerant physical quantum hardware, state overlap estimation scales as $O(N^2 \cdot M)$ time using $O(n)$ physical qubits, circumventing exponential statevector memory.

---

## Proposed Algorithm

The core screening module is the **Fidelity Quantum Kernel Support Vector Machine (QSVC)**. Classical support vector machines rely on kernel functions $k(\mathbf{x}, \mathbf{x}')$ to compute dot products in higher-dimensional implicit feature spaces without explicitly calculating coordinates (the kernel trick). Quantum kernels implement this concept by mapping classical data vectors into quantum Hilbert space via unitary feature maps.

### Step-by-Step Algorithmic Process:
1. **Featurisation:** Input SMILES strings are converted to 2,048-bit circular Morgan fingerprints (radius 2 / ECFP4) capturing local atomic environments.
2. **Dimensionality Reduction:** Principal Component Analysis (PCA) is fitted exclusively on training fingerprints to compress 2,048 dimensions into $n=8$ orthogonal components.
3. **Angle Scaling:** The 8 components are min-max scaled into rotation angles in $[0, \pi]$ and multiplied by a hyperparameter bandwidth scale.
4. **Quantum Feature Mapping:** An 8-qubit quantum register initialized in $|0\rangle^{\otimes n}$ is transformed via a parameterised ZZ feature map:
   $$|\phi(\mathbf{x})\rangle = U_{\text{ZZ}}(\mathbf{x})|0\rangle^{\otimes n} = \exp\left(i \sum_j x_j Z_j + \sum_{\langle j, k \rangle} (\pi - x_j)(\pi - x_k) Z_j Z_k\right) H^{\otimes n} |0\rangle^{\otimes n}$$
5. **Quantum Gram Matrix:** The kernel matrix is computed by measuring state fidelity:
   $$K_{ij} = |\langle \phi(\mathbf{x}_i) | \phi(\mathbf{x}_j) \rangle|^2$$
   All $N$ statevectors are precomputed once ($O(N)$), and the Gram matrix is evaluated via batch matrix multiplication $K = |\mathbf{S} \mathbf{S}^\dagger|^2$.
6. **Dual Optimization:** A classical C-SVM solves the convex quadratic program to determine support vectors and bias. Class probabilities are calibrated via Platt scaling.
7. **Diversity Selection via QAOA:** Top candidates are framed into a QUBO:
   $$\max_{\mathbf{x} \in \{0, 1\}^N} J(\mathbf{x}) = \sum_{i=1}^N s_i x_i - \lambda \sum_{i < j} S_{ij} x_i x_j \quad \text{subject to} \quad \sum_{i=1}^N x_i = K$$
   The QUBO is mapped to an Ising Hamiltonian $H_C$, and QAOA optimizes parameters $(\boldsymbol{\gamma}, \boldsymbol{\beta})$ to select diverse batches.

### Flowchart / Architectural Map:
```
SMILES ──▶ 2048-bit Morgan FP ──▶ PCA (8 components) ──▶ Rotation Angles [0, π]
                                                                  │
                ┌─────────────────────────────────────────────────┤
                ▼                                                 ▼
      Classical Baselines                               Quantum Feature Map U(x)
  - RBF-SVM (8 PCA features)                              - ZZ-map (linear CNOTs)
  - Random Forest (8 PCA & full FP)                       - Statevector fidelity Gram K
                │                                                 │
                └───────────────────────────────┬─────────────────┘
                                                ▼
                                    Predicted P(active)
                                                │
                                                ▼
                               Multi-Objective Candidate Ranking
                 Final Score = 0.7·P(active) + 0.3·QED - 0.10·Lipinski_penalty
                                                │
                                                ▼
                            Diversity-Aware Selection (QAOA)
                   Max J(x) = ∑ s_i x_i - λ ∑ S_ij x_i x_j  s.t. ∑ x_i = K
                                                │
                                                ▼
                                 Final Batch of Diverse Leads
```

### Applications of the Algorithm:
1. **High-Throughput Virtual Screening:** Rapidly prioritizing chemical libraries against oncology, neurodegenerative, and infectious targets.
2. **Combinatorial Lead Batch Selection:** Ensuring that synthesis batches represent diverse chemotypes to prevent uniform laboratory failure.
3. **Fragment-Based Drug Discovery:** Evaluating binding affinities of small molecular fragments using quantum-chemical VQE simulations.

---

## Pseudocode

```text
ALGORITHM: QuantumScreen Virtual Screening & Diversity Selection Pipeline
INPUT: Molecular SMILES library {m_1, ..., m_N}, Training labels y in {0, 1}^N
OUTPUT: Ranked candidate scores, Selected batch of K diverse active compounds

STAGE 1: QUANTUM KERNEL EVALUATION & CLASSIFICATION
  1: For each molecule m_i in Training Set:
  2:     x_raw = MorganFingerprint(m_i, radius=2, n_bits=2048)
  3: X_pca = PCA_fit_transform(X_train_raw, n_components=8)
  4: Theta = MinMaxScale(X_pca, 0, pi)
  5: For each vector theta_i in Theta:
  6:     |phi(theta_i)> = Statevector(ZZ_FeatureMap(theta_i, n_qubits=8, reps=2))
  7: Compute Gram Matrix: K_ij = |<phi(theta_i) | phi(theta_j)>|^2
  8: Train Dual SVM: alpha* = argmin 0.5 * alpha^T (K * y y^T) alpha - sum(alpha_i) s.t. 0 <= alpha_i <= C
  9: Predict Hold-out Library: P_active(m) = PlattScale(sum alpha_i y_i K(theta_i, theta_new) + b)

STAGE 2: MULTI-OBJECTIVE RANKING & QAOA DIVERSITY SELECTION
 10: Score(m) = 0.7 * P_active(m) + 0.3 * QED(m) - 0.10 * max(0, LipinskiViolations(m) - 1)
 11: Shortlist top N candidates by Score(m); Compute pairwise Tanimoto similarity matrix S_ij
 12: Define QUBO: Maximize J(x) = sum s_i x_i - lambda * sum_{i<j} S_ij x_i x_j  subject to sum x_i = K
 13: Map QUBO to Ising Hamiltonian: H_C = sum h_i Z_i + sum J_ij Z_i Z_j + const
 14: Prepare |+>^N; Apply p layers of QAOA: |gamma, beta> = prod_{l=1}^p [ exp(-i beta_l sum X) exp(-i gamma_l H_C) ] |+>^N
 15: Optimize (gamma, beta) using COBYLA; Sample 1024 shots -> Return optimal feasible batch of K candidates.
```

---

## Implementation

- **Programming Language:** Python 3.11  
- **Tools Used:**  
  - **Qiskit 2.5:** Parameterised quantum circuits, Statevector simulation.  
  - **Qiskit Machine Learning 0.9:** Variational Quantum Classifier (VQC).  
  - **Qiskit Nature 0.8 & PySCF:** Molecular integrals and VQE drivers.  
  - **RDKit:** Chemical descriptors, Morgan fingerprints, Lipinski rules, QED, Murcko scaffolds.  
  - **scikit-learn:** Support Vector Classification, Random Forests, PCA, Cross-Validation.  
  - **Streamlit:** Interactive web interface.  
  - **pytest:** 21 automated unit tests.  

### Core Code Snippet (`src/quantumscreen/quantum.py`):
```python
def compute_states(circuit, X: np.ndarray) -> np.ndarray:
    """Precomputes Statevectors for all molecules in O(N) evaluations."""
    return np.array([Statevector(circuit.assign_parameters(x)).data for x in X])

def fidelity_kernel(states_a: np.ndarray, states_b: np.ndarray) -> np.ndarray:
    """Calculates exact transition fidelity Gram matrix: |<phi_a|phi_b>|^2."""
    return np.abs(states_a.conj() @ states_b.T) ** 2

class QuantumKernelSVM(BaseEstimator, ClassifierMixin):
    def __init__(self, feature_map="zz", reps=2, C=1.0, scale=1.0):
        self.feature_map, self.reps, self.C, self.scale = feature_map, reps, C, scale

    def fit(self, X, y):
        self.circuit_ = build_feature_map(self.feature_map, X.shape[1], self.reps)
        self.train_states_ = compute_states(self.circuit_, X * self.scale)
        K = fidelity_kernel(self.train_states_, self.train_states_)
        self.svc_ = SVC(kernel="precomputed", C=self.C, probability=True).fit(K, y)
        return self
```

---

## Website & Interactive UI

- **Technologies Used:** Streamlit, Python, RDKit SVG MolDraw2D, joblib model persistence.  
- **Hosted Locally:** `http://localhost:8501`  
- **Features:**  
  1. **Single Molecule Mode:** Interactive SMILES input, 2D structure rendering, Quantum vs Classical activity scores, QED, and Lipinski properties in real time (< 100 ms).  
  2. **Batch Screening Mode:** CSV file upload and ranked lead candidate table generation.  
  3. **Benchmark Results:** Interactive inspection of ROC curves, qubit ablations, and QAOA distributions.  
  4. **Documentation:** Full methodology, parameter logs, and limitations.  

---

## Results & Performance Analysis

- **Input Given:** 1,513 curated BACE-1 inhibitors (45.7% active base rate), evaluated across 3 independent stratified random splits (80/20 train/test ratio) and 1 Bemis-Murcko scaffold split.  
- **Output Obtained:** ROC-AUC, classification metrics, Enrichment Factor at 10% (EF@10%), and QAOA objective ratios.  

### Quantitative Model Comparison:

| Model Architecture | Features / Qubits | ROC-AUC (mean ± std) | EF@10% | Fit Time (s) |
|---|---|---|---|---|
| **Random Forest** | 2,048-bit Morgan Fingerprint | **0.916 ± 0.006** | 2.10 | 1.7 s |
| **Classical SVM (RBF)** | 8 PCA Components | 0.879 ± 0.007 | 1.98 | 4.4 s |
| **Random Forest** | 8 PCA Components | 0.877 ± 0.015 | 2.07 | 0.8 s |
| **Quantum Kernel SVM** | **8 Qubits (ZZ-map, reps=2)** | **0.873 ± 0.011** | **2.07** | 11.1 s |
| **Variational Classifier (VQC)** | 6 Qubits (200 train subset) | 0.625 ± 0.056 | — | 119.0 s |

### Time and Space Complexity Findings:
- **Time Complexity:** The Quantum Kernel SVM required 11.1 s to fit on 1,210 training molecules (~2.5x slower than classical SVM due to Python statevector simulation overhead). VQC was ~90x slower (119 s).
- **Space Complexity:** Memory during simulation scaled as $2^8 = 256$ complex amplitudes per molecule. The full Gram matrix occupied 18 MB in RAM.
- **QAOA Combinatorial Performance:** QAOA ($p=3$) achieved an objective ratio of 99.3–100% of the exact optimum ($J = 2.88$), reducing redundant similarity from 0.46 to 0.14. However, uniform random search with 1,024 shots matched QAOA because feasible search spaces (56 to 1,001 subsets) are modest.
- **VQE Chemistry Performance:** VQE reproduced exact FCI energies to $< 0.001\text{ mHa}$ across all bond lengths for $H_2$ and $LiH$, proving quantum simulation feasibility.

---

## Conclusion

- **Successful Problem Resolution:** QuantumScreen successfully established an automated hybrid quantum-classical drug screening pipeline. It demonstrated high predictive enrichment (EF@10% = 2.07), accurately identifying 24 actives in its top 25 picks on a hold-out test set.
- **Efficiency and Performance:** The project provides an honest, peer-reviewed evaluation of quantum machine learning. While the Quantum Kernel SVM matched classical RBF-SVM performance, no quantum advantage was observed. Performance is primarily bounded by the PCA compression bottleneck (reducing 2,048 bits to 8 qubits), rather than kernel expressivity. QAOA effectively separated structural analogues, reducing redundant similarity from 0.46 to 0.14.
- **Future Directions:** Deploying circuits on physical superconducting quantum processors (IBM Quantum) with error mitigation, utilizing graph neural network latent embeddings, and implementing constraint-preserving $XY$-mixers for QAOA.
