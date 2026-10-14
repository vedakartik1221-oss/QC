const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, ShadingType,
  ImageRun, AlignmentType, PageBreak, Footer, PageNumber, LevelFormat, BorderStyle,
} = require("docx");

const N = JSON.parse(fs.readFileSync(__dirname + "/numbers.json", "utf8"));
const ROOT = __dirname + "/..";
const PURPLE = "4B2A91", FONT = "Arial", W = 9026;

const run = (t, o = {}) => new TextRun({ text: t, font: FONT, ...o });
// inline **bold** support
const runs = (text) => text.split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((s) =>
  s.startsWith("**") ? run(s.slice(2, -2), { bold: true }) : run(s));
const p = (text, o = {}) => new Paragraph({ children: runs(text), spacing: { after: 120, line: 276 }, ...o });
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [run(t, { bold: true, size: 32, color: PURPLE })], spacing: { before: 320, after: 140 } });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [run(t, { bold: true, size: 25, color: "333333" })], spacing: { before: 220, after: 100 } });
const bullets = (items) => items.map((t) => new Paragraph({ numbering: { reference: "bul", level: 0 }, children: runs(t), spacing: { after: 70, line: 270 } }));
const numConfigs = [];
const numbered = (items) => {
  const ref = "num" + numConfigs.length;
  numConfigs.push({ reference: ref, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] });
  return items.map((t) => new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs(t), spacing: { after: 70, line: 270 } }));
};
const caption = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 200 }, children: [run(t, { italics: true, size: 18, color: "555555" })] });

const border = { style: BorderStyle.SINGLE, size: 4, color: "BBBBBB" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(headers, rows, widths) {
  const cell = (t, w, head) => new TableCell({
    width: { size: w, type: WidthType.DXA }, borders,
    shading: head ? { fill: "E8DFF7", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: [run(String(t), { bold: head, size: 19 })] })],
  });
  return new Table({
    width: { size: W, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, widths[i], true)) }),
           ...rows.map((r) => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, widths[i], false)) }))],
  });
}
function fig(key, widthPx) {
  const f = N.figs[key];
  const h = Math.round((widthPx * f.h) / f.w);
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 },
    children: [new ImageRun({ type: "png", data: fs.readFileSync(`${ROOT}/${f.path}`), transformation: { width: widthPx, height: h },
      altText: { title: key, description: key, name: key } })] });
}
const gap = () => new Paragraph({ children: [], spacing: { after: 120 } });
const S = N.scr;

const c = [];
// ---------------- title page ----------------
c.push(new Paragraph({ spacing: { before: 2200 }, alignment: AlignmentType.CENTER, children: [run("CAPSTONE PROJECT REPORT", { size: 24, color: "777777", bold: true })] }));
c.push(new Paragraph({ spacing: { before: 400, after: 120 }, alignment: AlignmentType.CENTER, children: [run("QuantumScreen", { size: 64, bold: true, color: PURPLE })] }));
c.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 }, children: [run("A Quantum Computing-Based Drug Screening System to Identify Promising Drug Candidates", { size: 30 })] }));
c.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [run("Hybrid quantum-classical virtual screening for BACE-1 inhibitors using Qiskit", { size: 22, italics: true, color: "555555" })] }));
c.push(new Paragraph({ spacing: { before: 1800 }, alignment: AlignmentType.CENTER, children: [run("G Veda Kartik", { size: 28, bold: true })] }));
c.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [run("Roll No. CH.SC.U4CSE24212", { size: 24 })] }));
c.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [run("B.Tech Computer Science and Engineering", { size: 24 })] }));
c.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [run("Amrita Vishwa Vidyapeetham, Chennai", { size: 24 })] }));
c.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200 }, children: [run("Course: Quantum Computing  |  October 2026", { size: 22, color: "555555" })] }));
c.push(new Paragraph({ children: [new PageBreak()] }));

