const CheckerAPI = (() => {
  const BASE = typeof API_BASE_URL !== "undefined" ? API_BASE_URL : "";
  const MB = 1024 * 1024;
 
  const CONFIG = {
    "Image Creative": {
      key: "image", path: "/api/images/scan", maxBytes: 10 * MB,
      types: ["image/jpeg", "image/png", "image/webp"],
      typeHint: "Upload a JPEG, PNG or WebP image (SVG is not supported by the backend).",
    },
    "Audio Track": {
      key: "audio", path: "/api/media/audio/scan", maxBytes: 100 * MB,
      types: ["audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3", "audio/mp4",
              "audio/aac", "audio/ogg", "audio/flac", "audio/webm"],
      typeHint: "Upload a WAV, MP3, M4A, AAC, OGG, FLAC or WEBM audio file.",
    },
    "Video Reel": {
      key: "video", path: "/api/media/video/scan", maxBytes: 100 * MB,
      types: ["video/mp4", "video/quicktime", "video/x-msvideo", "video/webm", "video/x-matroska"],
      typeHint: "Upload an MP4, MOV, AVI, WEBM or MKV video file.",
    },
  };
 
  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined && text !== null) n.textContent = String(text);
    return n;
  };
 
  const toast = (msg, kind) =>
    typeof Toast !== "undefined" ? Toast.show(msg, kind) : console.log(msg);
 
  /** Pull every #RRGGBB out of the brand's palette string. */
  function paletteColors(brandId) {
    const brand = BrandManager.getBrands()[brandId];
    const found = (brand?.palettes || "").match(/#[0-9a-fA-F]{6}\b/g) || [];
    return [...new Set(found.map((c) => c.toUpperCase()))];
  }
 
  function badgeClass(status) {
    const s = String(status || "").toLowerCase();
    if (s === "pass" || s === "compliant") return "badge badge-pass";
    if (s === "fail" || s === "non_compliant") return "badge badge-fail";
    return "badge badge-warn";
  }
 
  const SEV = {
    critical: "var(--review-red)", fail: "var(--review-red)", high: "var(--review-red)",
    warning: "var(--review-yellow)", medium: "var(--review-yellow)", review_required: "var(--review-yellow)",
    pass: "var(--review-green)", info: "#a1a1aa", low: "#a1a1aa",
  };
  const sevColor = (v) => SEV[String(v || "").toLowerCase()] || "#a1a1aa";
  const pretty = (k) => k.replace(/_/g, " ");
  const LONG_TEXT = ["transcript", "text", "ocr_text", "extracted_text"];
 
  function section(parent, title) {
    const h = el("div", "", title);
    h.style.cssText = "font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;font-weight:700;" +
      "color:var(--text-muted);margin:22px 0 10px;";
    parent.appendChild(h);
  }
 
  function tile(label, value) {
    const t = el("div");
    t.style.cssText = "background:#0e0e11;border:1px solid var(--border-subtle);border-radius:10px;padding:12px 14px;";
    const l = el("div", "", pretty(label));
    l.style.cssText = "font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:var(--text-muted);margin-bottom:4px;";
    const v = el("div", "", typeof value === "boolean" ? (value ? "Yes" : "No") : (typeof value === "string" ? value.replace(/_/g, " ") : value));
    v.style.cssText = "font-size:1.15rem;font-weight:700;color:#fff;font-family:var(--font-mono);overflow-wrap:anywhere;";
    t.append(l, v);
    return t;
  }
 
  function renderFlag(parent, flag) {
    const obj = flag && typeof flag === "object" ? flag : { message: flag };
    const sev = obj.severity || obj.status || obj.result;
    const card = el("div");
    card.style.cssText = `background:#0e0e11;border:1px solid var(--border-subtle);border-left:4px solid ${sevColor(sev)};` +
      "border-radius:10px;padding:14px 16px;margin-bottom:10px;";
    const top = el("div");
    top.style.cssText = "display:flex;justify-content:space-between;gap:10px;align-items:baseline;";
    top.appendChild(el("strong", "", obj.title || obj.rule || obj.check || obj.category || (obj.type ? pretty(obj.type) : "Finding")));
    if (sev) {
      const tag = el("span", "", String(sev).replace(/_/g, " ").toUpperCase());
      tag.style.cssText = `font-size:.68rem;font-weight:700;color:${sevColor(sev)};white-space:nowrap;`;
      top.appendChild(tag);
    }
    card.appendChild(top);
    if (obj.matched_text) {
      const q = el("p", "", `\u201c${obj.matched_text}\u201d`);
      q.style.cssText = "margin:6px 0 0;font-family:var(--font-mono);font-size:.82rem;color:#fff;";
      card.appendChild(q);
    }
    const msg = obj.description || obj.message || obj.reason;
    if (msg) {
      const p = el("p", "", msg);
      p.style.cssText = "margin:6px 0 0;font-size:.86rem;color:var(--text-secondary);line-height:1.5;";
      card.appendChild(p);
    }
    const fix = obj.recommended_fix || obj.suggestion || obj.recommendation;
    if (fix) {
      const p = el("p", "", "Fix: " + fix);
      p.style.cssText = "margin:6px 0 0;font-size:.84rem;color:#d4d4d8;";
      card.appendChild(p);
    }
    parent.appendChild(card);
  }
 
  const isScalar = (v) => v === null || ["string", "number", "boolean"].includes(typeof v);
  const SUBCHECKS = ["loudness_check", "disclaimer_check", "palette_check"];
 
  /** Sort a result object into tiles / text / flags / colour swatches / notes / collapsed raw data. */
  function collect(data) {
    const out = { tiles: [], texts: [], flags: [], swatches: [], notes: [], rest: [] };
    for (const [k, v] of Object.entries(data)) {
      if (["filename", "brand_id", "overall_status", "status", "spoken_claim_flags"].includes(k)) continue;
 
      if (k === "transcription" && v && typeof v === "object") {
        if (v.language) out.tiles.push(["language", v.language]);
        out.texts.push(["transcript", v.transcript || "(No speech detected)"]);
        if (v.segments && v.segments.length) out.rest.push(["transcript segments", v.segments]);
        continue;
      }
      if (SUBCHECKS.includes(k) && v && typeof v === "object") {
        const label = k.replace("_check", "");
        for (const [sk, sv] of Object.entries(v)) {
          if (sk === "message") { if (sv) out.notes.push(sv); }
          else if (sk === "status") out.tiles.push([`${label} status`, sv]);
          else if (isScalar(sv)) { if (sv !== null && sv !== "") out.tiles.push([sk, sv]); }
          else if (Array.isArray(sv) && sv.every(isScalar) && sv.length <= 3) out.tiles.push([sk, sv.join(" to ")]);
          else out.rest.push([`${label} ${pretty(sk)}`, sv]);
        }
        continue;
      }
      if (["flags", "findings", "violations"].includes(k) && Array.isArray(v)) { out.flags.push(...v); continue; }
      if (k === "dominant_colors" && Array.isArray(v) && v.every((c) => c && c.hex)) { out.swatches = v; continue; }
      if (typeof v === "string" && (LONG_TEXT.includes(k) || v.length > 60)) { out.texts.push([k, v || "(none)"]); continue; }
      if (v !== null && typeof v === "object") { out.rest.push([k, v]); continue; }
      if (v !== null && v !== undefined && v !== "") out.tiles.push([k, v]);
    }
    return out;
  }
 
  function renderBlock(parent, data) {
    const c = collect(data);
 
    if (c.notes.length) {
      const n = el("p", "", c.notes.join(" "));
      n.style.cssText = "margin:14px 0 0;font-size:.88rem;color:var(--text-secondary);line-height:1.5;";
      parent.appendChild(n);
    }
 
    if (c.tiles.length) {
      section(parent, "Measurements");
      const grid = el("div");
      grid.style.cssText = "display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px;";
      c.tiles.forEach(([k, v]) => grid.appendChild(tile(k, v)));
      parent.appendChild(grid);
    }
 
    if (c.swatches.length) {
      section(parent, "Dominant colours");
      const row = el("div");
      row.style.cssText = "display:flex;flex-wrap:wrap;gap:10px;";
      c.swatches.forEach((col) => {
        const w = el("div");
        w.style.cssText = "display:flex;align-items:center;gap:8px;background:#0e0e11;border:1px solid var(--border-subtle);" +
          "border-radius:10px;padding:8px 12px;";
        const chip = el("span");
        chip.style.cssText = `width:22px;height:22px;border-radius:6px;border:1px solid #3f3f46;background:${String(col.hex).replace(/[^#0-9a-fA-F]/g, "")};`;
        const t = el("span", "", `${col.hex}  ${col.percentage ?? ""}${col.percentage !== undefined ? "%" : ""}`);
        t.style.cssText = "font-family:var(--font-mono);font-size:.8rem;";
        w.append(chip, t);
        row.appendChild(w);
      });
      parent.appendChild(row);
    }
 
    section(parent, `Findings (${c.flags.length})`);
    if (!c.flags.length) {
      const ok = el("p", "", "No issues found.");
      ok.style.color = "var(--review-green)";
      parent.appendChild(ok);
    }
    c.flags.forEach((f) => renderFlag(parent, f));
 
    c.texts.forEach(([k, v]) => {
      section(parent, pretty(k));
      const box = el("div", "", v);
      box.style.cssText = "background:#0e0e11;border:1px solid var(--border-subtle);border-radius:10px;" +
        "padding:14px 16px;line-height:1.7;font-size:.9rem;color:#d4d4d8;white-space:pre-wrap;";
      parent.appendChild(box);
    });
 
    c.rest.forEach(([k, v]) => {
      const d = el("details");
      d.style.cssText = "margin-top:14px;";
      const sm = el("summary", "", pretty(k));
      sm.style.cssText = "cursor:pointer;font-size:.82rem;color:var(--text-secondary);text-transform:capitalize;";
      const pre = el("pre", "", JSON.stringify(v, null, 2));
      pre.style.cssText = "margin:8px 0 0;padding:12px;background:#000;border-radius:8px;font-size:.76rem;" +
        "overflow-x:auto;color:#a1a1aa;";
      d.append(sm, pre);
      parent.appendChild(d);
    });
  }
 
  function statusPill(status) {
    return el("span", badgeClass(status), String(status || "review_required").replace(/_/g, " ").toUpperCase());
  }
 
  function renderResult(form, data) {
    let box = form.parentElement.querySelector(".scan-result-box");
    if (!box) {
      box = el("div", "scan-result-box");
      box.style.cssText = "background:#090a0f;border:1px solid var(--border-subtle);border-radius:14px;" +
        "padding:24px;margin-top:28px;";
      form.after(box);
    }
    box.replaceChildren();
 
    const head = el("div");
    head.style.cssText = "display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;";
    const left = el("div");
    left.style.cssText = "display:flex;align-items:center;gap:12px;";
    const title = el("h3", "", "Scan Results");
    title.style.margin = "0";
    left.append(title, statusPill(data.overall_status || data.status));
    head.appendChild(left);
    if (data.filename) {
      const f = el("span", "", data.filename);
      f.style.cssText = "font-size:.8rem;color:var(--text-muted);font-family:var(--font-mono);overflow-wrap:anywhere;";
      head.appendChild(f);
    }
    box.appendChild(head);
 
    if (data.video_check || data.audio_check) {
      [["Video check", data.video_check], ["Audio check", data.audio_check]].forEach(([label, sub]) => {
        if (!sub) return;
        const wrap = el("div");
        wrap.style.cssText = "margin-top:22px;padding-top:18px;border-top:1px solid var(--border-subtle);";
        const h = el("div");
        h.style.cssText = "display:flex;align-items:center;gap:10px;";
        const t = el("strong", "", label);
        t.style.fontSize = "1.02rem";
        h.append(t, statusPill(sub.overall_status));
        wrap.appendChild(h);
        if (sub.message) {
          const m = el("p", "", sub.message);
          m.style.cssText = "margin:8px 0 0;font-size:.86rem;color:var(--text-secondary);";
          wrap.appendChild(m);
        }
        renderBlock(wrap, sub);
        box.appendChild(wrap);
      });
    } else {
      renderBlock(box, data);
    }
    box.scrollIntoView({ behavior: "smooth", block: "start" });
  }
 
  async function run(form, type, brandId) {
    const cfg = CONFIG[type];
    if (!cfg) {
      toast(`${type} checker integration is not connected yet.`, "info");
      return;
    }
 
    const file = form.querySelector('input[type="file"]')?.files?.[0];
    if (!file) return toast("Please choose a file first.", "error");
    if (file.size === 0) return toast("The selected file is empty.", "error");
    if (file.size > cfg.maxBytes)
      return toast(`File must be ${cfg.maxBytes / MB} MB or smaller.`, "error");
    if (!cfg.types.includes(file.type)) return toast(cfg.typeHint, "error");
 
    const fd = new FormData();
    fd.append("file", file);
 
    if (cfg.key === "image") {
      const colors = paletteColors(brandId);
      if (!colors.length)
        return toast("This brand has no hex colours in its palette. Add some first.", "error");
      fd.append("brand_id", brandId);
      fd.append("approved_colors", JSON.stringify(colors));
    }
 
    if (cfg.key === "video") {
      const disclaimer = form.querySelector(".required-disclaimer-input")?.value.trim();
      if (!disclaimer) return toast("Enter the required on-screen disclaimer text.", "error");
      fd.append("required_disclaimer", disclaimer);
    }
 
    const button = form.querySelector('button[type="submit"]');
    const oldText = button?.textContent;
    if (button) { button.disabled = true; button.textContent = "Scanning..."; }
 
    try {
      const res = await fetch(BASE + cfg.path, { method: "POST", body: fd });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = Array.isArray(data.detail)
          ? data.detail.map((d) => d.msg).join("; ")
          : data.detail;
        throw new Error(detail || `Request failed (${res.status})`);
      }
      renderResult(form, data);
      toast("Scan complete.", "success");
    } catch (err) {
      console.error("Scan failed:", err);
      toast(
        err instanceof TypeError
          ? "Could not reach the backend. Is FastAPI running and is this page served from it?"
          : `Scan failed: ${err.message}`,
        "error"
      );
    } finally {
      if (button) { button.disabled = false; button.textContent = oldText; }
    }
  }
 
  /** One-time UI touches: show chosen file name, add the video disclaimer field. */
  function init() {
    document.querySelectorAll(".checker-panel form").forEach((form) => {
      const input = form.querySelector('input[type="file"]');
      const zone = input?.closest(".dropzone");
      if (input && zone) {
        const label = el("div", "file-chosen", "");
        label.style.cssText = "margin-top:8px;font-size:.82rem;color:var(--text-secondary);";
        zone.appendChild(label);
        input.addEventListener("click", (e) => e.stopPropagation()); // avoid re-opening picker
        input.addEventListener("change", () => {
          const f = input.files[0];
          label.textContent = f ? `${f.name} (${(f.size / MB).toFixed(2)} MB)` : "";
        });
      }
    });
 
    const videoForm = document.querySelector("#tab-video form");
    if (videoForm && !videoForm.querySelector(".required-disclaimer-input")) {
      const group = el("div", "form-group");
      group.appendChild(el("label", "form-label", "Required On-Screen Disclaimer"));
      const inp = el("input", "form-control required-disclaimer-input");
      inp.type = "text";
      inp.placeholder = "Exact disclaimer text that must appear on screen";
      group.appendChild(inp);
      const fileGroup = videoForm.querySelector(".dropzone")?.closest(".form-group");
      (fileGroup || videoForm.lastElementChild).before(group);
    }
  }
 
  document.addEventListener("DOMContentLoaded", init);
  return { run };
})();
 
