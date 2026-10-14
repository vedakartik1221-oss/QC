"""QuantumScreen demo UI.   Run:  streamlit run app.py"""
import base64
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from quantumscreen.config import Config  # noqa: E402
from quantumscreen.features import drug_likeness, morgan_matrix  # noqa: E402
from quantumscreen.pipeline import load_model, screen_smiles  # noqa: E402

st.set_page_config(page_title="QuantumScreen", page_icon="⚛️", layout="wide")
cfg = Config()
REPO = "https://github.com/vedakartik1221-oss/QC/blob/main"

st.html("""
<style>
/* ---- backdrop: deep-space gradient with soft glows ---- */
.stApp {
  background:
    radial-gradient(1100px 600px at 85% -10%, rgba(139,124,255,.22), transparent 60%),
    radial-gradient(900px 500px at -10% 30%, rgba(34,211,238,.12), transparent 60%),
    radial-gradient(800px 600px at 60% 110%, rgba(244,114,182,.10), transparent 60%),
    #070B1A;
  background-attachment: fixed;
}
[data-testid="stHeader"] {background: transparent;}
[data-testid="stSidebar"] {border-right: 1px solid rgba(139,124,255,.18);}

/* ---- hero ---- */
.qs-hero {position: relative; overflow: hidden; display: flex; align-items: center; gap: 2rem;
  padding: 2.2rem 2.4rem; border-radius: 1.4rem; margin-bottom: .6rem;
  background: linear-gradient(135deg, rgba(139,124,255,.20), rgba(34,211,238,.10) 55%, rgba(244,114,182,.12));
  border: 1px solid rgba(139,124,255,.35);
  box-shadow: 0 20px 60px -20px rgba(139,124,255,.45), inset 0 1px 0 rgba(255,255,255,.06);}
.qs-hero::before {content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .5;
  background-image: radial-gradient(rgba(255,255,255,.35) 1px, transparent 1px);
  background-size: 22px 22px; mask-image: linear-gradient(90deg, transparent, #000 70%);
  -webkit-mask-image: linear-gradient(90deg, transparent, #000 70%);}
.qs-hero-text {position: relative; flex: 1; min-width: 0;}
.qs-eyebrow {font-size: .78rem; letter-spacing: .18em; text-transform: uppercase; color: #7DD3FC; font-weight: 600;}
.qs-hero h1 {margin: .3rem 0 .6rem 0; padding: 0; font-size: 3rem; line-height: 1.1; font-weight: 700;
  background: linear-gradient(90deg, #FFFFFF, #C4B5FD 45%, #67E8F9);
  -webkit-background-clip: text; background-clip: text; color: transparent;}
.qs-hero p {margin: 0; color: rgba(231,233,255,.78); font-size: 1.08rem; max-width: 46rem; line-height: 1.55;}
.qs-tags {margin-top: 1.1rem; display: flex; gap: .5rem; flex-wrap: wrap;}
.qs-tags span {font-size: .78rem; padding: .3rem .75rem; border-radius: 999px; color: #E7E9FF;
  background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.14);}

/* ---- animated atom ---- */
.qs-atom {position: relative; width: 170px; height: 170px; flex: none;}
.qs-atom .nucleus {position: absolute; left: 50%; top: 50%; width: 26px; height: 26px; margin: -13px; border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, #fff, #A78BFA 45%, #6D28D9);
  box-shadow: 0 0 30px 8px rgba(167,139,250,.6); animation: qs-pulse 2.8s ease-in-out infinite;}
.qs-atom .orbit {position: absolute; inset: 0; border-radius: 50%;}
.qs-atom .orbit:nth-child(2) {transform: rotate(60deg) scaleY(.38);}
.qs-atom .orbit:nth-child(3) {transform: rotate(-60deg) scaleY(.38);}
.qs-atom .orbit:nth-child(4) {transform: rotate(0deg) scaleY(.38);}
.qs-atom .orbit > div {position: absolute; inset: 0; border-radius: 50%; border: 1.5px solid rgba(125,211,252,.5);
  animation: qs-spin 3.2s linear infinite;}
.qs-atom .orbit:nth-child(3) > div {border-color: rgba(244,114,182,.5); animation-duration: 4.1s; animation-direction: reverse;}
.qs-atom .orbit:nth-child(4) > div {border-color: rgba(196,181,253,.55); animation-duration: 5s;}
.qs-atom .orbit > div::after {content: ""; position: absolute; top: -6px; left: 50%; width: 11px; height: 11px;
  margin-left: -5.5px; border-radius: 50%; background: #67E8F9; box-shadow: 0 0 14px 4px rgba(103,232,249,.85);}
.qs-atom .orbit:nth-child(3) > div::after {background: #F9A8D4; box-shadow: 0 0 14px 4px rgba(244,114,182,.85);}
.qs-atom .orbit:nth-child(4) > div::after {background: #DDD6FE; box-shadow: 0 0 14px 4px rgba(196,181,253,.85);}
@keyframes qs-spin {to {transform: rotate(360deg);}}
@keyframes qs-pulse {50% {box-shadow: 0 0 44px 14px rgba(167,139,250,.75);}}
@media (max-width: 760px) {.qs-atom {display: none;} .qs-hero {padding: 1.5rem;} .qs-hero h1 {font-size: 2.2rem;}}

/* ---- glass cards: metrics and bordered containers ---- */
[data-testid="stMetric"] {background: linear-gradient(160deg, rgba(139,124,255,.12), rgba(18,25,53,.6));
  border-color: rgba(139,124,255,.3) !important; transition: transform .18s ease, box-shadow .18s ease;}
[data-testid="stMetric"]:hover {transform: translateY(-2px); box-shadow: 0 10px 30px -12px rgba(139,124,255,.6);}
[data-testid="stMetricValue"] {font-family: "Space Grotesk", sans-serif; font-weight: 600;}
[data-testid="stMetricLabel"] p {color: rgba(231,233,255,.7);}

/* ---- tabs as pills ---- */
[data-testid="stTabs"] [role="tablist"] {gap: .4rem; padding: .35rem; border-radius: 999px; width: fit-content;
  max-width: 100%; overflow-x: auto; background: rgba(18,25,53,.75); border: 1px solid rgba(139,124,255,.25);}
[data-testid="stTab"] {border-radius: 999px; padding: .45rem 1.1rem !important; height: auto; transition: background .15s ease;}
[data-testid="stTab"]:hover {background: rgba(139,124,255,.12);}
[data-testid="stTab"][aria-selected="true"] {background: linear-gradient(135deg, #8B7CFF, #6366F1);
  box-shadow: 0 6px 18px -6px rgba(139,124,255,.8);}
[data-testid="stTab"][aria-selected="true"] * {color: #fff !important;}
/* ---- buttons and progress ---- */
[data-testid="stBaseButton-primary"] {background: linear-gradient(135deg, #8B7CFF, #22D3EE); border: 0;
  box-shadow: 0 8px 24px -8px rgba(139,124,255,.9); transition: transform .15s ease, filter .15s ease;}
[data-testid="stBaseButton-primary"]:hover {transform: translateY(-1px); filter: brightness(1.1);}

/* ---- molecule images and section headings ---- */
[data-testid="stImage"] img {border-radius: .9rem;}
.qs-section {display: flex; align-items: center; gap: .6rem; margin: .8rem 0 .2rem 0;
  font-family: "Space Grotesk", sans-serif; font-weight: 600; font-size: 1.15rem;}
.qs-section::after {content: ""; flex: 1; height: 1px; background: linear-gradient(90deg, rgba(139,124,255,.55), transparent);}

/* ---- probability ring ---- */
.qs-ring-wrap {display: flex; align-items: center; gap: 1.4rem; flex-wrap: wrap;}
.qs-ring {width: 132px; height: 132px; flex: none; border-radius: 50%; display: grid; place-items: center;}
.qs-ring > div {width: 104px; height: 104px; border-radius: 50%; background: #0D1330; display: grid; place-items: center;
  text-align: center; font-family: "Space Grotesk", sans-serif;}
.qs-ring b {font-size: 1.7rem; line-height: 1;} .qs-ring small {display: block; opacity: .65; font-size: .7rem; margin-top: .25rem;}
.qs-verdict {font-family: "Space Grotesk", sans-serif; font-size: 1.45rem; font-weight: 600; margin: 0 0 .3rem 0;}
.qs-verdict.good {color: #6EE7B7;} .qs-verdict.bad {color: #FCA5A5;}
.qs-sub {color: rgba(231,233,255,.72); font-size: .93rem; margin: 0; line-height: 1.5;}

/* ---- top candidate rank badge ---- */
.qs-rank {display: flex; align-items: center; gap: .6rem; font-family: "Space Grotesk", sans-serif;}
.qs-rank b {display: inline-grid; place-items: center; width: 2rem; height: 2rem; border-radius: 50%; font-size: .95rem;
  background: linear-gradient(135deg, #8B7CFF, #22D3EE); color: #fff;}
.qs-rank span {opacity: .8; font-size: .92rem;}
</style>
""")