// ---------------- abstract ----------------
c.push(h1("Abstract"));
c.push(p("Virtual screening ranks large molecule libraries by their likelihood of binding a disease target so that only the most promising compounds are tested in the laboratory. This project builds **QuantumScreen**, a hybrid quantum-classical screening system implemented in Qiskit. Molecules from the BACE dataset (1513 inhibitors of beta-secretase 1, an Alzheimer's-disease target) are converted to Morgan fingerprints, compressed by PCA to 8 components and encoded into an 8-qubit quantum state by a ZZ feature map. A quantum-kernel support-vector machine scores each molecule, and candidates are ranked by combining the quantum activity probability with drug-likeness (QED and Lipinski's rule of five). A QAOA stage then chooses a batch of K mutually dissimilar candidates from the top of the ranking, and a Variational Quantum Classifier (VQC) and a Variational Quantum Eigensolver (VQE) module for H2 and LiH complete the quantum toolkit."));
c.push(p(`The quantum models are benchmarked against classical models on identical splits. The quantum-kernel SVM reaches a ROC-AUC of **0.873 ± 0.011** and an enrichment factor of **2.07** at 10 % (maximum possible 2.2), statistically indistinguishable from a classical RBF-SVM on the same features (0.879 ± 0.007) and below a Random Forest on the full fingerprint (0.916 ± 0.006). On a held-out library, the quantum score placed ${Math.round(S.precision_at_k_quantum_score * S.top_k)} actives in its top ${S.top_k}. The VQC was much slower and less accurate (0.625 ± 0.056), while VQE reproduced exact ground-state energies to below 0.001 mHa. For batch selection, a diversity-aware QUBO solved by QAOA reached 99 to 100 % of the optimum, but random search with the same number of shots did equally well. All circuits were simulated classically; **no quantum advantage was observed**, and the report analyses why.`));

// ---------------- 1 intro ----------------
c.push(h1("1. Introduction"));
c.push(p("Bringing a drug to market takes more than a decade and billions of dollars, and most candidates fail. Computational screening reduces this cost by predicting which molecules in a very large library are likely to be active, so that chemists synthesise and test only a short list. Machine-learning models trained on known actives and inactives (ligand-based screening) are a standard tool for this."));
c.push(p("Quantum computing offers two routes into this workflow. First, **quantum machine learning** encodes data in the exponentially large state space of a qubit register; a quantum kernel measures similarity between molecules in that space and can be used by classical algorithms such as the SVM. Second, **quantum chemistry** algorithms such as the VQE compute molecular energies, which underlie binding and reactivity. Present-day devices are noisy and small (the NISQ era), so practical projects use hybrid methods and simulation."));
c.push(h2("1.1 Problem statement"));
c.push(p("Develop a Quantum Computing-based Drug Screening System to identify promising drug candidates."));
c.push(h2("1.2 Objectives"));
c.push(...numbered([
  "Build an end-to-end screening pipeline in Qiskit, from SMILES strings to a ranked list of candidates.",
  "Implement quantum-kernel and variational quantum classifiers for activity prediction on a real drug target (BACE-1).",
  "Benchmark the quantum models against classical machine learning fairly (same splits, same features, same tuning budget).",
  "Rank candidates by combining predicted activity with drug-likeness, and choose a diverse batch of K candidates with QAOA.",
  "Demonstrate the quantum-chemistry route with VQE on small molecules.",
  "Deliver reproducible code, tests, documentation and a demo user interface.",
]));

// ---------------- 2 background ----------------
c.push(h1("2. Background"));
c.push(h2("2.1 Quantum feature maps and kernels"));
c.push(p("A feature map is a parameterised circuit U(x) that loads a data vector x into a quantum state |φ(x)⟩ = U(x)|0…0⟩. The fidelity kernel k(x, x′) = |⟨φ(x)|φ(x′)⟩|² measures the similarity of two molecules in a Hilbert space of dimension 2ⁿ. Because the resulting Gram matrix is positive semi-definite, it can be passed to a standard SVM (the idea behind the QSVC of Havlíček et al.). We compare four encodings: a plain Z map (no entanglement), the ZZ map with nearest-neighbour entanglement, the ZZ map with all-to-all entanglement, and a Pauli (Y, ZZ) map."));
c.push(h2("2.2 Variational Quantum Classifier"));
c.push(p("A VQC combines a feature map with a trainable ansatz (here RealAmplitudes). A classical optimiser (COBYLA) adjusts the circuit parameters to minimise a loss, and class probabilities are read from the measurement distribution. Every optimiser step evaluates all training circuits, which makes training expensive."));
c.push(h2("2.3 Variational Quantum Eigensolver"));
c.push(p("VQE minimises the energy expectation ⟨ψ(θ)|H|ψ(θ)⟩ of a molecular Hamiltonian over circuit parameters, giving an upper bound on the ground-state energy. We use the UCCSD ansatz started from the Hartree-Fock state, with the Hamiltonian built from PySCF in the STO-3G basis and mapped to qubits with the parity mapper."));

