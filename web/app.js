/* PetroTerratech web: fetch directo a la API Gradio del Space (sin dependencias externas). */
const $ = (id) => document.getElementById(id);
const connStatus = $("connStatus");
const fileInput = $("fileInput"), btnGo = $("btnGo"), conf = $("conf");
const SPACE_URL = "https://nicolasvillamilsanchez-petroterratech.hf.space";
// Se rellena cuando el Worker de Cloudflare exista; mientras tanto usa el Space.
const WORKER_URL = "https://petroterratech.cajaregistradora653.workers.dev";
let fileDataUrl = null;

conf.oninput = () => ($("confVal").textContent = conf.value);

function setStatus(t, cls) {
  connStatus.textContent = t;
  connStatus.className = "status" + (cls ? " " + cls : "");
}

const dbgEl = $("debugLog");
function dbg(...args) {
  const line = new Date().toLocaleTimeString() + " " + args.map((a) =>
    typeof a === "string" ? a : JSON.stringify(a).slice(0, 500)).join(" ");
  console.log("[pt]", ...args);
  if (dbgEl) {
    if (dbgEl.textContent === "— log listo —") dbgEl.textContent = "";
    dbgEl.textContent += line + "\n";
    dbgEl.scrollTop = dbgEl.scrollHeight;
  }
}
$("btnClear").onclick = () => { dbgEl.textContent = ""; };
$("btnCopy").onclick = async () => {
  try { await navigator.clipboard.writeText(dbgEl.textContent); setStatus("log copiado", "ok"); }
  catch (e) { setStatus("no se pudo copiar", "bad"); }
};

async function ping() {
  try {
    dbg("ping", SPACE_URL + "/gradio_api/info");
    const r = await fetch(SPACE_URL + "/gradio_api/info", { method: "GET" });
    dbg("ping status:", r.status);
    if (r.ok) { setStatus("conectado", "ok"); return true; }
  } catch (e) {
    dbg("ping fallo:", String((e && e.message) || e));
  }
  setStatus("despertando backend…", "");
  return false;
}

function setFile(f) {
  if (!f || !f.type.startsWith("image/")) return;
  const img = new Image();
  img.onload = () => {
    const s = Math.min(1, 640 / Math.max(img.width, img.height));
    const c = document.createElement("canvas");
    c.width = Math.round(img.width * s);
    c.height = Math.round(img.height * s);
    c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
    fileDataUrl = c.toDataURL("image/jpeg", 0.92);
    $("imgOrig").src = fileDataUrl;
    setStatus("imagen lista (" + c.width + "×" + c.height + ")", "ok");
    URL.revokeObjectURL(img.src);
  };
  img.src = URL.createObjectURL(f);
}
fileInput.onchange = (e) => setFile(e.target.files[0]);
const drop = $("drop");
drop.ondragover = (e) => { e.preventDefault(); drop.classList.add("over"); };
drop.ondragleave = () => drop.classList.remove("over");
drop.ondrop = (e) => { e.preventDefault(); drop.classList.remove("over"); setFile(e.dataTransfer.files[0]); };

const COLORS = ["#e6194b","#3cb44b","#ffe119","#4363d8","#f58231","#911eb4","#46f0f0","#f032e6",
  "#bcf60c","#fabebe","#008080","#e6beff","#9a6324","#fffac8","#800000","#aaffc3","#808000",
  "#ffd8b1","#000075","#808080","#ffffff","#000000","#a9a9a9","#00ff00"];

async function callPredict(imgUrl, confidence) {
  dbg("POST /gradio_api/call/predict, conf=", confidence, "img_bytes=", Math.round(imgUrl.length * 0.75));
  const post = await fetch(SPACE_URL + "/gradio_api/call/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data: [{ url: imgUrl }, confidence] }),
  });
  dbg("POST status:", post.status);
  if (!post.ok) throw new Error("HTTP " + post.status + " al iniciar predicción: " + (await post.text()).slice(0, 200));
  const { event_id } = await post.json();
  dbg("event_id:", event_id);
  const url = SPACE_URL + "/gradio_api/call/predict/" + event_id;
  const t0 = Date.now();
  let buf = "", polls = 0;
  while (Date.now() - t0 < 180000) {
    polls++;
    const r = await fetch(url);
    if (!r.ok) throw new Error("HTTP " + r.status + " esperando resultado");
    buf += await r.text();
    const events = buf.split("\n\n");
    buf = events.pop();
    for (const ev of events) {
      const line = ev.split("\n").find((l) => l.startsWith("data: "));
      dbg("poll", polls, "->", (line || ev).slice(0, 220));
      if (!line) continue;
      const msg = JSON.parse(line.slice(6));
      // Gradio 5: el resultado final llega como arreglo directo, sin envoltorio {msg}
      if (Array.isArray(msg)) return msg;
      if (msg.error) throw new Error(typeof msg.error === "string" ? msg.error : JSON.stringify(msg.error).slice(0, 200));
      if (msg.msg === "process_completed") return msg.output.data;
      if (msg.msg === "error" || msg.msg === "process_failed") {
        throw new Error((msg.output && msg.output.error) || msg.msg);
      }
      if (msg.msg === "process_generating" || msg.msg === "progress") {
        setStatus("analizando… " + (msg.output && msg.output.data ? "" : ""), "");
      }
    }
    await new Promise((res) => setTimeout(res, 1500));
  }
  throw new Error("Tiempo de espera agotado (3 min). El backend puede estar saturado.");
}

