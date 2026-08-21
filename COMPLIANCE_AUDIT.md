# AUDIT TECNICO — PRIVACY E COMPLIANCE

**Data**: 2026-08-21
**Sito analizzato**: https://vibecoder-star.github.io/appaltimonitor-landing/
**Metodo**: Revisione manuale del codice HTML/CSS/JS

---

## A. ACTUAL DATA COLLECTED

### Landing Page (index.html)

| Dato | Dove | Quando | Tipo |
|------|------|--------|------|
| Nessuno | — | Caricamento pagina | — |

**Nota**: La pagina statica non raccoglie dati dal visitatore.

### Form Opt-in (handleSubmit JS)

| Dato | Tipo | Obbligatorio |
|------|------|--------------|
| companyName | Personale (business) | Sì |
| businessEmail | Personale | Sì |
| industry | Categoria | Sì |
| geoArea | Categoria | Sì |
| services | Categoria | No |
| cpvCodes | Categoria | No |
| valueRange | Categoria | No |
| consentService | Consenso | Sì |
| consentMarketing | Consenso | No |
| consentPrivacy | Consenso | Sì |
| timestamp | Tecnico | Automatico |
| source | Tecnico | Automatico |
| consentVersion | Tecnico | Automatico |

### localStorage (Browser)

```javascript
// Linea 1043 di index.html
localStorage.setItem('appaltimonitor_optin', JSON.stringify(data));
```

**Contenuto**: Tutti i dati del form inclusi email e consensi.

### Backend (commercial_pipeline.py)

| Dato | File | Scopo |
|------|------|-------|
| Trial ID | data/trials/ | Gestione stato |
| Profile ID | data/trials/ | Riferimento |
| Email | data/trials/ | Comunicazione |
| Company name | profiles/ | Personalizzazione |
| Industry/geo/services | profiles/ | Filtri TED |
| Consent flags | data/optins/ | Compliance |
| Timestamps | data/trials/ | Audit |
| Reports sent | data/trials/ | Tracking |

### Email Log (data/logs/email_log.jsonl)

| Dato | Scopo |
|------|-------|
| Destinatario | Verifica invio |
| Oggetto | Debug |
| Stato invio | Audit |
| Errori | Debug |

### TED Pipeline (mvp_pipeline.py)

| Dato | Fonte | Natura |
|------|-------|--------|
| CPV, luogo, valore | TED API | Pubblico |
| Bandi TED | ted.europa.eu | Pubblico |

---

## B. ACTUAL TRACKING/COOKIES FOUND

### Cookies

```
❌ NESSUN COOKIE UTILIZZATO
```

La landing page NON imposta alcun cookie.

### localStorage

```
✅ UTILIZZATO (1 occorrenza)
- Chiave: appaltimonitor_optin
- Contenuto: dati del form (inclusa email)
- Scopo: memorizzazione temporanea prima invio
- Posizione: index.html:1043
```

### sessionStorage

```
❌ NON UTILIZZATO
```

### Analytics

```
❌ NESSUN ANALYTICS
- No Google Analytics
- No Meta Pixel
- No Plausible/Umami
- No log di accesso lato client
```

### Fonts/Immagini Esterne

```
❌ NESSUNA RISORSA ESTERNA
- Font: solo system fonts (-apple-system, Segoe UI, Roboto...)
- Immagini: nessuna (solo emoji CSS)
- CSS: incorporato in <style>
- JS: incorporato in <script>
```

### Fingerprinting

```
❌ NON PRESENTE
```

### Terze Parti

```
GitHub Pages  → hosting statico
Gmail SMTP    → invio email (solo dopo opt-in confermato)
TED API       → query pubbliche (solo dopo opt-in confermato)
```

---

## C. COOKIE BANNER REQUIRED?

### ❌ NO — Non è attualmente necessario

**Motivazione tecnica**:
1. **Nessun cookie imposto** — La pagina non usa `document.cookie`
2. **Nessun analytics** — Nessun tracciamento visitatori
3. **Nessun tracker** — Nessuno script di terze parti
4. **localStorage è funzionale** — Usato solo per memorizzare dati del form prima dell'invio

