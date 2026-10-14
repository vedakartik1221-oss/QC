"""Dataset loading, cleaning and splitting.

The BACE dataset (MoleculeNet) holds 1513 inhibitors of human beta-secretase 1
(BACE-1), an Alzheimer's-disease target, labelled active (1) / inactive (0).
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem, RDLogger
from rdkit.Chem.Scaffolds import MurckoScaffold
from sklearn.model_selection import train_test_split

RDLogger.DisableLog("rdApp.*")


def load_bace(path: str | Path, max_molecules: int | None = None, seed: int = 0) -> pd.DataFrame:
    """Load and clean the BACE csv.

    Returns a DataFrame with columns ``smiles`` (canonical), ``label`` (0/1) and,
    when present, ``pIC50`` and ``cid``. Invalid SMILES and duplicates are dropped.
    """
    df = pd.read_csv(path).rename(columns={"mol": "smiles", "Class": "label", "CID": "cid"})
    if not {"smiles", "label"} <= set(df.columns):
        raise ValueError("CSV must contain a SMILES column ('mol' or 'smiles') and a label column ('Class' or 'label').")

    canon = []
    for s in df["smiles"]:
        m = Chem.MolFromSmiles(str(s))
        canon.append(Chem.MolToSmiles(m) if m is not None else None)
    df["smiles"] = canon
    df = df.dropna(subset=["smiles"]).drop_duplicates(subset="smiles").reset_index(drop=True)
    df["label"] = df["label"].astype(int)

    if max_molecules and len(df) > max_molecules:
        df, _ = train_test_split(df, train_size=max_molecules, stratify=df["label"], random_state=seed)
        df = df.reset_index(drop=True)
    cols = [c for c in ["cid", "smiles", "label", "pIC50"] if c in df.columns]
    return df[cols]


def stratified_split(df: pd.DataFrame, test_size: float, seed: int):
    """Random split preserving the active/inactive ratio. Returns (train_idx, test_idx)."""
    idx = np.arange(len(df))
    tr, te = train_test_split(idx, test_size=test_size, stratify=df["label"].values, random_state=seed)
    return np.sort(tr), np.sort(te)


def scaffold_split(df: pd.DataFrame, test_size: float):
    """Deterministic Bemis-Murcko scaffold split (DeepChem style).

    Large scaffold groups go to the training set first; the remaining (rarer)
    scaffolds form the test set. This is a harder, more realistic split than a
    random one because test molecules have chemotypes unseen in training.
    """
    groups = defaultdict(list)
    for i, s in enumerate(df["smiles"]):
        groups[MurckoScaffold.MurckoScaffoldSmiles(smiles=s)].append(i)
    ordered = sorted(groups.values(), key=lambda g: (len(g), g[0]), reverse=True)
    cutoff = len(df) - int(round(test_size * len(df)))
    train, test = [], []
    for g in ordered:
        (test if len(train) + len(g) > cutoff else train).extend(g)
    return np.sort(np.array(train)), np.sort(np.array(test))
