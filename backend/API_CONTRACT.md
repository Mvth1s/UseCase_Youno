# Contrat d'API - Konsole Company Analyzer

Ce fichier est la source de verite pour le schema JSON echange entre frontend et backend.
Tout changement de modele dans `app/models.py` doit etre repercute ici.

---

## POST /analyze

Analyse un site web et renvoie un profil complet : tech stack, signaux GTM, profil entreprise et score B2B SaaS.

**Limite :** 10 requetes par minute par IP (reponse 429 au dela).

### Requete

```
POST /analyze
Content-Type: application/json
```

Corps :

```json
{
  "url": "stripe.com"
}
```

| Champ | Type   | Obligatoire | Description                                      |
|-------|--------|-------------|--------------------------------------------------|
| url   | string | oui         | URL du site a analyser. Le schema https:// est ajoute automatiquement si absent. |

---

### Reponse 200 OK

```json
{
  "url": "https://stripe.com",
  "page_title": "Stripe | Financial Infrastructure to Grow Your Revenue",
  "favicon_url": "https://stripe.com/favicon.ico",
  "tech_stack": {
    "frameworks": ["React", "Next.js"],
    "cdn": ["Cloudflare"],
    "cms": [],
    "server": ["nginx"],
    "analytics": ["Google Analytics 4", "Segment"],
    "tag_managers": ["Google Tag Manager"],
    "other": ["Stripe", "reCAPTCHA"]
  },
  "gtm_signals": {
    "chat_tools": ["Intercom"],
    "ad_pixels": ["LinkedIn Insight Tag", "Meta Pixel", "Google Ads"],
    "analytics_tools": ["Google Analytics 4", "Segment", "Amplitude"],
    "has_pricing_page": true,
    "has_demo_form": false,
    "has_careers_page": true
  },
  "profile": {
    "name": "Stripe",
    "description": "Infrastructure financiere en ligne pour accepter des paiements et gerer les revenus.",
    "sector": "Fintech / Paiements",
    "estimated_size": "grande entreprise >5000",
    "audience": "B2B"
  },
  "score": {
    "score": 87,
    "label": "Cible ideale B2B SaaS",
    "factors": [
      { "name": "Audience B2B", "points": 25, "max": 25 },
      { "name": "Analytics avances (Segment, Amplitude, Mixpanel...)", "points": 15, "max": 15 },
      { "name": "Page pricing presente", "points": 12, "max": 12 },
      { "name": "Pixels publicitaires B2B (LinkedIn, Google Ads, Bing)", "points": 12, "max": 12 },
      { "name": "Formulaire demo / Contact sales", "points": 0, "max": 10 },
      { "name": "Outil de chat client (Intercom, Drift, Crisp...)", "points": 10, "max": 10 },
      { "name": "Taille entreprise (cible PME/ETI)", "points": 2, "max": 8 },
      { "name": "Stack tech moderne (Next.js, React, Vue.js...)", "points": 8, "max": 8 }
    ]
  },
  "error": null
}
```

#### Description des champs de la reponse