def section(title: str):
    st.html(f'<div class="qs-section">{title}</div>')


def prob_ring(p: float, label: str = "P(active)") -> str:
    color = "#34D399" if p >= 0.5 else "#F87171"
    return (f'<div class="qs-ring" style="background: conic-gradient({color} {p * 100:.1f}%, '
            f'rgba(255,255,255,.08) 0); box-shadow: 0 0 40px -8px {color};">'
            f'<div><div><b>{p:.0%}</b><small>{label}</small></div></div></div>')


# ---------------------------------------------------------------- data / models
@st.cache_resource(show_spinner="Loading quantum model...")
def get_models():
    q_path, c_path = cfg.models_dir / "qsvm_final.joblib", cfg.models_dir / "svm_final.joblib"
    if not q_path.exists():
        return None
    enc, qsvm, meta = load_model(q_path)
    return enc, qsvm, (joblib.load(c_path) if c_path.exists() else None), meta


@st.cache_data
def example_molecules():
    df = pd.read_csv(cfg.data_path)
    return {"Known active": df[df.Class == 1].mol.iloc[3], "Known inactive": df[df.Class == 0].mol.iloc[3],
            "Aspirin": "CC(=O)Oc1ccccc1C(=O)O"}


@st.cache_data
def screening_summary():
    p = cfg.results_dir / "screening_summary.json"
    return json.loads(p.read_text()) if p.exists() else {}


