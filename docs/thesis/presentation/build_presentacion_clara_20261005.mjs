import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const root = "C:/Users/Acer/Documents/ChatGPT/THESIS";
const workDir = path.join(root, ".build", "presentation_clara_20261005");
const skillDir = "C:/Users/Acer/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations";
const outputDir = path.join(root, "vm_repo", "docs", "thesis", "presentation");
const finalPath = path.join(outputDir, "PRESENTACION_DATA_MOVEMENT_CLARA_20261005.pptx");
const draftPath = path.join(workDir, "candidate.pptx");
const runtimeHelpers = await import(pathToFileURL(path.join(skillDir, "container_tools", "runtime_helpers.mjs")).href);
const { Presentation, PresentationFile } = await runtimeHelpers.importRuntimeModule("@oai/artifact-tool");
const { resolvePresentationFont, applyPresentationChartFont } = await import(
  pathToFileURL(path.join(skillDir, "container_tools", "artifact_tool_utils.mjs")).href,
);

await fs.mkdir(workDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });
const font = resolvePresentationFont();

const C = {
  bg: "#F8F8F5",
  ink: "#172A33",
  body: "#293A42",
  muted: "#65757C",
  rule: "#CBD2D4",
  teal: "#087E78",
  tealLight: "#E7F2F0",
  slate: "#4B626D",
  slateLight: "#EFF2F2",
  white: "#FFFFFF",
};

const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });

function addText(slide, name, x, y, w, h, value, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position: { left: x, top: y, width: w, height: h },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = value;
  shape.text.style = {
    typeface: opts.typeface || font,
    fontSize: opts.size || 24,
    bold: Boolean(opts.bold),
    italic: Boolean(opts.italic),
    color: opts.color || C.body,
    alignment: opts.align || "left",
    verticalAlignment: opts.valign || "top",
    autoFit: "shrinkText",
    wrap: "square",
    lineSpacing: opts.lineSpacing || 1.0,
    insets: { top: 0, right: 0, bottom: 0, left: 0 },
  };
  return shape;
}

function addRect(slide, name, x, y, w, h, opts = {}) {
  return slide.shapes.add({
    geometry: opts.geometry || "rect",
    name,
    position: { left: x, top: y, width: w, height: h },
    fill: opts.fill || C.white,
    line: { style: opts.dash || "solid", fill: opts.line || C.rule, width: opts.width || 1.5 },
  });
}

function addNode(slide, name, x, y, w, h, label, opts = {}) {
  const shape = addRect(slide, name, x, y, w, h, {
    geometry: opts.geometry || "rect",
    fill: opts.fill || C.white,
    line: opts.line || C.slate,
    width: opts.width || 1.6,
  });
  shape.text = label;
  shape.text.style = {
    typeface: font,
    fontSize: opts.size || 21,
    bold: Boolean(opts.bold),
    color: opts.color || C.ink,
    alignment: "center",
    verticalAlignment: "middle",
    autoFit: "shrinkText",
    wrap: "square",
    insets: { top: 4, right: 5, bottom: 4, left: 5 },
  };
  return shape;
}

function arrow(slide, from, to, opts = {}) {
  return slide.shapes.connect(from, to, {
    kind: opts.kind || "straight",
    fromSide: opts.fromSide || "right",
    toSide: opts.toSide || "left",
    line: { style: opts.dash || "solid", fill: opts.color || C.teal, width: opts.width || 2.2 },
    tail: { type: "triangle", width: "med", length: "med" },
  });
}

function rule(slide, name, x, y, w, color = C.rule, height = 1) {
  return slide.shapes.add({
    geometry: "rect",
    name,
    position: { left: x, top: y, width: w, height },
    fill: color,
    line: { style: "solid", fill: color, width: 0 },
  });
}

function header(slide, title, number) {
  slide.background.fill = C.bg;
  addText(slide, "slide-title-" + number, 72, 42, 1136, 60, title, { size: 42, bold: true, color: C.ink });
  rule(slide, "title-rule-" + number, 72, 116, 1136, C.rule, 1.5);
  addText(slide, "slide-number-" + number, 1138, 672, 70, 22, String(number).padStart(2, "0"), { size: 15, color: C.muted, align: "right" });
}

function notes(slide, text) {
  slide.speakerNotes.textFrame.setText(text);
}

// 1. Title and research question.
{
  const s = deck.slides.add();
  s.background.fill = C.bg;
  rule(s, "cover-accent", 72, 114, 92, C.teal, 5);
  addText(s, "cover-title", 72, 162, 1050, 132, "Movimiento de datos en\nworkflows científicos", { size: 58, bold: true, color: C.ink, lineSpacing: 0.95 });
  addText(s, "cover-subtitle", 74, 334, 1060, 112,
    "Dado un workflow y el placement real de sus tareas, ¿cuánto movimiento de datos exigen sus dependencias entre ubicaciones y cuánto movimiento produce realmente el mecanismo de ejecución?",
    { size: 30, color: C.body, lineSpacing: 1.05 });
  addText(s, "cover-author", 74, 568, 850, 40, "Luis Sebastián Contreras Díaz  ·  Octubre de 2026", { size: 20, color: C.muted });
  notes(s, "Esta tesis pregunta cuánto movimiento de archivos requiere la estructura del workflow en las ubicaciones donde realmente se ejecutaron las tareas, y cuánto payload científico podemos confirmar a partir de las listas de transferencia y el historial de HTCondor. La palabra confirmado importa: no contamos paquetes de red. El objetivo de esta exposición es mostrar la idea, el cálculo y la evidencia de forma directa.");
}

