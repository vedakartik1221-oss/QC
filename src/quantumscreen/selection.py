"""Diversity-aware candidate selection with QAOA (Qiskit).

After the quantum-kernel model scores every molecule, a lab can only advance K of N shortlisted candidates.
Picking K molecules that are individually promising *and* mutually dissimilar (so one failed chemotype does not
sink the whole batch) is a quadratic binary optimisation problem:

    maximise   J(x) = sum_i s_i x_i  -  lam * sum_{i<j} S_ij x_i x_j      subject to  sum_i x_i = K

where s_i is a molecule's screening score (no experimental affinity is used) and S_ij the Tanimoto similarity of
two molecules. Because of the pairwise term, simply taking the top-K scores is *not* optimal in general; with
``lam = 0`` the problem degenerates to sorting (a useful sanity check, tested in ``tests/test_selection.py``).

The constraint is embedded as a QUBO penalty, mapped to an Ising Hamiltonian and solved with QAOA on a
statevector simulator, then compared with classical solvers (greedy, diversity-greedy, exact enumeration).
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp, Statevector
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from scipy.optimize import minimize

RDLogger.DisableLog("rdApp.*")


def tanimoto_matrix(smiles, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """Pairwise Tanimoto similarity of Morgan fingerprints (zero diagonal)."""
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=n_bits)
    fps = [gen.GetFingerprint(Chem.MolFromSmiles(s)) for s in smiles]
    S = np.array([DataStructs.BulkTanimotoSimilarity(f, fps) for f in fps])
    np.fill_diagonal(S, 0.0)
    return S


@dataclass
class SelectionProblem:
    scores: np.ndarray      # s_i, shape (N,)
    sim: np.ndarray         # S_ij, symmetric, zero diagonal
    k: int                  # budget
    lam: float = 0.5        # diversity weight
    penalty: float | None = None

    def __post_init__(self):
        self.scores = np.asarray(self.scores, float)
        self.n = len(self.scores)
        if not 1 <= self.k <= self.n:
            raise ValueError("budget k must satisfy 1 <= k <= N")
        if self.penalty is None:   # large enough that violating the budget never pays off
            self.penalty = 2.0 * (self.scores.max() + self.lam * self.sim.max())
        idx = np.arange(1 << self.n)
        self.bits = ((idx[:, None] >> np.arange(self.n)) & 1).astype(float)     # bit i = qubit i
        self._objective = self.bits @ self.scores - self.lam * ((self.bits @ self.sim) * self.bits).sum(1) / 2
        self._card = self.bits.sum(1)
        # QUBO energy to minimise: -J(x) + A (sum x - K)^2   (all 2^N values, used as the diagonal of H_C)
        self.energies = -self._objective + self.penalty * (self._card - self.k) ** 2

    # --- objective helpers -------------------------------------------------------------------
    def objective(self, x) -> float:
        x = np.asarray(x, float)
        return float(x @ self.scores - self.lam * x @ self.sim @ x / 2)

    def feasible_mask(self) -> np.ndarray:
        return self._card == self.k

    # --- Ising mapping x_i = (1 - Z_i)/2 ------------------------------------------------------
    def ising(self):
        """Return (h, J, const) with H_C = sum h_i Z_i + sum_{i<j} J_ij Z_i Z_j + const equal to the QUBO energy."""
        A, K, n = self.penalty, self.k, self.n
        a = -self.scores + A * (1 - 2 * K)                    # linear QUBO coefficients
        b = self.lam * self.sim + 2 * A * (1 - np.eye(n))     # quadratic QUBO coefficients (i != j)
        h = -a / 2 - b.sum(1) / 4
        J = np.triu(b, 1) / 4
        const = a.sum() / 2 + np.triu(b, 1).sum() / 4 + A * K ** 2
        return h, J, const

    def hamiltonian(self) -> SparsePauliOp:
        h, J, const = self.ising()
        terms = [("Z", [i], h[i]) for i in range(self.n)]
        terms += [("ZZ", [i, j], J[i, j]) for i in range(self.n) for j in range(i + 1, self.n)]
        terms.append(("", [], const))
        return SparsePauliOp.from_sparse_list(terms, num_qubits=self.n)


# --------------------------------------------------------------------------------------------
# classical solvers
# --------------------------------------------------------------------------------------------
def solve_exact(prob: SelectionProblem):
    """Enumerate all feasible subsets. Returns (x, J)."""
    feas = np.where(prob.feasible_mask())[0]
    best = feas[np.argmax(prob._objective[feas])]
    return prob.bits[best].astype(int), float(prob._objective[best])


def solve_topk(prob: SelectionProblem):
    """Greedy by score only (ignores diversity). Optimal when lam = 0."""
    x = np.zeros(prob.n, int)
    x[np.argsort(-prob.scores)[: prob.k]] = 1
    return x, prob.objective(x)


def solve_greedy_diverse(prob: SelectionProblem):
    """Sequential greedy on marginal gain s_i - lam * sum_{j selected} S_ij."""
    x = np.zeros(prob.n, int)
    for _ in range(prob.k):
        gain = prob.scores - prob.lam * (prob.sim @ x)
        gain[x == 1] = -np.inf
        x[int(np.argmax(gain))] = 1
    return x, prob.objective(x)


def random_baseline(prob: SelectionProblem, rng, n_draws: int = 200) -> float:
    """Mean objective of random feasible subsets."""
    feas = np.where(prob.feasible_mask())[0]
    return float(prob._objective[rng.choice(feas, size=min(n_draws, len(feas)))].mean())


# --------------------------------------------------------------------------------------------
# QAOA
# --------------------------------------------------------------------------------------------
class QAOASolver:
    """QAOA for a :class:`SelectionProblem` (cost layer RZ/RZZ, mixer RX, |+>^n start).

    The cost operator is rescaled by the energy range so that angles live on a comparable scale.
    The energy expectation is computed exactly from the statevector (noiseless simulation); the final
    answer is the best *feasible* bitstring among ``shots`` samples, with greedy repair if none is feasible.
    """

    def __init__(self, prob: SelectionProblem, p: int = 2, restarts: int = 4, maxiter: int = 80,
                 shots: int = 1024, seed: int = 0):
        self.prob, self.p, self.restarts, self.maxiter, self.shots, self.seed = prob, p, restarts, maxiter, shots, seed
        h, J, _ = prob.ising()
        self.scale = float(prob.energies.max() - prob.energies.min()) or 1.0
        self._E = (prob.energies - prob.energies.min()) / self.scale          # diagonal of the rescaled H_C
        self.h, self.J = h / self.scale, J / self.scale
        self.gamma = [Parameter(f"g{l}") for l in range(p)]
        self.beta = [Parameter(f"b{l}") for l in range(p)]
        self.circuit = self._build()

    def _build(self) -> QuantumCircuit:
        n = self.prob.n
        qc = QuantumCircuit(n)
        qc.h(range(n))
        for l in range(self.p):
            for i in range(n):
                qc.rz(2 * self.gamma[l] * self.h[i], i)
            for i in range(n):
                for j in range(i + 1, n):
                    qc.rzz(2 * self.gamma[l] * self.J[i, j], i, j)
            qc.rx(2 * self.beta[l], range(n))
        return qc

    def state(self, params) -> Statevector:
        bound = self.circuit.assign_parameters(dict(zip(self.gamma + self.beta, params)))
        return Statevector(bound)

    def expectation(self, params) -> float:
        return float(self.state(params).probabilities() @ self._E)

    def run(self) -> dict:
        rng = np.random.default_rng(self.seed)
        t0 = time.time()
        best = None
        for _ in range(self.restarts):
            x0 = np.concatenate([rng.uniform(0, 2 * np.pi, self.p), rng.uniform(0, np.pi / 2, self.p)])
            res = minimize(self.expectation, x0, method="COBYLA", options={"maxiter": self.maxiter, "rhobeg": 0.5})
            if best is None or res.fun < best.fun:
                best = res
        sv = self.state(best.x)
        probs = sv.probabilities()
        prob = self.prob
        feas = prob.feasible_mask()
        samples = rng.choice(len(probs), size=self.shots, p=probs / probs.sum())
        feasible_rate = float(feas[samples].mean())
        cand = samples[feas[samples]]
        if len(cand):
            pick = cand[np.argmax(prob._objective[cand])]
            repaired = False
        else:                                           # greedy repair of the most frequent shot
            pick = int(np.bincount(samples).argmax()); repaired = True
        x = prob.bits[pick].astype(int)
        if repaired:
            x = _repair(prob, x)
        _, j_opt = solve_exact(prob)
        opt_idx = np.where(feas)[0][np.argmax(prob._objective[feas])]
        # does QAOA concentrate probability on good subsets? compare the quality of its feasible outputs with random ones
        quality = float((probs[feas] * prob._objective[feas]).sum() / probs[feas].sum() / j_opt)
        random_quality = float(prob._objective[feas].mean() / j_opt)
        rs = rng.choice(np.where(feas)[0], size=self.shots)          # random search with the same number of shots
        return dict(x=x, objective=prob.objective(x), approx_ratio=prob.objective(x) / j_opt,
                    feasible_mass=float(probs[feas].sum()), feasible_rate_shots=feasible_rate,
                    p_optimal=float(probs[opt_idx]), quality=quality, random_quality=random_quality,
                    random_search_ratio=float(prob._objective[rs].max() / j_opt), expectation=best.fun * self.scale + prob.energies.min(),
                    params=best.x, repaired=repaired, runtime=time.time() - t0)


def _repair(prob: SelectionProblem, x: np.ndarray) -> np.ndarray:
    x = x.copy()
    while x.sum() > prob.k:                                # drop the least valuable selected molecule
        sel = np.where(x == 1)[0]
        x[sel[np.argmin(prob.scores[sel] - prob.lam * (prob.sim[sel] @ x))]] = 0
    while x.sum() < prob.k:                                # add the most valuable unselected molecule
        gain = prob.scores - prob.lam * (prob.sim @ x)
        gain[x == 1] = -np.inf
        x[int(np.argmax(gain))] = 1
    return x


# --------------------------------------------------------------------------------------------
# experiments
# --------------------------------------------------------------------------------------------
def run_selection_study(ranked, cfg, log=print):
    """Many random shortlists drawn from the top of the screening ranking; QAOA vs classical solvers.

    Returns ``(runs, lam_table)``: one row per (pool, N, method/p), and the sensitivity of score-only top-K to ``lam``.
    """
    import pandas as pd
    pool = ranked.head(cfg.sel_pool_top)
    smiles, scores = pool["smiles"].values, pool["final_score"].values
    S_full = tanimoto_matrix(smiles)
    rows = []
    for n in cfg.sel_sizes:
        k = max(3, n // 3)
        for pid in range(cfg.sel_pools):
            rng = np.random.default_rng(1000 * n + pid)
            idx = rng.choice(len(pool), n, replace=False)
            prob = SelectionProblem(scores[idx], S_full[np.ix_(idx, idx)], k, lam=cfg.sel_lambda)
            _, j_opt = solve_exact(prob)
            base = dict(N=n, K=k, pool=pid, n_feasible=int(prob.feasible_mask().sum()))
            rows.append(dict(**base, method="Top-K by score", p=0, ratio=solve_topk(prob)[1] / j_opt))
            rows.append(dict(**base, method="Greedy (diversity-aware)", p=0, ratio=solve_greedy_diverse(prob)[1] / j_opt))
            rows.append(dict(**base, method="Random feasible subset", p=0, ratio=random_baseline(prob, rng) / j_opt))
            for p in cfg.sel_p:
                r = QAOASolver(prob, p=p, restarts=cfg.sel_restarts, maxiter=cfg.sel_maxiter, shots=cfg.sel_shots, seed=pid).run()
                rows.append(dict(**base, method="QAOA (best feasible of shots)", p=p, ratio=r["approx_ratio"], feasible_mass=r["feasible_mass"],
                                 p_optimal=r["p_optimal"], quality=r["quality"], random_quality=r["random_quality"],
                                 random_search_ratio=r["random_search_ratio"], runtime=r["runtime"], repaired=r["repaired"]))
        log(f"[select] N={n}, K={k}: {cfg.sel_pools} pools done")
    runs = pd.DataFrame(rows)

    lam_rows = []
    n, k = max(cfg.sel_sizes), max(3, max(cfg.sel_sizes) // 3)
    for lam in cfg.sel_lambda_grid:
        for pid in range(cfg.sel_pools * 3):
            rng = np.random.default_rng(777 + pid)
            idx = rng.choice(len(pool), min(n, 12), replace=False)
            prob = SelectionProblem(scores[idx], S_full[np.ix_(idx, idx)], max(3, len(idx) // 3), lam=lam)
            lam_rows.append(dict(lam=lam, topk_ratio=solve_topk(prob)[1] / solve_exact(prob)[1],
                                 topk_is_optimal=bool(np.array_equal(solve_topk(prob)[0], solve_exact(prob)[0]))))
    return runs, pd.DataFrame(lam_rows)


def real_case(ranked, cfg, n: int = 12, p: int = 3):
    """Select K of the top-N ranked candidates: top-K vs diversity-aware exact vs QAOA. Returns a DataFrame."""
    import pandas as pd
    pool = ranked.head(n).reset_index(drop=True)
    k = max(3, n // 3)
    prob = SelectionProblem(pool["final_score"].values, tanimoto_matrix(pool["smiles"]), k, lam=cfg.sel_lambda)
    res = QAOASolver(prob, p=p, restarts=cfg.sel_restarts, maxiter=cfg.sel_maxiter, shots=cfg.sel_shots, seed=0).run()
    xs = {"top-K by score": solve_topk(prob), "diversity-aware exact": solve_exact(prob), "QAOA": (res["x"], res["objective"])}
    out = pool[["rank", "smiles", "known_label", "p_quantum_active", "QED", "final_score"]].copy()
    for name, (x, j) in xs.items():
        out[name] = x
    meta = {name: dict(objective=float(j), mean_pairwise_similarity=float(prob.sim[np.ix_(x == 1, x == 1)].sum() / (k * (k - 1))))
            for name, (x, j) in xs.items()}
    return out, meta, prob, res