@st.cache_data(max_entries=2000)
def mol_svg(smiles: str, w: int = 360, h: int = 280) -> str | None:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    d = rdMolDraw2D.MolDraw2DSVG(w, h)
    opts = d.drawOptions()
    rdMolDraw2D.SetDarkMode(opts)
    opts.setBackgroundColour((0, 0, 0, 0))
    opts.addStereoAnnotation = True
    opts.bondLineWidth = 2
    rdMolDraw2D.PrepareAndDrawMolecule(d, mol)
    d.FinishDrawing()
    return d.GetDrawingText()


def svg_data_uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def show_mol(smiles: str, w: int = 360, h: int = 280):
    svg = mol_svg(smiles, w, h)
    if svg:
        st.image(svg, width="stretch")


def predict(smiles_list):
    X = enc.transform(morgan_matrix(smiles_list))
    pq = qsvm.predict_proba(X)[:, 1]
    pc = svm.predict_proba(X)[:, 1] if svm is not None else None
    return pq, pc


models = get_models()
if models is None:
    st.error("No trained model found. Run `python main.py --stage screen` first (about 1 minute).")
    st.stop()
enc, qsvm, svm, meta = models
summary = screening_summary()

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### ⚛️ QuantumScreen")
    st.caption("Quantum-kernel virtual screening for BACE-1 inhibitors")
    with st.container(border=True):
        st.markdown("**Deployed model**")
        a, b = st.columns(2)
        a.metric("Qubits", meta.get("n_qubits"))
        b.metric("Feature map", str(meta.get("feature_map", "")).upper())
        a.metric("Circuit reps", meta.get("reps"))
        b.metric("Training set", meta.get("n_molecules"))
        cv = (meta.get("best_params") or {}).get("cv_auc")
        if cv is not None:
            st.caption(f"Cross-validated ROC-AUC {float(cv):.3f} · trained {meta.get('trained', '?')}")
    with st.container(border=True):
        st.markdown("**How candidates are ranked**")
        st.markdown(f"`{cfg.w_activity:.1f} × P(active)` + `{cfg.w_qed:.1f} × QED`, minus "
                    f"`{cfg.lipinski_penalty:.2f}` per Lipinski violation beyond the first.")
    st.caption("Quantum circuits are simulated classically. Research and teaching prototype, "
               "not a validated tool for drug decisions.")