// 2. Problem.
{
  const s = deck.slides.add();
  header(s, "El dato también debe llegar a la tarea", 2);
  addText(s, "problem-intro", 72, 142, 1090, 66,
    "En workflows de big data, mover archivos entre tareas y máquinas puede convertirse en un cuello de botella.",
    { size: 28, color: C.body });
  const w1 = addRect(s, "problem-worker-1", 92, 256, 410, 238, { fill: C.slateLight, line: C.slate, width: 1.6 });
  const w2 = addRect(s, "problem-worker-2", 778, 256, 410, 238, { fill: C.slateLight, line: C.slate, width: 1.6 });
  addText(s, "problem-worker-1-title", 116, 272, 340, 34, "WORKER 1", { size: 20, bold: true, color: C.slate });
  addText(s, "problem-worker-2-title", 802, 272, 340, 34, "WORKER 2", { size: 20, bold: true, color: C.slate });
  const t1 = addNode(s, "problem-task-1", 148, 342, 170, 76, "Tarea T1", { size: 23, bold: true, line: C.slate });
  const f1 = addNode(s, "problem-file-1", 340, 358, 116, 48, "f1 · 10 MiB", { size: 18, bold: true, geometry: "ellipse", line: C.teal, fill: C.tealLight });
  const t2 = addNode(s, "problem-task-2", 902, 342, 170, 76, "Tarea T2", { size: 23, bold: true, line: C.slate });
  arrow(s, t1, f1, { color: C.teal, width: 3 });
  arrow(s, f1, t2, { color: C.teal, width: 3 });
  addText(s, "problem-arrow-label", 526, 349, 250, 34, "archivo requerido", { size: 20, bold: true, color: C.teal, align: "center" });
  addText(s, "problem-arrow-caveat", 92, 503, 1096, 24,
    "La flecha muestra una dependencia de archivo; no una ruta física de red.",
    { size: 17, color: C.muted, align: "center" });
  addText(s, "problem-summary", 92, 535, 1096, 68,
    "La pregunta práctica: ¿cuánto movimiento exige este placement y cuánto confirma la ejecución?",
    { size: 26, bold: true, color: C.ink, align: "center", valign: "middle" });
  addText(s, "problem-citation", 92, 622, 1096, 24, "Contexto respaldado por Pietri y Sakellariou (2018) y Tang et al. (2024).", { size: 16, color: C.muted, align: "center" });
  notes(s, "Las dependencias entre tareas también son dependencias entre archivos. Si un archivo se produce en un worker y otra tarea lo consume en otro, el archivo tiene que estar disponible en la ubicación consumidora. La literatura de workflows intensivos en datos señala que la comunicación y el acceso a datos pueden limitar la ejecución. Eso motiva medir el movimiento, pero no significa que esta tesis haya medido tiempo perdido ni un cuello de botella físico en la red. La flecha representa una necesidad de ubicación, no una ruta de paquetes.\n\nFuentes: Pietri, I., y Sakellariou, R. (2018), https://doi.org/10.1145/3221269.3221298 ; Tang, M. et al. (2024), https://doi.org/10.1109/CLUSTER59578.2024.00038 .");
}

// 3. Literature, simplified.
{
  const s = deck.slides.add();
  header(s, "Qué encontró la investigación previa", 3);
  addText(s, "literature-lead", 72, 137, 1136, 42, "Cada línea ayuda a entender una parte del problema.", { size: 25, color: C.muted });
  const rows = [
    ["Bharathi et al. (2008)", "Describen patrones de workflows científicos. Nos orientan a validar más de una forma de dependencia."],
    ["Pietri y Sakellariou (2018)", "Incluyen costo de comunicación al ubicar tareas. Muestran por qué importa el placement."],
    ["Lee et al. (2023) · DataLife", "Siguen el ciclo de vida de datos entre tareas. Apoyan mirar archivos y consumidores, además del grafo."],
    ["Tang et al. (2024) · DaYu", "Relacionan datasets con operaciones I/O. Sus conclusiones requieren evidencia de I/O más detallada."],
    ["Devarajan et al. (2024) · DFTracer", "Capturan trazas de varias capas. Es más instrumentación que el análisis post-mortem de esta tesis."],
    ["Aurelio Vivas Meza (2026)", "Estudia scheduling que considera movimiento y NUMA. Su foco de localidad interna es distinto al staging entre workers."],
  ];
  let y = 190;
  for (let i = 0; i < rows.length; i++) {
    addText(s, "literature-author-" + i, 82, y, 300, 56, rows[i][0], { size: 20, bold: true, color: C.ink, valign: "middle" });
    addText(s, "literature-finding-" + i, 410, y, 780, 56, rows[i][1], { size: 21, color: C.body, valign: "middle" });
    if (i < rows.length - 1) rule(s, "literature-rule-" + i, 82, y + 65, 1106, C.rule, 1);
    y += 75;
  }
  addText(s, "literature-takeaway", 82, 650, 1040, 24, "La métrica de esta tesis complementa estos trabajos; responde una pregunta de medición diferente.", { size: 18, bold: true, color: C.teal });
  notes(s, "Bharathi y coautores describen estructuras recurrentes y una manera de generar workflows parametrizables. Por eso nuestra validación cubre proceso, pipeline, distribución, agregación y redistribución. Pietri y Sakellariou incorporan comunicación al proceso de scheduling: su interés es decidir una asignación que reduzca costos. Lee y coautores proponen DataLife para razonar sobre el ciclo de vida de datos y coordinar tareas. Tang y coautores presentan DaYu para conectar semántica de datasets con operaciones de I/O de formatos como HDF5. Devarajan y coautores presentan DFTracer para registrar eventos de flujo de datos de distintas capas con contexto de workflow. Aurelio Antonio Vivas Meza estudia estrategias de scheduling conscientes de NUMA; esto ayuda a explicar la importancia de localidad y arquitectura, aunque la localidad NUMA dentro de un nodo no es la misma capa que mover archivos entre workers.\n\nLa tesis no afirma que esos autores no estudiaran movimiento de datos. Su aporte inicial es integrar, por run, una referencia lógica condicionada al placement con movimientos científicos declarados y evidencia de HTCondor a nivel de job. La afirmación de que ninguna métrica existente ofrece la misma combinación debe limitarse a las fuentes consultadas, no presentarse como novedad universal.\n\nFuentes: Bharathi et al. (2008), https://doi.org/10.1109/WORKS.2008.4723958 ; Pietri y Sakellariou (2018), https://doi.org/10.1145/3221269.3221298 ; Lee et al. (2023), https://doi.org/10.1145/3581784.3607104 ; Tang et al. (2024), https://doi.org/10.1109/CLUSTER59578.2024.00038 ; Devarajan et al. (2024), https://doi.org/10.1109/SC41406.2024.00023 ; Vivas Meza (2026), disertación doctoral, Universidad de los Andes.");
}