c.push(h2("2.4 QAOA for candidate selection"));
c.push(p("The Quantum Approximate Optimization Algorithm solves binary optimisation problems by encoding the cost in an Ising Hamiltonian H_C and alternating p layers of the cost unitary exp(-iγH_C) and a mixer exp(-iβΣX) on a uniform superposition; the angles are tuned by a classical optimiser. We use it to choose K of N shortlisted molecules that are individually promising and mutually dissimilar."));

// ---------------- 3 data ----------------
c.push(h1("3. Dataset and Preprocessing"));
c.push(p("The **BACE** dataset from MoleculeNet contains 1513 inhibitors of human beta-secretase 1 (BACE-1), labelled active or inactive on a potency threshold of roughly IC50 = 100 nM (pIC50 = 7). After RDKit validation, canonicalisation and de-duplication, all 1513 molecules were kept (45.7 % active). The dataset's own labels were not modified."));
c.push(...numbered([
  "**Fingerprints:** 2048-bit Morgan (radius 2) fingerprints.",
  "**Compression:** PCA to n components (one per qubit; default 8). In the training split these 8 components keep about 36 % of the fingerprint variance.",
  "**Angle encoding:** components are min-max scaled to [0, π]; PCA and scaler are fitted on training data only to avoid leakage.",
  "**Splits:** 80/20 stratified random splits for 3 seeds, plus one deterministic Bemis-Murcko scaffold split to test generalisation to unseen chemotypes.",
]));

// ---------------- 4 design ----------------
c.push(h1("4. System Design"));
c.push(p("QuantumScreen is a hybrid pipeline: classical software prepares molecules and optimises the SVM, while Qiskit circuits supply the quantum feature space. A parallel branch trains classical baselines on exactly the same splits and features."));
c.push(table(["Stage", "Tool", "Output"], [
  ["Data cleaning and splitting", "RDKit, scikit-learn", "Canonical SMILES; random and scaffold splits"],
  ["Featurisation", "RDKit, PCA", "8 rotation angles per molecule"],
  ["Quantum encoding", "Qiskit feature maps, Statevector", "|φ(x)⟩ for every molecule"],
  ["Quantum kernel", "NumPy on statevectors", "Gram matrix |⟨φ(x)|φ(x′)⟩|²"],
  ["Classification", "scikit-learn SVM (precomputed kernel)", "P(active), tuned by inner cross-validation"],
  ["Ranking", "RDKit QED, Lipinski", "final score = 0.7·P(active) + 0.3·QED − 0.10·max(0, violations − 1)"],
  ["Batch selection", "QUBO, Ising mapping, Qiskit QAOA", "Diverse batch of K candidates from the top-ranked shortlist"],
  ["Quantum chemistry", "Qiskit Nature, PySCF, VQE", "Potential-energy curves of H2 and LiH"],
  ["Interface", "Streamlit", "Single-molecule scoring, batch screening, results browser"],
], [2300, 3000, 3726]));
c.push(gap());

