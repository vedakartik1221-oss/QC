"""Candidate ranking: combine the quantum activity score with drug-likeness."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Config
from .features import drug_likeness


def rank_candidates(df_lib: pd.DataFrame, p_active, cfg: Config, p_classical=None) -> pd.DataFrame:
    """Rank a screening library.

    ``final_score = w_activity * P(active) + w_qed * QED - penalty * max(0, violations - 1)``

    Lipinski is used as a *soft* penalty (one violation is tolerated, as in the rule
    of five) so that borderline molecules are de-prioritised rather than discarded. On
    BACE about 95 % of actives pass the rule, so it removes little signal but protects
    the shortlist from clearly non-drug-like molecules.
    """
    props = drug_likeness(df_lib["smiles"])
    out = df_lib.reset_index(drop=True).copy()
    out["p_quantum_active"] = np.asarray(p_active)
    if p_classical is not None:
        out["p_classical_active"] = np.asarray(p_classical)
    out = pd.concat([out, props], axis=1)
    penalty = cfg.lipinski_penalty * np.maximum(0, out["lipinski_violations"] - 1)
    out["final_score"] = cfg.w_activity * out["p_quantum_active"] + cfg.w_qed * out["QED"].fillna(0) - penalty
    out = out.sort_values("final_score", ascending=False).reset_index(drop=True)
    out.insert(0, "rank", np.arange(1, len(out) + 1))
    return out.rename(columns={"label": "known_label"})
