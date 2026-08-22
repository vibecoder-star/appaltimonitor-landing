# MAILCHIMP INTEGRATION — ARCHITECTURE & CREDENTIALS REQUIRED

**Data**: 2026-08-22
**Stato**: In attesa di credenziali API Mailchimp

---

## ARCHITETTURA EMAIL TARGET

```
APPALTIMONITOR EMAIL FLOW
│
├── TRANSACTIONAL (critico per il business)
│   ├── Double opt-in confirmation
│   ├── Welcome/trial email
│   ├── Report delivery
│   └── Service notifications
│
├── MARKETING (outreach)
│   ├── Commercial outreach
│   ├── Follow-up campaigns
│   └── Marketing automation
│
└── FALLBACK
    └── Gmail SMTP (se Mailchimp fallisce)
```

---

## CREDENTIALI NECESSARIE

### 1. Mailchimp API Key (Marketing)
**Dove crearla**:
1. Log in to Mailchimp
2. Click profile icon → Account
3. Extras → API keys
4. Create A Key
5. Copy the API key (format: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-us1`)

**Valore**: `MC_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-us1`

### 2. Mailchimp Mandrill Key (Transactional)
**Dove crearla**:
1. Log in to Mailchimp
2. Settings → Transactional Email
3. Enable Mandrill
4. Add domain (appalti monitor.it)
5. Get API key from Mandrill settings

**Valore**: `MANDRILL_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 3. Server Prefix
L'ultima parte dell'API key dopo `-` (es. `us1`, `us2`, `us6`)

---

## PROSSIMA AZIONE

**CEO deve fornire**:
1. MC_API_KEY (se si vuole marketing)
2. MANDRILL_KEY (se si vuole transactional)

**Dopo ricezione**:
1. Aggiorno `.env` con credenziali
2. Riavvio servizi
3. Test completo
4. Report finale

---

*Documento generato da Hermes*