// 4. Research question and contribution.
{
  const s = deck.slides.add();
  header(s, "La pregunta de esta tesis", 4);
  addText(s, "research-question", 116, 190, 1048, 190,
    "Dado un workflow y el placement real de sus tareas, ¿cuánto movimiento de datos exigen sus dependencias entre ubicaciones y cuánto movimiento produce realmente el mecanismo de ejecución?",
    { size: 38, bold: true, color: C.ink, align: "center", valign: "middle", lineSpacing: 1.02 });
  rule(s, "rq-accent", 530, 413, 220, C.teal, 4);
  addText(s, "research-contribution", 155, 456, 970, 86,
    "La respuesta combina el workflow, el worker donde corrió cada tarea, los tamaños de archivo y la evidencia de transferencia de cada job.",
    { size: 27, color: C.body, align: "center", valign: "middle" });
  addText(s, "research-boundary", 180, 570, 920, 48,
    "‘Lo que produce’ se estima con manifiestos y evidencia HTCondor por job; no con paquetes de red.",
    { size: 21, color: C.muted, align: "center" });
  notes(s, "Esta es la pregunta central del proyecto. La formulación es útil porque indica los datos que hacen falta: el workflow, su placement realmente observado y la evidencia de transferencias. Ajusto oralmente el verbo 'produce realmente': en nuestro caso significa volumen de archivos declarado y confirmado a nivel de trabajo, no bytes físicos observados en un cable. Analyzer trabaja después de la ejecución; no decide el placement.");
}

// 5. Three levels of the measurement boundary.
{
  const s = deck.slides.add();
  header(s, "Tres cantidades, tres tipos de evidencia", 5);
  const xs = [82, 466, 850];
  const titles = ["M_req · requerido", "M_rec · declarado", "M_obs · confirmado"];
  const body = [
    "Workflow + tamaños + ubicación real de las tareas.\n\nCuenta ubicaciones nuevas distintas donde cada archivo se necesita.",
    "Manifiestos efectivos de cada job.\n\nSuma las ocurrencias científicas que Pegasus/HTCondor declaran transferir.",
    "Manifiesto reconciliado con historial HTCondor.\n\nSuma las ocurrencias científicas confirmadas, solo con cobertura completa.",
  ];
  for (let i = 0; i < 3; i++) {
    addText(s, "boundary-title-" + i, xs[i], 178, 330, 48, titles[i], { size: 27, bold: true, color: i === 2 ? C.teal : C.ink });
    rule(s, "boundary-rule-" + i, xs[i], 236, 330, i === 2 ? C.teal : C.slate, 3);
    addText(s, "boundary-body-" + i, xs[i], 262, 330, 190, body[i], { size: 23, color: C.body, lineSpacing: 1.06 });
  }
  addText(s, "boundary-coverage", 82, 490, 1100, 48,
    "Coverage = ocurrencias confirmadas / ocurrencias declaradas. Si Coverage < 1, M_obs y DME quedan indeterminadas.",
    { size: 24, bold: true, color: C.ink, align: "center", valign: "middle" });
  addRect(s, "boundary-note-bg", 82, 565, 1106, 74, { fill: C.tealLight, line: C.teal, width: 1 });
  addText(s, "boundary-note", 104, 577, 1062, 50,
    "Comparten el payload científico y el run, pero no la misma regla de conteo: M_req cuenta destinos distintos; M_obs cuenta ocurrencias confirmadas por job. Ninguna mide paquetes de red.",
    { size: 20, color: C.ink, align: "center", valign: "middle" });
  notes(s, "Esta separación es la parte más importante para no sobreinterpretar. M_req se deriva de dependencias, tamaños y ubicaciones. M_rec sale de listas efectivas de archivos de entrada y salida de los jobs. M_obs no toma BytesSent o BytesRecvd como si fueran bytes científicos por archivo. La implementación usa estadísticas de transferencia por dirección del historial de HTCondor, como método, cantidad de archivos y bytes de la última ejecución, junto con estado, worker y número de intentos. La reconciliación confirma las ocurrencias declaradas a nivel de job. Luego M_obs suma tamaños de esas ocurrencias científicas del manifiesto. Coverage es por ocurrencia declarada. En las 31 ejecuciones experimentales Coverage fue 1; eso no equivale a una captura packet-level ni prueba la ruta física.");
}

