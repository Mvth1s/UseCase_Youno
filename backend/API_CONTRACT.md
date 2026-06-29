# Contrat d'API - Konsole Company Analyzer

Ce fichier est la source de verite pour le schema JSON echange entre frontend et backend.
Tout changement de modele dans `app/models.py` doit etre repercute ici.

---

## POST /analyze

Analyse un site web et renvoie un profil complet : tech stack, signaux GTM, profil entreprise et score B2B SaaS.

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
    "other": ["Stripe.js", "reCAPTCHA"]
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
    "estimated_size": "5000-10000 employes",
    "audience": "B2B"
  },
  "score": {
    "score": 87,
    "label": "Fort potentiel B2B SaaS",
    "factors": [
      { "name": "Audience B2B confirmee", "points": 25, "max": 25 },
      { "name": "Signaux analytics avances (Segment, Amplitude)", "points": 20, "max": 20 },
      { "name": "Page pricing presente", "points": 15, "max": 15 },
      { "name": "Pixels publicitaires B2B (LinkedIn)", "points": 15, "max": 15 },
      { "name": "Chat client (Intercom)", "points": 12, "max": 15 },
      { "name": "Formulaire demo absent", "points": 0, "max": 10 }
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
| tech_stack.frameworks            | string[]        | Frameworks JS/CSS detectes (React, Vue, Next.js...).                       |
| tech_stack.cdn                   | string[]        | CDN detectes (Cloudflare, Fastly...).                                      |
| tech_stack.cms                   | string[]        | CMS detectes (WordPress, Webflow...).                                      |
| tech_stack.server                | string[]        | Serveurs HTTP detectes via headers (nginx, Apache...).                     |
| tech_stack.analytics             | string[]        | Outils d'analytics detectes.                                               |
| tech_stack.tag_managers          | string[]        | Tag managers detectes (GTM...).                                            |
| tech_stack.other                 | string[]        | Autres technologies detectees.                                             |
| gtm_signals.chat_tools           | string[]        | Outils de chat client detectes (Intercom, Drift, Crisp...).               |
| gtm_signals.ad_pixels            | string[]        | Pixels publicitaires detectes (Meta Pixel, LinkedIn Insight Tag...).      |
| gtm_signals.analytics_tools      | string[]        | Outils d'analytics avances detectes (Segment, Amplitude...).              |
| gtm_signals.has_pricing_page     | boolean         | Une page pricing a ete detectee.                                           |
| gtm_signals.has_demo_form        | boolean         | Un formulaire de demande de demo a ete detecte.                           |
| gtm_signals.has_careers_page     | boolean         | Une page careers/jobs a ete detectee.                                      |
| profile.name                     | string          | Nom de l'entreprise infere par le LLM.                                    |
| profile.description              | string          | Description courte en francais de l'activite.                             |
| profile.sector                   | string          | Secteur d'activite.                                                        |
| profile.estimated_size           | string          | Taille estimee en nombre d'employes.                                       |
| profile.audience                 | string          | "B2B", "B2C" ou "mixed".                                                  |
| score.score                      | integer 0-100   | Score global de fit B2B SaaS.                                             |
| score.label                      | string          | Label lisible du score (ex. "Fort potentiel B2B SaaS").                   |
| score.factors                    | ScoreFactor[]   | Detail des facteurs contribuant au score.                                  |
| score.factors[].name             | string          | Nom du facteur.                                                            |
| score.factors[].points           | integer         | Points obtenus pour ce facteur.                                           |
| score.factors[].max              | integer         | Points maximum possible pour ce facteur.                                  |
| error                            | string or null  | Message d'erreur si l'analyse est partielle ou a echoue.                  |

---

## GET /health

Endpoint de sante pour les healthchecks Render.

### Reponse 200 OK

```json
{ "status": "ok" }
```

---

## Codes d'erreur HTTP

| Code | Situation                                                                 |
|------|---------------------------------------------------------------------------|
| 400  | URL manquante ou manifestement invalide (champ vide).                    |
| 422  | Corps de requete maleforme - validation Pydantic echouee.                |
| 503  | Site cible injoignable (timeout httpx, DNS introuvable, non-200).        |
| 500  | Erreur interne inattendue (bug, LLM indisponible non intercepte...).     |

En cas d'erreur, le corps de la reponse suit le format FastAPI standard :

```json
{ "detail": "Message d'erreur lisible." }
```
