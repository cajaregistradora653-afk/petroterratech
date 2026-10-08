/* PetroTerratech proxy — Cloudflare Worker (plan Free, sin tarjeta).
 * Recibe { image_b64, confidence } y llama a Roboflow serverless con la
 * clave privada guardada como secreto (ROBOFLOW_API_KEY). La clave NUNCA
 * llega al navegador. Devuelve { detections: [{class, confidence, polygon}] }.
 */
export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return cors(new Response(null, { status: 204 }));
    }
    if (request.method !== "POST") {
      return cors(json({ error: "Usa POST { image_b64, confidence }" }, 405));
    }
    try {
      const body = await request.json();
      const image_b64 = body.image_b64 || "";
      const conf = Math.min(0.9, Math.max(0.05, Number(body.confidence) || 0.25));
      if (!image_b64) return cors(json({ error: "falta image_b64" }, 400));
      if (!env.ROBOFLOW_API_KEY) return cors(json({ error: "falta secreto ROBOFLOW_API_KEY" }, 500));

      const rf = await fetch(
        "https://serverless.roboflow.com/petroterratech/" +
          encodeURIComponent(env.MODEL_VERSION || "2") +
          "?api_key=" +
          encodeURIComponent(env.ROBOFLOW_API_KEY),
        {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: image_b64,
        }
      );
      if (!rf.ok) return cors(json({ error: "roboflow " + rf.status }, 502));
      const d = await rf.json();
      const dets = (d.predictions || [])
        .filter((p) => p.confidence >= conf)
        .map((p) => ({
          class: p.class,
          confidence: Math.round(p.confidence * 1000) / 1000,
          polygon: (p.points || []).map((pt) => [pt.x, pt.y]),
          img_w: Number(d.image && d.image.width) || 0,
          img_h: Number(d.image && d.image.height) || 0,
        }));
      return cors(json({ detections: dets }));
    } catch (e) {
      return cors(json({ error: String((e && e.message) || e).slice(0, 300) }, 500));
    }
  },
};

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function cors(res) {
  const h = new Headers(res.headers);
  h.set("Access-Control-Allow-Origin", "*");
  h.set("Access-Control-Allow-Methods", "POST, OPTIONS");
  h.set("Access-Control-Allow-Headers", "Content-Type");
  return new Response(res.body, { status: res.status, headers: h });
}