// 6. Simple mathematics.
{
  const s = deck.slides.add();
  header(s, "La matemática en palabras sencillas", 6);
  addText(s, "formula-req-label", 90, 148, 1060, 37, "1. Movimiento lógico requerido", { size: 24, bold: true, color: C.slate });
  addText(s, "formula-req", 92, 194, 1096, 83,
    "M_req = Σ por archivo [ tamaño del archivo × número de ubicaciones nuevas requeridas ]",
    { size: 31, bold: true, color: C.ink, typeface: "Cambria Math", align: "center", valign: "middle" });
  addText(s, "formula-req-explain", 118, 280, 1040, 48,
    "Si varios consumidores están en el mismo worker, esa ubicación se cuenta una sola vez.",
    { size: 21, color: C.body, align: "center" });
  rule(s, "formula-rule", 92, 351, 1096, C.rule, 1.4);
  addText(s, "formula-coverage-label", 90, 376, 1060, 37, "2. Movimiento confirmado y razón", { size: 24, bold: true, color: C.slate });
  addText(s, "formula-coverage", 92, 411, 1096, 46,
    "Coverage = |C_sci| / |D_sci|",
    { size: 29, bold: true, color: C.ink, typeface: "Cambria Math", align: "center", valign: "middle" });
  addText(s, "formula-coverage-defs", 92, 457, 1096, 32,
    "D_sci: ocurrencias declaradas · C_sci: ocurrencias confirmadas por HTCondor a nivel de job",
    { size: 18, color: C.body, align: "center", valign: "middle" });
  addText(s, "formula-obs", 92, 496, 1096, 42,
    "M_obs = tamaños de C_sci, solo si Coverage = 1",
    { size: 23, bold: true, color: C.ink, typeface: "Cambria Math", align: "center", valign: "middle" });
  addText(s, "formula-dme", 92, 547, 1096, 50,
    "DME = M_req / M_obs",
    { size: 38, bold: true, color: C.teal, typeface: "Cambria Math", align: "center", valign: "middle" });
  addText(s, "formula-dme-note", 92, 612, 1096, 30,
    "La DME es una razón de volúmenes, no una medida de rapidez o rendimiento.",
    { size: 19, color: C.muted, align: "center" });
  notes(s, "La fórmula de RequiredMovement se puede leer como: tome el tamaño de cada archivo y multiplíquelo por el número de ubicaciones distintas, además de su origen, donde una tarea lo necesita. Luego sume esos valores. La reutilización local evita contar otra vez el mismo archivo para dos tareas en el mismo worker. Coverage pregunta cuántas ocurrencias declaradas fueron confirmadas. Solo si se confirmaron todas se calcula M_obs. Finalmente, DME divide el movimiento lógico requerido entre el volumen confirmado. Por ejemplo, una DME de un tercio dice que, en ese caso y bajo las definiciones acordadas, el requerimiento lógico representa un tercio del volumen confirmado. No demuestra que los otros dos tercios se pudieran evitar.");
}

// 7. Deployment model and offline analyzer.
{
  const s = deck.slides.add();
  header(s, "Dónde corre cada parte del sistema", 7);
  addText(s, "deploy-phase", 82, 137, 900, 32, "DURANTE EL WORKFLOW", { size: 18, bold: true, color: C.muted });
  const master = addRect(s, "deploy-master", 455, 180, 370, 100, { fill: C.white, line: C.ink, width: 2 });
  const worker1 = addRect(s, "deploy-worker1", 145, 362, 390, 92, { fill: C.white, line: C.slate, width: 1.7 });
  const worker2 = addRect(s, "deploy-worker2", 745, 362, 390, 92, { fill: C.white, line: C.slate, width: 1.7 });
  addText(s, "deploy-master-title", 477, 190, 326, 30, "pegasus-master", { size: 22, bold: true, color: C.ink, align: "center" });
  addText(s, "deploy-master-body", 477, 223, 326, 48,
    "Pegasus\nHTCondor central services\nSchedd · Collector · Negotiator",
    { size: 17, color: C.body, align: "center", valign: "middle" });
  addText(s, "deploy-worker1-title", 169, 371, 342, 27, "pegasus-worker1", { size: 21, bold: true, color: C.ink, align: "center" });
  addText(s, "deploy-worker1-body", 169, 400, 342, 42, "HTCondor slot · ejecuta tareas científicas", { size: 18, color: C.body, align: "center", valign: "middle" });
  addText(s, "deploy-worker2-title", 769, 371, 342, 27, "pegasus-worker2", { size: 21, bold: true, color: C.ink, align: "center" });
  addText(s, "deploy-worker2-body", 769, 400, 342, 42, "HTCondor slot · ejecuta tareas científicas", { size: 18, color: C.body, align: "center", valign: "middle" });
  arrow(s, master, worker1, { color: C.slate, width: 2, fromSide: "bottom", toSide: "top", kind: "elbow" });
  arrow(s, master, worker2, { color: C.slate, width: 2, fromSide: "bottom", toSide: "top", kind: "elbow" });
  addText(s, "deploy-control-label", 82, 154, 1090, 24, "El master coordina; los workers ejecutan los jobs.", { size: 18, color: C.body, align: "center" });
  addText(s, "deploy-config", 300, 463, 680, 24, "Pegasus 5.1.2 · HTCondor 25.12.2 · condorio", { size: 17, color: C.muted, align: "center" });
  rule(s, "deploy-separator", 82, 494, 1100, C.rule, 1.4);
  addText(s, "deploy-post-phase", 82, 508, 900, 27, "DESPUÉS DE LA EJECUCIÓN", { size: 18, bold: true, color: C.muted });
  const artifacts = addNode(s, "deploy-artifacts", 108, 545, 340, 64, "Run Pegasus preservado\n+ HTCondor history", { size: 18, line: C.slate });
  const analyzer = addNode(s, "deploy-analyzer", 523, 545, 264, 64, "Analyzer v1 · post-mortem", { size: 19, bold: true, line: C.teal, fill: C.tealLight });
  const reports = addNode(s, "deploy-reports", 875, 545, 278, 64, "Métricas + diagnósticos\n+ procedencia", { size: 18, line: C.slate });
  arrow(s, artifacts, analyzer, { color: C.teal });
  arrow(s, analyzer, reports, { color: C.teal });
  addText(s, "deploy-path-caveat", 82, 627, 1050, 27, "El diagrama no afirma una ruta física para los archivos.", { size: 17, color: C.muted, align: "center" });
  notes(s, "El pool probado tiene un master y dos workers. Pegasus y los servicios centrales HTCondor se ubican en pegasus-master; los jobs científicos se ejecutan en worker1 o worker2. El historial exportado aporta dónde corrió el job y estadísticas agregadas de transferencia por dirección. El análisis toma los artefactos preservados después del workflow. Analyzer no se inserta en la ruta de ejecución científica. Las flechas sólidas representan control y el flujo de artefactos hacia el análisis. El dibujo no afirma que el payload pase físicamente por el master ni que viaje directamente de worker a worker. Las versiones y el perfil `condorio` corresponden al entorno de validación documentado.");
}

