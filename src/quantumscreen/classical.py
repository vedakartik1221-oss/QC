"""Classical baselines evaluated on exactly the same splits as the quantum models."""
from __future__ import annotations

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.svm import SVC


def fit_rbf_svm(X, y, c_grid=(0.1, 1, 10, 100), cv_folds=3, seed=0):
    """RBF-kernel SVM with (C, gamma) tuned by inner CV ROC-AUC. Same inputs as the quantum model."""
    grid = {"C": list(c_grid), "gamma": ["scale", 0.1, 1.0, 3.0]}
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=seed)
    gs = GridSearchCV(SVC(kernel="rbf", probability=True, random_state=seed), grid, cv=cv, scoring="roc_auc")
    gs.fit(X, y)
    return gs.best_estimator_, gs.best_params_


def fit_random_forest(X, y, seed=0, n_estimators=300):
    return RandomForestClassifier(n_estimators=n_estimators, random_state=seed, n_jobs=1).fit(X, y)