async function callWorker(imgDataUrl, confidence) {
  const b64 = imgDataUrl.split(",")[1];
  dbg("POST worker, conf=", confidence, "img_bytes=", Math.round(b64.length * 0.75));
  const r = await fetch(WORKER_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_b64: b64, confidence }),
  });
  dbg("worker status:", r.status);
  if (!r.ok) throw new Error("HTTP " + r.status + ": " + (await r.text()).slice(0, 200));
  const out = await r.json();
  if (out.error) throw new Error(out.error);
  return out.detections || [];
}

function colorFor(cls) {
  let h = 0;
  for (const ch of cls) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return COLORS[h % COLORS.length];
}

function render(dets, imgSrc) {
  if (dets.length && dets[0].class === "ERROR") throw new Error(dets[0].detail || "error backend");
  const counts = {};
  dets.forEach((d) => { counts[d.class] = (counts[d.class] || 0) + 1; });
  const order = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
  const colormap = {};
  order.forEach((c) => { colormap[c] = colorFor(c); });
  $("chips").innerHTML = dets.length
    ? order.map((c) =>
        `<span class="chip" style="border-color:${colormap[c]}">${c}: ${counts[c]}</span>`).join("")
    : `<span class="chip">Sin detecciones a confianza ${conf.value} — prueba bajar el umbral</span>`;
  const img = new Image();
  img.onload = () => {
    const cv = $("canvasOut");
    cv.width = img.naturalWidth;
    cv.height = img.naturalHeight;
    const ctx = cv.getContext("2d");
    ctx.drawImage(img, 0, 0);
    dets.forEach((d) => {
      const poly = d.polygon || [];
      if (poly.length < 3) return;
      const sx = img.naturalWidth / (d.img_w || img.naturalWidth);
      const sy = img.naturalHeight / (d.img_h || img.naturalHeight);
      const col = colormap[d.class] || "#fff";
      ctx.beginPath();
      poly.forEach(([x, y], i) => {
        const px = x * sx, py = y * sy;
        if (i) ctx.lineTo(px, py); else ctx.moveTo(px, py);
      });
      ctx.closePath();
      ctx.fillStyle = col + "55";
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = col;
      ctx.stroke();
      const [lx, ly] = [poly[0][0] * sx, Math.max(14, poly[0][1] * sy - 6)];
      ctx.font = "bold 14px system-ui";
      ctx.fillStyle = col;
      ctx.fillText(`${d.class} ${d.confidence}`, lx, ly);
    });
    dbg("canvas renderizado:", dets.length, "detecciones");
  };
  img.src = imgSrc;
  $("rawJson").textContent = JSON.stringify(dets.map(({ class: c, confidence }) => ({ class: c, confidence })), null, 2);
  $("results").classList.remove("hidden");
}
btnGo.onclick = async () => {
  if (!fileDataUrl) { setStatus("primero sube una imagen", "bad"); return; }
  btnGo.disabled = true;
  btnGo.textContent = "Analizando…";
  setStatus("analizando…", "");
  try {
    const confidence = parseFloat(conf.value);
    let dets;
    if (WORKER_URL) {
      setStatus("analizando vía proxy…", "");
      dets = await callWorker(fileDataUrl, confidence);
    } else {
      setStatus("contactando backend…", "");
      await ping();
      const data = await callPredict(fileDataUrl, confidence);
      dbg("completado. data[0]:", JSON.stringify(data[0]).slice(0, 200));
      dbg("completado. data[1] (dets):", String(data[1]).slice(0, 400));
      dets = JSON.parse(data[1] || "[]");
    }
    render(dets, fileDataUrl);
    setStatus("listo", "ok");
  } catch (e) {
    let m = String((e && e.message) || e);
    if (/zerogpu|quota/i.test(m)) {
      m = "Cuota GPU gratuita agotada temporalmente. Espera unos minutos y reintenta con confianza 0.25.";
    }
    m = m.slice(0, 300);
    dbg("FALLO:", e && e.stack ? e.stack.slice(0, 600) : m);
    setStatus("error: " + m, "bad");
  }
  btnGo.disabled = false;
  btnGo.textContent = "Identificar minerales";
};

ping();
