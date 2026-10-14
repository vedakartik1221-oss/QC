import numpy as np
import pytest

from quantumscreen.config import Config
from quantumscreen.data import load_bace, scaffold_split, stratified_split
from quantumscreen.features import QuantumEncoder, drug_likeness, morgan_matrix


@pytest.fixture(scope="module")
def df():
    return load_bace(Config().data_path, max_molecules=300)


def test_load_bace_clean(df):
    assert {"smiles", "label"} <= set(df.columns)
    assert df.smiles.is_unique and set(df.label.unique()) == {0, 1}


def test_stratified_split_disjoint_and_balanced(df):
    tr, te = stratified_split(df, 0.2, seed=1)
    assert not set(tr) & set(te) and len(tr) + len(te) == len(df)
    assert abs(df.label.values[tr].mean() - df.label.values[te].mean()) < 0.05


def test_scaffold_split_disjoint(df):
    tr, te = scaffold_split(df, 0.2)
    assert not set(tr) & set(te) and len(tr) + len(te) == len(df)


def test_fingerprints_shape(df):
    X = morgan_matrix(df.smiles[:10], 2, 1024)
    assert X.shape == (10, 1024) and set(np.unique(X)) <= {0.0, 1.0}


def test_encoder_range_no_leakage(df):
    X = morgan_matrix(df.smiles)
    enc = QuantumEncoder(6).fit(X[:200])
    Z = enc.transform(X[200:])
    assert Z.shape[1] == 6 and Z.min() >= 0 and Z.max() <= np.pi + 1e-9


def test_drug_likeness_columns():
    props = drug_likeness(["CC(=O)Oc1ccccc1C(=O)O"])  # aspirin
    assert props.loc[0, "lipinski_violations"] == 0 and 0 < props.loc[0, "QED"] < 1
