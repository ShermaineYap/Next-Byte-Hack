# Demo video script (target 2:45)

The rules page asks for 2–5 minutes and the overview says 1–3, so 2:45 satisfies both.

**Setup before recording**

- Run `python -m scripts.seed_demo_reports` so the dashboard has data, then `uvicorn app.main:app`.
- Chrome, window about 1280×860, zoom 100%. Turn on "Play the caller's voice" in Settings so the call is audible.
- Optional phone shot: open the deployed URL on your phone and film it next to the laptop.
- Hands-free start for clean takes: `http://localhost:8000/?demo=police-bukit-aman&lang=en&autostart=1`

| Time | On screen | Voiceover |
| --- | --- | --- |
| 0:00–0:15 | Black screen, phone ringing sound, then the line "RM2.97 billion lost to scams in Malaysia in 2025" | "Last year Malaysians lost almost three billion ringgit to scams. Many of the victims were over sixty, on the phone with someone pretending to be the police." |
| 0:15–0:35 | Headline of the Kuching "Sergeant Tan" story; Semak Mule homepage | "A 72-year-old in Kuching lost 1.3 million ringgit to a 'Sergeant Tan'. The warnings exist, but nobody checks them during the call, when the caller is saying: don't hang up, don't tell your children." |
| 0:35–0:45 | ScamShield ready screen | "This is ScamShield. You put the call on speaker and tap one button." |
| 0:45–1:45 | Press **Check this call** (Bukit Aman demo). Let it run uncut: transcript scrolls, phrases highlight, screen goes amber, then red, the spoken warning plays, the account number shows "Reported 3 times" | Mostly silent, let the call play. One line when it turns red: "Thirty seconds in, before the money moves, it tells her to hang up, out loud, in Bahasa." |
| 1:45–1:55 | Tap **Alert my family**, show the WhatsApp message | "One tap tells her daughter what happened and which account the caller gave." |
| 1:55–2:10 | Switch to **Real bank fraud-desk check**, run it: stays green | "It also knows when not to panic. A real bank says it will never ask for your OTP, and ScamShield stays green." |
| 2:10–2:25 | README architecture diagram, then `eval/RESULTS.md` table | "Under the hood: a rules engine for Malay, English and Manglish, and Gemini as a second analyst that must quote the exact words it relies on. On ten test calls: six of six scams caught, zero false alarms." |
| 2:25–2:40 | Community dashboard | "Every report is anonymous, no audio, no transcript, just tactics and numbers, so new scam scripts and mule accounts show up in hours, not weeks." |
| 2:40–2:45 | Ready screen, big button | "ScamShield. Letak telefon, before it's too late." |

**Recording tips**

- Record the demo section as one continuous take; judges trust an uncut demo.
- Add captions; many judges watch muted.
- Upload to YouTube as Unlisted and paste the link on Devpost.
