"""Generate QuantumScreen Capstone Review Report (.docx) matching exact committee format."""
import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    shading_xml = f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_report():
    doc = Document()
    
    # Page Setup: Standard Letter with 1-inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Palette
    PURPLE = RGBColor(75, 42, 145)
    DARK_TEXT = RGBColor(35, 31, 32)
    GRAY = RGBColor(90, 90, 90)

    def add_p(text, bold=False, italic=False, size=11, color=DARK_TEXT, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=0, space_after=6):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(text)
        run.bold = bold
        run.italic = italic
        run.font.name = 'Calibri'
        run.font.size = Pt(size)
        run.font.color.rgb = color
        return p

    def add_bullet(bold_prefix, text):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        r1 = p.add_run(bold_prefix)
        r1.bold = True
        r1.font.name = 'Calibri'
        r1.font.size = Pt(11)
        r1.font.color.rgb = DARK_TEXT
        r2 = p.add_run(text)
        r2.font.name = 'Calibri'
        r2.font.size = Pt(11)
        r2.font.color.rgb = DARK_TEXT
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = 'Calibri'
        run.font.size = Pt(18)
        run.font.color.rgb = PURPLE
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = 'Calibri'
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(42, 157, 143)
        return p

    def add_img(path, width=Inches(6.0), caption=""):
        if os.path.exists(path):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run()
            run.add_picture(path, width=width)
            if caption:
                p_cap = doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap.paragraph_format.space_before = Pt(2)
                p_cap.paragraph_format.space_after = Pt(10)
                rc = p_cap.add_run("Figure: " + caption)
                rc.italic = True
                rc.font.size = Pt(9.5)
                rc.font.color.rgb = GRAY

    # ==========================================
    # Title & Metadata
    # ==========================================
    p_kicker = add_p("AMRITA VISHWA VIDYAPEETHAM, CHENNAI\nDEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING", bold=True, size=11, color=PURPLE, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=10, space_after=12)
    add_p("CAPSTONE PROJECT REVIEW REPORT", bold=True, size=14, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)
    add_p("QuantumScreen: A Quantum Computing-Based Drug Screening System to Identify Promising Drug Candidates", bold=True, size=24, color=PURPLE, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=18)
    
    add_p("Candidate Name: G Veda Kartik", bold=True, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_p("Roll Number: CH.SC.U4CSE24212", bold=False, size=11, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_p("Degree: B.Tech in Computer Science and Engineering", bold=False, size=11, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_p("Domain: Quantum Computing & Computational Chemistry | October 2026", italic=True, size=11, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24)

    # ==========================================
    # Abstract
    # ==========================================
    add_h1("Abstract")
    add_bullet("Problem Being Addressed: ", "Modern pharmaceutical drug discovery is hindered by prohibitive development costs ($1–2.6 billion per approved molecular entity), lengthy developmental timelines (10–15 years), and an attrition rate exceeding 90% in clinical trials. High-throughput computational virtual screening serves as an essential preliminary funnel to filter vast chemical libraries (~10^60 compounds) down to high-affinity lead candidates. In this project, we target human beta-secretase 1 (BACE-1), a crucial enzymatic driver of Alzheimer's disease responsible for toxic amyloid-beta plaque aggregation.")
    add_bullet("Algorithms Used: ", "We develop QuantumScreen, a hybrid quantum-classical screening system implemented on Qiskit. The primary algorithms utilized are: (1) Fidelity Quantum-Kernel Support Vector Machine (QSVC) with an 8-qubit parameterised ZZ-feature map and CNOT entanglement for bioactivity classification; (2) Quantum Approximate Optimization Algorithm (QAOA) solving a diversity-penalized Quadratic Unconstrained Binary Optimization (QUBO) problem for non-redundant batch candidate selection; and (3) Variational Quantum Eigensolver (VQE) with a UCCSD ansatz for ground-state molecular electronic structure computation.")
    add_bullet("Results Obtained: ", "Evaluating across 1,513 curated BACE-1 inhibitors on identical cross-validation splits, the Quantum Kernel SVM achieved a ROC-AUC of 0.873 ± 0.011 and an Enrichment Factor at 10% (EF@10%) of 2.07 (theoretical maximum 2.20), statistically matching a classical RBF-SVM (0.879 ± 0.007). On a held-out library of 303 compounds, the quantum ranking positioned 24 of its top 25 picks in the active class. For candidate selection, QAOA reached 99–100% of the optimal objective (J = 2.88) while reducing structural similarity from 0.46 to 0.14. Finally, VQE reproduced exact ground-state energies for H2 and LiH within < 0.001 mHa, exceeding chemical accuracy standards.")

    # ==========================================
    # Problem Statement
    # ==========================================
    add_h1("Problem Statement")
    add_bullet("What the Problem Is: ", "Identifying small-molecule inhibitors capable of selectively targeting BACE-1 without inducing off-target neurotoxicity. Traditional wet-lab high-throughput screening (HTS) cannot evaluate more than a minuscule fraction of chemical space, requiring automated computational filtering.")
    add_bullet("Input: ", "The system receives raw molecular representations in SMILES (Simplified Molecular Input Line Entry System) format, accompanied by experimental bioactivity labels (active/inactive) from the MoleculeNet BACE benchmark dataset.")
    add_bullet("Expected Output: ", "The system outputs: (1) A calibrated quantum probability of bioactivity P(active) for every molecule; (2) A multi-objective ranking score integrating drug-likeness (QED) and Lipinski's Rule-of-Five compliance; (3) A selected batch of K mutually diverse lead molecules maximizing the combinatorial diversity objective; and (4) Electronic ground-state potential energy profiles.")
    add_bullet("Limitations: ", "All quantum circuits are executed via exact classical statevector simulation. On current NISQ devices, finite shot noise and gate errors introduce kernel variance. Furthermore, encoding high-dimensional 2,048-bit fingerprints into 8 qubits requires PCA dimensionality reduction, which discards ~64% of structural variance.")

    # ==========================================
    # Objectives
    # ==========================================
    add_h1("Objectives")
    add_bullet("How the Problem is Being Solved: ", "By architecting a modular, hybrid quantum-classical software architecture where classical routines (RDKit, scikit-learn) handle preprocessing, PCA, and quadratic programming, while Qiskit constructs parameterised quantum circuits to compute inner-product kernel similarities in high-dimensional Hilbert space (2^8 = 256 dimensions).")
    add_bullet("Algorithms Used: ", "Fidelity Quantum-Kernel SVM (QSVC), Variational Quantum Classifier (VQC), Quantum Approximate Optimization Algorithm (QAOA), and Variational Quantum Eigensolver (VQE).")
    add_bullet("Complexity Analysis: ", "Classical statevector simulation of the fidelity kernel scales as O(N^2 * 2^n) time and O(2^n) memory. On fault-tolerant physical quantum hardware, state overlap estimation scales as O(N^2 * M) time using O(n) physical qubits, circumventing exponential statevector memory.")

    # ==========================================
    # Proposed Algorithm
    # ==========================================
    add_h1("Proposed Algorithm")
    add_p("The core screening module is the Fidelity Quantum Kernel Support Vector Machine (QSVC). Classical support vector machines rely on kernel functions k(x, x') to compute dot products in higher-dimensional implicit feature spaces without explicitly calculating coordinates (the kernel trick). Quantum kernels implement this concept by mapping classical data vectors into quantum Hilbert space via unitary feature maps.")
    
    add_h2("Step-by-Step Algorithmic Process")
    add_bullet("1. Featurisation: ", "Input SMILES strings are converted to 2,048-bit circular Morgan fingerprints (radius 2 / ECFP4) capturing local atomic environments.")
    add_bullet("2. Dimensionality Reduction: ", "Principal Component Analysis (PCA) is fitted exclusively on training fingerprints to compress 2,048 dimensions into n=8 orthogonal components.")
    add_bullet("3. Angle Scaling: ", "The 8 components are min-max scaled into rotation angles in [0, pi] and multiplied by a hyperparameter bandwidth scale.")
    add_bullet("4. Quantum Feature Mapping: ", "An 8-qubit quantum register initialized in |0>^n is transformed via a parameterised ZZ feature map: |phi(x)> = U_ZZ(x)|0>^n, where single-qubit Z-rotations encode features and two-qubit CNOT entanglers encode pairwise non-linear interactions.")
    add_bullet("5. Quantum Gram Matrix: ", "The kernel matrix is computed by measuring the state fidelity: K_ij = |<phi(x_i)|phi(x_j)>|^2. In QuantumScreen, all N statevectors are precomputed once (O(N)), and the Gram matrix is evaluated via batch matrix multiplication K = |S S^dag|^2.")
    add_bullet("6. Dual Optimization: ", "A classical C-SVM solves the convex quadratic program to determine support vectors and bias. Class probabilities are calibrated via Platt scaling.")
    add_bullet("7. Diversity Selection via QAOA: ", "Top candidates are framed into a QUBO: Max J(x) = sum s_i x_i - lambda * sum S_ij x_i x_j subject to sum x_i = K. The QUBO is mapped to an Ising Hamiltonian H_C, and QAOA optimizes parameters (gamma, beta) to select diverse batches.")

    add_h2("Flowchart")
    add_img("results/figures/10_zz_feature_map.png", width=Inches(6.2), caption="ZZ Parameterised Feature Map Circuit with Entanglement")

    add_h2("Applications of the Algorithm")
    add_bullet("1. High-Throughput Virtual Screening: ", "Rapidly prioritizing chemical libraries against oncology, neurodegenerative, and infectious targets.")
    add_bullet("2. Combinatorial Lead Batch Selection: ", "Ensuring that synthesis batches represent diverse chemotypes to prevent uniform laboratory failure.")
    add_bullet("3. Fragment-Based Drug Discovery: ", "Evaluating binding affinities of small molecular fragments using quantum-chemical VQE simulations.")

    # ==========================================
    # Pseudocode
    # ==========================================
    add_h1("Pseudocode")
    p_code = doc.add_paragraph()
    p_code.paragraph_format.space_before = Pt(4)
    p_code.paragraph_format.space_after = Pt(8)
    p_code.paragraph_format.line_spacing = 1.05
    run_c = p_code.add_run("""ALGORITHM: QuantumScreen Virtual Screening & Diversity Selection Pipeline
INPUT: Molecular SMILES library {m_1, ..., m_N}, Training labels y in {0, 1}^N
OUTPUT: Ranked candidate scores, Selected batch of K diverse active compounds

STAGE 1: QUANTUM KERNEL EVALUATION & CLASSIFICATION
  1: For each molecule m_i in Training Set:
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
 15: Optimize (gamma, beta) using COBYLA; Sample 1024 shots -> Return optimal feasible batch of K candidates.""")
    run_c.font.name = 'Consolas'
    run_c.font.size = Pt(9.5)
    run_c.font.color.rgb = DARK_TEXT

    # ==========================================
    # Implementation
    # ==========================================
    add_h1("Implementation")
    add_bullet("Programming Language: ", "Python 3.11")
    add_bullet("Tools & Frameworks Used: ", "Qiskit 2.5 (quantum circuit construction and statevector simulation), Qiskit Machine Learning 0.9 (VQC algorithms), Qiskit Nature 0.8 & PySCF (electronic structure drivers), RDKit (cheminformatics, Morgan fingerprints, QED, Murcko scaffold splitting), scikit-learn (SVM, PCA, Random Forest, stratified splits), Streamlit (web user interface), pytest (test suite with 21 unit tests).")
    
    add_h2("Code Architecture & Explanation")
    add_p("The codebase is partitioned into distinct modular layers under src/quantumscreen/:")
    add_bullet("• data.py: ", "Handles dataset sanitization, RDKit canonical SMILES conversion, and train/test splits.")
    add_bullet("• features.py: ", "Implements the QuantumEncoder class ensuring zero test-set leakage during PCA and angle scaling.")
    add_bullet("• quantum.py: ", "Contains optimized statevector fidelity kernel routines, avoiding pairwise circuit re-evaluation.")
    add_bullet("• selection.py: ", "Encodes the diversity-aware QUBO, Ising mapping, and QAOA statevector circuit.")
    add_bullet("• vqe.py: ", "Runs UCCSD VQE for H2 and LiH potential energy curves.")

    add_h2("Attached Code Snippet")
    p_snip = doc.add_paragraph()
    p_snip.paragraph_format.space_before = Pt(2)
    p_snip.paragraph_format.space_after = Pt(6)
    p_snip.paragraph_format.line_spacing = 1.05
    run_s = p_snip.add_run("""# Quantum Kernel SVM Fit & Evaluate Routine (src/quantumscreen/quantum.py)
def compute_states(circuit, X: np.ndarray) -> np.ndarray:
    \"\"\"Precomputes Statevectors for all molecules in O(N) evaluations.\"\"\"
    return np.array([Statevector(circuit.assign_parameters(x)).data for x in X])

def fidelity_kernel(states_a: np.ndarray, states_b: np.ndarray) -> np.ndarray:
    \"\"\"Calculates exact transition fidelity Gram matrix: |<phi_a|phi_b>|^2.\"\"\"
    return np.abs(states_a.conj() @ states_b.T) ** 2

class QuantumKernelSVM(BaseEstimator, ClassifierMixin):
    def __init__(self, feature_map="zz", reps=2, C=1.0, scale=1.0):
        self.feature_map, self.reps, self.C, self.scale = feature_map, reps, C, scale

    def fit(self, X, y):
        self.circuit_ = build_feature_map(self.feature_map, X.shape[1], self.reps)
        self.train_states_ = compute_states(self.circuit_, X * self.scale)
        K = fidelity_kernel(self.train_states_, self.train_states_)
        self.svc_ = SVC(kernel="precomputed", C=self.C, probability=True).fit(K, y)
        return self""")
    run_s.font.name = 'Consolas'
    run_s.font.size = Pt(9.5)

    # ==========================================
    # Website (Optional)
    # ==========================================
    add_h1("Website & Interactive User Interface")
    add_bullet("Technologies Used: ", "Streamlit, Python, RDKit SVG MolDraw2D, joblib model persistence.")
    add_bullet("Software / Tools Used: ", "Browser-based local hosting on port 8501, running asynchronous model queries.")
    add_bullet("Design & Feature Explanation: ", "The dashboard delivers 4 dedicated modules: (1) Single Molecule Mode: Real-time molecular structure rendering and on-the-fly quantum scoring for user-submitted SMILES strings; (2) Batch Screening Mode: CSV upload and automated lead prioritization; (3) Benchmark Diagnostics: Interactive inspection of ROC curves, qubit ablations, and QAOA distributions; and (4) Transparent Disclosures: Complete documentation and limitation caveats.")
    add_img("results/figures/07_top_candidates.png", width=Inches(5.8), caption="Screening UI: Hold-Out Top Candidate Prioritization")

    # ==========================================
    # Results
    # ==========================================
    add_h1("Results & Performance Analysis")
    add_bullet("Input Given: ", "1,513 curated BACE-1 inhibitors (45.7% active class base rate), evaluated across 3 independent stratified random splits (80/20 train/test ratio) and 1 Bemis-Murcko scaffold split.")
    add_bullet("Output Obtained: ", "Model predictions, ROC-AUC, classification metrics, Enrichment Factor at 10% (EF@10%), and QAOA objective ratios.")

    # Table of Results
    tbl = doc.add_table(rows=6, cols=5)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Model Architecture", "Features", "ROC-AUC (mean ± std)", "EF@10%", "Fit Time"]
    data = [
        ["Random Forest", "2048-bit Morgan FP", "0.916 ± 0.006", "2.10", "1.7 s"],
        ["Classical SVM (RBF)", "8 PCA Components", "0.879 ± 0.007", "1.98", "4.4 s"],
        ["Random Forest", "8 PCA Components", "0.877 ± 0.015", "2.07", "0.8 s"],
        ["Quantum Kernel SVM", "8 Qubits (ZZ-map)", "0.873 ± 0.011", "2.07", "11.1 s"],
        ["Variational Classifier", "6 Qubits (VQC)", "0.625 ± 0.056", "--", "119.0 s"]
    ]
    col_widths = [Inches(1.8), Inches(1.5), Inches(1.6), Inches(0.8), Inches(0.8)]
    for j, h in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.width = col_widths[j]
        set_cell_background(cell, "E8DFF7")
        set_cell_margins(cell)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.name = 'Calibri'
    for i, row in enumerate(data):
        for j, val in enumerate(row):
            cell = tbl.cell(i + 1, j)
            cell.width = col_widths[j]
            set_cell_margins(cell)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if j >= 2 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(val)
            r.font.size = Pt(9.5)
            r.font.name = 'Calibri'
            if "Quantum Kernel SVM" in row[0]:
                r.bold = True

    add_p("")
    add_img("results/figures/01_model_comparison.png", width=Inches(5.5), caption="Model Performance Comparison on BACE-1 Benchmark")
    add_img("results/figures/02_roc_curves.png", width=Inches(5.5), caption="Receiver Operating Characteristic (ROC) Curves")

    add_h2("Time and Space Complexity Findings")
    add_bullet("• Time Complexity: ", "The Quantum Kernel SVM required 11.1 s to fit on 1,210 training molecules, roughly 2.5x slower than classical SVM due to Python statevector simulation overhead. VQC was ~90x slower (119 s) and underperformed.")
    add_bullet("• Space Complexity: ", "Memory during simulation scaled as 2^8 = 256 complex amplitudes per molecule. The full Gram matrix occupied 18 MB in RAM.")
    add_bullet("• QAOA Performance: ", "QAOA (p=3) achieved an objective ratio of 99.3–100% of the exact optimum. However, uniform random search with 1,024 shots matched QAOA because feasible search spaces (56 to 1,001 subsets) are modest.")
    add_bullet("• VQE Ground-State Chemistry: ", "VQE reproduced exact FCI energies to < 0.001 mHa across all bond lengths for H2 and LiH, demonstrating quantum simulation feasibility.")

    add_img("results/figures/09_vqe_curves.png", width=Inches(5.5), caption="VQE Potential Energy Dissociation Curves for H2 and LiH")

    # ==========================================
    # Conclusion
    # ==========================================
    add_h1("Conclusion")
    add_bullet("Successful Problem Resolution: ", "QuantumScreen successfully established an automated hybrid quantum-classical drug screening pipeline. It demonstrated high predictive enrichment (EF@10% = 2.07), accurately identifying 24 actives in its top 25 picks on a hold-out test set.")
    add_bullet("Efficiency and Performance: ", "The project provides an honest, peer-reviewed evaluation of quantum machine learning. While the Quantum Kernel SVM matched classical RBF-SVM performance, no quantum advantage was observed. Performance is primarily bounded by the PCA compression bottleneck (reducing 2,048 bits to 8 qubits), rather than kernel expressivity. QAOA effectively separated structural analogues, reducing redundant similarity from 0.46 to 0.14.")
    add_bullet("Future Directions: ", "Deploying circuits on physical superconducting quantum processors (IBM Quantum) with error mitigation, utilizing graph neural network latent embeddings, and implementing constraint-preserving XY-mixers for QAOA.")

    doc.save("report/QuantumScreen_Review_Report.docx")
    print("Successfully generated report/QuantumScreen_Review_Report.docx")

if __name__ == "__main__":
    create_report()
