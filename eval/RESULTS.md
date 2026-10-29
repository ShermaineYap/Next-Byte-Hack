# Evaluation results (rules engine only)

- Scam calls flagged high-risk: **6 of 6**
- False alarms on legitimate calls: **0 of 4** (1 shown as 'be careful')
- Average time to first warning on scam calls: **~31 s** of speech (at 2.5 words/s)

| Call | Expected | ScamShield verdict | Risk | Scam type | Warning after | Correct |
| --- | --- | --- | --- | --- | --- | --- |
| "Sergeant" from Bukit Aman | scam | high | 0.99 | Police impersonation (Macau scam) | line 7/9 (~33 s) | yes |
| LHDN tax arrears | scam | high | 0.99 | Tax office (LHDN) impersonation | line 6/7 (~37 s) | yes |
| "Card centre" asks for TAC | scam | high | 0.85 | Bank impersonation | line 5/6 (~31 s) | yes |
| Parcel held by customs | scam | high | 0.99 | Parcel / courier scam | line 5/6 (~29 s) | yes |
| "MCMC": your line will be cut | scam | high | 0.99 | Telco / MCMC impersonation | line 4/5 (~30 s) | yes |
| Guaranteed-returns investment | scam | high | 0.99 | Investment scam | line 4/5 (~25 s) | yes |
| Real bank fraud-desk check | legit | low | 0.00 | — | — | yes |
| Clinic appointment reminder | legit | low | 0.00 | — | — | yes |
| Delivery rider at the guardhouse | legit | low | 0.00 | — | — | yes |
| Son asks for RM50 for parking | legit | caution | 0.45 | — | — | yes |

Calls are scripted by the team (see `app/data/scenarios.json`) from patterns in PDRM/NSRC advisories, so this is a functional test, not a field accuracy claim. 'Caution' on a legitimate call (e.g. a family member asking for money) is counted as correct: the app says 'be careful', not 'scam'.