// 8. Workflow patterns.
{
  const s = deck.slides.add();
  header(s, "Cinco formas de organizar las tareas", 8);
  addText(s, "patterns-intro", 82, 136, 1110, 36, "Los patrones cambian quién produce archivos y quién los consume.", { size: 23, color: C.muted });
  const left = 302;
  const rowY = [192, 280, 368, 456, 544];
  const labels = ["Process", "Pipeline", "Distribución", "Agregación", "Redistribución"];
  for (let i = 0; i < labels.length; i++) addText(s, "pattern-label-" + i, 82, rowY[i], 196, 50, labels[i], { size: 22, bold: true, color: C.ink, valign: "middle" });
  // Process: input -> one task -> output.
  let a = addNode(s, "pattern-process-in", left, rowY[0], 116, 48, "Entrada", { size: 18, geometry: "ellipse", line: C.teal, fill: C.tealLight });
  let b = addNode(s, "pattern-process-task", left + 214, rowY[0], 134, 48, "T1", { size: 21, bold: true });
  let c = addNode(s, "pattern-process-out", left + 456, rowY[0], 116, 48, "Salida", { size: 18, geometry: "ellipse", line: C.teal, fill: C.tealLight });
  arrow(s, a, b, { color: C.teal }); arrow(s, b, c, { color: C.teal });
  // Pipeline: serial tasks.
  a = addNode(s, "pattern-pipe-t1", left + 60, rowY[1], 112, 48, "T1", { size: 20, bold: true });
  b = addNode(s, "pattern-pipe-t2", left + 275, rowY[1], 112, 48, "T2", { size: 20, bold: true });
  c = addNode(s, "pattern-pipe-t3", left + 490, rowY[1], 112, 48, "T3", { size: 20, bold: true });
  arrow(s, a, b); arrow(s, b, c);
  // Distribution: one producer to several consumers.
  a = addNode(s, "pattern-dist-t1", left + 24, rowY[2], 110, 48, "T1", { size: 20, bold: true });
  const b1 = addNode(s, "pattern-dist-t2", left + 458, rowY[2] - 6, 110, 42, "T2", { size: 19, bold: true });
  const b2 = addNode(s, "pattern-dist-t3", left + 622, rowY[2] + 30, 110, 42, "T3", { size: 19, bold: true });
  arrow(s, a, b1); arrow(s, a, b2);
  addText(s, "pattern-dist-note", left + 736, rowY[2] + 3, 154, 36, "1 productor\n→ varios", { size: 16, color: C.muted, valign: "middle" });
  // Aggregation: several producers to one consumer.
  const p1 = addNode(s, "pattern-agg-t1", left + 24, rowY[3] - 20, 110, 27, "T1", { size: 17, bold: true });
  const p2 = addNode(s, "pattern-agg-t2", left + 24, rowY[3] + 12, 110, 27, "T2", { size: 17, bold: true });
  const p3 = addNode(s, "pattern-agg-t3", left + 24, rowY[3] + 44, 110, 27, "T3", { size: 17, bold: true });
  const q = addNode(s, "pattern-agg-t4", left + 458, rowY[3] + 6, 122, 48, "T4", { size: 20, bold: true });
  arrow(s, p1, q); arrow(s, p2, q); arrow(s, p3, q);
  addText(s, "pattern-agg-note", left + 620, rowY[3] + 15, 260, 32, "varios → 1", { size: 17, color: C.muted, valign: "middle" });
  // Redistribution: producer group to consumer group.
  const r1 = addNode(s, "pattern-redist-producers", left + 25, rowY[4], 230, 48, "Productores T1, T2", { size: 19, bold: true });
  const r2 = addNode(s, "pattern-redist-consumers", left + 510, rowY[4], 245, 48, "Consumidores T3, T4", { size: 19, bold: true });
  arrow(s, r1, r2, { color: C.teal });
  addText(s, "patterns-note", 82, 634, 1090, 26, "La estructura del workflow se valida por separado del worker que recibe cada tarea.", { size: 17, color: C.muted, align: "center" });
  notes(s, "Bharathi y coautores describen patrones para representar formas distintas de workflows científicos. En nuestro banco controlado, process usa una transformación; pipeline conecta etapas; distribución comparte una salida con varias tareas; agregación combina salidas de varias tareas; y redistribución reparte los datos entre varias tareas posteriores. Estos nombres describen la forma de dependencias del workflow. El placement se define aparte, por ejemplo tareas en un mismo worker o distribuidas entre los dos workers. No todos los patrones se validaron con las mismas variantes de ubicación: la matriz tiene diez condiciones en total.");
}

// 9. Method and validation.
{
  const s = deck.slides.add();
  header(s, "Cómo validamos el cálculo", 9);
  const steps = [
    ["1", "Fijar", "workflow, archivos, tamaños y placement esperado"],
    ["2", "Ejecutar", "Pegasus/HTCondor en el pool de dos workers"],
    ["3", "Reconciliar", "manifiestos con el historial por job"],
    ["4", "Comparar", "salidas del Analyzer con cálculos manuales independientes"],
  ];
  let sx = 82;
  for (let i = 0; i < steps.length; i++) {
    addText(s, "method-step-number-" + i, sx, 174, 54, 58, steps[i][0], { size: 38, bold: true, color: C.teal, align: "center", valign: "middle" });
    addText(s, "method-step-title-" + i, sx + 65, 170, 212, 32, steps[i][1], { size: 22, bold: true, color: C.ink });
    addText(s, "method-step-body-" + i, sx + 65, 210, 212, 84, steps[i][2], { size: 19, color: C.body });
    if (i < steps.length - 1) rule(s, "method-divider-" + i, sx + 292, 174, 1.4, C.rule, 120);
    sx += 286;
  }
  rule(s, "method-stat-rule", 82, 338, 1096, C.rule, 1.3);
  addText(s, "method-stat-main", 82, 369, 1096, 58,
    "5 patrones  ·  10 condiciones  ·  31 workflows independientes  ·  3 o más réplicas por condición",
    { size: 25, bold: true, color: C.ink, align: "center", valign: "middle" });
  addText(s, "method-stat-detail", 125, 446, 1010, 64,
    "Placement, M_req y M_rec coincidieron con los oráculos. Las 31 ejecuciones fueron válidas y tuvieron Coverage = 1.",
    { size: 23, color: C.body, align: "center", valign: "middle" });
  addText(s, "method-caveat", 140, 542, 980, 65,
    "La evidencia valida estas condiciones y este pool. No demuestra el mismo comportamiento en cualquier arquitectura.",
    { size: 20, color: C.muted, align: "center", valign: "middle" });
  notes(s, "Congelamos el DAG y la lista de archivos, calculamos un oráculo independiente y luego verificamos que el placement observado coincidiera con el diseñado. Reconciliamos entradas y salidas declaradas con estadísticas de HTCondor a nivel de job. Corremos cinco patrones en diez condiciones y 31 workflows independientes, con al menos tres en cada condición. Todas las salidas coincidieron con los oráculos en M_req y M_rec, todas tuvieron Coverage igual a uno y el análisis fue determinista. Process, same-w1, 10 MiB cuenta con cuatro réplicas métricas; el desglose de tiempo completo tiene tres porque falta un registro histórico. La validación es acotada al pool de dos workers y a los tamaños/configuraciones ensayados.");
}

