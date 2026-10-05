import { Client } from "https://cdn.jsdelivr.net/npm/@gradio/client@1.9.4/dist/index.js";

const $ = (id) => document.getElementById(id);
const connStatus = $("connStatus");
const fileInput = $("fileInput"), btnGo = $("btnGo"), conf = $("conf");
const SPACE_URL = "https://nicolasvillamilsanchez-petroterratech.hf.space";
let client = null, fileBlob = null;

conf.oninput = () => ($("confVal").textContent = conf.value);

async function connect() {
  connStatus.textContent = "conectando…";
  try {
    client = await Client.connect(SPACE_URL);
    connStatus.textContent = "conectado";
    connStatus.className = "status ok";
    btnGo.disabled = !fileBlob;
  } catch (e) {
    connStatus.textContent = "sin conexión, reintentando…";
    connStatus.className = "status bad";
    client = null;
    setTimeout(connect, 8000);
  }
}
connect();

function setFile(f) {
  if (!f || !f.type.startsWith("image/")) return;
  fileBlob = f;
  $("imgOrig").src = URL.createObjectURL(f);
  btnGo.disabled = !client;
}
fileInput.onchange = (e) => setFile(e.target.files[0]);
const drop = $("drop");
drop.ondragover = (e) => { e.preventDefault(); drop.classList.add("over"); };
drop.ondragleave = () => drop.classList.remove("over");
drop.ondrop = (e) => { e.preventDefault(); drop.classList.remove("over"); setFile(e.dataTransfer.files[0]); };

const COLORS = ["#e6194b","#3cb44b","#ffe119","#4363d8","#f58231","#911eb4","#46f0f0","#f032e6",
  "#bcf60c","#fabebe","#008080","#e6beff","#9a6324","#fffac8","#800000","#aaffc3","#808000",
  "#ffd8b1","#000075","#808080","#ffffff","#000000","#a9a9a9","#00ff00"];

btnGo.onclick = async () => {
  if (!client || !fileBlob) return;
  btnGo.disabled = true;
  btnGo.textContent = "Analizando…";
  try {
    const res = await client.predict("/predict", [fileBlob, parseFloat(conf.value)]);
    const [ann, jsonStr] = res.data;
    const url = ann && ann.url ? ann.url : ann;
    $("imgAnn").src = url;
    const dets = JSON.parse(jsonStr || "[]");
    const counts = {};
    dets.forEach((d) => { counts[d.class] = (counts[d.class] || 0) + 1; });
    $("chips").innerHTML = dets.length
      ? Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([c, n], i) =>
          `<span class="chip" style="border-color:${COLORS[i % 24]}">${c}: ${n}</span>`).join("")
      : `<span class="chip">Sin detecciones a confianza ${conf.value} — prueba bajar el umbral</span>`;
    $("rawJson").textContent = JSON.stringify(dets.map(({ class: c, confidence }) => ({ class: c, confidence })), null, 2);
    $("results").classList.remove("hidden");
  } catch (e) {
    alert("Error de inferencia: " + (e.message || e));
  }
  btnGo.disabled = false;
  btnGo.textContent = "Identificar minerales";
};