| Champ                            | Type            | Description                                                                 |
|----------------------------------|-----------------|-----------------------------------------------------------------------------|
| url                              | string          | URL analysee (normalisee avec schema https://).                            |
| page_title                       | string          | Balise `<title>` de la page.                                               |
| favicon_url                      | string or null  | URL du favicon detecte.                                                    |
| tech_stack.frameworks            | string[]        | Frameworks JS detectes (React, Vue.js, Next.js...).                        |
| tech_stack.cdn                   | string[]        | CDN detectes (Cloudflare, Vercel, Netlify...).                             |
| tech_stack.cms                   | string[]        | CMS detectes (WordPress, Webflow, Shopify...).                             |
| tech_stack.server                | string[]        | Serveurs HTTP detectes via headers (nginx, Apache...).                     |
| tech_stack.analytics             | string[]        | Outils d'analytics detectes.                                               |
| tech_stack.tag_managers          | string[]        | Tag managers detectes (GTM...).                                            |
| tech_stack.other                 | string[]        | Autres technologies detectees (Stripe, Sentry, Auth0...).                 |
| gtm_signals.chat_tools           | string[]        | Outils de chat client detectes (Intercom, Drift, Crisp...).               |
| gtm_signals.ad_pixels            | string[]        | Pixels publicitaires detectes (Meta Pixel, LinkedIn Insight Tag...).      |
| gtm_signals.analytics_tools      | string[]        | Outils d'analytics detectes (Segment, Amplitude, Mixpanel...).            |
| gtm_signals.has_pricing_page     | boolean         | Une page pricing a ete detectee parmi les liens internes.                 |
| gtm_signals.has_demo_form        | boolean         | Un formulaire de demande de demo a ete detecte (lien ou CTA).            |
| gtm_signals.has_careers_page     | boolean         | Une page careers/jobs a ete detectee parmi les liens internes.            |
| profile.name                     | string          | Nom de l'entreprise infere par le LLM.                                    |
| profile.description              | string          | Description courte en francais de l'activite.                             |
| profile.sector                   | string          | Secteur d'activite.                                                        |
| profile.estimated_size           | string          | Taille estimee. Valeurs canoniques : `"startup <50"`, `"PME 50-500"`, `"ETI 500-5000"`, `"grande entreprise >5000"`. |
| profile.audience                 | string          | `"B2B"`, `"B2C"` ou `"mixed"`.                                            |
| score.score                      | integer 0-100   | Score global de fit B2B SaaS (somme des 8 facteurs, clampe a 100).       |
| score.label                      | string          | Label qualitatif : "Cible ideale B2B SaaS" (>=80), "Fort potentiel B2B" (>=60), "Potentiel modere" (>=40), "Faible signal B2B" (>=20), "Hors cible" (<20). |
| score.factors                    | ScoreFactor[]   | Detail des 8 facteurs. Toujours 8 entrees, y compris les facteurs a 0 pt.|
| score.factors[].name             | string          | Nom du facteur.                                                            |
| score.factors[].points           | integer         | Points obtenus pour ce facteur.                                           |
| score.factors[].max              | integer         | Points maximum possible pour ce facteur.                                  |
| error                            | string or null  | Message d'erreur si l'analyse est partielle.                              |

#### Tableau des 8 facteurs (total max = 100 pts)

| # | Facteur | Max | Logique |
|---|---------|-----|---------|
| 1 | Audience B2B | 25 | B2B=25, mixed=12, B2C=0 |
| 2 | Analytics avances | 15 | 1 outil=9, 2=12, 3+=15 (Segment, Amplitude, Mixpanel, Heap, FullStory, PostHog, Rudderstack) |
| 3 | Page pricing | 12 | Present=12, absent=0 |
| 4 | Pixels B2B | 12 | LinkedIn(8) + Google Ads(6) + Bing(3), plafonne a 12 |
| 5 | Formulaire demo | 10 | Present=10, absent=0 |
| 6 | Chat client | 10 | Au moins 1 outil=10, aucun=0 |
| 7 | Taille entreprise | 8 | PME=8, ETI=6, startup=4, grande entreprise=2, inconnu=0 |
| 8 | Stack tech moderne | 8 | Au moins 1 framework moderne=8, aucun=0 |

---

## GET /health

Endpoint de sante pour les healthchecks Render. Supporte GET et HEAD.

### Reponse 200 OK

```json
{ "status": "ok" }
```

---

## Codes d'erreur HTTP

| Code | Situation                                                                 |
|------|---------------------------------------------------------------------------|
| 400  | URL manquante, invalide ou contenu non-HTML.                             |
| 422  | Corps de requete maleforme : validation Pydantic echouee.               |
| 429  | Limite de 10 requetes par minute par IP depassee.                       |
| 503  | Site cible injoignable (timeout, DNS introuvable, erreur HTTP, redirections excessives). |
| 500  | Erreur interne inattendue.                                               |

En cas d'erreur, le corps de la reponse suit le format FastAPI standard :

```json
{ "detail": "Message d'erreur lisible." }
```
