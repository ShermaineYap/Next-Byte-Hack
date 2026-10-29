# Devpost submission (copy-paste ready)

**Project name:** ScamShield MY

**Tagline (max 200 chars):** A real-time phone-scam co-pilot for Malaysian seniors: it listens to a suspicious call on speaker, spots scam tactics as they happen, and tells you to hang up before the money moves.

**Built with (tags):** python, fastapi, gemini, javascript, pwa, web-speech-api, sqlite, pytest

**Links:** GitHub repo · demo video (YouTube) · live demo URL (if deployed)

**Screenshots to upload, in this order:** `docs/screenshots/3-scam-warning.png`, `4-mobile-amaran.png`, `5-legit-bank-call.png`, `2-caution.png`, `6-community-dashboard.png`, `1-ready.png`

---

## Inspiration

In November 2025 a 72-year-old woman in Kuching lost more than RM1.3 million to a man on the phone who called himself "Sergeant Tan". He told her that her IC had been used for money laundering, that there was a warrant for her arrest, and that she must not tell her children. Then he gave her a "safe account".

Her story is not unusual. Malaysians lost RM2.97 billion to scams in 2025, almost double the year before, and only RM10.9 million has ever been returned. Phone scams alone accounted for over 5,097 cases and RM241 million last year.

The warnings already exist: PDRM advisories, the Semak Mule portal, the 997 hotline. But nobody checks them *during* the call, while a confident voice is telling you to stay on the line and keep it secret. We wanted something that sits in the room with our grandparents at exactly that moment.

## What it does

ScamShield is a web app a senior opens when a call feels wrong.

1. **Tap one big button** ("Semak panggilan ini") and put the call on speaker.
2. **ScamShield transcribes the call live**, in Malay, English or Manglish, and highlights scam phrases as they are spoken: *akaun selamat*, *jangan beritahu sesiapa*, *waran tangkap*.
3. **A risk meter climbs** as it recognises eight tactics from PDRM and NSRC advisories: impersonating police or LHDN, inventing a crime, threats and urgency, secrecy, moving money, asking for OTP/TAC, remote-access apps, and too-good-to-be-true offers.
4. **Numbers are checked**: any account or phone number the caller reads out is extracted and checked against a mule-account registry, with a link to PDRM Semak Mule.
5. **When it is sure, the whole screen turns red**: "Ini penipuan. Letak telefon." It speaks the warning out loud, vibrates, and offers one tap to WhatsApp a family member (with the scam type and numbers) or call 997.
6. **After the call**, one tap sends an anonymous report (tactics and numbers only, never audio or transcript) to a community dashboard showing which scripts and mule accounts are active right now.

It also knows when *not* to panic: a real Maybank fraud-desk call that says "we will never ask for your OTP" stays green, and a son asking his mum for RM50 for parking gets "be careful", not "scam".

## How we built it

- **Backend:** Python + FastAPI. One `/api/analyze` endpoint merges three signals into a single verdict.
- **Rules engine:** a hand-built taxonomy of eight tactics with Malay, English and Manglish patterns, negation handling ("will *never* ask you to transfer" does not count, but "*jangan risau*, pindahkan..." still does) and combination scoring for the classic scripts (authority + safe account = Macau scam).
- **Gemini analyst:** the same transcript goes to Gemini with a Malaysian scam-pattern prompt and a strict JSON response schema (risk, tactics, evidence, explanation in BM and English). Every evidence phrase must appear verbatim in the transcript or it is discarded, so the model cannot invent a reason. The final risk is the higher of rules and Gemini, so the app keeps working if the model is slow or rate-limited.
- **Speech:** three modes: scripted demo calls (with the caller's voice played through text-to-speech), the browser's built-in speech recognition, and Gemini transcription, for which the browser records 6-second chunks and converts them to 16 kHz WAV with the Web Audio API.
- **Front end:** a dependency-free installable PWA designed for older eyes: Atkinson Hyperlegible (a typeface the Braille Institute designed for low-vision readers), huge tap targets, and a whole-screen colour state you can read from across a table.
- **Reports:** anonymous SQLite reports and a dashboard of tactics, scam types and reported numbers.
- **Testing:** 23 pytest tests (Gemini mocked), an evaluation script that replays 10 scripted calls line by line, and an end-to-end browser test of the Gemini audio path against a mock server.
- We used AI coding assistants during development and wrote all code during the hackathon.

## Challenges we ran into

- **Manglish.** Real calls switch language mid-sentence ("Aunty, your akaun will be frozen kalau tak settle today"). We wrote patterns for both languages per tactic and let Gemini handle what rules miss.
- **Legitimate calls sound like scams.** Banks really do call about card transactions, and they say "OTP" and "transfer" in every call, only negated. Negation handling, and refusing to let "jangan risau" count as a negation, took several iterations.
- **Semak Mule has no public API** and is protected against automated queries. We did not scrape it; the prototype uses a clearly labelled demo registry and links to the official portal, with a clean interface ready for an official data feed.
- **Browser audio formats.** Browsers record WebM, Ogg or MP4; we convert every chunk to 16 kHz mono WAV in the browser so transcription works everywhere.

## Accomplishments that we're proud of

- **6 of 6 scam calls flagged, 0 false alarms on 4 legitimate calls**, with the first warning about 30 seconds into the call, in most calls before the caller has finished giving the "safe account" details.
- It works with **no API key at all** (rules + browser speech), so anyone can run it and judges can try it in one click.
- A UI built for someone who has never used an app like this: one button, two languages, and a red screen that says exactly what to do.

## What we learned

- Scam calls follow remarkably consistent scripts; a small, well-chosen taxonomy catches most of them, and the LLM's job is the long tail and the explanation.
- Designing for seniors is mostly subtraction: one action per screen, words over icons, and the instruction ("hang up") bigger than the analysis.
- Telling people *why* matters. Showing the exact phrases the caller used makes the warning believable.

## What's next for ScamShield MY

- Android dialer integration so protection starts automatically on calls from unknown numbers.
- Sharing anonymous reports with the National Scam Response Centre so new scripts and mule accounts surface within hours of the first call.
- On-device transcription (Whisper on WebGPU) so audio never leaves the phone.
- Chinese and Tamil support.

## Team

Shermaine Yap Shi Min, Asia Pacific University of Technology and Innovation (APU), Malaysia.
