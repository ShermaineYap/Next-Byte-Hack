"""Deterministic scam-tactic detector for Malay, English and Manglish call transcripts.

This is the "rule floor": it runs instantly, needs no API key, and keeps the app
useful when the LLM is slow, rate-limited or offline. The taxonomy follows the
tactics PDRM and the National Scam Response Centre (NSRC) warn about publicly:
impersonating an authority, inventing an offence, threats and urgency, secrecy,
moving money to a "safe account", harvesting OTP/TAC codes, remote-access apps,
and too-good-to-be-true offers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Taxonomy
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Tactic:
    id: str
    label_en: str
    label_ms: str
    weight: float
    patterns: tuple[str, ...]
    negatable: bool = False  # "we will NEVER ask for your OTP" should not count


TACTICS: tuple[Tactic, ...] = (
    Tactic(
        "authority",
        "Claims to be police, government or a regulator",
        "Mengaku sebagai polis, kerajaan atau badan kawal selia",
        0.35,
        (
            r"\bpolis\b", r"\bpolice\b", r"\bpdrm\b", r"bukit aman", r"\binsp[ei]ct?or\b",
            r"\binspektor\b", r"\bsarjan\b", r"\bsergeant\b", r"\bkoperal\b", r"\bcorporal\b",
            r"\blhdn\b", r"hasil dalam negeri", r"inland revenue", r"bank negara", r"\bbnm\b",
            r"\bmahkamah\b", r"\bcourt\b", r"\bmcmc\b", r"\bkastam\b", r"\bcustoms\b",
            r"jabatan siasatan", r"commercial crime", r"\bjsjk\b", r"\bsprm\b", r"\bmacc\b",
            r"\bpendakwa raya\b", r"\bprosecutor\b",
        ),
    ),
    Tactic(
        "fabricated_offence",
        "Says you are linked to a crime or investigation",
        "Mendakwa anda terlibat dalam jenayah atau siasatan",
        0.35,
        (
            r"pengubahan wang haram", r"money[- ]laundering", r"\bamla\b", r"\bdadah\b",
            r"\bdrugs?\b", r"illegal (items?|goods|substances?)", r"barang(an)? (terlarang|haram)",
            r"terlibat (dalam|dengan) (satu )?(kes|jenayah|sindiket|siasatan)",
            r"involved in (a |an )?(case|crime|syndicate|investigation|fraud)",
            r"(nombor|akaun|kad pengenalan|mykad|nama|ic) (telefon )?(anda|awak|puan|encik|tuan)\s+(telah\s+)?"
            r"(digunakan|disalahgunakan|dikaitkan|didaftarkan)",
            r"your (phone )?(number|account|ic|identity|name|mykad) (was|has been|have been|is being) "
            r"(used|misused|linked|registered)",
            r"\bsindiket\b", r"\bsyndicate\b", r"kes jenayah", r"criminal case", r"\bsiasatan\b",
            r"under investigation",
        ),
    ),
    Tactic(
        "threat_urgency",
        "Threats, arrest warnings or pressure to act now",
        "Ugutan, amaran tangkap atau desakan bertindak segera",
        0.25,
        (
            r"\bwaran(t)?\b", r"ditangkap", r"\btangkap\b", r"\barrest(ed)?\b", r"\bpenjara\b",
            r"\bjail\b", r"\bprison\b",
            r"(akaun|account|wang|duit|simpanan|savings).{0,25}(dibekukan|dibeku|dibekukan|beku|frozen|freeze|disekat)",
            r"senarai hitam", r"blacklist", r"dalam (masa )?\d+ (jam|minit)", r"within \d+ (hours?|minutes?)", r"\bin \d+ (minutes?|hours?)\b",
            r"\bsegera\b", r"\bimmediately\b", r"\burgent(ly)?\b", r"sekarang juga", r"right now",
            r"hari ini juga", r"\bsaman\b", r"last chance", r"peluang terakhir",
        ),
    ),
    Tactic(
        "secrecy",
        "Tells you to keep it secret or stay on the line",
        "Menyuruh anda merahsiakan atau jangan letak telefon",
        0.35,
        (
            r"jangan (beritahu|bagitahu|bagitau|cakap|maklumkan|bincang)",
            r"(don'?t|do not) (tell|inform|discuss with)", r"\brahsia\b", r"\bsulit\b", r"confidential",
            r"(keep|kept) (this|it) (secret|private|between)", r"jangan letak (telefon|phone|fon)",
            r"(don'?t|do not) hang up", r"stay on the line", r"jangan (tutup|matikan) (telefon|panggilan)",
            r"seorang diri", r"by yourself", r"(masuk|pergi) (ke )?(dalam )?bilik",
        ),
    ),
    Tactic(
        "money_transfer",
        "Asks you to move money to another account",
        "Meminta anda memindahkan wang ke akaun lain",
        0.45,
        (
            r"akaun selamat", r"safe(ty)? account",
            r"\b(pindah|pindahkan|transfer|hantar|masukkan|deposit|bank[- ]?in|bayar|pay)\b.{0,40}"
            r"\b(wang|duit|money|simpanan|savings|semua|all|rm ?\d+|ringgit|deposit|fee|yuran)\b",
            r"\b(wang|duit|money|simpanan|savings)\b.{0,30}\b(pindah|pindahkan|transfer|keluarkan|withdraw)\b",
            r"akaun (pegawai|amanah|sementara|kerajaan|bank negara|siasatan|pihak ketiga)",
            r"(trust|government|temporary|holding|escrow|investigation|third[- ]party) account",
            r"\bbitcoin\b", r"\bcrypto\b", r"\busdt\b", r"(gift card|kad hadiah|kad tambah nilai)",
            r"keluarkan (wang|duit|semua)", r"withdraw (all|your)",
        ),
        negatable=True,
    ),
    Tactic(
        "credentials",
        "Asks for OTP, TAC, PIN or banking passwords",
        "Meminta OTP, TAC, PIN atau kata laluan perbankan",
        0.6,
        (
            r"\b(otp|tac)\b", r"kod (pengesahan|keselamatan|tac|otp)",
            r"(verification|security|one[- ]time) (code|password|pin)", r"\bpin\b", r"kata laluan",
            r"\bpassword\b", r"\bcvv\b", r"nombor kad (bank|kredit|debit|atm)", r"card number",
            r"(username|nama pengguna|user id).{0,25}(bank|banking)",
            r"online banking.{0,30}(login|log masuk|password|kata laluan|username)",
        ),
        negatable=True,
    ),
    Tactic(
        "remote_access",
        "Asks you to install an app or open a link",
        "Meminta anda memasang aplikasi atau membuka pautan",
        0.4,
        (
            r"\banydesk\b", r"teamviewer", r"\bapk\b",
            r"(muat turun|download|install|pasang).{0,30}(aplikasi|app|apk|software|perisian)",
            r"(klik|click|tekan|buka|open).{0,20}(pautan|link|url)", r"screen ?shar(e|ing)", r"kongsi skrin",
        ),
        negatable=True,
    ),
    Tactic(
        "too_good",
        "Promises prizes or guaranteed returns",
        "Menjanjikan hadiah atau pulangan terjamin",
        0.35,
        (
            r"pulangan.{0,20}(dijamin|tetap|\d+ ?(%|peratus))", r"guaranteed (returns?|profits?|income)",
            r"(untung|profit|keuntungan|returns?).{0,20}\d+ ?(%|peratus|percent)", r"you (have )?won",
            r"anda (telah )?(menang|memenangi)", r"\bhadiah\b", r"\bprize\b", r"cabutan bertuah",
            r"lucky draw", r"\bpelaburan\b", r"investment (scheme|plan|opportunity|package)",
            r"(free|percuma) (gift|hadiah)", r"processing fee", r"yuran (pemprosesan|proses|pendaftaran)",
            r"double your money", r"gandakan (wang|duit)",
        ),
    ),
)

TACTIC_BY_ID = {t.id: t for t in TACTICS}

# Pairs that together form the classic Malaysian phone-scam scripts.
COMBOS: tuple[tuple[frozenset[str], float], ...] = (
    (frozenset({"authority", "money_transfer"}), 0.25),
    (frozenset({"authority", "credentials"}), 0.2),
    (frozenset({"fabricated_offence", "secrecy"}), 0.15),
    (frozenset({"too_good", "money_transfer"}), 0.15),
    (frozenset({"credentials", "threat_urgency"}), 0.15),
)

# Scam "family" names, checked in priority order once risk is at least "caution".
SCAM_TYPES: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    ("lhdn", "Tax office (LHDN) impersonation", "Penyamaran LHDN (cukai)", (r"\blhdn\b", r"hasil dalam negeri", r"inland revenue", r"\bcukai\b", r"\btax\b")),
    ("parcel", "Parcel / courier scam", "Penipuan bungkusan / kurier", (r"\bparcel\b", r"bungkusan", r"pos ?laju", r"\bkurier\b", r"\bcourier\b", r"\bdhl\b", r"\bj&t\b")),
    ("telco", "Telco / MCMC impersonation", "Penyamaran telco / MCMC", (r"\bmcmc\b", r"(line|talian).{0,30}(disconnected|diputuskan|cut|ditamatkan)", r"\btelco\b")),
    ("police", "Police impersonation (Macau scam)", "Penyamaran polis (Macau scam)", (r"\bpolis\b", r"\bpolice\b", r"\bpdrm\b", r"bukit aman", r"\bsarjan\b", r"\bsergeant\b", r"\binspektor\b", r"\binspector\b", r"\bwaran", r"\bwarrant\b")),
    ("investment", "Investment scam", "Penipuan pelaburan", (r"pelaburan", r"investment", r"\bcrypto\b", r"\bbitcoin\b", r"\bforex\b", r"guaranteed returns?", r"pulangan")),
    ("prize", "Prize / lucky-draw scam", "Penipuan hadiah / cabutan bertuah", (r"\bhadiah\b", r"\bprize\b", r"lucky draw", r"cabutan bertuah", r"you (have )?won", r"menang")),
    ("bank", "Bank impersonation", "Penyamaran bank", (r"\bmaybank\b", r"\bcimb\b", r"public bank", r"\brhb\b", r"hong leong", r"\bbsn\b", r"card cent(re|er)", r"\bkad (kredit|debit)\b", r"credit card", r"\bbank\b(?![- ]?in\b)")),
)

_NEGATOR = re.compile(
    r"\b(never|tidak akan|tak akan|takkan|will not|won'?t|don'?t|do not|jangan|tidak pernah|tak pernah|"
    r"bukan|no one|nobody|tidak sesekali|not ask|tak minta|tidak minta|never ask)\b"
)
# "jangan risau" (don't worry) is reassurance, not negation: scammers say it constantly.
_REASSURANCE = re.compile(r"\b(jangan (risau|takut|panik|bimbang)|don'?t (worry|panic|be afraid)|do not (worry|panic))\b")
_SENTENCE_BREAK = re.compile(r"[.!?;\n]")

LEVELS = (("low", 0.0), ("caution", 0.35), ("high", 0.7))

ADVICE = {
    "high": {
        "ms": "Amaran: ini mungkin panggilan penipuan. Polis, LHDN dan bank tidak akan meminta anda memindahkan wang "
        "atau memberi kod TAC. Letak telefon sekarang. Jika wang sudah dipindahkan, hubungi 997 (NSRC) segera.",
        "en": "Warning: this is likely a scam call. Police, LHDN and banks will never ask you to move money or share a "
        "TAC code. Hang up now. If money has already been sent, call 997 (NSRC) immediately.",
    },
    "caution": {
        "ms": "Berhati-hati. Jangan pindahkan wang atau beri sebarang kod. Letak telefon dan hubungi sendiri organisasi "
        "itu menggunakan nombor rasmi mereka.",
        "en": "Be careful. Do not send money or share any code. Hang up and call the organisation yourself on its "
        "official number.",
    },
    "low": {
        "ms": "Tiada tanda penipuan dikesan setakat ini. Teruskan berhati-hati.",
        "en": "No scam signs detected so far. Stay alert.",
    },
}


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

_COMPILED = {t.id: tuple(re.compile(p, re.IGNORECASE) for p in t.patterns) for t in TACTICS}
_SCAM_TYPE_COMPILED = tuple((k, en, ms, tuple(re.compile(p, re.IGNORECASE) for p in ps)) for k, en, ms, ps in SCAM_TYPES)


@dataclass
class TacticHit:
    id: str
    label_en: str
    label_ms: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class RuleResult:
    risk: float
    level: str
    tactics: list[TacticHit]
    scam_type: str | None
    scam_type_ms: str | None
    negated: list[str]  # evidence phrases ignored because the speaker negated them

    def to_dict(self) -> dict:
        return {
            "risk": round(self.risk, 3),
            "level": self.level,
            "tactics": [t.__dict__ for t in self.tactics],
            "scam_type": self.scam_type,
            "scam_type_ms": self.scam_type_ms,
            "negated": self.negated,
        }


def level_for(risk: float) -> str:
    level = "low"
    for name, threshold in LEVELS:
        if risk >= threshold:
            level = name
    return level


def _is_negated(text: str, start: int) -> bool:
    """True if a negator sits in the same sentence, shortly before the match."""
    window_start = max(0, start - 60)
    window = text[window_start:start]
    breaks = list(_SENTENCE_BREAK.finditer(window))
    if breaks:
        window = window[breaks[-1].end():]
    window = _REASSURANCE.sub(" ", window)
    return bool(_NEGATOR.search(window))


def score_tactics(found: set[str]) -> float:
    remaining = 1.0
    for tid in found:
        remaining *= 1.0 - TACTIC_BY_ID[tid].weight
    risk = 1.0 - remaining
    for pair, bonus in COMBOS:
        if pair <= found:
            risk += bonus
    return min(risk, 0.99)


def classify_scam_type(text: str) -> tuple[str | None, str | None]:
    for _key, en, ms, patterns in _SCAM_TYPE_COMPILED:
        if any(p.search(text) for p in patterns):
            return en, ms
    return None, None


def analyze_rules(transcript: str) -> RuleResult:
    text = transcript or ""
    hits: list[TacticHit] = []
    negated: list[str] = []
    for tactic in TACTICS:
        evidence: list[str] = []
        for pattern in _COMPILED[tactic.id]:
            for m in pattern.finditer(text):
                phrase = m.group(0).strip()
                if tactic.negatable and _is_negated(text, m.start()):
                    if phrase not in negated:
                        negated.append(phrase)
                    continue
                if phrase and phrase.lower() not in (e.lower() for e in evidence):
                    evidence.append(phrase)
        if evidence:
            hits.append(TacticHit(tactic.id, tactic.label_en, tactic.label_ms, evidence[:6]))

    risk = score_tactics({h.id for h in hits}) if hits else 0.0
    level = level_for(risk)
    scam_type, scam_type_ms = classify_scam_type(text) if level != "low" else (None, None)
    return RuleResult(risk, level, hits, scam_type, scam_type_ms, negated)
