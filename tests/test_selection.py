import numpy as np
import pytest
from qiskit.quantum_info import Statevector

from quantumscreen.selection import (QAOASolver, SelectionProblem, solve_exact, solve_greedy_diverse, solve_topk)

RNG = np.random.default_rng(3)


def _problem(n=6, k=3, lam=0.5):
    s = RNG.uniform(0.5, 0.9, n)
    S = RNG.uniform(0, 0.8, (n, n)); S = (S + S.T) / 2; np.fill_diagonal(S, 0)
    return SelectionProblem(s, S, k, lam=lam)


def test_ising_hamiltonian_equals_qubo_energy():
    prob = _problem()
    H = prob.hamiltonian()
    for i in RNG.choice(2 ** prob.n, 12, replace=False):
        e = Statevector.from_int(int(i), 2 ** prob.n).expectation_value(H).real
        assert e == pytest.approx(prob.energies[i], abs=1e-9)


def test_topk_is_exactly_optimal_without_diversity_term():
    for _ in range(10):
        prob = _problem(n=8, k=3, lam=0.0)
        assert np.array_equal(solve_topk(prob)[0], solve_exact(prob)[0])


def test_topk_suboptimal_with_redundant_candidates():
    s = np.array([0.90, 0.89, 0.60, 0.59, 0.20])
    S = np.zeros((5, 5)); S[0, 1] = S[1, 0] = 0.95            # two near-duplicate leaders
    prob = SelectionProblem(s, S, 2, lam=1.0)
    assert solve_topk(prob)[1] < solve_exact(prob)[1]
    assert solve_greedy_diverse(prob)[1] == pytest.approx(solve_exact(prob)[1])


def test_qaoa_circuit_matches_exact_evolution():
    prob = _problem(n=4, k=2)
    qaoa = QAOASolver(prob, p=1)
    gamma, beta = 0.7, 0.4
    psi = np.full(16, 0.25, dtype=complex)
    psi = np.exp(-1j * gamma * qaoa._E) * psi
    rx = np.cos(beta) * np.eye(2) - 1j * np.sin(beta) * np.array([[0, 1], [1, 0]])
    mixer = rx
    for _ in range(3):
        mixer = np.kron(mixer, rx)
    expected = mixer @ psi
    got = qaoa.state([gamma, beta]).data
    assert abs(np.vdot(expected, got)) == pytest.approx(1.0, abs=1e-9)   # equal up to global phase


def test_qaoa_solver_returns_feasible_selection():
    prob = _problem(n=6, k=3)
    res = QAOASolver(prob, p=2, restarts=2, maxiter=30, shots=256, seed=0).run()
    assert res["x"].sum() == prob.k and 0 < res["approx_ratio"] <= 1.0 + 1e-9
    assert 0 <= res["feasible_mass"] <= 1