**Riferimento normativo**:
- Direttiva ePrivacy (2002/58/CE) — Art. 5(3)
- Garante Privacy — Linee cookie (2021)
- Il banner cookie è richiesto per cookie **non essenziali** e **tracker**
- localStorage funzionale al servizio è generalmente considerato essenziale

**Attenzione**: Se in futuro si aggiungeranno analytics (Google Analytics, Plussible, ecc.), sarà necessario un banner.

---

## D. PRIVACY POLICY INFORMATION THAT MUST BE DISCLOSED

### Dati Obbligatori da Inserire

| Sezione | Contenuto |
|---------|-----------|
| **Titolare** | Nome/Ragione sociale, P.IVA, indirizzo, email |
| **Dati raccolti** | Elenco completo (form + localStorage) |
| **Finalità** | Fornitura servizio, marketing (opzionale) |
| **Base giuridica** | Consenso esplicito (Art. 6 GDPR) |
| **Destinatari** | Nessun terzo, solo fornitori tecnici (GitHub, Gmail) |
| **Trasferimento** | Extra UE: no (server Italia/Europa) |
| **Conservazione** | Durata servizio + 30 giorni (da definire precisamente) |
| **Diritti** | Accesso, rettifica, cancellazione, limitazione, opposizione, portabilità |
| **Reclamo** | Diritto di reclamo al Garante |
| **Fonti dati** | Dati forniti dall'utente + dati pubblici TED |

### Esempio Testo Privacy (Minima)

> **Titolare**: [Nome Azienda], P.IVA [numero], [indirizzo], [email]
>
> **Dati raccolti**: nome aziendale, email, settore, zona, servizi, consensi
>
> **Finalità**: fornire il servizio di intelligence sugli appalti pubblici; inviare comunicazioni commerciali (solo con consenso)
>
> **Base giuridica**: consenso dell'interessato (art. 6 GDPR)
>
> **Conservazione**: i dati sono conservati per la durata del servizio e per 30 giorni dopo la cancellazione
>
> **Diritti**: l'utente può accedere, rettificare, cancellare i dati, opporsi al trattamento e richiedere la portabilità, scrivendo a [email]
>
> **Reclamo**: è possibile presentare reclamo al Garante per la protezione dei dati personali

---

## E. TERMS OF SERVICE INFORMATION NEEDED

### Per Servizio Pagamento

| Sezione | Contenuto |
|---------|-----------|
| **Oggetto** | Fornitura servizio intelligence appalti |
| **Prezzi** | Starter €29, Professional €59, Enterprise €99 (ipotesi) |
| **Pagamento** | Carta di credito/Stripe |
| **Rinnovo** | Mensile, cancellazione libera |
| **Rimborso** | 14 giorni dal pagamento (diritto recesso) |
| **SLA** | Nessuna garanzia di risultati |
| **Limitazione responsabilità** | Nessuna garanzia di aggiornamento TED |
| **Legge applicabile** | Italia |
| **Foro competente** | [Città del foro] |

---

## F. MISSING LEGAL/BUSINESS IDENTITY

### Dati Mancanti nel Sito

| Campo | Stato | Dove Inserirlo |
|-------|-------|----------------|
| **Nome legale/Ragione sociale** | ❌ Mancante | Footer + Privacy |
| **P.IVA** | ❌ Mancante | Footer + Privacy |
| **Indirizzo legale** | ❌ Mancante | Footer + Privacy |
| **Email contatto** | ✅ Presente (info@appaltimonitor.it) | Footer |
| **REA** | ❌ Mancante | Footer (se società) |
| **Codice fiscale** | ❌ Mancante | Privacy (se ditta individuale) |

---

## G. EXACT BLOCKERS BEFORE FIRST REAL USER

### Bloccanti

| Blocker | Impatto | Risoluzione |
|---------|---------|-------------|
| **Privacy Policy non pubblicata** | ALTA | Redigere e pubblicare pagina privacy |
| **Termini di servizio** | ALTA | Redigere TOS per pagamenti |
| **Dati legali mancanti** | ALTA | Inserire P.IVA, nome, indirizzo nel footer |
| **Consenso non sufficientemente documentato** | MEDIA | Migliorare evidenza del consenso |
| **Conservazione non precisata** | MEDIA | Definire esattamente i tempi |
| **Data Processing Agreement con Gmail** | BASSA | Non obbligatorio ma consigliato |

