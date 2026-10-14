"""Central configuration for QuantumScreen.

Every tunable knob of the pipeline lives in :class:`Config`, so experiments are
reproducible and the CLI (``main.py``) only has to override a few fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Config:
    # ---- paths -------------------------------------------------------------
    data_path: Path = ROOT / "data" / "bace.csv"
    results_dir: Path = ROOT / "results"
    models_dir: Path = ROOT / "models"

    # ---- data --------------------------------------------------------------
    max_molecules: int | None = None      # None = use the full BACE set (1513 molecules)
    test_size: float = 0.2
    seeds: tuple = (0, 1, 2)              # repeated random splits for mean +/- std

    # ---- features ----------------------------------------------------------
    fp_radius: int = 2                    # Morgan (ECFP4-like) radius
    fp_bits: int = 2048

    # ---- quantum model -----------------------------------------------------
    n_qubits: int = 8                     # PCA components == qubits
    feature_map: str = "zz"               # z | zz | zz_full | pauli_yzz
    reps: int = 2
    qubit_ablation: tuple = (4, 6, 8, 10)
    feature_map_ablation: tuple = (("z", 2), ("zz", 1), ("zz", 2), ("zz_full", 2), ("pauli_yzz", 2))

    # ---- hyper-parameter search (inner CV on the training split only) ------
    c_grid: tuple = (0.1, 1.0, 10.0, 100.0)
    scale_grid: tuple = (0.25, 0.5, 1.0)  # multiplies the encoded angles (kernel bandwidth)
    cv_folds: int = 3

    # ---- VQC (variational classifier) --------------------------------------
    vqc_qubits: int = 6
    vqc_train_size: int = 200
    vqc_maxiter: int = 120

    # ---- ranking -----------------------------------------------------------
    w_activity: float = 0.7               # weight of the quantum activity probability
    w_qed: float = 0.3                    # weight of the drug-likeness (QED) score
    lipinski_penalty: float = 0.10        # subtracted per Lipinski violation beyond one
    top_k: int = 25

    # ---- QAOA candidate selection ------------------------------------------
    sel_pool_top: int = 40                # shortlists are drawn from the top-N of the screening ranking
    sel_sizes: tuple = (8, 10, 12, 14)    # number of candidates N (= qubits)
    sel_p: tuple = (1, 2, 3)              # QAOA depths
    sel_pools: int = 8                    # random shortlists per size
    sel_lambda: float = 0.5               # diversity weight
    sel_lambda_grid: tuple = (0.0, 0.25, 0.5, 1.0)
    sel_restarts: int = 3
    sel_maxiter: int = 60
    sel_shots: int = 1024

    # ---- VQE ---------------------------------------------------------------
    h2_bond_lengths: tuple = (0.4, 0.5, 0.6, 0.7, 0.74, 0.8, 0.9, 1.0, 1.25, 1.5, 2.0, 2.5)
    lih_bond_lengths: tuple = (1.0, 1.25, 1.5, 1.6, 1.75, 2.0, 2.5, 3.0)

    def ensure_dirs(self) -> None:
        (self.results_dir / "figures").mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
