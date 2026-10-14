const fs = require("fs");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require("/mnt/skills/public/pptx/scripts/apply_theme.js");

const N = JSON.parse(fs.readFileSync(__dirname + "/numbers.json", "utf8"));
const ROOT = __dirname + "/..";
const S = N.scr;

const THEME = {
  name: "QuantumScreen", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1B1340", lt1: "FFFFFF", dk2: "2B1B5E", lt2: "F4F1FB",
            accent1: "6C3FC5", accent2: "2A9D8F", accent3: "F4A261", accent4: "B8A1E3", accent5: "4B2A91", accent6: "6B7280",
            hlink: "6C3FC5", folHlink: "4B2A91" },
};
const HEX = { quantum: "6C3FC5", classical: "2A9D8F", ink: "1B1340", muted: "6B7280", grid: "D9D4E8" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "QuantumScreen - Capstone Presentation";
pres.author = "G Veda Kartik";
const C = pres.SchemeColor;

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "TITLE_DARK", background: { color: C.text2 },
  objects: [],
  slideNumber: undefined,
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.7, y: 0.4, w: 11.9, h: 0.9, fontSize: 34, bold: true, color: C.text2, margin: 0, valign: "middle" }, text: "" } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 11, color: C.accent6, align: "right" },
});
pres.defineSlideMaster({
  title: "CLOSE_DARK", background: { color: C.text2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.7, y: 0.4, w: 11.9, h: 0.9, fontSize: 34, bold: true, color: C.background1, margin: 0, valign: "middle" }, text: "" } },
  ],
});

// ---------- helpers ----------
async function icon(name, color = "#FFFFFF") {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(fa[name], { color, size: 256 }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
const T = (slide, text, o) => slide.addText(text, { isTextBox: true, margin: 0, ...o });
const img = (key) => ({ path: `${ROOT}/${N.figs[key].path}`, w: N.figs[key].w, h: N.figs[key].h });
function fitImage(slide, key, x, y, maxW, maxH, name) {
  const f = N.figs[key]; const r = Math.min(maxW / f.w, maxH / f.h);
  const w = f.w * r, h = f.h * r;
  slide.addImage({ path: `${ROOT}/${f.path}`, x: x + (maxW - w) / 2, y: y + (maxH - h) / 2, w, h, objectName: name || key, altText: name || key });
  return { w, h };
}
function card(slide, x, y, w, h, name) {
  slide.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.12, fill: { color: C.background2 }, line: { type: "none" }, objectName: name });
}
async function stat(slide, x, y, w, big, label, opts = {}) {
  card(slide, x, y, w, opts.h || 1.45, "stat-card");
  T(slide, big, { x: x + 0.25, y: y + 0.12, w: w - 0.5, h: 0.75, fontSize: opts.bigSize || 40, bold: true, color: opts.color || C.accent5, fontFace: "Cambria", valign: "middle", objectName: "stat-value" });
  T(slide, label, { x: x + 0.25, y: y + 0.88, w: w - 0.5, h: (opts.h || 1.45) - 0.98, fontSize: 14, color: C.text1, valign: "top", objectName: "stat-label" });
}
const chartBase = () => ({
  catAxisLabelColor: "1B1340", valAxisLabelColor: "6B7280", catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 12, valAxisLabelFontSize: 11, valGridLine: { color: HEX.grid, size: 0.5 }, catGridLine: { style: "none" },
  dataLabelColor: "1B1340", dataLabelFontFace: "+mn-lt", dataLabelFontSize: 12, legendFontFace: "+mn-lt", legendFontSize: 12, legendColor: "1B1340",
  titleFontFace: "+mn-lt", titleFontSize: 14, titleColor: "1B1340",
});
const num = (s) => parseFloat(String(s).split(" ")[0]);

