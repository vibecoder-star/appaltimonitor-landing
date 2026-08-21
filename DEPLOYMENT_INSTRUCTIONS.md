# Deployment Instructions — GitHub Pages

## Prerequisites

1. GitHub account
2. Git installed locally
3. Repository created on GitHub

## Option A: Deploy via GitHub Actions (Recommended)

### Step 1: Prepare the repository structure

```bash
cd /opt/autonomous-venture-engine/appalti-monitor
git init
git add .
git commit -m "Initial commit: AppaltiMonitor landing page"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/appaltimonitor-landing.git
git push -u origin main
```

### Step 2: Configure GitHub Pages

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Pages**
3. Under **Source**, select **GitHub Actions**
4. The workflow will automatically deploy on push to `main`

### Step 3: Verify deployment

After pushing, the site will be available at:
`https://YOUR_USERNAME.github.io/appaltimonitor-landing/`

## Option B: Deploy via gh-pages branch (Alternative)

```bash
cd /opt/autonomous-venture-engine/appalti-monitor/landing-page
git init
git add .
git commit -m "Deploy landing page"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/appaltimonitor-landing.git
git push -u origin main

# Create orphan gh-pages branch
git checkout --orphan gh-pages
git rm -rf .
git checkout main -- index.html
git add index.html
git commit -m "Deploy to GitHub Pages"
git push origin gh-pages
```

Then configure GitHub Pages to use `gh-pages` branch.

## Option C: Deploy via `docs/` folder on main branch

1. Move `index.html` to `docs/` folder
2. In Settings → Pages, select `docs` folder on `main` branch

## Post-Deployment

### Custom Domain (Optional)

If you purchase a domain later:

1. Add a `CNAME` file in the root with your domain:
   ```
   appaltimonitor.it
   ```
2. Configure DNS with your registrar:
   - A record: 185.199.108.153
   - A record: 185.199.109.153
   - A record: 185.199.110.153
   - A record: 185.199.111.153

### HTTPS

GitHub Pages automatically provisions HTTPS certificates. No additional configuration needed.

## File Structure for Deployment

```
landing-page/
├── index.html          # Main landing page
├── .github/
│   └── workflows/
│       └── deploy.yml  # GitHub Actions workflow
└── README.md           # Repository documentation
```

## Current File Locations

- Landing page: `/opt/autonomous-venture-engine/appalti-monitor/landing-page/index.html`
- Opt-in workflow: `/opt/autonomous-venture-engine/appalti-monitor/landing-page/optin_workflow.py` (backend only, not deployed)
- Deployment config: `/opt/autonomous-venture-engine/appalti-monitor/landing-page/.github/workflows/deploy.yml`

## Testing Locally

Before deploying, test locally:

```bash
cd /opt/autonomous-venture-engine/appalti-monitor/landing-page
python3 -m http.server 8000
# Open http://localhost:8000 in your browser
```

## Important Notes

1. The `optin_workflow.py` file is NOT needed on GitHub Pages — it's for backend processing only
2. Form submissions currently use `localStorage` (demo mode)
3. For production, integrate with a backend service (Formspree, Netlify Forms, or custom)
4. GitHub Pages is free for public repositories

## Estimated Time

- Setup: 5 minutes
- Deployment: 2-3 minutes after push
- DNS propagation (custom domain): 24-48 hours