// 10. Worked pipeline example.
{
  const s = deck.slides.add();
  header(s, "Ejemplo manual: el mismo pipeline, dos placements", 10);
  addText(s, "example-sub", 82, 136, 1120, 34, "Tres tareas, seis ocurrencias científicas de 10 MiB; el historial confirma las seis.", { size: 22, color: C.muted });
  // Local placement row.
  addText(s, "example-local-label", 82, 188, 185, 34, "Todas en W1", { size: 22, bold: true, color: C.ink });
  addText(s, "example-local-lane", 82, 224, 76, 46, "W1", { size: 18, bold: true, color: C.slate, valign: "middle" });
  const inA = addNode(s, "example-local-input", 168, 226, 95, 40, "input\n10 MiB", { size: 15, geometry: "ellipse", line: C.teal, fill: C.tealLight });
  const a1 = addNode(s, "example-local-t1", 295, 220, 98, 52, "T1", { size: 20, bold: true });
  const a2 = addNode(s, "example-local-t2", 457, 220, 98, 52, "T2", { size: 20, bold: true });
  const a3 = addNode(s, "example-local-t3", 619, 220, 98, 52, "T3", { size: 20, bold: true });
  const outA = addNode(s, "example-local-output", 765, 226, 110, 40, "final\n10 MiB", { size: 15, geometry: "ellipse", line: C.teal, fill: C.tealLight });
  arrow(s, inA, a1); arrow(s, a1, a2, { color: C.slate }); arrow(s, a2, a3, { color: C.slate }); arrow(s, a3, outA);
  addText(s, "example-local-metrics", 903, 212, 282, 68, "M_req = 20 MiB\nM_obs = 60 MiB · DME = 0.33", { size: 20, bold: true, color: C.ink, valign: "middle" });
  rule(s, "example-separator", 82, 309, 1096, C.rule, 1.3);
  // Cross placement: rows are worker lanes.
  addText(s, "example-cross-label", 82, 336, 185, 34, "Se reparten", { size: 22, bold: true, color: C.ink });
  addText(s, "example-cross-w1", 82, 385, 72, 34, "W1", { size: 18, bold: true, color: C.slate });
  addText(s, "example-cross-w2", 82, 475, 72, 34, "W2", { size: 18, bold: true, color: C.slate });
  rule(s, "example-lane1", 166, 422, 707, C.rule, 1);
  rule(s, "example-lane2", 166, 512, 707, C.rule, 1);
  const inB = addNode(s, "example-cross-input", 168, 379, 95, 40, "input\n10 MiB", { size: 15, geometry: "ellipse", line: C.teal, fill: C.tealLight });
  const b1 = addNode(s, "example-cross-t1", 295, 374, 98, 52, "T1", { size: 20, bold: true });
  const b2 = addNode(s, "example-cross-t2", 497, 464, 98, 52, "T2", { size: 20, bold: true });
  const b3 = addNode(s, "example-cross-t3", 699, 374, 98, 52, "T3", { size: 20, bold: true });
  const outB = addNode(s, "example-cross-output", 820, 379, 95, 40, "final\n10 MiB", { size: 15, geometry: "ellipse", line: C.teal, fill: C.tealLight });
  arrow(s, inB, b1); arrow(s, b1, b2, { color: C.teal }); arrow(s, b2, b3, { color: C.teal }); arrow(s, b3, outB);
  addText(s, "example-cross-metrics", 943, 391, 240, 83, "M_req = 40 MiB\nM_obs = 60 MiB\nDME = 0.67", { size: 20, bold: true, color: C.ink, valign: "middle" });
  addText(s, "example-coverage", 168, 552, 1000, 42, "Coverage = 6 / 6 = 1.  M_obs = 6 × 10 MiB = 60 MiB en ambos placements.", { size: 22, bold: true, color: C.teal, align: "center", valign: "middle" });
  addText(s, "example-caption", 145, 612, 1045, 28, "Las flechas muestran ubicaciones requeridas en el modelo; no una ruta física de red.", { size: 17, color: C.muted, align: "center" });
  notes(s, "El ejemplo es el caso de pipeline de tres tareas. Cada una de las seis ocurrencias científicas pesa 10 MiB: el input, dos archivos intermedios y las tres salidas incluidas por el contrato de los jobs. La reconciliación confirmó seis de seis y el volumen manifestado confirmado es 60 MiB.\n\nCon todas las tareas en W1, solo el input tiene que llegar a W1 y el resultado final se ubica en el destino final: 20 MiB de M_req. Los intermedios pasan entre tareas locales. DME es 20/60, aproximadamente 0.33.\n\nCon T1 en W1, T2 en W2 y T3 en W1, los dos intermedios requieren ubicaciones nuevas; junto con input y salida final, M_req es 40 MiB. M_obs sigue en 60 MiB, de modo que DME es 40/60, aproximadamente 0.67. Las flechas representan exigencias lógicas de disponibilidad de archivos; las trazas actuales no prueban la ruta física de red ni una transferencia directa entre workers.");
}