// ---------------- 5 implementation ----------------
c.push(h1("5. Implementation"));
c.push(p("The code is organised as a Python package (src/quantumscreen) with a command-line entry point (main.py), a Streamlit application (app.py), an executed Jupyter notebook and a pytest suite. Software versions: Qiskit 2.5.2, Qiskit Machine Learning 0.9.1, Qiskit Nature 0.8.0, Qiskit Algorithms 0.4.0, RDKit 2026.03, scikit-learn 1.8."));
c.push(h2("5.1 Exact statevector kernel"));
c.push(p("Qiskit Machine Learning's FidelityQuantumKernel runs one overlap circuit per pair of molecules, which scales as N². Because the simulation is exact and noiseless, we instead compute each molecule's statevector once and obtain the whole kernel as |S_A† S_B|². This is mathematically identical, matches the official implementation to about 10⁻¹² (verified in the test suite) and makes it possible to use all 1513 molecules. On real hardware the kernel entries would have to be estimated from finite shots."));
c.push(h2("5.2 Fair tuning and baselines"));
c.push(p("The kernel scale (a bandwidth multiplying the angles) and the SVM parameter C are chosen by 3-fold cross-validated ROC-AUC on the training split only. The classical RBF-SVM receives the same inner-CV budget over C and gamma and the same 8 PCA features, so differences reflect the kernel rather than the data or tuning. A Random Forest is evaluated both on the same 8 features and on the full fingerprint."));
c.push(h2("5.3 Testing and reproducibility"));
c.push(p("Twenty-one automated tests cover splits, encoder ranges, kernel properties (unit diagonal, symmetry, positive semi-definiteness), equivalence with Qiskit's FidelityQuantumKernel, the SVM, the enrichment metric, ranking, the QUBO-to-Ising mapping (exact to 1e-14), the QAOA circuit against exact matrix evolution, and the VQE ground-state energy of H2. All randomness is seeded and dependency versions are pinned."));

// ---------------- 6 results ----------------
c.push(h1("6. Experiments and Results"));
c.push(p("Random-split results are the mean ± standard deviation over 3 seeds on the full dataset. EF@10 % is the enrichment factor: the hit-rate in the top-ranked 10 % divided by the overall hit-rate (1 = random, maximum about 2.2 for this dataset)."));
c.push(h2("6.1 Quantum versus classical"));
c.push(table(["Model", "ROC-AUC", "Accuracy", "F1", "EF@10%", "Fit (s)"], N.main, [3026, 1600, 1250, 900, 1050, 1200]));
c.push(fig("cmp", 540)); c.push(caption("Figure 1. ROC-AUC of the headline models (mean ± std over 3 seeds)."));
c.push(p("The quantum-kernel SVM and the classical RBF-SVM that sees the same 8 features are statistically indistinguishable: the 0.006 AUC gap is smaller than one standard deviation of either. Both are below the Random Forest on the full fingerprint, which retains far more information. The quantum model takes about 2.5 times longer to fit because it is simulated on a classical CPU."));
c.push(fig("roc", 360)); c.push(caption("Figure 2. ROC curves on the hold-out set (seed 0)."));
c.push(h2("6.2 Feature-map ablation"));
c.push(table(["Feature map (8 qubits)", "ROC-AUC", "EF@10%"], N.fm, [4026, 2800, 2200]));
c.push(fig("fm", 420)); c.push(caption("Figure 3. Feature-map ablation."));
c.push(p("All five encodings lie within 0.012 AUC of each other, which is inside the seed-to-seed noise. The un-entangled Z map (0.877) performs as well as the entangling maps, so on this data entanglement does not appear to drive performance."));
c.push(h2("6.3 Number of qubits"));
c.push(table(["Qubits", "Quantum kernel SVM", "Classical RBF SVM", "Quantum fit (s)", "Classical fit (s)"], N.qubits, [1000, 2400, 2400, 1600, 1626]));
c.push(fig("qb", 400)); c.push(caption("Figure 4. Effect of the number of qubits (PCA components)."));
c.push(p("Accuracy rises from 4 to 8 qubits for both families and then plateaus. The classical SVM is at least as good at every size and the gap closes at 8 qubits."));
c.push(h2("6.4 Generalisation to new chemotypes"));
c.push(table(["Model", "Random AUC", "Scaffold AUC", "Scaffold EF@10%"], N.scaffold, [3926, 1700, 1700, 1700]));
c.push(fig("sc", 480)); c.push(caption("Figure 5. Random versus scaffold split."));
c.push(p("When the test molecules have scaffolds unseen in training, every model degrades sharply (AUC falls by 0.13 to 0.21). The quantum and classical SVMs again perform alike (0.677 versus 0.667). This is a single deterministic split, so no standard deviation is available and small differences should not be over-interpreted."));
c.push(h2("6.5 Variational quantum classifier"));
c.push(table(["Model (200 training molecules, 6 qubits)", "ROC-AUC", "F1", "Fit time (s)"], N.vqc, [4426, 1900, 1100, 1600]));
c.push(fig("vqc", 440)); c.push(caption("Figure 6. VQC versus kernel SVM and classical SVM on a small training set."));
c.push(p("The VQC (ZZ feature map, RealAmplitudes ansatz, 120 COBYLA iterations) is clearly worse than the quantum-kernel SVM and about 90 times slower to train. It was not hyper-parameter tuned and is probably under-trained, so this shows the practical cost of variational training rather than a fundamental limit."));
c.push(h2("6.6 Virtual screening of a hold-out library"));
c.push(p(`A model trained on 80 % of BACE ranked the unseen 20 % (${S.library_size} molecules, ${(S.base_hit_rate * 100).toFixed(1)} % truly active).`));
c.push(table(["Ranking", `Precision@${S.top_k}`, "EF@10%"], N.screen, [5426, 1800, 1800]));
c.push(fig("top", 440)); c.push(caption("Figure 7. Top 15 candidates by final score (purple: known active; orange: known inactive)."));
c.push(p(`The quantum score places ${Math.round(S.precision_at_k_quantum_score * S.top_k)} actives in its top ${S.top_k} and the drug-likeness-adjusted ranking places ${Math.round(S.precision_at_k_final_score * S.top_k)}. This is a single split, and the difference to the classical score (${Math.round(S.precision_at_k_classical * S.top_k)} of ${S.top_k}) is three molecules, so it is suggestive rather than significant; the 3-seed EF@10 % is the more reliable comparison (quantum 2.07, classical SVM 1.98, Random Forest 2.10). Adding QED trades a little hit-rate for more drug-like shortlists. Lipinski's rule barely discriminates here: ${(S.actives_passing_lipinski * 100).toFixed(0)} % of actives and ${(S.inactives_passing_lipinski * 100).toFixed(0)} % of inactives pass.`));
c.push(fig("ker", 300)); c.push(caption("Figure 8. Quantum kernel matrix of 150 test molecules, sorted by class."));
c.push(p(`The kernel matrix is bright only on the diagonal and for similar molecules: most pairs of molecules are nearly orthogonal in the quantum feature space, a known "kernel concentration" effect. Cross-validation accordingly selects a small angle scale (${S.quantum_best_params.scale}).`));

