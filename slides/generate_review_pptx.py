"""Generate QuantumScreen Capstone Review Presentation matching exact committee format."""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Theme Colors
    BG_DARK = RGBColor(27, 19, 64)       # Deep Indigo
    BG_LIGHT = RGBColor(248, 247, 252)   # Soft lavender off-white
    PURPLE_ACC = RGBColor(108, 63, 197)  # Primary Quantum Purple
    TEAL_ACC = RGBColor(42, 157, 143)    # Classical Teal
    TEXT_DARK = RGBColor(27, 19, 64)
    TEXT_MUTED = RGBColor(107, 114, 128)
    WHITE = RGBColor(255, 255, 255)
    CARD_BG = RGBColor(240, 237, 248)
    ORANGE_ACC = RGBColor(231, 111, 81)

    def add_bg(slide, dark=False):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        shape.fill.solid()
        shape.fill.fore_color.rgb = BG_DARK if dark else BG_LIGHT
        shape.line.fill.background()
        return shape

    def add_header(slide, title_text, category_text="CAPSTONE PROJECT REVIEW | QUANTUM COMPUTING"):
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = PURPLE_ACC

        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(28)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_DARK

    def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=None):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1.5)
        else:
            card.line.fill.background()
        return card

    # ==========================================
    # SLIDE 1: Title Slide
    # ==========================================
    s1 = prs.slides.add_slide(blank_layout)
    add_bg(s1, dark=True)

    tbox = s1.shapes.add_textbox(Inches(1.0), Inches(1.2), Inches(11.3), Inches(5.0))
    tf1 = tbox.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "CAPSTONE PROJECT REVIEW  |  QUANTUM COMPUTING"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = RGBColor(184, 161, 227)

    p2 = tf1.add_paragraph()
    p2.text = "QuantumScreen"
    p2.font.size = Pt(54)
    p2.font.bold = True
    p2.font.color.rgb = WHITE
    p2.space_before = Pt(14)

    p3 = tf1.add_paragraph()
    p3.text = "A Quantum Computing-Based Drug Screening System to Identify Promising Drug Candidates"
    p3.font.size = Pt(22)
    p3.font.color.rgb = RGBColor(220, 215, 240)
    p3.space_before = Pt(10)

    p4 = tf1.add_paragraph()
    p4.text = "Student Name: G Veda Kartik\nRoll Number: CH.SC.U4CSE24212\nDegree: B.Tech Computer Science and Engineering\nInstitution: Amrita Vishwa Vidyapeetham, Chennai\nReview Date: October 2026"
    p4.font.size = Pt(16)
    p4.font.color.rgb = WHITE
    p4.space_before = Pt(36)

    # Add decorative kernel figure on right
    if os.path.exists("results/figures/08_kernel_matrix.png"):
        s1.shapes.add_picture("results/figures/08_kernel_matrix.png", Inches(8.3), Inches(1.8), Inches(4.2), Inches(4.2))

    # ==========================================
    # SLIDE 2: Problem Statement
    # ==========================================
    s2 = prs.slides.add_slide(blank_layout)
    add_bg(s2)
    add_header(s2, "Slide 2: Problem Statement", "Problem Identification")

    add_card(s2, 0.8, 1.8, 5.7, 5.1)
    tbox = s2.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.1), Inches(4.6))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "What is the Problem?"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = PURPLE_ACC

    points1 = [
        "Pharmaceutical drug discovery takes over 10–15 years and costs $1–2.6 billion per approved drug.",
        "Over 90% of candidate molecules fail in clinical trials due to lack of efficacy or unanticipated toxicity.",
        "Target Focus: BACE-1 (beta-secretase 1), an essential enzyme in Alzheimer's disease pathology responsible for toxic amyloid-beta plaque accumulation.",
        "The chemical space of pharmacologically viable drug-like molecules is astronomically vast (~10^60 compounds), rendering exhaustive wet-lab screening physically impossible."
    ]
    for pt in points1:
        p = tf.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_DARK
        p.space_before = Pt(12)

    add_card(s2, 6.8, 1.8, 5.7, 5.1)
    tbox = s2.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.1), Inches(4.6))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Why Does It Need to be Solved?"
    p.font.size = Pt(22)
    p.font.bold = True
    p.font.color.rgb = TEAL_ACC

    points2 = [
        "Virtual screening acts as a high-throughput computational funnel, computationally prioritizing only the top 0.1% most promising leads for physical assay.",
        "Alzheimer's disease has an urgent unmet medical need with devastating global health and economic impacts.",
        "Classical machine learning struggles with non-linear correlations in sparse molecular representations without severe heuristic approximations.",
        "Quantum Computing offers exponentially large Hilbert spaces (2^n states for n qubits), providing natural mathematical geometry for complex molecular similarity and combinatorial optimization."
    ]
    for pt in points2:
        p = tf.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_DARK
        p.space_before = Pt(12)

    # ==========================================
    # SLIDE 3: Objectives
    # ==========================================
    s3 = prs.slides.add_slide(blank_layout)
    add_bg(s3)
    add_header(s3, "Slide 3: Project Objectives & Algorithmic Strategy", "Proposed Strategy")

    objs = [
        ("1. End-to-End Hybrid Screening Pipeline", "Build a complete pipeline from raw SMILES chemical strings to ranked, drug-like molecular leads using Qiskit, RDKit, and scikit-learn.", PURPLE_ACC),
        ("2. Quantum Machine Learning for Scoring", "Implement a Quantum-Kernel Support Vector Machine (QSVC) using parameterised ZZ-feature maps to map molecules into a 2^8 Hilbert space.", TEAL_ACC),
        ("3. Combinatorial Diversity Selection (QAOA)", "Formulate candidate batch selection as a QUBO balancing potency against Tanimoto redundancy, solved via QAOA on simulated statevectors.", ORANGE_ACC),
        ("4. Rigorous Classical Benchmarking", "Evaluate against tuned classical RBF-SVM and Random Forests on identical splits and features to rigorously quantify if quantum advantage exists.", PURPLE_ACC),
        ("5. Quantum Chemistry Foundation (VQE)", "Implement Variational Quantum Eigensolver (VQE) with UCCSD ansatz on H2 and LiH to demonstrate ground-state energy computation.", TEAL_ACC),
        ("6. Production UI & Reproducibility", "Deliver an interactive Streamlit web dashboard for live screening, backed by automated unit tests and reproducible CLI stages.", ORANGE_ACC),
    ]

    for i, (title, desc, col) in enumerate(objs):
        row = i // 3
        col_idx = i % 3
        x = 0.8 + col_idx * 3.95
        y = 1.8 + row * 2.6
        add_card(s3, x, y, 3.75, 2.35)
        tbox = s3.shapes.add_textbox(Inches(x + 0.2), Inches(y + 0.2), Inches(3.35), Inches(1.95))
        tf = tbox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = col
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(13)
        p2.font.color.rgb = TEXT_DARK
        p2.space_before = Pt(8)

    # ==========================================
    # SLIDE 4: Proposed Algorithm - Quantum Kernel SVM
    # ==========================================
    s4 = prs.slides.add_slide(blank_layout)
    add_bg(s4)
    add_header(s4, "Slide 4: Proposed Algorithm — Quantum Kernel SVM (QSVC)", "Algorithm Details")

    add_card(s4, 0.8, 1.8, 6.0, 5.1)
    tbox = s4.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.4), Inches(4.6))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Algorithm: Fidelity Quantum Kernel SVM"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = PURPLE_ACC

    steps = [
        "1. Featurisation: SMILES -> 2048-bit Morgan Fingerprint (radius 2 / ECFP4).",
        "2. Dimensionality Reduction: PCA compresses 2048 bits into n=8 orthogonal components (fitted on train split only).",
        "3. Quantum Feature Mapping: Angles scaled to [0, pi] and loaded into an 8-qubit register via a parameterised ZZ feature map:",
        "   |phi(x)> = U_ZZ(x) |0>^n = exp(i sum x_j Z_j + sum (pi - x_j)(pi - x_k) Z_j Z_k) H^n |0>^n",
        "4. Quantum Kernel Gram Matrix: Computes transition fidelity in 2^8 Hilbert space:",
        "   K(x_i, x_j) = |<phi(x_i)|phi(x_j)>|^2",
        "5. Dual SVM Optimization: Solves classical quadratic program to find optimal separating hyperplane with precomputed quantum Gram matrix."
    ]
    for s in steps:
        p = tf.add_paragraph()
        p.text = s
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_DARK
        p.space_before = Pt(7)

    # Circuit picture on right
    add_card(s4, 7.1, 1.8, 5.4, 5.1)
    if os.path.exists("results/figures/10_zz_feature_map.png"):
        s4.shapes.add_picture("results/figures/10_zz_feature_map.png", Inches(7.3), Inches(2.2), Inches(5.0), Inches(1.5))
    if os.path.exists("results/figures/08_kernel_matrix.png"):
        s4.shapes.add_picture("results/figures/08_kernel_matrix.png", Inches(8.3), Inches(4.0), Inches(2.7), Inches(2.7))

    # ==========================================
    # SLIDE 5: Pseudocode & Mathematical Formulation
    # ==========================================
    s5 = prs.slides.add_slide(blank_layout)
    add_bg(s5)
    add_header(s5, "Slide 5: Pseudocode & Multi-Stage Algorithmic Flow", "Algorithm Pseudocode")

    add_card(s5, 0.8, 1.8, 11.7, 5.1)
    tbox = s5.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(11.1), Inches(4.6))
    tf = tbox.text_frame
    tf.word_wrap = True

    pseudo = """ALGORITHM: QuantumScreen Virtual Screening & Diversity Selection Pipeline
INPUT: Molecular library SMILES strings {m_1, ..., m_N}, Training labels y in {0, 1}^N
OUTPUT: Ranked candidate scores, Selected batch of K diverse active compounds

STAGE 1: QUANTUM KERNEL EVALUATION & CLASSIFICATION
  1: For each molecule m_i in Dataset:
  2:     x_raw = MorganFingerprint(m_i, radius=2, n_bits=2048)
  3: X_pca = PCA_fit_transform(X_train_raw, n_components=8)
  4: Theta = MinMaxScale(X_pca, 0, pi)
  5: For each vector theta_i in Theta:
  6:     |phi(theta_i)> = Statevector(ZZ_FeatureMap(theta_i, n_qubits=8, reps=2))
  7: Compute Gram Matrix: K_ij = |<phi(theta_i) | phi(theta_j)>|^2
  8: Train Dual SVM: alpha* = argmin 0.5 * alpha^T (K * y y^T) alpha - sum(alpha_i) s.t. 0 <= alpha_i <= C
  9: Predict Hold-out Library: P_active(m) = PlattScale(sum alpha_i y_i K(theta_i, theta_new) + b)

STAGE 2: MULTI-OBJECTIVE RANKING & QAOA DIVERSITY SELECTION
 10: Score(m) = 0.7 * P_active(m) + 0.3 * QED(m) - 0.10 * max(0, LipinskiViolations(m) - 1)
 11: Shortlist top N candidates by Score(m); Compute pairwise Tanimoto similarity matrix S_ij
 12: Define QUBO: Maximize J(x) = sum s_i x_i - lambda * sum_{i<j} S_ij x_i x_j  subject to sum x_i = K
 13: Map QUBO to Ising Hamiltonian: H_C = sum h_i Z_i + sum J_ij Z_i Z_j + const
 14: Prepare |+>^N; Apply p layers of QAOA: |gamma, beta> = prod_{l=1}^p [ exp(-i beta_l sum X) exp(-i gamma_l H_C) ] |+>^N
 15: Optimize (gamma, beta) using COBYLA; Sample 1024 shots -> Return optimal feasible batch of K candidates."""

    p = tf.paragraphs[0]
    p.text = pseudo
    p.font.name = "Consolas"
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_DARK

    # ==========================================
    # SLIDE 6: Algorithm Complexity
    # ==========================================
    s6 = prs.slides.add_slide(blank_layout)
    add_bg(s6)
    add_header(s6, "Slide 6: Computational Complexity Analysis", "Complexity Analysis")

    add_card(s6, 0.8, 1.8, 5.7, 5.1)
    tbox = s6.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.1), Inches(4.6))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Time Complexity Analysis"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = PURPLE_ACC

    tc = [
        "• Fingerprint & PCA: O(N * d) where d=2048, N=1513 molecules (Classical preprocessing).",
        "• Statevector Preparation: O(N * 2^n) where n=8 qubits (each state computed once in linear algebra).",
        "• Quantum Kernel Evaluation: O(N^2 * 2^n) via matrix multiplication |S S^dag|^2 in simulation.",
        "   -> On Fault-Tolerant Quantum Hardware: O(N^2 * M * D) where M is shot budget and D is circuit depth (bypasses 2^n exponential statevector simulation!).",
        "• SVM Dual Training: O(N_sv^3) standard quadratic programming solver.",
        "• QAOA Execution: O(p * 2^n * N_iter) in classical statevector simulation vs O(p * M * N_iter) on quantum hardware."
    ]
    for c in tc:
        p = tf.add_paragraph()
        p.text = c
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_DARK
        p.space_before = Pt(8)

    add_card(s6, 6.8, 1.8, 5.7, 5.1)
    tbox = s6.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.1), Inches(4.6))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Space Complexity Analysis"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = TEAL_ACC

    sc = [
        "• Classical Simulation Memory: O(2^n) complex amplitudes per quantum statevector. For n=8, 2^8 = 256 complex numbers (trivial); for n=30, exceeds 16 GB RAM.",
        "• Physical Quantum Register Memory: O(n) qubits! This represents an exponential spatial compression on physical quantum processors.",
        "• Precomputed Kernel Matrix: O(N^2) memory footprint to store the pairwise N x N similarity Gram matrix (1513 x 1513 floats ≈ 18 MB).",
        "• QAOA Parameter Storage: O(2p) variational parameters (gamma_l, beta_l) where depth p in {1, 2, 3} (minimal classical memory overhead).",
        "• Classical Feature Storage: Reduced from 2048 bits to 8 floats per molecule (256x compression ratio)."
    ]
    for c in sc:
        p = tf.add_paragraph()
        p.text = c
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_DARK
        p.space_before = Pt(8)

    # ==========================================
    # SLIDE 7: Implementation
    # ==========================================
    s7 = prs.slides.add_slide(blank_layout)
    add_bg(s7)
    add_header(s7, "Slide 7: Implementation Details & Code Architecture", "Technology & Code")

    add_card(s7, 0.8, 1.8, 4.8, 5.1)
    tbox = s7.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(4.4), Inches(4.6))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Stack & Architecture"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = PURPLE_ACC

    stack_info = [
        "• Language: Python 3.11",
        "• Quantum Computing: Qiskit 2.5, Qiskit Machine Learning 0.9, Qiskit Nature 0.8, Qiskit Algorithms 0.4",
        "• Cheminformatics: RDKit (Morgan fingerprints, Lipinski rules, QED, Murcko scaffolds)",
        "• Machine Learning: scikit-learn (SVM, Random Forest, PCA, cross-validation)",
        "• Web Deployment: Streamlit (interactive UI)",
        "• Testing: pytest (21 automated unit tests verifying mathematical PSD property, Qiskit equivalence, and Ising conservation)"
    ]
    for s in stack_info:
        p = tf.add_paragraph()
        p.text = s
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_DARK
        p.space_before = Pt(8)

    add_card(s7, 5.9, 1.8, 6.6, 5.1)
    tbox = s7.shapes.add_textbox(Inches(6.1), Inches(2.0), Inches(6.2), Inches(4.6))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Core Implementation Code Snippet"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = TEAL_ACC

    code_snippet = """# Optimized Quantum Kernel & State Evaluation
def compute_states(circuit, X: np.ndarray) -> np.ndarray:
    \"\"\"Compute statevectors once for all samples (O(N) not O(N^2)).\"\"\"
    return np.array([Statevector(circuit.assign_parameters(x)).data for x in X])

def fidelity_kernel(states_a, states_b) -> np.ndarray:
    \"\"\"Exact Gram Matrix: |<phi_a|phi_b>|^2.\"\"\"
    return np.abs(states_a.conj() @ states_b.T) ** 2

# Hybrid Quantum-Kernel Support Vector Machine
class QuantumKernelSVM(BaseEstimator, ClassifierMixin):
    def fit(self, X, y):
        self.circuit_ = build_feature_map(self.feature_map, n_qubits=8, reps=2)
        self.train_states_ = compute_states(self.circuit_, X * self.scale)
        K = fidelity_kernel(self.train_states_, self.train_states_)
        self.svc_ = SVC(kernel="precomputed", C=self.C, probability=True).fit(K, y)
        return self

    def predict_proba(self, X):
        test_states = compute_states(self.circuit_, X * self.scale)
        K_test = fidelity_kernel(test_states, self.train_states_)
        return self.svc_.predict_proba(K_test)"""

    p = tf.add_paragraph()
    p.text = code_snippet
    p.font.name = "Consolas"
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_DARK
    p.space_before = Pt(6)

    # ==========================================
    # SLIDE 8: Results & Analysis (Virtual Screening)
    # ==========================================
    s8 = prs.slides.add_slide(blank_layout)
    add_bg(s8)
    add_header(s8, "Slide 8: Results & Analysis — Virtual Screening Benchmarks", "Benchmarking Results")

    add_card(s8, 0.8, 1.8, 6.2, 5.1)
    tbox = s8.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.8), Inches(4.6))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Benchmark Results (1,513 BACE Molecules)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = PURPLE_ACC

    res_table = """Model Architecture              ROC-AUC          EF@10%    Time (s)
Random Forest (2048-bit FP)    0.916 ± 0.006    2.10       1.7 s
Classical RBF-SVM (8 PCA)      0.879 ± 0.007    1.98       4.4 s
Random Forest (8 PCA)          0.877 ± 0.015    2.07       0.8 s
Quantum Kernel SVM (8 qubits)  0.873 ± 0.011    2.07      11.1 s
Variational Classifier (VQC)   0.625 ± 0.056    --       119.0 s

Key Analytical Findings:
• No Quantum Advantage: Quantum-kernel SVM (0.873) matches but does not beat classical SVM (0.879).
• Bottleneck Identified: Compressing 2048 bits into 8 PCA components retains only ~36% variance.
• Entanglement: The unentangled Z map (0.877) matches the entangling ZZ map (0.873).
• Virtual Screening Precision: On a held-out library of 303 molecules, the quantum score placed 24 of its top 25 picks in the active class!"""

    p = tf.add_paragraph()
    p.text = res_table
    p.font.name = "Consolas"
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_DARK
    p.space_before = Pt(6)

    # Add images
    add_card(s8, 7.3, 1.8, 5.2, 5.1)
    if os.path.exists("results/figures/01_model_comparison.png"):
        s8.shapes.add_picture("results/figures/01_model_comparison.png", Inches(7.5), Inches(2.0), Inches(4.8), Inches(2.4))
    if os.path.exists("results/figures/02_roc_curves.png"):
        s8.shapes.add_picture("results/figures/02_roc_curves.png", Inches(7.5), Inches(4.5), Inches(4.8), Inches(2.3))

    # ==========================================
    # SLIDE 9: Results & Analysis (QAOA & VQE)
    # ==========================================
    s9 = prs.slides.add_slide(blank_layout)
    add_bg(s9)
    add_header(s9, "Slide 9: Results & Analysis — QAOA Selection & VQE Chemistry", "Optimization & Chemistry")

    add_card(s9, 0.8, 1.8, 5.7, 5.1)
    tbox = s9.shapes.add_textbox(Inches(1.0), Inches(2.0), Inches(5.3), Inches(4.6))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "QAOA Combinatorial Selection"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ORANGE_ACC

    qaoa_text = [
        "• Problem: Select K=4 diverse candidates from top N=12 leads.",
        "• Score-only Top-K selects 3 near-duplicate analogues (pairwise Tanimoto similarity = 0.46, objective J = 1.96).",
        "• Diversity-aware QAOA & Exact solver achieve J = 2.88 and reduce redundant similarity to 0.14!",
        "• Honest Diagnostic: Best-of-shots achieves 99-100% of optimum, but random search with 1024 shots does equally well because search spaces are small (56 to 1001 feasible subsets)."
    ]
    for q in qaoa_text:
        p = tf.add_paragraph()
        p.text = q
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_DARK
        p.space_before = Pt(6)

    if os.path.exists("results/figures/12b_selected_molecules_slide.png"):
        s9.shapes.add_picture("results/figures/12b_selected_molecules_slide.png", Inches(1.0), Inches(4.5), Inches(5.3), Inches(2.2))

    add_card(s9, 6.8, 1.8, 5.7, 5.1)
    tbox = s9.shapes.add_textbox(Inches(7.0), Inches(2.0), Inches(5.3), Inches(4.6))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "VQE Molecular Ground-State Energies"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = TEAL_ACC

    vqe_text = [
        "• Quantum Chemistry Demonstration: Computing ground-state energies underlying drug-target binding.",
        "• System: H2 (2 qubits, 3 params) and LiH (4 qubits in active space, 8 params).",
        "• Ansatz: Unitary Coupled Cluster (UCCSD) with Hartree-Fock reference state.",
        "• Accuracy: Max error < 0.001 mHa against exact Full Configuration Interaction (Chemical accuracy is 1.6 mHa).",
        "• H2 equilibrium energy at 0.74 A is -1.137 Ha, exactly matching STO-3G theory."
    ]
    for v in vqe_text:
        p = tf.add_paragraph()
        p.text = v
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_DARK
        p.space_before = Pt(6)

    if os.path.exists("results/figures/09_vqe_curves.png"):
        s9.shapes.add_picture("results/figures/09_vqe_curves.png", Inches(7.0), Inches(4.5), Inches(5.3), Inches(2.2))

    # ==========================================
    # SLIDE 10: Website / Interactive UI
    # ==========================================
    s10 = prs.slides.add_slide(blank_layout)
    add_bg(s10)
    add_header(s10, "Slide 10: Interactive Web Application (Streamlit)", "System Demonstration")

    add_card(s10, 0.8, 1.8, 11.7, 5.1)
    tbox = s10.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(11.1), Inches(4.6))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Production Web Dashboard Capabilities (Running on localhost:8501)"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = PURPLE_ACC

    ui_pts = [
        ("Tab 1: Single Molecule Screening", "Input custom SMILES strings or select benchmarks (e.g. Aspirin vs known BACE inhibitors). Visualizes real-time 2D molecular structures (RDKit), predicted Quantum P(active), Classical SVM P(active), and full Lipinski / QED drug-likeness profiles."),
        ("Tab 2: High-Throughput Batch Screening", "Paste multi-line SMILES or upload screening CSV libraries. Executes vectorized quantum encoding and outputs ranked leads combining quantum affinity and drug-likeness, downloadable as CSV."),
        ("Tab 3: Benchmark Analytics & Diagnostics", "Interactive inspection of full experimental benchmark metrics, ROC curves, qubit ablations, feature map comparisons, and QAOA distributions."),
        ("Tab 4: Documentation & Transparent Disclosures", "Comprehensive methodology, parameter logs, and scientific limitations displayed directly in the user interface."),
        ("Deployment & Performance", "Built on Streamlit with joblib cached model persistence, executing single-molecule quantum scoring in < 100 milliseconds.")
    ]
    for title, desc in ui_pts:
        p = tf.add_paragraph()
        p.text = "• " + title + ": " + desc
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_DARK
        p.space_before = Pt(10)

    # ==========================================
    # SLIDE 11: Limitations
    # ==========================================
    s11 = prs.slides.add_slide(blank_layout)
    add_bg(s11)
    add_header(s11, "Slide 11: Honest Scientific Limitations & viva Defense", "Project Limitations")

    add_card(s11, 0.8, 1.8, 11.7, 5.1)
    tbox = s11.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(11.1), Inches(4.6))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Critical Limitations (Transparent Scientific Disclosures)"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = ORANGE_ACC

    limits = [
        "1. Classical Simulation: All circuits are simulated with noiseless statevectors; real quantum hardware introduces gate infidelities and shot noise.",
        "2. No Quantum Advantage: The quantum kernel matches (0.873) but does not beat classical SVM (0.879). Classical Random Forest on 2048-bit fingerprints reaches 0.916.",
        "3. PCA Dimensionality Bottleneck: Compressing 2048 fingerprint bits into 8 qubits discards ~64% of chemical variance.",
        "4. Ligand-Based Only: Screening evaluates 2D similarity to known binders; it does not model 3D target binding pocket physics or molecular docking.",
        "5. Single Target Scope: Evaluated on 1,513 BACE-1 molecules; cross-target generalization requires broader evaluation.",
        "6. Toy Molecule Chemistry: VQE is demonstrated on small molecules (H2, LiH); drug-sized molecules exceed current quantum hardware capabilities.",
        "7. QAOA Penalty Formulation: Embeds cardinality as a penalty; between 48% and 78% of sampled probability mass lands on infeasible bitstrings."
    ]
    for lim in limits:
        p = tf.add_paragraph()
        p.text = lim
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_DARK
        p.space_before = Pt(8)

    # ==========================================
    # SLIDE 12: Conclusion
    # ==========================================
    s12 = prs.slides.add_slide(blank_layout)
    add_bg(s12)
    add_header(s12, "Slide 12: Conclusion & Future Research Directions", "Summary & Roadmap")

    add_card(s12, 0.8, 1.8, 5.7, 5.1)
    tbox = s12.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.1), Inches(4.6))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Project Conclusions"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = PURPLE_ACC

    c_pts = [
        "• Successfully developed an end-to-end hybrid quantum virtual screening pipeline for BACE-1 inhibitors.",
        "• Quantum-kernel SVM demonstrated competitive predictive efficacy (AUC 0.873, EF@10% 2.07), identifying 24 actives in top 25 picks.",
        "• Diversity-aware QAOA successfully decoupled near-duplicate compounds, reducing redundant similarity from 0.46 to 0.14.",
        "• Established an honest, peer-reviewed benchmark proving that near-term quantum advantage in ligand screening is currently bounded by classical data compression."
    ]
    for pt in c_pts:
        p = tf.add_paragraph()
        p.text = pt
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_DARK
        p.space_before = Pt(10)

    add_card(s12, 6.8, 1.8, 5.7, 5.1)
    tbox = s12.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.1), Inches(4.6))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Future Work"
    p.font.size = Pt(20)
    p.font.bold = True
    p.font.color.rgb = TEAL_ACC

    f_pts = [
        "• Hardware Deployment: Run optimized circuits on physical IBM Quantum superconducting hardware with Zero-Noise Extrapolation.",
        "• Learned Latent Spaces: Replace linear PCA with Graph Neural Network (GNN) molecular embeddings prior to quantum encoding.",
        "• Constraint-Preserving QAOA: Implement XY mixers and Dicke state initialization to enforce exact cardinality without penalty loss.",
        "• Trainable Quantum Kernels: Utilize Quantum Kernel Alignment (QKA) to optimize feature map parameters directly on molecular binding data.",
        "• Hybrid Docking Integration: Combine quantum scores with MM-GBSA free energy calculations."
    ]
    for pt in f_pts:
        p = tf.add_paragraph()
        p.text = pt
        p.font.size = Pt(14)
        p.font.color.rgb = TEXT_DARK
        p.space_before = Pt(10)

    # ==========================================
    # SLIDE 13: Thank You
    # ==========================================
    s13 = prs.slides.add_slide(blank_layout)
    add_bg(s13, dark=True)

    tbox = s13.shapes.add_textbox(Inches(1.5), Inches(2.0), Inches(10.3), Inches(3.8))
    tf = tbox.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "Thank You!"
    p.font.size = Pt(56)
    p.font.bold = True
    p.font.color.rgb = WHITE

    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.text = "Open for Questions & Evaluation"
    p2.font.size = Pt(26)
    p2.font.color.rgb = RGBColor(184, 161, 227)
    p2.space_before = Pt(14)

    p3 = tf.add_paragraph()
    p3.alignment = PP_ALIGN.CENTER
    p3.text = "G Veda Kartik (CH.SC.U4CSE24212)\nDepartment of Computer Science and Engineering\nAmrita Vishwa Vidyapeetham, Chennai\nCapstone Project: Quantum Computing"
    p3.font.size = Pt(18)
    p3.font.color.rgb = WHITE
    p3.space_before = Pt(28)

    prs.save("slides/QuantumScreen_Review_Presentation.pptx")
    print("Successfully generated slides/QuantumScreen_Review_Presentation.pptx")

if __name__ == "__main__":
    create_deck()
