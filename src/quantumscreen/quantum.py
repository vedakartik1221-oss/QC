"""Quantum models built with Qiskit.

* :func:`build_feature_map` - parameterised data-encoding circuits.
* :func:`compute_states` / :func:`fidelity_kernel` - exact statevector quantum kernel
  ``k(x, x') = |<phi(x)|phi(x')>|^2`` (mathematically identical to Qiskit Machine
  Learning's ``FidelityQuantumKernel`` in the noiseless limit, but orders of
  magnitude faster because every state is computed once, not once per pair).
* :class:`QuantumKernelSVM` - SVM on the precomputed quantum kernel (the QSVC idea).
* :func:`train_vqc` - Qiskit Machine Learning's variational quantum classifier.
"""
from __future__ import annotations

import warnings

import numpy as np
from qiskit.circuit.library import pauli_feature_map, z_feature_map, zz_feature_map
from qiskit.quantum_info import Statevector
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.svm import SVC

warnings.filterwarnings("ignore", category=DeprecationWarning)

FEATURE_MAPS = ("z", "zz", "zz_full", "pauli_yzz")


def build_feature_map(name: str, n_qubits: int, reps: int = 2):
    """Return a data-encoding circuit.

    ``z``         angle encoding, no entanglement (classically simulable control)
    ``zz``        ZZ feature map, linear (nearest-neighbour) entanglement
    ``zz_full``   ZZ feature map, all-to-all entanglement
    ``pauli_yzz`` Pauli feature map with Y and ZZ rotations
    """
    name = name.lower()
    if name == "z":
        return z_feature_map(n_qubits, reps=reps)
    if name == "zz":
        return zz_feature_map(n_qubits, reps=reps, entanglement="linear")
    if name == "zz_full":
        return zz_feature_map(n_qubits, reps=reps, entanglement="full")
    if name == "pauli_yzz":
        return pauli_feature_map(n_qubits, reps=reps, paulis=["Y", "ZZ"], entanglement="linear")
    raise ValueError(f"Unknown feature map {name!r}; choose from {FEATURE_MAPS}")


def compute_states(circuit, X: np.ndarray) -> np.ndarray:
    """Statevectors |phi(x)> for every row of X, shape (n_samples, 2**n_qubits)."""
    return np.array([Statevector(circuit.assign_parameters(x)).data for x in X])


def fidelity_kernel(states_a: np.ndarray, states_b: np.ndarray) -> np.ndarray:
    """Kernel matrix |<a_i|b_j>|^2."""
    return np.abs(states_a.conj() @ states_b.T) ** 2


class QuantumKernelSVM(BaseEstimator, ClassifierMixin):
    """Support-vector machine on a fidelity quantum kernel.

    Inputs are rotation angles in [0, pi] (see :class:`features.QuantumEncoder`);
    ``scale`` multiplies them and acts as the kernel bandwidth.
    """

    def __init__(self, feature_map="zz", reps=2, C=1.0, scale=1.0, probability=True, random_state=0):
        self.feature_map = feature_map
        self.reps = reps
        self.C = C
        self.scale = scale
        self.probability = probability
        self.random_state = random_state

    def _circuit(self, n_qubits):
        return build_feature_map(self.feature_map, n_qubits, self.reps)

    def fit(self, X, y, train_states=None):
        self.circuit_ = self._circuit(X.shape[1])
        self.train_states_ = train_states if train_states is not None else compute_states(self.circuit_, X * self.scale)
        K = fidelity_kernel(self.train_states_, self.train_states_)
        self.svc_ = SVC(kernel="precomputed", C=self.C, probability=self.probability,
                        random_state=self.random_state).fit(K, y)
        self.classes_ = self.svc_.classes_
        return self

    def _k(self, X):
        return fidelity_kernel(compute_states(self.circuit_, X * self.scale), self.train_states_)

    def decision_function(self, X):
        return self.svc_.decision_function(self._k(X))

    def predict_proba(self, X):
        return self.svc_.predict_proba(self._k(X))

    def predict(self, X):
        return self.svc_.predict(self._k(X))


def fit_qsvm_tuned(X, y, feature_map="zz", reps=2, c_grid=(0.1, 1, 10, 100),
                   scale_grid=(0.25, 0.5, 1.0), cv_folds=3, seed=0):
    """Tune (scale, C) by stratified CV ROC-AUC on the training data, then refit.

    Training statevectors are computed once per ``scale`` and re-used for every C
    and every CV fold, so tuning cost is ``len(scale_grid)`` state computations.
    Returns ``(model, cv_table)``.
    """
    circuit = build_feature_map(feature_map, X.shape[1], reps)
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=seed)
    best, table, cache = (-1.0, None, None), [], {}
    for scale in scale_grid:
        states = compute_states(circuit, X * scale)
        cache[scale] = states
        K = fidelity_kernel(states, states)
        for C in c_grid:
            auc = cross_val_score(SVC(kernel="precomputed", C=C), K, y, cv=cv, scoring="roc_auc").mean()
            table.append(dict(scale=scale, C=C, cv_auc=auc))
            if auc > best[0]:
                best = (auc, scale, C)
    _, scale, C = best
    model = QuantumKernelSVM(feature_map, reps, C=C, scale=scale, random_state=seed)
    model.fit(X, y, train_states=cache[scale])
    model.best_params_ = dict(scale=scale, C=C, cv_auc=best[0])
    return model, table


def train_vqc(Xtr, ytr, n_qubits: int, maxiter: int = 120, seed: int = 0):
    """Train Qiskit Machine Learning's VQC (ZZ feature map + RealAmplitudes ansatz, COBYLA).

    Returns the fitted classifier. Use :func:`vqc_scores` to obtain P(active).
    """
    from qiskit.circuit.library import real_amplitudes
    from qiskit.primitives import StatevectorSampler
    from qiskit_machine_learning.algorithms import VQC
    from qiskit_machine_learning.optimizers import COBYLA
    from qiskit_machine_learning.utils import algorithm_globals

    algorithm_globals.random_seed = seed
    vqc = VQC(
        feature_map=build_feature_map("zz", n_qubits, reps=1),
        ansatz=real_amplitudes(n_qubits, reps=2),
        optimizer=COBYLA(maxiter=maxiter),
        sampler=StatevectorSampler(seed=seed),
    )
    vqc.fit(Xtr, np.eye(2)[np.asarray(ytr, dtype=int)])  # VQC expects one-hot targets
    return vqc


def vqc_scores(vqc, X) -> np.ndarray:
    """P(class = 1) for each row, from the VQC's output distribution."""
    probs = vqc.neural_network.forward(X, vqc.weights)
    return np.asarray(probs)[:, 1]
