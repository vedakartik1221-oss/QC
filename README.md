# ⚛️ QuantumScreen — Quantum Computing-Based Drug Screening System

**Capstone project, Quantum Computing** · G Veda Kartik (CH.SC.U4CSE24212) · Amrita Vishwa Vidyapeetham

> *Develop a Quantum Computing-based Drug Screening System to identify promising drug candidates.*

QuantumScreen is a **hybrid quantum-classical virtual-screening pipeline** built on **Qiskit**. It scores molecules for activity
against **BACE-1** (an Alzheimer's-disease target) with a **quantum-kernel SVM**, ranks them together with drug-likeness (QED / Lipinski),
selects a **diverse batch of K candidates with QAOA** (a QUBO with a Tanimoto-redundancy term), benchmarks the quantum models honestly against classical machine learning, and adds a **VQE** module that computes molecular
ground-state energies (H2, LiH) as the quantum-chemistry side of drug discovery.

```
SMILES ─▶ Morgan fingerprint ─▶ PCA (8) ─▶ angles ─▶ Qiskit feature map ─▶ quantum kernel ─▶ SVM ─▶ P(active) ─▶ rank (+QED, Lipinski) ─▶ QUBO ─▶ QAOA ─▶ diverse batch of K
```

## Key results (1513 BACE molecules, exact statevector simulation, 3 seeds)

| Model | ROC-AUC | EF@10% |
|---|---|---|
| Random Forest, full 2048-bit fingerprint | **0.916 ± 0.006** | 2.10 |
| Classical RBF-SVM, 8 PCA features | 0.879 ± 0.007 | 1.98 |
| **Quantum-kernel SVM (ZZ map, 8 qubits)** | **0.873 ± 0.011** | **2.07** |
| Variational quantum classifier (small data) | 0.625 ± 0.056 | – |

* The quantum-kernel SVM **matches but does not beat** a classical SVM on the same features — we report **no quantum advantage**.
* Entanglement didn't help (the un-entangled `z` map scores 0.877); more than 8 qubits didn't help; VQC is ~90× slower and worse than the kernel SVM.
* On a hold-out library the quantum score put **24 of its top 25** picks in the active class (library base rate 45 %); EF@10 % = 2.12 (max 2.20).
* **QAOA batch selection:** choosing 4 of the top-12 candidates by score alone gives three near-duplicate molecules (objective 1.96); the diversity-aware QUBO, solved by QAOA and by exact enumeration, gives chemically varied sets (2.88). QAOA reaches 99-100 % of the optimum, but **random search with the same shots does equally well** and QAOA's output distribution is no better than random sampling: again no quantum advantage.
* VQE reproduces exact H2 and LiH ground-state energies to < 0.001 mHa (chemical accuracy is 1.6 mHa).

Full tables, ablations and honest caveats: [`docs/RESULTS.md`](docs/RESULTS.md) and [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

![comparison](results/figures/01_model_comparison.png)

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt                      # core + tests/notebook (app-only: requirements.txt)
pip install -r requirements-vqe.txt                      # optional: VQE (use WSL/Colab on Windows)

pytest -q                                                # 21 tests
python main.py --quick                                   # ~1 min smoke run (VQE is skipped automatically if PySCF is not installed)
python main.py                                           # full pipeline, ~20-40 min on a laptop CPU (about 20 min measured on 1 core)
streamlit run app.py                                     # demo UI (models are included in models/)
```

Skip the optional parts with `python main.py --no-vqc --no-vqe`. All CLI options: [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md).

## What's inside

| Path | Purpose |
|---|---|
| `src/quantumscreen/` | the library: data, features, quantum models, classical baselines, benchmark, ranking, VQE, plots |
| `main.py` | command-line pipeline (stages: benchmark, screen, select, vqe, figures) |
| `app.py` | Streamlit demo: score a molecule, screen a batch, browse results |
| `notebooks/QuantumScreen_Walkthrough.ipynb` | executed step-by-step walkthrough |
| `tests/` | pytest suite (kernel properties, equivalence with Qiskit ML's `FidelityQuantumKernel`, splits, ranking, QUBO/Ising/QAOA checks, VQE) |
| `results/` | all CSV tables, JSON summaries and figures from the full run |
| `models/` | trained quantum and classical models used by the app |
| `report/`, `slides/` | project report (Word) and presentation (PowerPoint) |
| `docs/` | architecture, methodology, user guide, API reference, results, limitations |

## Documentation

| Document | Contents |
|---|---|
| [ARCHITECTURE](docs/ARCHITECTURE.md) | data flow, module map, design decisions |
| [METHODOLOGY](docs/METHODOLOGY.md) | dataset, quantum kernels, VQC, VQE, evaluation protocol, ranking formula, references |
| [USER_GUIDE](docs/USER_GUIDE.md) | installation, CLI, outputs, app, own data, troubleshooting, hardware extension |
| [API_REFERENCE](docs/API_REFERENCE.md) | every module and public function |
| [RESULTS](docs/RESULTS.md) | all experiments with tables and figures |
| [LIMITATIONS](docs/LIMITATIONS.md) | what the project does *not* show, and future work |

## Technology

Qiskit 2.5 · Qiskit Machine Learning 0.9 · Qiskit Nature 0.8 · Qiskit Algorithms 0.4 · RDKit · scikit-learn · PySCF · Streamlit

## Data & credits

BACE dataset: Subramanian et al., *J. Chem. Inf. Model.* 56 (2016); distributed via MoleculeNet (Wu et al., *Chem. Sci.* 2018).
Quantum kernel idea: Havlíček et al., *Nature* 567 (2019). VQE: Peruzzo et al., *Nat. Commun.* 5 (2014).

> **Scope note.** All quantum circuits are simulated classically. This is a research/education prototype, not a validated tool for drug decisions.