# ---------------------------------------------------------------- header
st.html("""
<div class="qs-hero">
  <div class="qs-hero-text">
    <div class="qs-eyebrow">Quantum machine learning · Drug discovery</div>
    <h1>QuantumScreen</h1>
    <p>Score molecules for activity against <b>BACE-1</b>, an Alzheimer's disease target, with a
    quantum-kernel support vector machine, then rank them by predicted activity and drug-likeness.</p>
    <div class="qs-tags"><span>⚛️ Qiskit</span><span>🧬 Quantum kernel SVM</span><span>🧪 RDKit</span>
    <span>📊 1,513 BACE molecules</span><span>💻 Simulated circuits</span></div>
  </div>
  <div class="qs-atom"><div class="nucleus"></div><div class="orbit"><div></div></div>
    <div class="orbit"><div></div></div><div class="orbit"><div></div></div></div>
</div>
""")

if summary:
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Top-25 hit rate", f"{summary['precision_at_k_quantum_score']:.0%}",
              f"vs {summary['base_hit_rate']:.0%} base rate", delta_color="off", border=True)
    h2.metric("Enrichment @10%", f"{summary['ef10_quantum']:.2f}×",
              f"classical SVM {summary['ef10_classical']:.2f}×", delta_color="off", border=True)
    h3.metric("Hold-out molecules", summary["library_size"], border=True)
    h4.metric("Actives passing Lipinski", f"{summary['actives_passing_lipinski']:.0%}", border=True)

tab1, tab2, tab3, tab4 = st.tabs([":material/science: Single molecule", ":material/list_alt: Batch screening",
                                  ":material/monitoring: Benchmark results", ":material/info: About"])