c.push(h2("6.8 Diversity-aware batch selection with QAOA"));
c.push(p("A laboratory can advance only K of N shortlisted molecules. We choose K candidates that maximise J(x) = Σ sᵢxᵢ − λ Σ Sᵢⱼ xᵢxⱼ, where sᵢ is the screening score (model output, QED and Lipinski penalty; **no experimental affinity is used, since it would leak the answer**) and Sᵢⱼ is the Tanimoto similarity of two molecules (λ = 0.5). The budget is embedded as a QUBO penalty and mapped to an Ising Hamiltonian (verified exactly), and solved with QAOA (p = 1 to 3, Qiskit statevector simulation, COBYLA) and with classical solvers. Results are means over " + N.qaoa.pools + " random shortlists per size, drawn from the 40 best-ranked hold-out molecules."));
c.push(table(["Objective / exact optimum", "N=8", "N=10", "N=12", "N=14"], N.qaoa.A, [3826, 1300, 1300, 1300, 1300]));
c.push(gap());
c.push(fig("sel", 570)); c.push(caption("Figure 9. Left: solution quality. Middle: QAOA output quality relative to random feasible subsets. Right: score-only top-K versus the diversity weight λ."));
c.push(p("**The problem is non-trivial:** score-only top-K reaches only 78 to 92 % of the optimum and degrades with N, and it is exactly optimal only when λ = 0. **QAOA's best sample and a diversity-aware classical greedy both reach 99 to 100 % of the optimum, but random search with the same 1024 shots does equally well**, because the search spaces are small (56 to 1001 feasible subsets). The honest diagnostic is the whole output distribution:"));
c.push(table(["N", "Feasible subsets", "QAOA feasible mass (p=3)", "QAOA P(optimal)", "Uniform over feasible", "QAOA quality / random", "Run time (s)"], N.qaoa.B, [700, 1250, 1500, 1300, 1300, 1676, 1300]));
c.push(gap());
c.push(p("QAOA's output quality is 1.00 times that of random feasible subsets and its probability on the optimal subset is below uniform sampling of feasible subsets (for example 0.0003 versus 0.001 at N = 14), because only about a third of its probability mass is feasible with the penalty-embedded constraint. With p ≤ 3 and a small optimiser budget (3 restarts, 60 iterations), QAOA therefore did not concentrate probability on good subsets, and we claim no quantum advantage. Simulation cost grows as 2^N (about 11 s per run at N = 14)."));
c.push(p("**Real case.** Selecting 4 of the 12 best-ranked candidates:"));
c.push(table(["Method (N = 12, K = 4)", "Objective J", "Mean pairwise Tanimoto"], N.qaoa.R, [4426, 2000, 2600]));
c.push(fig("mol", 400)); c.push(caption("Figure 10. The four molecules chosen by each method (rank and screening score shown)."));
c.push(p("Score-only top-K picks three near-duplicate analogues (mean similarity 0.46), whereas QAOA and the exact diversity-aware solver choose chemically varied sets (mean similarity about 0.14, objective 2.88 versus 1.96); QAOA's set differs from the exact optimum by one molecule (ratio 0.999)."));

