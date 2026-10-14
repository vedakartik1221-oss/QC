import numpy as np
import pytest

from quantumscreen.config import Config
from quantumscreen.data import load_bace
from quantumscreen.ranking import rank_candidates


def test_rank_candidates_sorted_and_penalised():
    df = load_bace(Config().data_path, max_molecules=40)
    p = np.linspace(0, 1, len(df))
    r = rank_candidates(df, p, Config())
    assert list(r["rank"]) == list(range(1, len(df) + 1))
    assert r["final_score"].is_monotonic_decreasing
    assert {"QED", "lipinski_violations", "p_quantum_active"} <= set(r.columns)


def test_vqe_h2_ground_state():
    pytest.importorskip("qiskit_nature")
    pytest.importorskip("pyscf")
    from quantumscreen.vqe import vqe_curve
    d = vqe_curve("H2", (0.74,))
    assert d.E_vqe[0] == pytest.approx(-1.1373, abs=2e-3)   # literature value, STO-3G
    assert d.error_mHa[0] < 1.6                              # chemical accuracy
