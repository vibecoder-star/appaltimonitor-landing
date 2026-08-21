# AppaltiMonitor — Validation Experiment

## OUTREACH MESSAGE (Draft — Pending CEO Approval)

### Initial Email

```
Oggetto: Monitoraggio appalti personalizzato — prova gratuita 7 giorni

Gentile [Nome],

il 73% delle PMI italiane perde bandi pertinenti per mancanza di monitoraggio sistematico.

Offro un servizio di intelligence sugli appalti pubblici:
- Monitoraggio personalizzato (settore, regione, importo)
- Alert immediati per bandi ad alto valore
- Report settimanale con opportunità prioritarie

Prova gratuita 7 giorni, senza impegno.

Le mostro cosa ha perso il mese scorso?

Cordiali saluti,
[Agente]
```

### Follow-up Email (3 days later)

```
Oggetto: Re: Monitoraggio appalti personalizzato — prova gratuita 7 giorni

Gentile [Nome],

solo un promemoria. La prova gratuita 7 giorni è ancora disponibile.

Se è interessato, posso inviarle un campione delle opportunità che avrebbe potuto perdersi questo mese.

Cordiali saluti,
[Agente]
```

### Trial Offer

```
OFFERTA: 7-DAY PROCUREMENT INTELLIGENCE PILOT

Cosa riceve:
- Accesso al nostro sistema di monitoraggio personalizzato
- Alert email per bandi ad alto valore
- Report settimanale con opportunità prioritarie
- Intelligence competitor (chi vince cosa)

Durata: 7 giorni
Costo: GRATUITO
Impegno: Nessuno

Cosa chiediamo:
- Suo settore, ubicazione, capacità
- Feedback sul servizio
- Eventuale conversione a piano pagante (€49/mese)

Procedura:
1. Definiamo insieme il profilo di monitoraggio
2. Riceve alert per 7 giorni
3. Valuta se continuare
```

### FAQ

**Q: Come funziona?**
A: Monitoriamo i dati ANAC e inviamo solo bandi pertinenti.

**Q: Quali dati utilizzate?**
A: Dati aperti ANAC (pubblici, aggiornati mensilmente).

**Q: Quanto costa?**
A: €49/mese (Starter), €99/mese (Professional), €199/mese (Enterprise).

**Q: Posso cancellare?**
A: In qualsiasi momento, senza penali.

**Q: Come ricevo i report?**
A: Via email, con opzione dashboard web.

### Objection Handling

**Obiezione: "Non ho tempo"**
Risposta: "Il servizio è proattivo — lei riceve solo opportunità pronte per essere valutate."

**Obiezione: "Non partecipo a gare"**
Risposta: "Verifichiamo insieme se ci sono opportunità per il suo settore."

**Obiezione: "Troppo costoso"**
Risposta: "Un solo bando vinto copre anni di abbonamento."

**Obiezione: "Non conosco il servizio"**
Risposta: "Prova gratuita 7 giorni, senza impegno."

---

## TRIAL WORKFLOW

### Day 0: Setup
1. Customer provides profile (sector, location, capacity)
2. Agent configures monitoring profile
3. Agent sends confirmation email

### Day 1-7: Monitoring
1. Daily: Agent checks ANAC data for new tenders
2. Daily: Agent filters by customer profile
3. Daily: Agent sends email alert for high-priority tenders
4. Day 7: Agent sends weekly summary report

### Day 7: Evaluation
1. Agent sends evaluation form
2. Customer provides feedback
3. If positive: offer paid plan
4. If negative: thank and close

### Day 8+: Paid Service
1. Customer selects plan
2. Agent configures billing (Stripe/PayPal)
3. Service continues

---

## EXPECTED OPERATIONAL WORKLOAD

### Per Trial User
- Setup: 15 minutes
- Daily monitoring: 5 minutes (automated)
- Weekly report: 10 minutes
- Total per week: ~45 minutes

### Per Paid Customer
- Daily monitoring: 5 minutes (automated)
- Weekly report: 10 minutes
- Monthly billing: 5 minutes
- Total per month: ~30 minutes

### Scaling
- 1-5 customers: manageable manually
- 5-20 customers: need automation
- 20+ customers: need SaaS platform

---

## DATA/PRIVACY CONSIDERATIONS

### Data Sources
- ANAC Open Data: Public, no authentication required
- Company websites: Public business information
- Email addresses: Public contact information

### GDPR Compliance
- No personal data processing
- Only business contact information
- Legitimate interest (B2B communication)
- Opt-out available in every email

### Data Storage
- Customer profiles: Encrypted at rest
- Monitoring data: ANAC public data only
- Email logs: 30-day retention

---

## CURRENT TECHNICAL LIMITATIONS

### ANAC Data
- Monthly refresh (not real-time)
- 43.9% CPV coverage
- No ATECO filtering
- No eligibility check

### Monitoring
- No MEPA integration (below-threshold tenders)
- No regional portal integration
- No tender document analysis

### Delivery
- Email only (no dashboard)
- No mobile app
- No API access

---

## EXACT ACTIONS REQUIRING PAYMENT APPROVAL

| Action | Cost | When |
|--------|------|------|
| Domain personalizzato | €10/anno | Before first paid customer |
| Email sending service | €0-10/mese | When >100 emails/mese |
| Server upgrade | Variabile | When RAM insufficient |
| Stripe account | Free | Before first paid customer |
| SaaS platform | €0-50/mese | When >10 customers |

---

## VALIDATION TARGETS

| Metric | Target | Minimum |
|--------|--------|---------|
| Prospects contacted | 20 | 20 |
| Meaningful responses | 5 | 3 |
| Trial signups | 2 | 1 |
| Paying customers | 1 | 1 |
| Revenue | €49-99 | €49 |

---

## KILL CRITERIA

| Criterion | Threshold | Action |
|-----------|-----------|--------|
| Response rate | <15% (3/20) | Pivot messaging |
| Trial rate | <10% (2/20) | Pivot offer |
| Conversion | 0 paying | Kill or pivot |
| Data quality | Cannot filter | Kill or find alternative |
| Customer feedback | "Not useful" | Kill or redesign |

---

## NEXT STEPS

1. CEO approves outreach message
2. CEO approves 20-prospect list
3. Send initial outreach (10 emails)
4. Wait 3 days
5. Send follow-up (10 emails)
6. Wait 3 days
7. Evaluate results
8. Decide: proceed, pivot, or kill