// 11. Results chart.
{
  const s = deck.slides.add();
  header(s, "Qué cambió al comparar placements", 11);
  addText(s, "results-intro", 82, 137, 1116, 50,
    "DME por patrón. Local = tareas en W1; distribuido = tareas repartidas entre W1 y W2.",
    { size: 22, color: C.body });
  const chart = s.charts.add("bar", {
    position: { left: 110, top: 196, width: 1060, height: 370 },
    categories: ["Pipeline", "Distribución", "Agregación", "Redistribución"],
    series: [
      { name: "Local en W1", values: [0.33, 0.50, 0.50, 0.25], fill: C.slate },
      { name: "Repartido W1–W2", values: [0.67, 0.75, 0.75, 0.63], fill: C.teal },
    ],
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 70 },
    hasLegend: true,
    legend: { position: "bottom", overlay: false, textStyle: { fill: C.body, fontSize: 18, typeface: font } },
    xAxis: { textStyle: { fill: C.body, fontSize: 19, typeface: font }, line: { style: "solid", fill: C.rule, width: 1 }, majorGridlines: null },
    yAxis: { min: 0, max: 1, majorUnit: 0.25, numberFormatCode: "0.00", textStyle: { fill: C.muted, fontSize: 17, typeface: font }, line: { style: "solid", fill: C.rule, width: 1 }, majorGridlines: { style: "solid", fill: C.rule, width: 1 } },
    dataLabels: { showValue: true, position: "outEnd", textStyle: { fill: C.ink, fontSize: 16, bold: true, typeface: font } },
    chartFill: C.bg,
    chartLine: { style: "solid", fill: C.bg, width: 0 },
    plotAreaFill: C.bg,
    plotAreaLine: { style: "solid", fill: C.bg, width: 0 },
  });
  applyPresentationChartFont(chart, { fontFamily: font });
  addText(s, "results-observation", 82, 586, 1116, 48,
    "Al cambiar el placement, M_req y DME cambiaron en estos cuatro patrones.",
    { size: 20, color: C.ink, align: "center", valign: "middle" });
  addText(s, "results-process", 82, 636, 1116, 24,
    "DME compara volúmenes; un valor bajo no demuestra por sí solo que hubiera bytes evitables.",
    { size: 16, color: C.muted, align: "center" });
  notes(s, "El gráfico presenta DME para los cuatro patrones con comparación de ubicación. Pipeline cambia de un tercio a dos tercios. Distribución y agregación cambian de 0.50 a 0.75. Redistribución cambia de 0.25 a 0.625. En esas comparaciones M_rec y M_obs se mantuvieron constantes dentro del patrón; M_req aumentó porque el placement requería más ubicaciones nuevas. Para process, la condición de 20 MiB duplicó tanto M_req como M_obs frente a 10 MiB, y DME quedó en 1. Un valor menor de DME señala que el M_req de este modelo es menor respecto al M_obs confirmado; no identifica por sí solo bytes desperdiciados o evitables. Estas son respuestas de la métrica bajo los factores ensayados, no mejoras o caídas de rendimiento.");
}

// 12. Operational cost and limits of overhead claims.
{
  const s = deck.slides.add();
  header(s, "El costo medido ocurre después del workflow", 12);
  addText(s, "cost-intro", 82, 140, 1110, 42, "No agregamos un tracer dentro de los jobs. Medimos recolección, análisis y evidencia preservada.", { size: 23, color: C.body });
  const cols = [82, 462, 842];
  const labels = ["Preparación", "Analyzer v1", "Preservación"];
  const values = [
    "T_collect\n2.53 s promedio\n\nEntrada para el Analyzer\n18.62 MiB",
    "Wall-clock\n0.73 s promedio\n\nCPU 0.36 s\nMemoria pico 22.49 MiB",
    "Informes\n0.185 MiB por run\n\nEvidencia adicional\n0.701 MiB por run",
  ];
  for (let i = 0; i < 3; i++) {
    addText(s, "cost-label-" + i, cols[i], 220, 300, 36, labels[i], { size: 23, bold: true, color: i === 1 ? C.teal : C.ink, align: "center" });
    rule(s, "cost-rule-" + i, cols[i] + 15, 267, 270, i === 1 ? C.teal : C.slate, 3);
    addText(s, "cost-values-" + i, cols[i], 292, 300, 180, values[i], { size: 23, color: C.body, align: "center", valign: "middle" });
  }
  rule(s, "cost-column-rule-1", 424, 214, 1.2, C.rule, 286);
  rule(s, "cost-column-rule-2", 804, 214, 1.2, C.rule, 286);
  addRect(s, "cost-caveat-bg", 82, 542, 1096, 92, { fill: C.slateLight, line: C.rule, width: 1 });
  addText(s, "cost-caveat", 102, 553, 1056, 68,
    "Los logs nativos se generan durante la ejecución, pero su costo no se aisló con control ON/OFF. No atribuimos a Analyzer un porcentaje del runtime.",
    { size: 21, color: C.ink, align: "center", valign: "middle" });
  notes(s, "Separamos tres conceptos. El logging nativo de Pegasus y HTCondor aparece durante la ejecución, pero en esta campaña no se añadió un tracer adicional dentro de los jobs ni se hizo un control emparejado sin logging; por ello no estimamos una fracción causal del runtime atribuible al Analyzer. La preparación posterior de los artefactos tomó en promedio 2.527 segundos. Analyzer tomó 0.726 segundos de wall-clock, con 0.272 segundos de CPU usuario y 0.083 de CPU sistema, que suman 0.355 segundos; la cifra de 0.36 se redondeó. La memoria RSS pico media fue 22.49 MiB. El input lógico del análisis promedió 18.617 MiB; los informes primarios 0.185 MiB por ejecución y la evidencia post-mortem adicional preservada 0.701 MiB por run. Esos resultados describen este runner, no una tasa universal.");
}

