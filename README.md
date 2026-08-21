# AppaltiMonitor — Landing Page

Landing page statica per AppaltiMonitor, servizio di intelligence sugli appalti pubblici basato sui dati TED (Tenders Electronic Daily).

## Deploy

Questa landing page è progettata per essere deployata su GitHub Pages (gratuito).

### Struttura

```
├── index.html              # Landing page completa
├── .github/workflows/
│   └── deploy.yml          # GitHub Actions per auto-deploy
├── optin_workflow.py       # Backend workflow (non deployato su Pages)
├── DEPLOYMENT_INSTRUCTIONS.md
└── README.md
```

### Deploy su GitHub Pages

1. Crea repository su GitHub
2. Push del codice
3. Abilita GitHub Pages → Source: GitHub Actions
4. Il sito sarà disponibile su: `https://USERNAME.github.io/REPO-NAME/`

### Test locale

```bash
python3 -m http.server 8000
# Apri http://localhost:8000
```

## Funzionalità

- Landing page responsive (mobile-first)
- Form opt-in con validazione
- Double opt-in workflow (backend)
- Sezione FAQ con toggle
- Pricing hypotheses
- Privacy policy
- Smooth scroll

## Tecnologie

- HTML5/CSS3/JS vanilla (no framework)
- Nessuna dipendenza esterna
- 100% statico (compatibile GitHub Pages)

## Licenza

Proprietario — AppaltiMonitor
