# API reference

All modules live in `src/quantumscreen/`. Import with `from quantumscreen.<module> import ...`.

## `config`
**`Config`** (dataclass) - every tunable setting: paths, `max_molecules`, `test_size`, `seeds`, `fp_radius`, `fp_bits`,
`n_qubits`, `feature_map`, `reps`, `qubit_ablation`, `feature_map_ablation`, `c_grid`, `scale_grid`, `cv_folds`,
VQC settings (`vqc_qubits`, `vqc_train_size`, `vqc_maxiter`), ranking weights (`w_activity`, `w_qed`,
`lipinski_penalty`, `top_k`), VQE bond lengths. `Config.ensure_dirs()` creates the output folders.

## `data`
| Function | Description |
|---|---|
| `load_bace(path, max_molecules=None, seed=0)` | Load csv, canonicalise SMILES, drop invalid/duplicates. Returns DataFrame `[cid, smiles, label, pIC50]`. |
| `stratified_split(df, test_size, seed)` | Random split preserving class ratio. Returns `(train_idx, test_idx)`. |
| `scaffold_split(df, test_size)` | Deterministic Bemis-Murcko scaffold split. Returns `(train_idx, test_idx)`. |

## `features`
| Item | Description |
|---|---|
| `morgan_matrix(smiles, radius=2, n_bits=2048)` | Binary fingerprint matrix `(n, n_bits)`. |
| `drug_likeness(smiles)` | DataFrame: `MW, LogP, HBD, HBA, TPSA, RotB, QED, lipinski_violations, passes_lipinski`. |
| `QuantumEncoder(n_qubits)` | sklearn transformer: PCA to `n_qubits` components, scaled to angles in [0, pi]. `fit` on training data only. |

## `quantum`
| Item | Description |
|---|---|
| `FEATURE_MAPS` | `("z", "zz", "zz_full", "pauli_yzz")` |
| `build_feature_map(name, n_qubits, reps=2)` | Qiskit `QuantumCircuit` that encodes a data vector. |
| `compute_states(circuit, X)` | Statevectors for each row of `X` -> `(n, 2**n_qubits)` complex array. |
| `fidelity_kernel(states_a, states_b)` | Kernel matrix `abs(<a_i|b_j>)^2`. |
| `QuantumKernelSVM(feature_map, reps, C, scale, probability, random_state)` | sklearn-style classifier: `fit`, `predict`, `predict_proba`, `decision_function`. |
| `fit_qsvm_tuned(X, y, feature_map, reps, c_grid, scale_grid, cv_folds, seed)` | Tunes `(scale, C)` by inner CV, returns `(model, cv_table)`; `model.best_params_` holds the winners. |
| `train_vqc(Xtr, ytr, n_qubits, maxiter, seed)` | Trains Qiskit ML `VQC`. |
| `vqc_scores(vqc, X)` | `P(class = 1)` for each row. |

## `classical`
`fit_rbf_svm(X, y, c_grid, cv_folds, seed)` -> `(model, best_params)`; `fit_random_forest(X, y, seed, n_estimators=300)`.

## `metrics`
`classification_metrics(y, score, threshold=0.5)` -> dict (`auc, accuracy, precision, recall, f1, ef10`);
`enrichment_factor(y, score, fraction=0.10)`; `precision_at_k(y, score, k)`.

## `benchmark`
`run_split(...)`, `run_vqc_benchmark(...)`, `run_all(df, cfg, log, run_vqc=True)` -> `(runs, vqc_runs, roc_store)`,
`summarise(runs, group=...)` -> mean/std table.

## `ranking`
`rank_candidates(df_lib, p_active, cfg, p_classical=None)` -> ranked DataFrame with `rank, smiles, known_label,
p_quantum_active, QED, lipinski_violations, ..., final_score`.

## `pipeline`
| Function | Description |
|---|---|
| `final_screen(df, cfg, log)` | Train on 80 %, rank the held-out 20 %, compute screening metrics, save deployment models. |
| `save_model(model, encoder, path, meta)` / `load_model(path)` | Persist / restore `(encoder, QuantumKernelSVM, meta)`. |
| `screen_smiles(smiles, encoder, model, cfg)` | Score and rank any list of SMILES. |

## `selection`
| Item | Description |
|---|---|
| `tanimoto_matrix(smiles)` | Pairwise Morgan-fingerprint Tanimoto similarity (zero diagonal). |
| `SelectionProblem(scores, sim, k, lam=0.5, penalty=None)` | QUBO for diversity-aware selection. `.energies` (all 2^N QUBO energies), `.objective(x)`, `.ising()` -> `(h, J, const)`, `.hamiltonian()` -> `SparsePauliOp`. |
| `solve_exact(prob)`, `solve_topk(prob)`, `solve_greedy_diverse(prob)`, `random_baseline(prob, rng)` | Classical comparators; each returns `(x, J)` (the random baseline returns the mean J). |
| `QAOASolver(prob, p, restarts, maxiter, shots, seed)` | Qiskit QAOA. `.state(params)`, `.expectation(params)`, `.run()` -> dict with `x`, `objective`, `approx_ratio`, `feasible_mass`, `p_optimal`, `quality`, `random_quality`, `random_search_ratio`, `runtime`. |
| `run_selection_study(ranked, cfg, log)` | Many random shortlists: returns `(runs, lambda_table)`. |
| `real_case(ranked, cfg, n=12, p=3)` | Select K of the top-N candidates with top-K, exact and QAOA. |

## `vqe`
`vqe_curve(molecule, bond_lengths, maxiter=150)` with `molecule` in `{"H2", "LiH"}` -> DataFrame
`[bond_length_A, n_qubits, n_parameters, E_hf, E_exact, E_vqe, error_mHa]`.

## `plots`
One function per figure (`plot_main_comparison`, `plot_roc`, `plot_qubit_ablation`, `plot_featuremap_ablation`,
`plot_scaffold`, `plot_vqc`, `plot_vqe`, `plot_kernel_heatmap`, `plot_top_candidates`).
