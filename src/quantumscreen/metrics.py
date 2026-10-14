"""Evaluation metrics: classification quality and virtual-screening enrichment."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score


def enrichment_factor(y_true, score, fraction: float = 0.10) -> float:
    """EF@fraction: hit-rate in the top-ranked fraction divided by the overall hit-rate.

    EF = 1 means no better than random picking; the maximum is ``1 / base_rate``.
    """
    y_true, score = np.asarray(y_true), np.asarray(score)
    k = max(1, int(round(fraction * len(y_true))))
    top = np.argsort(-score, kind="stable")[:k]
    return float(y_true[top].mean() / y_true.mean())


def precision_at_k(y_true, score, k: int) -> float:
    y_true, score = np.asarray(y_true), np.asarray(score)
    top = np.argsort(-score, kind="stable")[:k]
    return float(y_true[top].mean())


def classification_metrics(y_true, score, threshold: float = 0.5) -> dict:
    pred = (np.asarray(score) >= threshold).astype(int)
    return dict(
        auc=roc_auc_score(y_true, score),
        accuracy=accuracy_score(y_true, pred),
        precision=precision_score(y_true, pred, zero_division=0),
        recall=recall_score(y_true, pred, zero_division=0),
        f1=f1_score(y_true, pred, zero_division=0),
        ef10=enrichment_factor(y_true, score, 0.10),
    )
