"""QuantumScreen demo UI.   Run:  streamlit run app.py"""
import sys
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st
from rdkit import Chem
from rdkit.Chem import Draw

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from quantumscreen.config import Config  # noqa: E402
from quantumscreen.features import drug_likeness, morgan_matrix  # noqa: E402
from quantumscreen.pipeline import load_model, screen_smiles  # noqa: E402

st.set_page_config(page_title="QuantumScreen", page_icon="⚛️", layout="wide")
cfg = Config()


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
            "Aspirin (not a BACE ligand)": "CC(=O)Oc1ccccc1C(=O)O"}


st.title("⚛️ QuantumScreen")
st.caption("Hybrid quantum-classical virtual screening for BACE-1 inhibitors (Alzheimer's target). "
           "Built with Qiskit - quantum kernel SVM, simulated on a classical computer.")

models = get_models()
if models is None:
    st.error("No trained model found. Run `python main.py --stage screen` first (about 1 minute).")
    st.stop()
enc, qsvm, svm, meta = models

tab1, tab2, tab3, tab4 = st.tabs(["Single molecule", "Batch screening", "Benchmark results", "About"])

with tab1:
    ex = example_molecules()
    choice = st.selectbox("Load an example", ["(type your own)"] + list(ex))
    smiles = st.text_input("SMILES", value="" if choice == "(type your own)" else ex[choice])
    if smiles:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            st.warning("That is not a valid SMILES string.")
        else:
            X = enc.transform(morgan_matrix([smiles]))
            pq = float(qsvm.predict_proba(X)[0, 1])
            c1, c2 = st.columns([1, 2])
            c1.image(Draw.MolToImage(mol, size=(360, 300)))
            with c2:
                m1, m2, m3 = st.columns(3)
                m1.metric("Quantum P(active)", f"{pq:.1%}")
                if svm is not None:
                    m2.metric("Classical SVM P(active)", f"{float(svm.predict_proba(X)[0, 1]):.1%}")
                m3.metric("Verdict", "Promising" if pq >= 0.5 else "Unlikely")
                props = drug_likeness([smiles]).iloc[0]
                st.dataframe(props.rename("value").to_frame().T.round(2), width="stretch")
                st.caption("The model was trained on BACE-1 data; molecules far from that chemical space give unreliable scores.")

with tab2:
    st.write("Paste one SMILES per line, or upload a CSV with a `smiles` column.")
    text = st.text_area("SMILES list", height=140)
    up = st.file_uploader("...or CSV", type="csv")
    smi = [s.strip() for s in text.splitlines() if s.strip()]
    if up is not None:
        smi += pd.read_csv(up)["smiles"].dropna().astype(str).tolist()
    if smi and st.button("Screen & rank", type="primary"):
        valid = [s for s in smi if Chem.MolFromSmiles(s) is not None]
        if len(valid) < len(smi):
            st.warning(f"Skipped {len(smi) - len(valid)} invalid SMILES.")
        ranked = screen_smiles(valid, enc, qsvm, cfg).drop(columns=["passes_lipinski"], errors="ignore")
        st.dataframe(ranked.round(3), width="stretch")
        st.download_button("Download ranked CSV", ranked.to_csv(index=False), "ranked_candidates.csv")

with tab3:
    res = cfg.results_dir
    if (res / "benchmark_summary.csv").exists():
        s = pd.read_csv(res / "benchmark_summary.csv")
        s = s[s.split == "random"][["model", "auc_mean", "auc_std", "f1_mean", "ef10_mean", "fit_seconds_mean"]]
        st.dataframe(s.round(3), width="stretch", hide_index=True)
    for f in sorted((res / "figures").glob("*.png")):
        st.image(str(f), caption=f.stem.replace("_", " "))
    if not (res / "benchmark_summary.csv").exists():
        st.info("Run `python main.py` to generate the benchmark results.")

with tab4:
    st.markdown(f"""
**Model:** quantum-kernel SVM, `{meta.get('feature_map')}` feature map (reps={meta.get('reps')}), {meta.get('n_qubits')} qubits,
trained on {meta.get('n_molecules')} BACE molecules. **Pipeline:** SMILES -> Morgan fingerprint -> PCA -> qubit angles -> quantum kernel -> SVM -> rank with QED/Lipinski.

**Honest note:** the quantum circuits are *simulated*; on this data the quantum kernel performs about as well as a classical RBF SVM,
not better. See `docs/METHODOLOGY.md` and `docs/LIMITATIONS.md`.
""")