### Non Bloccanti

| Elemento | Impatto | Note |
|----------|---------|------|
| Cookie banner | BASSO | Non necessario (nessun cookie) |
| Dominio personalizzato | BASSO | Opzionale |

---

## H. RECOMMENDED MINIMUM-COMPLIANCE IMPLEMENTATION

### Azioni Minime Obbligatorie

1. **Pagina Privacy Policy** — Redigere e pubblicare `privacy.html`
2. **Pagina Termini di Servizio** — Redigere `terms.html`
3. **Aggiornare Footer** — Inserire dati legali:
   ```
   © 2026 [Nome Azienda] — P.IVA [numero] — [indirizzo]
   ```
4. **Link nel Footer** — Aggiungere link a Privacy e TOS
5. **Migliorare evidenza consenso** — Rendere più visible il checkbox privacy

### Modifiche al Footer Attuale

**Prima**:
```html
<footer>
    <p>&copy; 2026 AppaltiMonitor</p>
    <p><a href="#privacy">Privacy Policy</a> | <a href="#faq">FAQ</a> | ...</p>
</footer>
```

**Dopo**:
```html
<footer>
    <p>&copy; 2026 [Nome Azienda] — P.IVA [numero]</p>
    <p>[Indirizzo] — [email]</p>
    <p><a href="/privacy.html">Privacy Policy</a> | <a href="/terms.html">Termini di Servizio</a> | ...</p>
</footer>
```

### Modifiche alla Sezione Privacy in Pagina

La sezione `#privacy` attuale è informativa ma **non è una Privacy Policy formale**.

**Azioni**:
1. Creare `privacy.html` separato con testo legale completo
2. Creare `terms.html` separato per TOS
3. Aggiornare link nel footer per puntare alle nuove pagine

---

## DATA FLOW MAP

```
VISITOR (anonimo)
    │
    ▼
LANDING PAGE (static HTML/CSS/JS)
    │ ← Nessun dato raccolto
    │ ← Nessun cookie imposto
    │ ← Nessun tracker
    ▼
OPT-IN FORM (browser)
    │ ← Dati inseriti dall'utente
    │ ← Consensi raccolti (3 checkbox)
    │ ← Salvataggio in localStorage
    ▼
BACKEND (commercial_pipeline.py)
    │ ← Creazione profilo
    │ ← Creazione trial (stato: PENDING)
    │ ← Invio email conferma
    ▼
STORAGE (file JSON)
    │ ← data/optins/
    │ ← data/confirmed/
    │ ← data/trials/
    │ ← profiles/
    ▼
EMAIL (Gmail SMTP)
    │ ← Invio a email fornita
    │ ← Log in email_log.jsonl
    ▼
TED API (query pubblica)
    │ ← Query per CPV/Italia
    │ ← Dati pubblici (bandi)
    ▼
REPORT (generato)
    │ ← Markdown + HTML
    │ ← Salvato in reports/
    │ ← Inviato via email
    ▼
TRIAL ACTIVE (7 giorni)
    │ ← Report settimanali
    │ ← Controllo scadenza
    │ ← Conversion offer
```

---

## RIEPILOGO FINALE

| Elemento | Stato |
|----------|-------|
| Cookie banner | ❌ NON NECESSARIO |
| Cookie tracker | ❌ NON PRESENTI |
| Analytics | ❌ NON PRESENTI |
| localStorage | ✅ PRESENTE (dati form) |
| Privacy Policy formale | ❌ MANCANTE |
| Termini di Servizio | ❌ MANCANTE |
| Dati legali footer | ❌ MANCANTI |
| Consensi GDPR | ✅ PRESENTI |
| Email delivery | ✅ FUNZIONANTE |
| Test suite | ✅ 37/37 |

### Verdetto

> **MVP TECNICAMENTE FUNZIONANTE MA NON LEGALMENTE PUBBLICABILE**
> 
> Il sistema è operativo e testati, ma mancano:
> 1. Privacy Policy formale (obbligatoria)
> 2. Dati legali nel footer (obbligatori)
> 3. Termini di servizio (necessari per pagamenti)
>
> **Non pubblicare finché non sono inseriti questi elementi.**

---

*Audit completato. Nessuna modifica effettuata.*
