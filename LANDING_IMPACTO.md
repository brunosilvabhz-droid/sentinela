# Landing Page IMPACTO

Landing page institucional da IMPACTO em React + Vite + Tailwind CSS.

## Estrutura

```text
frontend/
  vite.config.js
  src/
    main.jsx
    constants.ts
    SentinelaApp.jsx
    pages/
      LandingPage.jsx
    components/
      landing/
        Header.jsx
        Hero.jsx
        ProblemSection.jsx
        SolutionsSection.jsx
        SentinelaSection.jsx
        HowItWorksSection.jsx
        BenefitsSection.jsx
        CTASection.jsx
        Footer.jsx
        SectionHeader.jsx
    assets/
      impacto-logo.png
```

## Rotas

```text
/      Landing page IMPACTO
/app   Console local do SENTINELA
/ack   Confirmação pública de leitura de alerta
```

## Constantes

Arquivo: `frontend/src/constants.ts`

```text
WHATSAPP_URL
SENTINELA_LOGIN_URL
COMPANY_DOMAIN
```

Em produção, `SENTINELA_LOGIN_URL` aponta para:

```text
https://app.impactocg.com/login
```

Localmente, `frontend/.env.local` usa:

```text
VITE_SENTINELA_LOGIN_URL=/app
```

## Instalação

```bash
cd frontend
npm install
```

## Desenvolvimento

```bash
npm run dev
```

Para escolher porta:

```bash
npm run dev -- --host 127.0.0.1 --port 5183
```

## Build

```bash
npm run build
```

## Deploy

### Vercel

```text
Framework: Vite
Root Directory: frontend
Build Command: npm run build
Output Directory: dist
```

### Netlify

```text
Base directory: frontend
Build command: npm run build
Publish directory: frontend/dist
```

### Variáveis úteis

```text
VITE_API_URL=https://sentinela-api.onrender.com/api/v1
VITE_SENTINELA_LOGIN_URL=https://app.impactocg.com/login
```