c.push(h2("6.9 VQE for H2 and LiH"));
c.push(table(["Molecule", "Qubits", "Parameters", "Bond lengths", "Max error vs exact (mHa)", "HF error at equilibrium (mHa)"], N.vqe, [1700, 1000, 1350, 1300, 1800, 1876]));
c.push(fig("vqe", 560)); c.push(caption("Figure 11. Potential-energy curves: Hartree-Fock, exact (FCI) and VQE."));
c.push(p("VQE with a UCCSD ansatz reproduces the exact ground-state energy far inside chemical accuracy (1.6 mHa) at every bond length and recovers the correlation energy that Hartree-Fock misses. The H2 equilibrium energy of −1.137 Ha at 0.74 Å matches the literature STO-3G value. These are noiseless statevector simulations with exact expectation values, so near-zero error is expected; real hardware would add shot noise and gate errors."));

// ---------------- 7 discussion ----------------
c.push(h1("7. Discussion"));
c.push(p("**The quantum model works but does not win.** The quantum-kernel SVM is a competent classifier (AUC 0.87, EF@10 % 2.07 out of a possible 2.2), yet it ties a classical RBF-SVM on identical inputs. Several observations suggest why:"));
c.push(...bullets([
  "**Information bottleneck.** Compressing 2048 fingerprint bits into 8 qubits keeps only about 36 % of the variance. A Random Forest that sees the full fingerprint beats every 8-feature model (0.916 versus 0.87 to 0.88), so the compression, not the kernel, limits accuracy.",
  "**Entanglement is not contributing.** The un-entangled Z map scores the same as the ZZ and Pauli maps, and deeper circuits do not help.",
  "**Kernel concentration.** Most molecule pairs are nearly orthogonal in the quantum feature space, which forces a small bandwidth and limits how much a kernel can generalise.",
  "**More qubits did not help beyond 8**, because the extra PCA components add little signal.",
  "**Variational training is costly.** The VQC needs about 90 times more time than the kernel SVM and still scores lower.",
  "**QAOA is matched by random search.** For batch selection the diversity-aware QUBO is genuinely non-trivial (top-K by score reaches only 78 to 92 % of the optimum), yet with at most 1001 feasible subsets random sampling with the same shots finds equally good batches, and QAOA's output distribution is no better than random.",
]));
c.push(p("**What the project does show.** A complete, tested and reproducible hybrid quantum-classical screening pipeline; a fair benchmark methodology (identical splits, features and tuning; repeated seeds; scaffold split; enrichment metrics); a ranking procedure that couples quantum predictions with drug-likeness; and a quantum-chemistry demonstration whose energies agree with exact results."));

