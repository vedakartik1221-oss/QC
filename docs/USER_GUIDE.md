# User guide

## 1. Requirements

* Python **3.10 - 3.12** (developed on 3.12)
* ~2 GB free RAM, any CPU (no GPU needed; the circuits are small statevector simulations)
* Windows, macOS or Linux

## 2. Installation

```bash
# 1. unzip the project and open a terminal inside the quantumscreen/ folder
python -m venv .venv
# Windows:        .venv\Scripts\activate
# macOS / Linux:  source .venv/bin/activate

# 2. core dependencies (quantum kernel, VQC, benchmark, UI) + tests and notebook
#    (requirements.txt alone is enough to run the app)
pip install -r requirements-dev.txt

# 3. OPTIONAL - VQE module (needs PySCF)
pip install -r requirements-vqe.txt
```

> **Windows note:** PySCF has no official Windows wheels. Either (a) install and run the VQE stage inside **WSL2**
> (Ubuntu) or **Google Colab**, or (b) skip it with `python main.py --no-vqe`. Everything else works natively on Windows.

Verify the installation:

```bash
pytest -q          # 21 tests should pass (VQE test is skipped automatically if PySCF is missing)
```

## 3. Running the pipeline

| Command | What it does | Approx. time (1 CPU) |
|---|---|---|
| `python main.py --quick` | small smoke run on 400 molecules, 1 seed; writes to `results_quick/` | < 1 min |
| `python main.py` | full pipeline: benchmark, ablations, scaffold split, VQC, ranking, VQE, figures | 20 - 40 min (about 20 min measured on 1 CPU core) |
| `python main.py --stage benchmark` | benchmark + figures only | 12 - 25 min |
| `python main.py --stage screen` | train final models, rank the hold-out library, save models for the app | ~1 min |
| `python main.py --stage select` | QAOA diversity-aware selection study (needs `results/ranked_candidates.csv`, created by `--stage screen`) | ~6 min |
| `python main.py --stage vqe` | VQE curves only | ~1 min |
| `python main.py --stage figures` | redraw figures from saved CSVs | seconds |
| `python main.py --no-vqc` | skip the slow variational classifier | saves ~10 min |
| `python main.py --qubits 6 --seeds 0 1` | override the qubit count / seeds | - |

Other options: `--data path/to/bace.csv`, `--max-molecules N`, `--no-vqe`. Defaults live in `src/quantumscreen/config.py`.

## 4. Outputs (`results/`)

| File | Content |
|---|---|
| `benchmark_runs.csv` | one row per (model, split, seed): AUC, accuracy, precision, recall, F1, EF10, timings, best hyper-parameters |
| `benchmark_summary.csv` | the same aggregated (mean, std) |
| `vqc_runs.csv`, `vqc_summary.csv` | VQC vs QSVM vs classical SVM on a small training set |
| `ranked_candidates.csv` | the hold-out screening library ranked by `final_score` |
| `screening_summary.json` | precision@k, EF10, Lipinski statistics |
| `selection_runs.csv`, `selection_summary.csv`, `selection_lambda.csv` | QAOA vs classical selection, per pool and aggregated; lambda sweep |
| `selected_diverse_candidates.csv`, `selection_real_case.json` | batch of K candidates chosen from the top-12 by top-K, exact and QAOA |
| `vqe_h2.csv`, `vqe_lih.csv` | HF, exact and VQE energies per bond length |
| `figures/*.png` | figures used in the report and slides |

Trained models are saved to `models/` (`qsvm_final.joblib`, `svm_final.joblib`).

## 5. Streamlit demo app

```bash
python main.py --stage screen     # once, to create the models (skip if models/ is already filled)
streamlit run app.py
```

Tabs: **Single molecule** (paste a SMILES; get quantum and classical probabilities, structure drawing, drug-likeness),
**Batch screening** (paste SMILES or upload a CSV with a `smiles` column; download the ranked list),
**Benchmark results** (tables and figures) and **About**.

## 6. Using the code as a library

```python
from quantumscreen.config import Config
from quantumscreen.pipeline import load_model, screen_smiles

cfg = Config()
encoder, model, meta = load_model(cfg.models_dir / "qsvm_final.joblib")
ranked = screen_smiles(["CC(=O)Oc1ccccc1C(=O)O", "c1ccccc1CCN"], encoder, model, cfg)
print(ranked[["rank", "smiles", "p_quantum_active", "QED", "final_score"]])
```

## 7. Using your own dataset

Provide a CSV with a SMILES column named `mol` (or `smiles`) and a binary label column named `Class` (or `label`):

```bash
python main.py --data my_target.csv
```

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: qiskit_nature` or PySCF build errors | Use `--no-vqe`, or run the VQE stage in WSL2 / Colab |
| `ImportError` from Qiskit after upgrading | Re-install the pinned versions: `pip install -r requirements.txt --force-reinstall` |
| Run is slow | Use `--quick`, `--no-vqc`, fewer seeds (`--seeds 0`), or fewer qubits (`--qubits 6`); the ablation to 10 qubits is the most expensive step |
| Streamlit says "No trained model found" | Run `python main.py --stage screen` |
| Memory error with many qubits | The statevector grows as 2^n; keep n <= 12 on a laptop |
| Results differ slightly between machines | Platt scaling and SVM solvers are seeded, but BLAS differences can change the 3rd decimal |

## 9. Running on real quantum hardware (optional extension)

Replace `compute_states`/`fidelity_kernel` in `src/quantumscreen/quantum.py` with Qiskit Machine Learning's
`FidelityQuantumKernel(feature_map=..., fidelity=ComputeUncompute(sampler=<IBM Runtime SamplerV2>))` and use a small
subset (a few dozen molecules, 4-6 qubits): kernel evaluation needs O(N^2) circuit executions. You need an IBM Quantum
account and API token; the code does not require one for the default simulator workflow.
