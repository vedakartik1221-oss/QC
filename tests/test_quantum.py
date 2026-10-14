import numpy as np
import pytest
from qiskit_machine_learning.kernels import FidelityQuantumKernel

from quantumscreen.metrics import enrichment_factor
from quantumscreen.quantum import (FEATURE_MAPS, QuantumKernelSVM, build_feature_map, compute_states,
                                   fidelity_kernel)

RNG = np.random.default_rng(0)


@pytest.mark.parametrize("name", FEATURE_MAPS)
def test_kernel_properties(name):
    X = RNG.uniform(0, np.pi, (12, 4))
    S = compute_states(build_feature_map(name, 4, 2), X)
    K = fidelity_kernel(S, S)
    assert np.allclose(np.diag(K), 1.0)                      # k(x, x) = 1
    assert np.allclose(K, K.T)                               # symmetric
    assert K.min() >= -1e-12 and K.max() <= 1 + 1e-12        # fidelities in [0, 1]
    assert np.linalg.eigvalsh(K).min() > -1e-9               # positive semi-definite


def test_matches_qiskit_fidelity_quantum_kernel():
    X = RNG.uniform(0, np.pi, (6, 4))
    circuit = build_feature_map("zz", 4, 2)
    ours = fidelity_kernel(compute_states(circuit, X), compute_states(circuit, X))
    official = FidelityQuantumKernel(feature_map=circuit).evaluate(X)
    assert np.allclose(ours, official, atol=1e-8)


def test_qsvm_learns_separable_problem():
    X = np.vstack([RNG.normal(0.8, 0.2, (30, 4)), RNG.normal(2.3, 0.2, (30, 4))]).clip(0, np.pi)
    y = np.array([0] * 30 + [1] * 30)
    model = QuantumKernelSVM("zz", 1, C=10, scale=0.5).fit(X, y)
    assert (model.predict(X) == y).mean() > 0.95
    p = model.predict_proba(X)
    assert p.shape == (60, 2) and np.allclose(p.sum(axis=1), 1)


def test_enrichment_factor():
    y = np.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
    assert enrichment_factor(y, np.arange(10)[::-1], 0.2) == pytest.approx(5.0)   # perfect ranking
    assert enrichment_factor(y, np.arange(10), 0.2) == pytest.approx(0.0)         # worst ranking


def test_unknown_feature_map():
    with pytest.raises(ValueError):
        build_feature_map("nope", 4)