// ---------------- 8 limitations ----------------
c.push(h1("8. Limitations and Future Work"));
c.push(h2("8.1 Limitations"));
c.push(...bullets([
  "All circuits are simulated classically and noiselessly. No speed-up is measured or claimed, and real devices would add noise and shot-noise in the kernel estimate.",
  "One qubit per PCA component restricts the encoding to 4 to 10 qubits; exact simulation cost grows as 2ⁿ.",
  "BACE covers one target with 1513 molecules; the results do not establish generalisation to other targets or truly novel chemistry (the scaffold split is a first step).",
  "Scoring is ligand-based; no protein-ligand docking or binding free-energy calculation is performed.",
  "VQE is demonstrated on molecules far smaller than any drug and is not numerically coupled to the classifier.",
  "QAOA is simulated for at most 14 qubits with a penalty-embedded budget (only about a third of the probability mass is feasible) and a small optimiser budget; the diversity weight λ is a heuristic modelling choice.",
  "The ranking weights (0.7 / 0.3 / 0.10) are heuristic, and probabilities are Platt-scaled approximations.",
]));
c.push(h2("8.2 Future work"));
c.push(...bullets([
  "Run the best circuits on IBM Quantum hardware with error mitigation and quantify the noise penalty; study finite-shot kernels with Qiskit Aer noise models.",
  "Replace PCA with a learned low-dimensional embedding (for example an autoencoder) before the quantum layer; try trainable feature maps and kernel alignment.",
  "Add a docking or MM-GBSA stage and use VQE-computed fragment energies to re-rank the top candidates.",
  "Use constraint-preserving XY mixers and warm-started QAOA for the selection stage, and test larger shortlists on tensor-network simulators or hardware.",
  "Extend the benchmark to more targets and more seeds, with statistical significance tests.",
]));

// ---------------- 9 conclusion ----------------
c.push(h1("9. Conclusion"));
c.push(p("QuantumScreen demonstrates how quantum machine learning and quantum chemistry can be combined into a drug-screening workflow with Qiskit. The quantum-kernel SVM identified active BACE-1 inhibitors with ROC-AUC 0.87 and enrichment close to the theoretical maximum, matching a classical SVM on the same features while not surpassing it; the strongest model overall was a classical Random Forest on the full fingerprint. A diversity-aware QAOA stage produced near-optimal, chemically varied batches of candidates, although random search matched it. VQE reproduced exact molecular energies for H2 and LiH. Honest benchmarking shows that, on current simulators and for this task, quantum models are competitive but not superior, and it identifies the feature-compression step as the main obstacle. The released code, tests and documentation make the study fully reproducible and a base for hardware experiments."));

// ---------------- references ----------------
c.push(h1("References"));
c.push(...numbered([
  "V. Havlíček et al., “Supervised learning with quantum-enhanced feature spaces,” Nature 567, 209-212 (2019).",
  "A. Peruzzo et al., “A variational eigenvalue solver on a photonic quantum processor,” Nature Communications 5, 4213 (2014).",
  "Z. Wu et al., “MoleculeNet: a benchmark for molecular machine learning,” Chemical Science 9, 513-530 (2018).",
  "G. Subramanian et al., “Computational modeling of β-secretase 1 (BACE-1) inhibitors using ligand based approaches,” J. Chem. Inf. Model. 56, 1936-1949 (2016).",
  "G. R. Bickerton et al., “Quantifying the chemical beauty of drugs,” Nature Chemistry 4, 90-98 (2012).",
  "Qiskit, Qiskit Machine Learning and Qiskit Nature documentation, https://qiskit.org.",
]));

// ---------------- appendix ----------------
c.push(h1("Appendix A. Reproducing the results"));
c.push(...["pip install -r requirements.txt            # add requirements-vqe.txt for VQE (WSL/Colab on Windows)",
  "pytest -q                                   # 21 tests",
  "python main.py --quick                      # smoke run, under 1 minute",
  "python main.py                              # full pipeline (about 20 minutes on one CPU core)",
  "streamlit run app.py                        # demo interface"].map((t) =>
  new Paragraph({ spacing: { after: 40 }, shading: { fill: "F3F3F3", type: ShadingType.CLEAR, color: "auto" }, children: [run(t, { font: "Courier New", size: 18 })] })));
c.push(p("Detailed documentation is provided in the project's docs folder: architecture, methodology, user guide, API reference, results and limitations.", { spacing: { before: 140, after: 120 } }));

const doc = new Document({
  creator: "G Veda Kartik", title: "QuantumScreen - Capstone Report",
  styles: { default: { document: { run: { font: FONT, size: 22 } } } },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] },
    ...numConfigs,
  ] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [run("QuantumScreen  |  G Veda Kartik  |  Page ", { size: 16, color: "777777" }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: "777777" })] })] }) },
    children: c,
  }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(__dirname + "/QuantumScreen_Report.docx", b); console.log("report written", b.length); });
