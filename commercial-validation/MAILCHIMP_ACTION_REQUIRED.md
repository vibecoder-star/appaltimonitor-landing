# MAILCHIMP INTEGRATION — CEO ACTION REQUIRED

**Data**: 2026-08-22

---

## 🔴 CEO DEVE CREARE 2 API KEY

### 1. MANDRILL KEY (Transaction Email) — PRIORITARIA

Serve per inviare email transazionali (conferma, report, benvenuto).

**Procedura**:

1. Vai su https://mailchimp.com
2. Login con `appalti.monitor@gmail.com`
3. Clicca **Profile** (in alto a destra) → **Account**
4. Clicca **Extras** → **API keys**
5. Scorri fino a **Mandrill**
6. Clicca **Enable Mandrill**
7. Vai su https://mandrillapp.com
8. Clicca **Settings** → **SMTP & API Info**
9. Clicca **+ New API Key**
10. Copia la key (es. `md-xxxxxxxxxxxxxxxx`)

**Questa key è OBBLIGATORIA per le email transazionali.**

---

### 2. MAILCHIMP API KEY (Marketing) — OPZIONALE

Serve per campagne marketing e automazioni.

**Procedura**:

1. Vai su https://mailchimp.com
2. Login con `appalti.monitor@gmail.com`
3. Clicca **Profile** (in alto a destra) → **Account**
4. Clicca **Extras** → **API keys**
5. Clicca **Create A Key**
6. Copia la key (es. `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-us1`)

**Questa key è OPZIONALE per ora.**

---

## COSA INVIARE A HERMES

**PRIORITÀ 1** (obbligatoria):
```
MANDRILL_KEY=md-xxxxxxxxxxxxxxxx
```

**PRIORITÀ 2** (opzionale):
```
MC_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-us1
```

---

## DOPO IL RICEVIMENTO

Hermes eseguirà autonomamente:
1. Aggiornamento `.env` con nuove credenziali
2. Riavvio `appaltimonitor-api`
3. Test email transazionale a `laboratoriosansone@gmail.com`
4. Verifica completa del flusso
5. Report finale

---

**STOP — In attesa di API Key da Mailchimp**