# ---------------------------------------------------------------- single molecule
with tab1:
    ex = example_molecules()

    def _load_example():
        if st.session_state.example:
            st.session_state.smiles = ex[st.session_state.example]

    st.pills("Try an example", list(ex), key="example", on_change=_load_example)
    smiles = st.text_input("SMILES string", key="smiles", placeholder="e.g. CC(=O)Oc1ccccc1C(=O)O").strip()

    if not smiles:
        st.info("Paste a SMILES string above or pick an example to score a molecule.", icon=":material/arrow_upward:")
    elif Chem.MolFromSmiles(smiles) is None:
        st.warning("That is not a valid SMILES string.", icon=":material/error:")
    else:
        pq, pc = predict([smiles])
        pq, pc = float(pq[0]), (float(pc[0]) if pc is not None else None)
        props = drug_likeness([smiles]).iloc[0]
        promising = pq >= 0.5

        left, right = st.columns([1, 1.35], gap="large")
        with left:
            show_mol(smiles)
            st.caption(f"`{smiles}`")
        with right:
            with st.container(border=True):
                verdict = ("good", "Promising candidate", "The quantum model predicts this molecule is likely "
                           "to inhibit BACE-1.") if promising else \
                          ("bad", "Unlikely to be active", "The quantum model predicts this molecule is unlikely "
                           "to inhibit BACE-1.")
                st.html(f'<div class="qs-ring-wrap">{prob_ring(pq)}<div><p class="qs-verdict {verdict[0]}">'
                        f'{verdict[1]}</p><p class="qs-sub">{verdict[2]}</p></div></div>')
                m1, m2 = st.columns(2)
                m1.metric("Quantum kernel SVM", f"{pq:.1%}")
                if pc is not None:
                    m2.metric("Classical RBF SVM", f"{pc:.1%}", f"{(pc - pq) * 100:+.1f} pts vs quantum"
                              if abs(pq - pc) >= 0.001 else None, delta_color="off")
                    if (pq >= 0.5) != (pc >= 0.5):
                        st.caption(":orange[The two models disagree, so treat this score with extra caution.]")
                    else:
                        st.caption("Both models agree on the verdict.")

            viol = int(props.lipinski_violations)
            if viol <= 1:
                st.success(f"Passes Lipinski's rule of five ({viol} violation{'s' if viol != 1 else ''}).",
                           icon=":material/verified:")
            else:
                st.error(f"Fails Lipinski's rule of five ({viol} violations).", icon=":material/report:")

        section("🧪 Drug-likeness")
        rules = [("Mol. weight", props.MW, 500, "{:.0f}", "Molecular weight in Da"),
                 ("LogP", props.LogP, 5, "{:.2f}", "Octanol-water partition coefficient"),
                 ("H donors", props.HBD, 5, "{:.0f}", "Hydrogen-bond donors"),
                 ("H acceptors", props.HBA, 10, "{:.0f}", "Hydrogen-bond acceptors")]
        cols = st.columns(7)
        for col, (label, val, limit, fmt, tip) in zip(cols, rules):
            ok = val <= limit
            col.metric(label, fmt.format(val), f"{'✓' if ok else '✗'} ≤ {limit}", help=f"{tip}. Lipinski limit {limit}.",
                       delta_color="normal" if ok else "inverse", delta_arrow="off", border=True)
        cols[4].metric("QED", f"{props.QED:.2f}", help="Quantitative estimate of drug-likeness, 0 to 1", border=True)
        cols[5].metric("TPSA (Å²)", f"{props.TPSA:.0f}", help="Topological polar surface area", border=True)
        cols[6].metric("Rot. bonds", f"{props.RotB:.0f}", help="Rotatable bonds", border=True)
        st.caption("The model was trained on BACE-1 data; molecules far from that chemical space give unreliable scores.")

