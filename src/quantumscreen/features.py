"""Molecular featurisation: fingerprints, drug-likeness and the qubit encoder."""
from __future__ import annotations

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem import QED, Crippen, Descriptors, Lipinski, rdFingerprintGenerator, rdMolDescriptors
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.decomposition import PCA

RDLogger.DisableLog("rdApp.*")


def morgan_matrix(smiles, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """Binary Morgan (ECFP-like) fingerprints, shape (n_molecules, n_bits), float32."""
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=n_bits)
    rows = []
    for s in smiles:
        m = Chem.MolFromSmiles(s)
        if m is None:
            raise ValueError(f"Invalid SMILES: {s!r}")
        rows.append(gen.GetFingerprintAsNumPy(m))
    return np.asarray(rows, dtype=np.float32)


def drug_likeness(smiles) -> pd.DataFrame:
    """Physicochemical properties, QED and Lipinski rule-of-five violations."""
    rows = []
    for s in smiles:
        m = Chem.MolFromSmiles(s)
        mw, logp = Descriptors.MolWt(m), Crippen.MolLogP(m)
        hbd, hba = Lipinski.NumHDonors(m), Lipinski.NumHAcceptors(m)
        try:
            qed = QED.qed(m)
        except Exception:  # pragma: no cover - extremely rare RDKit failures
            qed = np.nan
        viol = int(mw > 500) + int(logp > 5) + int(hbd > 5) + int(hba > 10)
        rows.append(dict(MW=mw, LogP=logp, HBD=hbd, HBA=hba,
                         TPSA=rdMolDescriptors.CalcTPSA(m),
                         RotB=rdMolDescriptors.CalcNumRotatableBonds(m),
                         QED=qed, lipinski_violations=viol, passes_lipinski=viol <= 1))
    return pd.DataFrame(rows)


class QuantumEncoder(BaseEstimator, TransformerMixin):
    """PCA(n_qubits) followed by min-max scaling to rotation angles in [0, pi].

    Fitted on the *training* fingerprints only (no leakage); test values are
    clipped to the fitted range. One PCA component is mapped to one qubit.
    """

    def __init__(self, n_qubits: int = 8, random_state: int = 0):
        self.n_qubits = n_qubits
        self.random_state = random_state

    def fit(self, X, y=None):
        self.pca_ = PCA(n_components=self.n_qubits, random_state=self.random_state).fit(X)
        Z = self.pca_.transform(X)
        self.lo_, self.hi_ = Z.min(axis=0), Z.max(axis=0)
        return self

    def transform(self, X):
        Z = (self.pca_.transform(X) - self.lo_) / (self.hi_ - self.lo_ + 1e-12)
        return np.clip(Z, 0.0, 1.0) * np.pi