// 13. Utility, interpretation and scope.
{
  const s = deck.slides.add();
  header(s, "Para qué sirve la métrica", 13);
  addText(s, "utility-main", 82, 150, 1090, 67,
    "Permite comparar cuánto movimiento lógico exige cada placement frente al volumen de archivos que la ejecución declara y cuya evidencia logra confirmar.",
    { size: 28, bold: true, color: C.ink, align: "center", valign: "middle" });
  const useY = 272;
  addText(s, "utility-use-1", 98, useY, 318, 115, "Comparar placements\ny configuraciones", { size: 23, bold: true, color: C.teal, align: "center", valign: "middle" });
  addText(s, "utility-use-2", 478, useY, 318, 115, "Ubicar patrones con\nmás movimiento confirmado", { size: 23, bold: true, color: C.teal, align: "center", valign: "middle" });
  addText(s, "utility-use-3", 858, useY, 318, 115, "Priorizar qué casos\nmedir en rendimiento", { size: 23, bold: true, color: C.teal, align: "center", valign: "middle" });
  addText(s, "utility-business", 120, 418, 1040, 54,
    "Uso potencial: orientar decisiones de placement y staging; el impacto en tiempo o dinero debe medirse aparte.",
    { size: 21, color: C.body, align: "center", valign: "middle" });
  rule(s, "utility-rule", 82, 496, 1096, C.rule, 1.2);
  addText(s, "utility-limits", 96, 516, 1072, 95,
    "No mide paquetes de red, ancho de banda, I/O físico de disco, RAM o NUMA, FLOPs, uso de CPU/GPU ni rendimiento del scheduler. La campaña valida un pool de dos workers.",
    { size: 20, color: C.muted, align: "center", valign: "middle" });
  addText(s, "utility-last-line", 98, 630, 1080, 28,
    "La DME agrega información sobre archivos y placement; no reemplaza métricas de tiempo, I/O o recursos.",
    { size: 18, bold: true, color: C.ink, align: "center" });
  notes(s, "La utilidad inmediata es descriptiva. Un equipo puede comparar placements para un mismo workflow, observar qué patrones piden más ubicaciones nuevas y usar esos casos para decidir qué medir después. En un contexto de negocio o de operación, esto puede ayudar a priorizar experimentos de staging, almacenamiento o asignación de tareas. No demuestra que vaya a reducir costos ni que un placement sea el óptimo. Para afirmar impacto en runtime, ancho de banda o gasto harían falta mediciones específicas y controles adecuados. El modelo puede representar más ubicaciones, pero la evidencia empírica actual cubre dos workers. Tampoco mezclamos tráfico de red con I/O físico, memoria RAM o localidad NUMA.");
}

// 14. Selected references.
{
  const s = deck.slides.add();
  header(s, "Fuentes principales", 14);
  const refs = [
    "Bharathi et al. (2008). Characterization of Scientific Workflows. WORKS. doi:10.1109/WORKS.2008.4723958",
    "Deelman et al. (2015). Pegasus, a Workflow Management System for Science Automation. FGCS. doi:10.1016/j.future.2014.10.008",
    "Pietri & Sakellariou (2018). Scheduling Data-Intensive Scientific Workflows with Reduced Communication. SSDBM. doi:10.1145/3221269.3221298",
    "Lee et al. (2023). Data Flow Lifecycles for Optimizing Workflow Coordination. SC. doi:10.1145/3581784.3607104",
    "Tang et al. (2024). DaYu: Optimizing Distributed Scientific Workflows by Decoding Dataflow Semantics and Dynamics. CLUSTER. doi:10.1109/CLUSTER59578.2024.00038",
    "Devarajan et al. (2024). DFTracer: An Analysis-Friendly Data Flow Tracer for AI-Driven Workflows. SC. doi:10.1109/SC41406.2024.00023",
    "Vivas Meza (2026). Scheduling Strategies for Efficient Data Movement in Data-Intensive Scientific Workflow Execution. Disertación doctoral, Universidad de los Andes.",
  ];
  let y = 149;
  for (let i = 0; i < refs.length; i++) {
    addText(s, "reference-" + i, 91, y, 1090, 59, refs[i], { size: 19, color: C.body, valign: "middle" });
    if (i < refs.length - 1) rule(s, "reference-rule-" + i, 91, y + 64, 1088, C.rule, 1);
    y += 72;
  }
  addText(s, "reference-note", 91, 660, 1090, 18, "La comparación de literatura cubre el conjunto consultado y no afirma novedad universal.", { size: 15, color: C.muted, align: "center" });
  notes(s, "Referencias completas y enlaces primarios:\n\nBharathi, S., Chervenak, A., Deelman, E., Mehta, G., Su, M.-H., y Vahi, K. (2008). Characterization of scientific workflows. https://doi.org/10.1109/WORKS.2008.4723958\nDeelman, E. et al. (2015). Pegasus, a workflow management system for science automation. https://doi.org/10.1016/j.future.2014.10.008\nPietri, I., y Sakellariou, R. (2018). Scheduling data-intensive scientific workflows with reduced communication. https://doi.org/10.1145/3221269.3221298\nLee, H. et al. (2023). Data Flow Lifecycles for Optimizing Workflow Coordination. https://doi.org/10.1145/3581784.3607104\nTang, M. et al. (2024). DaYu: Optimizing Distributed Scientific Workflows by Decoding Dataflow Semantics and Dynamics. https://doi.org/10.1109/CLUSTER59578.2024.00038\nDevarajan, H. et al. (2024). DFTracer: An Analysis-Friendly Data Flow Tracer for AI-Driven Workflows. https://doi.org/10.1109/SC41406.2024.00023\nVivas Meza, A. A. (2026). Scheduling strategies for efficient data movement in data-intensive scientific workflow execution. Disertación doctoral, Universidad de los Andes. Descripción institucional del trabajo: https://www.alcf.anl.gov/events/scheduling-strategies-efficient-data-movement-data-intensive-scientific-workflow-execution");
}

const pptx = await PresentationFile.exportPptx(deck);
await pptx.save(draftPath);
await pptx.save(finalPath);
await fs.rm(draftPath + ".inspect.ndjson", { force: true });
await fs.rm(finalPath + ".inspect.ndjson", { force: true });
console.log(JSON.stringify({ finalPath, draftPath, font, slideCount: 14 }, null, 2));