(async () => {
  // ================= 1. title =================
  pres.addSection({ title: "Introduction" });
  let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Introduction" });
  T(s, "CAPSTONE PROJECT  |  QUANTUM COMPUTING", { x: 0.8, y: 0.9, w: 7.4, h: 0.4, fontSize: 14, bold: true, color: C.accent4, charSpacing: 2, objectName: "kicker" });
  T(s, "QuantumScreen", { x: 0.8, y: 1.5, w: 7.4, h: 1.2, fontSize: 60, bold: true, color: C.background1, fontFace: "Cambria", objectName: "deck-title" });
  T(s, "A quantum computing-based drug screening system to identify promising drug candidates", { x: 0.8, y: 2.8, w: 7.0, h: 1.2, fontSize: 24, color: C.background1, valign: "top", objectName: "subtitle" });
  T(s, [{ text: "G Veda Kartik", options: { bold: true, breakLine: true } }, { text: "Roll No. CH.SC.U4CSE24212", options: { breakLine: true } }, { text: "Amrita Vishwa Vidyapeetham, Chennai" }],
    { x: 0.8, y: 5.3, w: 7, h: 1.2, fontSize: 16, color: C.accent4, valign: "top", paraSpaceAfter: 4, objectName: "author" });
  const k = N.figs.ker; const kw = 4.6, kh = kw * k.h / k.w;
  s.addShape(pres.ShapeType.roundRect, { x: 8.2, y: 1.6, w: kw + 0.4, h: kh + 0.4, rectRadius: 0.15, fill: { color: C.background1 }, line: { type: "none" }, objectName: "kernel-frame" });
  s.addImage({ path: `${ROOT}/${k.path}`, x: 8.4, y: 1.8, w: kw, h: kh, objectName: "kernel-matrix", altText: "Quantum kernel matrix heatmap" });
  T(s, "Quantum kernel matrix of 150 BACE molecules", { x: 8.2, y: 1.6 + kh + 0.55, w: kw + 0.4, h: 0.35, fontSize: 12, color: C.accent4, align: "center", objectName: "kernel-caption" });
  s.addNotes("Introduce the project: a hybrid quantum-classical screening system built in Qiskit for BACE-1, an Alzheimer's target. The picture is the quantum kernel: similarity of molecules in an 8-qubit feature space.");

  // ================= 2. why =================
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Introduction" });
  s.addText("Why quantum drug screening?", { placeholder: "title" });
  const rows = [
    ["FaFlask", "Screening is the bottleneck", "Virtual screening ranks huge libraries so only the best few compounds are tested in the lab."],
    ["FaBrain", "Target: BACE-1", "An Alzheimer's-disease enzyme. Dataset: 1513 inhibitors labelled active or inactive."],
    ["FaAtom", "The quantum idea", "Encode a molecule in an n-qubit state and compare molecules in a 2^n-dimensional space."],
  ];
  for (let i = 0; i < rows.length; i++) {
    const y = 1.7 + i * 1.7;
    s.addShape(pres.ShapeType.ellipse, { x: 0.7, y, w: 0.9, h: 0.9, fill: { color: C.accent1 }, line: { type: "none" }, objectName: "icon-circle" });
    s.addImage({ data: await icon(rows[i][0]), x: 0.93, y: y + 0.23, w: 0.44, h: 0.44, objectName: "icon", altText: rows[i][1] });
    T(s, rows[i][1], { x: 1.9, y: y - 0.05, w: 5.9, h: 0.45, fontSize: 20, bold: true, color: C.text2, fontFace: "Cambria", objectName: "row-head" });
    T(s, rows[i][2], { x: 1.9, y: y + 0.42, w: 5.9, h: 0.9, fontSize: 15, color: C.text1, valign: "top", objectName: "row-body" });
  }
  await stat(s, 8.6, 1.7, 4.0, "1,513", "molecules, 45.7% active");
  await stat(s, 8.6, 3.4, 4.0, "8 qubits", "one PCA component per qubit, simulated exactly");
  await stat(s, 8.6, 5.1, 4.0, "3 seeds", "plus a scaffold split and ablations");
  s.addNotes("Motivation and scope. Quantum models are simulated classically; the goal is a fair, honest comparison.");

  // ================= 3. pipeline =================
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Introduction" });
  s.addText("A hybrid quantum-classical pipeline", { placeholder: "title" });
  const steps = [
    ["SMILES", "RDKit cleaning, scaffold and random splits"],
    ["Fingerprint + PCA", "2048-bit Morgan to 8 angles in [0, π]"],
    ["Qiskit feature map", "ZZ circuit loads a molecule into 8 qubits"],
    ["Kernel + SVM", "Fidelity kernel, C and scale tuned by CV"],
    ["Rank + select", "Final score, then QAOA picks a diverse batch of K"],
  ];
  const cw = 2.2, gapx = 0.2, x0 = 0.7;
  steps.forEach((st, i) => {
    const x = x0 + i * (cw + gapx);
    card(s, x, 1.9, cw, 3.0, "step-card");
    s.addShape(pres.ShapeType.ellipse, { x: x + 0.25, y: 2.15, w: 0.6, h: 0.6, fill: { color: i === 2 || i === 3 ? C.accent1 : C.accent2 }, line: { type: "none" }, objectName: "step-badge" });
    T(s, String(i + 1), { x: x + 0.25, y: 2.15, w: 0.6, h: 0.6, fontSize: 20, bold: true, color: C.background1, align: "center", valign: "middle", objectName: "step-num" });
    T(s, st[0], { x: x + 0.25, y: 3.0, w: cw - 0.5, h: 0.6, fontSize: 18, bold: true, color: C.text2, fontFace: "Cambria", valign: "top", objectName: "step-title" });
    T(s, st[1], { x: x + 0.25, y: 3.65, w: cw - 0.5, h: 1.1, fontSize: 14, color: C.text1, valign: "top", objectName: "step-body" });
    if (i < steps.length - 1) s.addShape(pres.ShapeType.rightArrow, { x: x + cw - 0.02, y: 3.25, w: gapx + 0.04, h: 0.3, fill: { color: C.accent4 }, line: { type: "none" }, objectName: "arrow" });
  });
  s.addShape(pres.ShapeType.ellipse, { x: 0.7, y: 5.45, w: 0.2, h: 0.2, fill: { color: C.accent1 }, line: { type: "none" }, objectName: "legend-q" });
  T(s, "Quantum steps", { x: 1.0, y: 5.37, w: 2, h: 0.36, fontSize: 14, color: C.text1, valign: "middle", objectName: "legend-q-text" });
  s.addShape(pres.ShapeType.ellipse, { x: 3.0, y: 5.45, w: 0.2, h: 0.2, fill: { color: C.accent2 }, line: { type: "none" }, objectName: "legend-c" });
  T(s, "Classical steps", { x: 3.3, y: 5.37, w: 2, h: 0.36, fontSize: 14, color: C.text1, valign: "middle", objectName: "legend-c-text" });
  T(s, "Classical baselines (RBF-SVM, Random Forest) run on the same splits, features and tuning budget. VQC and VQE are separate modules.", { x: 0.7, y: 5.95, w: 11.9, h: 0.7, fontSize: 16, color: C.text1, valign: "top", objectName: "baseline-note" });
  s.addNotes("Walk through the five stages. Stress fairness: identical splits, identical PCA features and the same inner cross-validation for the classical SVM.");

  // ================= 4. kernel =================
  pres.addSection({ title: "Method" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Method" });
  s.addText("How the quantum kernel works", { placeholder: "title" });
  const k3 = [
    ["Encode", "|φ(x)⟩ = U(x)|0…0⟩", "A feature map turns a molecule's 8 angles into a quantum state."],
    ["Compare", "k(x, x′) = |⟨φ(x)|φ(x′)⟩|²", "Fidelity between two states is the similarity of two molecules."],
    ["Classify", "SVM on the kernel matrix", "A classical SVM uses the quantum similarities to separate actives."],
  ];
  k3.forEach((r, i) => {
    const y = 1.6 + i * 1.28;
    card(s, 0.7, y, 6.0, 1.12, "step-card");
    T(s, r[0], { x: 0.95, y: y + 0.1, w: 1.3, h: 0.4, fontSize: 18, bold: true, color: C.accent1, fontFace: "Cambria", objectName: "k-head" });
    T(s, r[1], { x: 2.25, y: y + 0.1, w: 4.3, h: 0.4, fontSize: 18, bold: true, color: C.text2, objectName: "k-formula" });
    T(s, r[2], { x: 0.95, y: y + 0.55, w: 5.55, h: 0.5, fontSize: 14, color: C.text1, valign: "top", objectName: "k-body" });
  });
  const cf = N.figs; // circuit figure
  const circ = { path: `${ROOT}/results/figures/10_zz_feature_map.png`, w: 1700, h: 412 };
  s.addShape(pres.ShapeType.roundRect, { x: 0.7, y: 5.5, w: 11.9, h: 1.3, rectRadius: 0.12, fill: { color: C.background1 }, line: { color: C.accent4, width: 1 }, objectName: "circuit-frame" });
  const ch = 1.1, cwid = ch * circ.w / circ.h;
  s.addImage({ path: circ.path, x: 0.8, y: 5.6, w: cwid, h: ch, objectName: "zz-circuit", altText: "ZZ feature map circuit on 4 qubits" });
  T(s, "ZZ feature map (4 qubits shown): Hadamards, Z rotations by the data, entangling ZZ rotations.", { x: 0.8 + cwid + 0.3, y: 5.6, w: 12.6 - (0.8 + cwid + 0.3) - 0.2, h: 1.1, fontSize: 14, color: C.text1, valign: "middle", objectName: "circuit-caption" });
  // right: highlights
  card(s, 7.0, 1.6, 5.6, 3.7, "info-card");
  s.addImage({ data: await icon("FaCogs", "#6C3FC5"), x: 7.3, y: 1.85, w: 0.5, h: 0.5, objectName: "icon-cogs", altText: "gears" });
  T(s, "Design choices", { x: 8.0, y: 1.85, w: 4.4, h: 0.5, fontSize: 20, bold: true, color: C.text2, fontFace: "Cambria", valign: "middle", objectName: "design-head" });
  T(s, [
    { text: "Exact statevector kernel: identical to Qiskit's FidelityQuantumKernel (verified to 1e-12), but fast enough for all 1513 molecules", options: { bullet: true, breakLine: true } },
    { text: "PCA and scaler fitted on training data only", options: { bullet: true, breakLine: true } },
    { text: "Kernel scale and C chosen by inner cross-validation", options: { bullet: true, breakLine: true } },
    { text: "21 automated tests", options: { bullet: true } },
  ], { x: 7.3, y: 2.55, w: 5.1, h: 2.6, fontSize: 14, color: C.text1, valign: "top", paraSpaceAfter: 6, objectName: "design-bullets" });
  s.addNotes("Explain encode, compare, classify. The simulation is exact and noiseless, so there is no speed-up claim.");

  // ================= 5. headline =================
  pres.addSection({ title: "Results" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("Quantum matches classical, no advantage", { placeholder: "title" });
  const m = N.main; // order: RF FP, SVM, RF PCA, QSVM
  const labels = ["Random Forest (full fingerprint)", "Classical SVM (8 features)", "Random Forest (8 features)", "Quantum kernel SVM (8 qubits)"];
  s.addChart(pres.charts.BAR, [{ name: "ROC-AUC", labels, values: m.map((r) => num(r[1])) }], {
    x: 0.7, y: 1.5, w: 7.6, h: 4.9, barDir: "bar", chartColors: [HEX.classical, HEX.classical, HEX.classical, HEX.quantum], barGapWidthPct: 45,
    showValue: true, dataLabelFormatCode: "0.000", dataLabelPosition: "outEnd", showLegend: false, showTitle: true, title: "ROC-AUC, random split (mean of 3 seeds)",
    valAxisMinVal: 0.5, valAxisMaxVal: 1.0, valAxisMajorUnit: 0.1, catAxisOrientation: "maxMin", ...chartBase(),
    objectName: "auc-chart",
  });
  await stat(s, 8.8, 1.6, 3.8, "0.873 vs 0.879", "quantum vs classical SVM on the same 8 features: gap smaller than one std", { bigSize: 30, h: 1.7 });
  await stat(s, 8.8, 3.5, 3.8, "2.07", "enrichment at 10%, close to the maximum possible 2.2", { h: 1.5 });
  T(s, "Full-fingerprint Random Forest wins (0.916): the 2048 → 8 compression, not the kernel, is the bottleneck.", { x: 8.8, y: 5.2, w: 3.8, h: 1.3, fontSize: 14, bold: true, color: C.text2, valign: "top", objectName: "takeaway" });
  s.addNotes("Main result. Quantum-kernel SVM AUC 0.873 +/- 0.011 versus 0.879 +/- 0.007 for the classical SVM. No quantum advantage; 8 PCA components keep only about 36% of the variance.");

  // ================= 6. ablations =================
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("Entanglement and qubits: little effect", { placeholder: "title" });
  s.addChart(pres.charts.LINE, [
    { name: "Quantum kernel SVM", labels: N.qubits.map((r) => r[0] + " qubits"), values: N.qubits.map((r) => num(r[1])) },
    { name: "Classical RBF SVM", labels: N.qubits.map((r) => r[0] + " qubits"), values: N.qubits.map((r) => num(r[2])) },
  ], {
    x: 0.7, y: 1.5, w: 6.0, h: 4.3, chartColors: [HEX.quantum, HEX.classical], lineSize: 3, lineDataSymbolSize: 9, showLegend: true, legendPos: "b",
    showTitle: true, title: "ROC-AUC vs number of qubits", valAxisMinVal: 0.82, valAxisMaxVal: 0.9, valAxisMajorUnit: 0.02, valAxisLabelFormatCode: "0.00", ...chartBase(), objectName: "qubit-chart",
  });
  const fmN = N.fm.map((r) => ({ l: r[0].replace(" (reps ", " r").replace(")", ""), v: num(r[1]) }));
  s.addChart(pres.charts.BAR, [{ name: "ROC-AUC", labels: fmN.map((r) => r.l), values: fmN.map((r) => r.v) }], {
    x: 6.9, y: 1.5, w: 5.8, h: 4.3, barDir: "bar", chartColors: [HEX.quantum], barGapWidthPct: 45, showValue: true, dataLabelFormatCode: "0.000", dataLabelPosition: "outEnd",
    showLegend: false, showTitle: true, title: "Feature maps (8 qubits)", valAxisMinVal: 0.8, valAxisMaxVal: 0.9, valAxisMajorUnit: 0.02, valAxisLabelFormatCode: "0.00", catAxisOrientation: "maxMin", ...chartBase(), objectName: "fm-chart",
  });
  card(s, 0.7, 6.0, 12.0, 0.85, "takeaway-card");
  T(s, "The un-entangled Z map (0.877) scores the same as entangling ZZ maps; accuracy plateaus at 8 qubits. Entanglement is not what drives performance here.", { x: 0.95, y: 6.05, w: 11.5, h: 0.75, fontSize: 15, bold: true, color: C.text2, valign: "middle", objectName: "takeaway" });
  s.addNotes("All five encodings are within 0.012 AUC, inside seed noise. The classical SVM is at least as good at every qubit count.");

  // ================= 7. scaffold =================
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("The hard test: unseen scaffolds", { placeholder: "title" });
  const sc = N.scaffold; // RF FP, RF PCA, SVM, QSVM
  const pick = [sc[2], sc[3], sc[0]];
  const scl = ["Classical SVM", "Quantum kernel SVM", "Random Forest (full FP)"];
  s.addChart(pres.charts.BAR, [
    { name: "Random split", labels: scl, values: pick.map((r) => parseFloat(r[1])) },
    { name: "Scaffold split", labels: scl, values: pick.map((r) => parseFloat(r[2])) },
  ], {
    x: 0.7, y: 1.5, w: 7.6, h: 4.9, barDir: "col", barGrouping: "clustered", chartColors: ["B8A1E3", "4B2A91"], barGapWidthPct: 60, showValue: true, dataLabelFormatCode: "0.00", dataLabelPosition: "outEnd",
    showLegend: true, legendPos: "b", showTitle: true, title: "ROC-AUC: random vs scaffold split", valAxisMinVal: 0.5, valAxisMaxVal: 1.0, valAxisMajorUnit: 0.1, valAxisLabelFormatCode: "0.0", ...chartBase(), objectName: "scaffold-chart",
  });
  await stat(s, 8.8, 1.6, 3.8, "-0.13 to -0.21", "AUC drop for every model when test scaffolds are new", { bigSize: 30, h: 1.7 });
  await stat(s, 8.8, 3.5, 3.8, "0.677 vs 0.667", "quantum vs classical SVM, scaffold split", { bigSize: 30, h: 1.5 });
  T(s, "One deterministic split, so no error bars: small differences should not be over-interpreted.", { x: 8.8, y: 5.2, w: 3.8, h: 1.2, fontSize: 14, color: C.text1, valign: "top", objectName: "caveat" });
  s.addNotes("Generalisation to new chemotypes is the realistic screening scenario and it is much harder for all models.");

  // ================= 8. VQC =================
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("VQC: slower and less accurate", { placeholder: "title" });
  const vq = N.vqc; // sorted: SVM, QSVM, VQC
  s.addChart(pres.charts.BAR, [{ name: "ROC-AUC", labels: ["Classical SVM", "Quantum kernel SVM", "VQC"], values: vq.map((r) => num(r[1])) }], {
    x: 0.7, y: 1.5, w: 7.2, h: 4.9, barDir: "col", chartColors: [HEX.classical, HEX.quantum, "B8A1E3"], barGapWidthPct: 60, showValue: true, dataLabelFormatCode: "0.000", dataLabelPosition: "outEnd",
    showLegend: false, showTitle: true, title: "ROC-AUC with 200 training molecules, 6 qubits", valAxisMinVal: 0.4, valAxisMaxVal: 1.0, valAxisMajorUnit: 0.1, valAxisLabelFormatCode: "0.0", ...chartBase(), objectName: "vqc-chart",
  });
  await stat(s, 8.5, 1.6, 4.1, "0.625", "VQC AUC (±0.056) vs 0.811 for the kernel SVM", { h: 1.5 });
  await stat(s, 8.5, 3.3, 4.1, "119 s", "VQC fit time vs 1.3 s for the kernel SVM (about 90x)", { h: 1.5 });
  T(s, "ZZ map + RealAmplitudes ansatz, COBYLA, 120 iterations, 3 seeds. Not tuned and probably under-trained: it shows the practical cost of variational training.", { x: 8.5, y: 5.05, w: 4.1, h: 1.5, fontSize: 14, color: C.text1, valign: "top", objectName: "vqc-note" });
  s.addNotes("Every optimiser step evaluates all training circuits, so the VQC is trained on a small balanced subset and compared on that same subset.");

  // ================= 9. screening =================
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("Screening a hold-out library", { placeholder: "title" });
  const t = N.figs.top; const tw = 6.6, th = tw * t.h / t.w;
  card(s, 0.7, 1.55, 7.0, th + 0.4, "fig-card");
  s.addImage({ path: `${ROOT}/${t.path}`, x: 0.9, y: 1.75, w: tw, h: th, objectName: "top-candidates", altText: "Top 15 ranked candidates" });
  T(s, `A model trained on 80% of BACE ranks ${S.library_size} unseen molecules (${(S.base_hit_rate * 100).toFixed(0)}% truly active). Final score = 0.7 P(active) + 0.3 QED, minus a Lipinski penalty.`, { x: 0.7, y: 1.55 + th + 0.6, w: 7.0, h: 1.0, fontSize: 14, color: C.text1, valign: "top", objectName: "screen-note" });
  await stat(s, 8.1, 1.6, 4.5, `${Math.round(S.precision_at_k_quantum_score * S.top_k)} / ${S.top_k}`, "top-ranked quantum picks that are truly active (classical: " + Math.round(S.precision_at_k_classical * S.top_k) + " / " + S.top_k + ")", { h: 1.6 });
  await stat(s, 8.1, 3.4, 4.5, S.ef10_quantum.toFixed(2), `EF at 10% (max ${(1 / S.base_hit_rate).toFixed(2)}); classical ${S.ef10_classical.toFixed(2)}`, { h: 1.5 });
  T(s, "Single split: the 3-molecule gap to the classical score is suggestive, not significant. The 3-seed EF (2.07 vs 1.98) is the safer comparison.", { x: 8.1, y: 5.1, w: 4.5, h: 1.4, fontSize: 14, bold: true, color: C.text2, valign: "top", objectName: "caution" });
  s.addNotes("Ranked output is saved to results/ranked_candidates.csv and is browsable in the Streamlit app.");

  // ================= 9b. QAOA batch selection =================
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("Choosing a diverse batch with QAOA", { placeholder: "title" });
  const mf = N.figs.mol2; const mw = 7.2, mh = mw * mf.h / mf.w;
  card(s, 0.7, 1.55, 7.6, mh + 0.4, "fig-card");
  s.addImage({ path: `${ROOT}/${mf.path}`, x: 0.9, y: 1.75, w: mw, h: mh, objectName: "selected-molecules", altText: "Molecules selected by score-only top-K and by QAOA" });
  T(s, "Pick 4 of the 12 best-ranked candidates. Maximise  J(x) = Σ sᵢxᵢ − λ Σ Sᵢⱼ xᵢxⱼ  (score minus Tanimoto redundancy), mapped to an Ising Hamiltonian and solved with QAOA. The exact diversity-aware optimum scores J = 2.88 too.", { x: 0.7, y: 1.55 + mh + 0.6, w: 7.6, h: 1.4, fontSize: 14, color: C.text1, valign: "top", objectName: "qaoa-note" });
  await stat(s, 8.7, 1.6, 3.9, "1.96 → 2.88", "objective: score-only top-K vs diversity-aware (exact and QAOA)", { bigSize: 34, h: 1.6 });
  await stat(s, 8.7, 3.4, 3.9, "0.46 → 0.14", "mean pairwise similarity of the chosen batch", { bigSize: 34, h: 1.5 });
  T(s, "Top-K picked three near-duplicate analogues. No experimental affinity is used in the score, to avoid leaking the answer.", { x: 8.7, y: 5.1, w: 3.9, h: 1.5, fontSize: 14, bold: true, color: C.text2, valign: "top", objectName: "qaoa-caution" });
  s.addNotes("Without the pairwise term this problem is solved exactly by sorting, so QAOA would be pointless. With the diversity term, score-only top-K is not optimal. The Ising mapping is verified exactly in the tests.");

  // ================= 9c. QAOA vs random =================
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("QAOA matches random search", { placeholder: "title" });
  const A = N.qaoa.A; const nl = ["N=8", "N=10", "N=12", "N=14"];
  const rowv = (i) => A[i].slice(1).map(parseFloat);
  s.addChart(pres.charts.LINE, [
    { name: "Top-K by score", labels: nl, values: rowv(0) },
    { name: "Random feasible subset", labels: nl, values: rowv(1) },
    { name: "Diversity-aware greedy", labels: nl, values: rowv(2) },
    { name: "QAOA p=3, best of 1024 shots", labels: nl, values: rowv(5) },
    { name: "Random search, 1024 shots", labels: nl, values: rowv(6) },
  ], {
    x: 0.7, y: 1.5, w: 7.6, h: 4.9, chartColors: ["E76F51", "9CA3AF", HEX.classical, HEX.quantum, "4B2A91"], lineSize: 3, lineDataSymbolSize: 8,
    showLegend: true, legendPos: "b", showTitle: true, title: "Objective / exact optimum, mean of 8 shortlists per size",
    valAxisMinVal: 0.7, valAxisMaxVal: 1.02, valAxisMajorUnit: 0.1, valAxisLabelFormatCode: "0.0", ...chartBase(), objectName: "qaoa-chart",
  });
  await stat(s, 8.8, 1.6, 3.8, "1.00x", "QAOA output quality vs random feasible subsets (1 = no better than random)", { h: 1.7 });
  await stat(s, 8.8, 3.5, 3.8, "0.0003 vs 0.001", "P(optimal) at N=14: QAOA vs uniform sampling of feasible subsets", { bigSize: 26, h: 1.5 });
  T(s, "Best-of-shots reaches 99-100% of the optimum, but only because the spaces are tiny (56 to 1001 feasible subsets). No quantum advantage.", { x: 8.8, y: 5.2, w: 3.8, h: 1.4, fontSize: 14, bold: true, color: C.text2, valign: "top", objectName: "qaoa-takeaway" });
  s.addNotes("Be candid: QAOA with p up to 3 and a small optimiser budget does not beat random sampling of feasible subsets. Only about a third of its probability mass is feasible because the budget is a penalty. A constraint-preserving XY mixer and warm starts are the next step.");

  // ================= 10. VQE =================
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("VQE: exact energies for H2 and LiH", { placeholder: "title" });
  const v = N.figs.vqe; const vw = 7.6, vh = vw * v.h / v.w;
  card(s, 0.7, 1.6, 7.8, vh + 0.4, "fig-card");
  s.addImage({ path: `${ROOT}/${v.path}`, x: 0.8, y: 1.8, w: vw, h: vh, objectName: "vqe-curves", altText: "VQE potential energy curves for H2 and LiH" });
  T(s, "UCCSD ansatz, STO-3G basis, parity mapping: H2 on 2 qubits and LiH on 4 qubits (active space).", { x: 0.7, y: 1.6 + vh + 0.65, w: 7.8, h: 0.8, fontSize: 14, color: C.text1, valign: "top", objectName: "vqe-note" });
  await stat(s, 8.9, 1.6, 3.7, "< 0.001 mHa", "max error vs exact at every bond length (chemical accuracy: 1.6 mHa)", { bigSize: 30, h: 1.7 });
  await stat(s, 8.9, 3.5, 3.7, "-1.137 Ha", "H2 at 0.74 Å, matching the literature STO-3G value", { bigSize: 30, h: 1.5 });
  T(s, "Noiseless simulation with exact expectation values, so near-zero error is expected. Real hardware adds shot noise and gate errors.", { x: 8.9, y: 5.2, w: 3.7, h: 1.3, fontSize: 14, color: C.text1, valign: "top", objectName: "vqe-caveat" });
  s.addNotes("This is the quantum-chemistry route: molecular energies underlie binding. It is a demonstration and is not numerically coupled to the classifier.");

  // ================= 11. close =================
  pres.addSection({ title: "Wrap-up" });
  s = pres.addSlide({ masterName: "CLOSE_DARK", sectionTitle: "Wrap-up" });
  s.addText("Takeaways and next steps", { placeholder: "title" });
  T(s, "What we found", { x: 0.7, y: 1.6, w: 5.8, h: 0.5, fontSize: 22, bold: true, color: C.accent4, fontFace: "Cambria", objectName: "left-head" });
  T(s, [
    { text: "Working, tested, reproducible hybrid pipeline in Qiskit", options: { bullet: true, breakLine: true } },
    { text: "Quantum kernel SVM: AUC 0.87, EF 2.07 of 2.2, equal to a classical SVM", options: { bullet: true, breakLine: true } },
    { text: "No quantum advantage: compression to 8 qubits is the bottleneck", options: { bullet: true, breakLine: true } },
    { text: "QAOA batch selection near-optimal, but equal to random search", options: { bullet: true, breakLine: true } },
    { text: "VQC far slower and weaker; VQE reproduces exact energies", options: { bullet: true } },
  ], { x: 0.7, y: 2.25, w: 5.8, h: 3.9, fontSize: 16, color: C.background1, valign: "top", paraSpaceAfter: 8, objectName: "findings" });
  T(s, "Next steps", { x: 7.0, y: 1.6, w: 5.6, h: 0.5, fontSize: 22, bold: true, color: C.accent4, fontFace: "Cambria", objectName: "right-head" });
  T(s, [
    { text: "Run on IBM Quantum hardware with error mitigation", options: { bullet: true, breakLine: true } },
    { text: "Learned embeddings instead of PCA; trainable feature maps", options: { bullet: true, breakLine: true } },
    { text: "Add docking and VQE fragment energies to re-rank candidates", options: { bullet: true, breakLine: true } },
    { text: "XY-mixer / warm-start QAOA on larger shortlists", options: { bullet: true, breakLine: true } },
    { text: "More targets and seeds, with significance tests", options: { bullet: true } },
  ], { x: 7.0, y: 2.25, w: 5.6, h: 3.9, fontSize: 16, color: C.background1, valign: "top", paraSpaceAfter: 8, objectName: "next-steps" });
  T(s, "Thank you  |  Questions?", { x: 0.7, y: 6.3, w: 11.9, h: 0.6, fontSize: 24, bold: true, color: C.background1, fontFace: "Cambria", objectName: "closing" });
  s.addNotes("Be upfront that the circuits are simulated and that no quantum advantage was found. The value is the pipeline, the fair benchmark and the analysis.");

  await pres.writeFile({ fileName: __dirname + "/QuantumScreen_Presentation.pptx" });
  await applyTheme(__dirname + "/QuantumScreen_Presentation.pptx", THEME);
  console.log("deck written");
})().catch((e) => { console.error(e); process.exit(1); });