# ---------------------------------------------------------------- batch screening
with tab2:
    example_csv = ROOT / "test_batch_screening.csv"

    def _load_batch_example():
        st.session_state.batch_text = "\n".join(pd.read_csv(example_csv)["smiles"].dropna().astype(str))

    in1, in2 = st.columns([1.4, 1], gap="large")
    with in1:
        text = st.text_area("SMILES, one per line", key="batch_text", height=180,
                            placeholder="CC(=O)Oc1ccccc1C(=O)O\nCCN(CC)CC...")
        if example_csv.exists():
            st.button("Load example set", icon=":material/lab_profile:", on_click=_load_batch_example)
    with in2:
        up = st.file_uploader("Or upload a CSV with a `smiles` column", type="csv")

    smi = [s.strip() for s in text.splitlines() if s.strip()]
    if up is not None:
        up_df = pd.read_csv(up)
        if "smiles" in up_df.columns:
            smi += up_df["smiles"].dropna().astype(str).tolist()
        else:
            st.error("The uploaded CSV has no `smiles` column.")

    if st.button(f"Screen & rank {len(smi)} molecule{'s' if len(smi) != 1 else ''}" if smi else "Screen & rank",
                 type="primary", icon=":material/rocket_launch:", disabled=not smi):
        valid = [s for s in smi if Chem.MolFromSmiles(s) is not None]
        with st.spinner(f"Simulating quantum kernels for {len(valid)} molecules..."):
            ranked = screen_smiles(valid, enc, qsvm, cfg) if valid else pd.DataFrame()
            if valid and svm is not None:
                _, pc = predict(ranked["smiles"].tolist())
                ranked.insert(ranked.columns.get_loc("p_quantum_active") + 1, "p_classical_active", pc)
        st.session_state.batch = dict(ranked=ranked, n_in=len(smi), n_bad=len(smi) - len(valid))

    res = st.session_state.get("batch")
    if res:
        ranked = res["ranked"]
        if res["n_bad"]:
            st.warning(f"Skipped {res['n_bad']} invalid SMILES.", icon=":material/error:")
        if not ranked.empty:
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Screened", len(ranked), border=True)
            s2.metric("Promising (P ≥ 50%)", int((ranked.p_quantum_active >= 0.5).sum()), border=True)
            s3.metric("Pass Lipinski", int(ranked.passes_lipinski.sum()), border=True)
            s4.metric("Best final score", f"{ranked.final_score.max():.3f}", border=True)

            section("🏆 Top candidates")
            for col, (_, row) in zip(st.columns(3), ranked.head(3).iterrows()):
                with col.container(border=True):
                    st.html(f'<div class="qs-rank"><b>{row["rank"]}</b><span>final score '
                            f'{row.final_score:.3f}</span></div>')
                    show_mol(row.smiles, 300, 220)
                    st.caption(f"P(active) {row.p_quantum_active:.0%} · QED {row.QED:.2f}")

            section("📋 Full ranking")
            table = ranked.copy()
            table.insert(1, "structure", [svg_data_uri(mol_svg(s, 220, 160)) for s in table.smiles])
            pct = dict(min_value=0.0, max_value=1.0, format="percent")
            st.dataframe(
                table, hide_index=True, width="stretch", row_height=70,
                column_order=["rank", "structure", "smiles", "final_score", "p_quantum_active", "p_classical_active",
                              "QED", "passes_lipinski", "MW", "LogP", "HBD", "HBA", "TPSA", "RotB"],
                column_config={
                    "rank": st.column_config.NumberColumn("#", width=40),
                    "structure": st.column_config.ImageColumn("Structure", width=110),
                    "smiles": st.column_config.TextColumn("SMILES", width="medium"),
                    "final_score": st.column_config.ProgressColumn("Final score", format="%.3f",
                                                                   min_value=0.0, max_value=1.0),
                    "p_quantum_active": st.column_config.ProgressColumn("Quantum P(active)", **pct),
                    "p_classical_active": st.column_config.ProgressColumn("Classical P(active)", **pct),
                    "QED": st.column_config.ProgressColumn("QED", format="%.2f", min_value=0.0, max_value=1.0),
                    "passes_lipinski": st.column_config.CheckboxColumn("Lipinski"),
                    "MW": st.column_config.NumberColumn("MW", format="%.0f"),
                    "LogP": st.column_config.NumberColumn(format="%.2f"),
                    "TPSA": st.column_config.NumberColumn(format="%.0f"),
                })
            st.download_button("Download ranked CSV", ranked.to_csv(index=False), "ranked_candidates.csv",
                               mime="text/csv", icon=":material/download:")
    elif not smi:
        st.info("Add molecules above, or load the example set, then press **Screen & rank**.",
                icon=":material/arrow_upward:")

# ---------------------------------------------------------------- benchmark
FIGURES = {
    "01_model_comparison": ("Model comparison", "ROC-AUC of every model on random splits."),
    "02_roc_curves": ("ROC curves", "Quantum vs classical models on the test split."),
    "03_qubit_ablation": ("Qubit ablation", "More than 8 qubits does not help."),
    "04_featuremap_ablation": ("Feature-map ablation", "Entanglement does not improve accuracy here."),
    "05_scaffold_split": ("Scaffold split", "Harder generalisation to new chemical scaffolds."),
    "06_vqc_comparison": ("Variational classifier", "VQC is slower and weaker than the kernel SVM."),
    "07_top_candidates": ("Top candidates", "Best-ranked molecules from the hold-out screen."),
    "08_kernel_matrix": ("Quantum kernel matrix", "Similarity between molecules in Hilbert space."),
    "09_vqe_curves": ("VQE energy curves", "Ground-state energies of H₂ and LiH."),
    "10_zz_feature_map": ("ZZ feature map", "The circuit that encodes a molecule into qubits."),
    "11_qaoa_selection": ("QAOA batch selection", "Choosing a diverse batch of candidates."),
    "12_selected_molecules": ("Selected molecules", "The diverse batch picked by QAOA."),
}

