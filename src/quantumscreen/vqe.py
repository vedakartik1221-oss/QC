"""Variational Quantum Eigensolver (VQE) for small molecules with Qiskit Nature.

Demonstrates the *quantum-chemistry* side of quantum drug discovery: computing a
molecule's ground-state energy (the quantity underlying binding-energy and
reactivity estimates) with a UCCSD ansatz, validated against exact diagonalisation
and Hartree-Fock. Only tiny molecules (H2, LiH) fit on a simulator/NISQ device.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from qiskit.primitives import StatevectorEstimator
from qiskit_algorithms import VQE, NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import SLSQP
from qiskit_nature.second_q.algorithms import GroundStateEigensolver
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import ParityMapper
from qiskit_nature.second_q.transformers import FreezeCoreTransformer

HARTREE_TO_MILLI = 1000.0
CHEMICAL_ACCURACY_MHA = 1.6


def _problem(molecule: str, d: float):
    atom = f"H 0 0 0; H 0 0 {d}" if molecule == "H2" else f"Li 0 0 0; H 0 0 {d}"
    problem = PySCFDriver(atom=atom, basis="sto3g").run()
    if molecule == "LiH":
        # freeze the 1s core and drop two non-bonding orbitals -> 3 spatial orbitals, 2 electrons
        problem = FreezeCoreTransformer(freeze_core=True, remove_orbitals=[3, 4]).transform(problem)
    return problem


def vqe_curve(molecule: str, bond_lengths, maxiter: int = 150) -> pd.DataFrame:
    """Potential-energy curve. Returns Hartree-Fock, exact (FCI in the active space) and VQE energies."""
    rows = []
    for d in bond_lengths:
        problem = _problem(molecule, d)
        mapper = ParityMapper(num_particles=problem.num_particles)  # + 2-qubit reduction
        hf = HartreeFock(problem.num_spatial_orbitals, problem.num_particles, mapper)
        ansatz = UCCSD(problem.num_spatial_orbitals, problem.num_particles, mapper, initial_state=hf)

        vqe = VQE(StatevectorEstimator(), ansatz, SLSQP(maxiter=maxiter), initial_point=np.zeros(ansatz.num_parameters))
        e_vqe = GroundStateEigensolver(mapper, vqe).solve(problem).total_energies[0].real
        e_exact = GroundStateEigensolver(mapper, NumPyMinimumEigensolver()).solve(problem).total_energies[0].real
        rows.append(dict(molecule=molecule, bond_length_A=d, n_qubits=ansatz.num_qubits,
                         n_parameters=ansatz.num_parameters, E_hf=problem.reference_energy,
                         E_exact=e_exact, E_vqe=e_vqe,
                         error_mHa=abs(e_vqe - e_exact) * HARTREE_TO_MILLI))
    return pd.DataFrame(rows)
