/* ScamShield MY — front end. Plain JS, no build step. */
(() => {
  "use strict";

  // ---------------------------------------------------------------- strings
  const T = {
    ms: {
      idleKicker: "Sedia", idleTitle: "Panggilan mencurigakan?",
      idleBody: "Pasang pembesar suara, tekan butang, dan saya akan dengar bersama anda.",
      startBtn: "Semak panggilan ini", riskWord: "risiko penipuan",
      lowKicker: "Sedang mendengar", lowTitle: "Tiada tanda penipuan setakat ini",
      cautionKicker: "Berhati-hati", cautionTitle: "Jangan beri wang atau kod",
      highKicker: "Amaran penipuan", highTitle: "Ini penipuan. Letak telefon.",
      endedKicker: "Panggilan tamat",
      waBtn: "Beritahu keluarga", nsrcBtn: "Telefon 997 (NSRC)", stopBtn: "Tamat",
      reportBtn: "Hantar laporan tanpa nama", reportSent: "Laporan dihantar. Terima kasih.",
      againBtn: "Semak panggilan lain",
      reportNote: "Laporan hanya mengandungi taktik dan nombor yang disebut, bukan rakaman atau transkrip.",
      heardTitle: "Apa yang didengar", heardEmpty: "Transkrip akan muncul di sini.",
      whyTitle: "Kenapa", numTitle: "Nombor yang disebut", setTitle: "Tetapan",
      modeLegend: "Cara mendengar", modeDemo: "Panggilan demo (skrip)",
      modeBrowser: "Mikrofon: pengecaman suara pelayar (percuma)",
      modeGemini: "Mikrofon: Gemini (lebih tepat, perlu kunci API)",
      demoPick: "Pilih panggilan demo", speakCaller: "Mainkan suara pemanggil (demo)",
      voiceWarn: "Amaran suara apabila penipuan dikesan", familyNum: "Nombor WhatsApp ahli keluarga",
      dashLink: "Lihat laporan komuniti",
      disclaimer: "Prototaip hackathon, bukan pengganti nasihat PDRM. Jika ragu, letak telefon dan hubungi 997.",
      caller: "Pemanggil", you: "Anda", heard: "Didengar",
      hintDemo: "Demo: ", hintBrowser: "Guna Chrome atau Edge. Pasang pembesar suara dan letak telefon dekat.",
      hintGemini: "Gemini akan menukar suara kepada teks setiap 6 saat.",
      hintNoKey: "Kunci Gemini belum ditetapkan pada pelayan. Guna mod pelayar atau demo.",
      engineLlm: "Gemini + peraturan", engineRules: "Peraturan sahaja",
      reported: (n) => `Dilaporkan ${n} kali`, notFound: "Tiada dalam rekod demo", unchecked: "Belum disemak",
      demoData: "Data demo. Sahkan di", checkSelf: "Semak sendiri di",
      micDenied: "Mikrofon tidak dibenarkan. Benarkan akses mikrofon, atau guna panggilan demo.",
      noSpeech: "Pelayar ini tiada pengecaman suara. Guna Chrome atau Edge, atau mod demo.",
      netError: "Tidak dapat menghubungi pelayan. Semak sambungan internet.",
      warnSpeech: "Amaran. Ini mungkin penipuan. Polis dan bank tidak akan minta anda pindahkan wang atau beri kod. Letak telefon sekarang.",
      waText: (a) => `Amaran ScamShield: saya baru terima panggilan yang mungkin penipuan` +
        (a.type ? ` (${a.type})` : "") + `, risiko ${a.pct}%. ` +
        (a.tactics ? `Pemanggil: ${a.tactics}. ` : "") +
        (a.numbers ? `Nombor disebut: ${a.numbers}. ` : "") + `Tolong telefon saya sekarang.`,
    },
    en: {
      idleKicker: "Ready", idleTitle: "Suspicious call?",
      idleBody: "Put the call on speaker, press the button, and I'll listen with you.",
      startBtn: "Check this call", riskWord: "scam risk",
      lowKicker: "Listening", lowTitle: "No scam signs so far",
      cautionKicker: "Be careful", cautionTitle: "Don't send money or codes",
      highKicker: "Scam warning", highTitle: "This is a scam. Hang up.",
      endedKicker: "Call ended",
      waBtn: "Alert my family", nsrcBtn: "Call 997 (NSRC)", stopBtn: "End",
      reportBtn: "Send anonymous report", reportSent: "Report sent. Thank you.",
      againBtn: "Check another call",
      reportNote: "Reports contain only the tactics and numbers mentioned, never the recording or transcript.",
      heardTitle: "What I heard", heardEmpty: "The transcript will appear here.",
      whyTitle: "Why", numTitle: "Numbers mentioned", setTitle: "Settings",
      modeLegend: "How to listen", modeDemo: "Demo call (scripted)",
      modeBrowser: "Microphone: browser speech recognition (free)",
      modeGemini: "Microphone: Gemini (more accurate, needs API key)",
      demoPick: "Choose a demo call", speakCaller: "Play the caller's voice (demo)",
      voiceWarn: "Spoken warning when a scam is detected", familyNum: "Family member's WhatsApp number",
      dashLink: "See community reports",
      disclaimer: "Hackathon prototype, not a substitute for PDRM advice. If in doubt, hang up and call 997.",
      caller: "Caller", you: "You", heard: "Heard",
      hintDemo: "Demo: ", hintBrowser: "Use Chrome or Edge. Put the call on speaker and keep the phone close.",
      hintGemini: "Gemini turns speech into text every 6 seconds.",
      hintNoKey: "No Gemini key is set on the server. Use browser or demo mode.",
      engineLlm: "Gemini + rules", engineRules: "Rules only",
      reported: (n) => `Reported ${n} times`, notFound: "Not in demo records", unchecked: "Not checked",
      demoData: "Demo data. Verify on", checkSelf: "Check it yourself on",
      micDenied: "Microphone access was blocked. Allow the microphone, or use a demo call.",
      noSpeech: "This browser has no speech recognition. Use Chrome or Edge, or demo mode.",
      netError: "Can't reach the server. Check your internet connection.",
      warnSpeech: "Warning. This is likely a scam. Police and banks will never ask you to move money or share a code. Hang up now.",
      waText: (a) => `ScamShield alert: I just got a call that may be a scam` +
        (a.type ? ` (${a.type})` : "") + `, ${a.pct}% risk. ` +
        (a.tactics ? `The caller: ${a.tactics}. ` : "") +
        (a.numbers ? `Numbers mentioned: ${a.numbers}. ` : "") + `Please call me now.`,
    },
  };

  // ---------------------------------------------------------------- state
  const $ = (id) => document.getElementById(id);
  const RANK = { idle: -1, low: 0, caution: 1, high: 2 };
  const store = {
    get(k, d) { try { const v = localStorage.getItem("ss:" + k); return v === null ? d : v; } catch { return d; } },
    set(k, v) { try { localStorage.setItem("ss:" + k, v); } catch { /* private mode */ } },
  };

  let lang = store.get("lang", "ms") === "en" ? "en" : "ms";
  let health = { llm_enabled: false };
  let scenarios = [];
  let phase = "idle";          // idle | live | done
  let session = 0;             // bumps on every start/stop to cancel async loops
  let lines = [];              // {speaker, text}
  let interim = "";
  let analysis = null;
  let shownLevel = "idle";     // sticky: never drops during a call
  let warned = false;
  let warningDone = Promise.resolve();
  let recognizer = null;
  let media = null;

  const t = (k) => T[lang][k];

  // ---------------------------------------------------------------- i18n
  function applyStrings() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const v = t(el.dataset.i18n);
      if (typeof v === "string") el.textContent = v;
    });
    document.querySelectorAll(".lang button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === lang)));
    fillScenarios();
    render();
  }

  function fillScenarios() {
    const sel = $("scenario");
    const keep = sel.value || store.get("scenario", "police-bukit-aman");
    sel.innerHTML = "";
    for (const s of scenarios) {
      const o = document.createElement("option");
      o.value = s.id;
      o.textContent = lang === "ms" ? s.title_ms : s.title_en;
      sel.appendChild(o);
    }
    if (scenarios.some((s) => s.id === keep)) sel.value = keep;
  }

  const mode = () => document.querySelector('input[name="mode"]:checked').value;
  const scenario = () => scenarios.find((s) => s.id === $("scenario").value);

  function modeHint() {
    const m = mode();
    if (m === "demo") { const s = scenario(); return s ? t("hintDemo") + (lang === "ms" ? s.title_ms : s.title_en) : ""; }
    if (m === "browser") return t("hintBrowser");
    return health.llm_enabled ? t("hintGemini") : t("hintNoKey");
  }

  // ---------------------------------------------------------------- render
  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function highlight(text, phrases) {
    if (!phrases.length) return escapeHtml(text);
    const re = new RegExp(phrases.map((p) => p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|"), "gi");
    let out = "", last = 0, m;
    while ((m = re.exec(text))) {
      if (!m[0]) { re.lastIndex++; continue; }
      out += escapeHtml(text.slice(last, m.index)) + "<mark>" + escapeHtml(m[0]) + "</mark>";
      last = m.index + m[0].length;
    }
    return out + escapeHtml(text.slice(last));
  }

  function evidencePhrases() {
    if (!analysis) return [];
    const all = analysis.tactics.flatMap((x) => x.evidence).filter((p) => p && p.length > 1);
    return [...new Set(all)].sort((a, b) => b.length - a.length);
  }

  function renderTranscript() {
    const box = $("transcript");
    if (!lines.length && !interim) { box.innerHTML = `<p class="empty">${escapeHtml(t("heardEmpty"))}</p>`; return; }
    const phrases = evidencePhrases();
    const who = { caller: t("caller"), you: t("you"), mic: t("heard") };
    box.innerHTML = lines.map((l) =>
      `<p class="line ${l.speaker}"><span class="who">${escapeHtml(who[l.speaker] || "")}</span>${highlight(l.text, phrases)}</p>`
    ).join("") + (interim ? `<p class="line interim">${escapeHtml(interim)}</p>` : "");
    box.scrollTop = box.scrollHeight;
  }

  function renderVerdict() {
    document.body.dataset.level = shownLevel;
    const kicker = $("verdictKicker"), title = $("verdictTitle"), body = $("verdictBody");
    $("meter").hidden = phase === "idle";
    $("actionsIdle").hidden = phase !== "idle";
    $("actionsLive").hidden = phase !== "live";
    $("actionsDone").hidden = phase !== "done";
    $("modeHint").textContent = modeHint();

    if (phase === "idle") {
      kicker.textContent = t("idleKicker"); title.textContent = t("idleTitle"); body.textContent = t("idleBody");
      return;
    }
    const lvl = shownLevel === "idle" ? "low" : shownLevel;
    const type = analysis && (lang === "ms" ? analysis.scam_type_ms || analysis.scam_type : analysis.scam_type);
    kicker.textContent = phase === "done" ? t("endedKicker") : lvl === "high" ? (type || t("highKicker")) : t(lvl + "Kicker");
    title.textContent = t(lvl + "Title");
    if (analysis) {
      body.textContent = analysis["advice_" + lang];
    } else {
      body.textContent = t("idleBody");
    }
    const pct = analysis ? Math.round(analysis.risk * 100) : 0;
    $("meterPct").textContent = pct + "%";
    $("meterFill").style.width = Math.max(pct, 2) + "%";
    $("engineBadge").textContent = analysis ? (analysis.engine === "gemini+rules" ? t("engineLlm") : t("engineRules")) : "";
    $("waBtn").href = whatsappLink();
  }

  function renderDetails() {
    const why = $("whyBlock"), nums = $("numBlock");
    why.hidden = !analysis || !analysis.tactics.length;
    if (!why.hidden) {
      $("explain").textContent = analysis["explanation_" + lang];
      $("tactics").innerHTML = analysis.tactics.map((x) =>
        `<li><strong>${escapeHtml(lang === "ms" ? x.label_ms : x.label_en)}</strong>` +
        (x.evidence.length ? `<span class="ev">"${x.evidence.slice(0, 3).map(escapeHtml).join('", "')}"</span>` : "") + `</li>`
      ).join("");
    }
    nums.hidden = !analysis || !analysis.lookups.length;
    if (!nums.hidden) {
      $("numbers").innerHTML = analysis.lookups.map((lk) => {
        const status = lk.status === "reported" ? t("reported")(lk.reports) : lk.status === "not_found" ? t("notFound") : t("unchecked");
        const prefix = lk.source === "demo" ? t("demoData") : t("checkSelf");
        return `<li class="${lk.status}"><span class="num">${escapeHtml(formatNumber(lk))}</span>` +
          `<span class="status">${escapeHtml(status)}</span>` +
          `<span class="note">${escapeHtml(prefix)} <a href="${lk.check_url}" target="_blank" rel="noopener">Semak Mule</a></span></li>`;
      }).join("");
    }
  }

  function formatNumber(lk) {
    const d = lk.number;
    if (lk.kind === "phone") return d.replace(/^(01\d)(\d{3,4})(\d{4})$/, "$1-$2 $3");
    return d.replace(/(\d{4})(?=\d)/g, "$1 ");
  }

  function render() { renderVerdict(); renderTranscript(); renderDetails(); }

  // ---------------------------------------------------------------- analysis
  let inflight = false, pending = false;
  async function requestAnalysis() {
    if (inflight) { pending = true; return; }
    inflight = true;
    const mySession = session;
    try {
      do {
        pending = false;
        const transcript = lines.map((l) => l.text).join("\n");
        if (!transcript.trim()) break;
        const res = await fetch("/api/analyze", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ transcript, use_llm: health.llm_enabled }),
        });
        if (!res.ok) throw new Error("HTTP " + res.status);
        const data = await res.json();
        if (mySession !== session && phase !== "done") break;
        onAnalysis(data);
      } while (pending);
    } catch (err) {
      console.warn(err);
      $("modeHint").textContent = t("netError");
    } finally {
      inflight = false;
    }
  }

  function onAnalysis(data) {
    analysis = data;
    if (RANK[data.level] > RANK[shownLevel]) shownLevel = data.level;
    if (shownLevel === "high" && !warned && phase === "live") {
      warned = true;
      document.body.classList.add("flash");
      setTimeout(() => document.body.classList.remove("flash"), 2000);
      if (navigator.vibrate) navigator.vibrate([400, 200, 400]);
      if ($("voiceWarn").checked) {
        warningDone = (async () => {
          speechSynthesis.cancel();
          await sleep(200);
          await speak(t("warnSpeech"), lang, { rate: 0.95 });
        })();
      }
    }
    render();
  }

  // ---------------------------------------------------------------- speech output
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  let voices = [];
  const loadVoices = () => { voices = "speechSynthesis" in window ? speechSynthesis.getVoices() : []; };
  if ("speechSynthesis" in window) { loadVoices(); speechSynthesis.onvoiceschanged = loadVoices; }

  function pickVoice(l) {
    const order = l === "ms" ? ["ms", "id"] : ["en-MY", "en-SG", "en-GB", "en"];
    for (const p of order) { const v = voices.find((x) => x.lang.replace("_", "-").startsWith(p)); if (v) return v; }
    return null;
  }

  function speak(text, l, { pitch = 1, rate = 1 } = {}) {
    if (!("speechSynthesis" in window)) return sleep(Math.max(1500, text.split(" ").length * 380));
    return new Promise((resolve) => {
      const u = new SpeechSynthesisUtterance(text);
      const v = pickVoice(l);
      if (v) u.voice = v;
      u.lang = v ? v.lang : (l === "ms" ? "ms-MY" : "en-GB");
      u.pitch = pitch; u.rate = rate;
      let done = false;
      const finish = () => { if (!done) { done = true; resolve(); } };
      u.onend = finish; u.onerror = finish;
      setTimeout(finish, text.split(" ").length * 650 + 4000); // some browsers never fire onend
      speechSynthesis.speak(u);
    });
  }

  // ---------------------------------------------------------------- transcript input
  function addLine(speaker, text) {
    text = (text || "").trim();
    if (!text) return;
    lines.push({ speaker, text });
    renderTranscript();
    requestAnalysis();
  }

  async function runDemo(mySession) {
    const sc = scenario();
    if (!sc) return;
    await sleep(600);
    for (const line of sc.lines) {
      if (mySession !== session) return;
      addLine(line.speaker, line.text);
      if ($("speakCaller").checked) {
        await speak(line.text, sc.lang, line.speaker === "you" ? { pitch: 1.35, rate: 1.05 } : { pitch: 0.85, rate: 1 });
      } else {
        await sleep(Math.max(1800, line.text.split(" ").length * 330));
      }
      await warningDone;
      await sleep(350);
    }
    if (mySession === session) setTimeout(() => { if (mySession === session) stop(); }, 1500);
  }

  function runBrowserSpeech(mySession) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { $("modeHint").textContent = t("noSpeech"); stop(); return; }
    recognizer = new SR();
    recognizer.lang = lang === "ms" ? "ms-MY" : "en-MY";
    recognizer.continuous = true;
    recognizer.interimResults = true;
    recognizer.onresult = (e) => {
      interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) addLine("mic", r[0].transcript); else interim += r[0].transcript;
      }
      renderTranscript();
    };
    recognizer.onerror = (e) => {
      if (e.error === "not-allowed" || e.error === "service-not-allowed") { $("modeHint").textContent = t("micDenied"); stop(); }
    };
    recognizer.onend = () => { if (mySession === session && phase === "live") { try { recognizer.start(); } catch { /* already started */ } } };
    recognizer.start();
  }

  async function runGemini(mySession) {
    try {
      media = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: true } });
    } catch {
      $("modeHint").textContent = t("micDenied"); stop(); return;
    }
    let queue = Promise.resolve();
    while (mySession === session && phase === "live") {
      const blob = await recordChunk(media, 6000);
      if (!blob || !blob.size) continue;
      queue = queue.then(() => transcribeChunk(blob, mySession));
    }
  }

  function recordChunk(stream, ms) {
    return new Promise((resolve) => {
      const rec = new MediaRecorder(stream);
      const parts = [];
      rec.ondataavailable = (e) => e.data.size && parts.push(e.data);
      rec.onstop = () => resolve(new Blob(parts, { type: rec.mimeType }));
      rec.start();
      setTimeout(() => rec.state !== "inactive" && rec.stop(), ms);
    });
  }

  // Gemini accepts WAV everywhere; browsers record WebM/Ogg/MP4, so convert to 16 kHz mono WAV.
  async function toWav(blob) {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const decoded = await ctx.decodeAudioData(await blob.arrayBuffer());
    ctx.close();
    const rate = 16000;
    const off = new OfflineAudioContext(1, Math.ceil(decoded.duration * rate), rate);
    const src = off.createBufferSource();
    src.buffer = decoded; src.connect(off.destination); src.start();
    const pcm = (await off.startRendering()).getChannelData(0);
    const buf = new ArrayBuffer(44 + pcm.length * 2), v = new DataView(buf);
    const w = (o, s) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
    w(0, "RIFF"); v.setUint32(4, 36 + pcm.length * 2, true); w(8, "WAVE"); w(12, "fmt ");
    v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
    v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true);
    w(36, "data"); v.setUint32(40, pcm.length * 2, true);
    for (let i = 0; i < pcm.length; i++) { const s = Math.max(-1, Math.min(1, pcm[i])); v.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true); }
    return new Blob([buf], { type: "audio/wav" });
  }

  async function transcribeChunk(blob, mySession) {
    try {
      const fd = new FormData();
      fd.append("audio", await toWav(blob), "chunk.wav");
      const res = await fetch("/api/transcribe", { method: "POST", body: fd });
      if (res.status === 503) { $("modeHint").textContent = t("hintNoKey"); stop(); return; }
      if (!res.ok) return;
      const { text } = await res.json();
      if (mySession === session) addLine("mic", text);
    } catch (err) { console.warn(err); }
  }

  // ---------------------------------------------------------------- session control
  function start() {
    session++;
    phase = "live"; lines = []; interim = ""; analysis = null; shownLevel = "low"; warned = false;
    warningDone = Promise.resolve();
    $("reportBtn").disabled = false; $("reportBtn").textContent = t("reportBtn");
    render();
    const m = mode();
    if (m === "demo") runDemo(session);
    else if (m === "browser") runBrowserSpeech(session);
    else runGemini(session);
  }

  function stop() {
    if (phase !== "live") return;
    session++;
    phase = "done"; interim = "";
    if (recognizer) { try { recognizer.onend = null; recognizer.stop(); } catch { /* noop */ } recognizer = null; }
    if (media) { media.getTracks().forEach((tr) => tr.stop()); media = null; }
    if ("speechSynthesis" in window && !warned) speechSynthesis.cancel();
    $("reportBtn").hidden = !analysis || analysis.level === "low";
    $("reportNote").hidden = $("reportBtn").hidden;
    render();
  }

  function reset() {
    session++;
    phase = "idle"; lines = []; analysis = null; shownLevel = "idle";
    if ("speechSynthesis" in window) speechSynthesis.cancel();
    render();
  }

  function whatsappLink() {
    const a = analysis || { risk: 0, tactics: [], lookups: [] };
    const msg = t("waText")({
      type: lang === "ms" ? a.scam_type_ms || a.scam_type : a.scam_type,
      pct: Math.round((a.risk || 0) * 100),
      tactics: a.tactics.slice(0, 3).map((x) => (lang === "ms" ? x.label_ms : x.label_en).toLowerCase()).join("; "),
      numbers: (a.lookups || []).map(formatNumber).join(", "),
    });
    const num = ($("family").value || "").replace(/\D/g, "");
    return `https://wa.me/${num}?text=${encodeURIComponent(msg)}`;
  }

  async function sendReport() {
    if (!analysis) return;
    const btn = $("reportBtn");
    btn.disabled = true;
    try {
      const res = await fetch("/api/report", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ analysis }) });
      btn.textContent = res.ok ? t("reportSent") : t("netError");
    } catch { btn.textContent = t("netError"); btn.disabled = false; }
  }

  // ---------------------------------------------------------------- wiring
  $("startBtn").addEventListener("click", start);
  $("stopBtn").addEventListener("click", stop);
  $("againBtn").addEventListener("click", reset);
  $("reportBtn").addEventListener("click", sendReport);
  document.querySelectorAll(".lang button").forEach((b) => b.addEventListener("click", () => {
    lang = b.dataset.lang; store.set("lang", lang); applyStrings();
  }));
  document.querySelectorAll('input[name="mode"]').forEach((r) => r.addEventListener("change", () => {
    store.set("mode", mode());
    $("scenarioField").hidden = mode() !== "demo";
    $("speakCaller").parentElement.hidden = mode() !== "demo";
    renderVerdict();
  }));
  $("scenario").addEventListener("change", () => { store.set("scenario", $("scenario").value); renderVerdict(); });
  $("family").value = store.get("family", "");
  $("family").addEventListener("change", () => { store.set("family", $("family").value); renderVerdict(); });

  const savedMode = store.get("mode", "demo");
  const radio = document.querySelector(`input[name="mode"][value="${savedMode}"]`);
  if (radio) radio.checked = true;
  $("scenarioField").hidden = mode() !== "demo";
  $("speakCaller").parentElement.hidden = mode() !== "demo";

  // Deep links for recording the demo: /?demo=police-bukit-aman&lang=en&autostart=1
  const params = new URLSearchParams(location.search);
  if (params.get("lang") === "en" || params.get("lang") === "ms") lang = params.get("lang");

  Promise.all([
    fetch("/api/health").then((r) => r.json()).catch(() => health),
    fetch("/api/scenarios").then((r) => r.json()).catch(() => []),
  ]).then(([h, sc]) => {
    health = h; scenarios = sc;
    applyStrings();
    if (params.get("demo")) {
      document.querySelector('input[name="mode"][value="demo"]').checked = true;
      $("scenario").value = params.get("demo");
      $("scenarioField").hidden = false;
      if (params.get("voice") === "0") $("speakCaller").checked = false;
      renderVerdict();
      if (params.get("autostart") === "1") start();
    }
  });
  applyStrings();

  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
})();