with tab3:
    rdir = cfg.results_dir
    if (rdir / "benchmark_summary.csv").exists():
        bench = pd.read_csv(rdir / "benchmark_summary.csv")
        split = st.segmented_control("Data split", ["random", "scaffold"], default="random",
                                     format_func=lambda s: {"random": "Random split", "scaffold": "Scaffold split"}[s])
        b = bench[bench.split == (split or "random")].sort_values("auc_mean", ascending=False)
        st.dataframe(
            b[["model", "family", "auc_mean", "auc_std", "f1_mean", "ef10_mean", "fit_seconds_mean"]],
            hide_index=True, width="stretch",
            column_config={
                "model": st.column_config.TextColumn("Model", width="large"),
                "family": st.column_config.TextColumn("Family"),
                "auc_mean": st.column_config.ProgressColumn("ROC-AUC", format="%.3f", min_value=0.5, max_value=1.0),
                "auc_std": st.column_config.NumberColumn("± std", format="%.3f"),
                "f1_mean": st.column_config.NumberColumn("F1", format="%.3f"),
                "ef10_mean": st.column_config.NumberColumn("EF@10%", format="%.2f"),
                "fit_seconds_mean": st.column_config.NumberColumn("Fit time (s)", format="%.1f"),
            })
        st.caption("Mean over 3 seeds. The quantum kernel matches, but does not beat, a classical SVM on the same features.")
    else:
        st.info("Run `python main.py` to generate the benchmark results.")

    figs = [f for f in sorted((rdir / "figures").glob("*.png")) if f.stem in FIGURES]
    for i in range(0, len(figs), 2):
        for col, f in zip(st.columns(2), figs[i:i + 2]):
            title, note = FIGURES[f.stem]
            with col.container(border=True):
                st.markdown(f"**{title}**")
                st.caption(note)
                st.image(str(f), width="stretch")

# ---------------------------------------------------------------- about
with tab4:
    section("⚙️ How it works")
    steps = [(":material/edit_note:", "SMILES", "Molecule as text"),
             (":material/fingerprint:", "Fingerprint", "2048-bit Morgan"),
             (":material/compress:", "PCA", f"{meta.get('n_qubits')} components → qubit angles"),
             (":material/memory:", "Quantum kernel", f"{str(meta.get('feature_map', '')).upper()} feature map"),
             (":material/hub:", "SVM", "P(active)"),
             (":material/leaderboard:", "Rank", "+ QED & Lipinski")]
    for col, (icon, name, desc) in zip(st.columns(len(steps)), steps):
        with col.container(border=True):
            st.markdown(f"{icon} **{name}**")
            st.caption(desc)

    st.info("**Honest note:** the quantum circuits are *simulated* on a classical computer. On this data the quantum "
            "kernel performs about as well as a classical RBF SVM, not better: there is no quantum advantage.",
            icon=":material/lightbulb:")

    c1, c2 = st.columns(2)
    with c1:
        section("📚 Documentation")
        for name, desc in [("METHODOLOGY", "dataset, kernels, evaluation"), ("RESULTS", "all experiments"),
                           ("LIMITATIONS", "what this does not show"), ("USER_GUIDE", "install and CLI")]:
            st.markdown(f"- [{name.replace('_', ' ').title()}]({REPO}/docs/{name}.md): {desc}")
    with c2:
        section("🙏 Credits")
        st.markdown("BACE data: Subramanian et al., *J. Chem. Inf. Model.* 2016 (via MoleculeNet).  \n"
                    "Quantum kernels: Havlíček et al., *Nature* 2019.  \n"
                    "Capstone project, Amrita Vishwa Vidyapeetham.")
