"""
Module de detection de la tech stack a partir du HTML et des headers HTTP.

Logique de detection pure par signatures -- aucun LLM, aucune heuristique complexe.
Chaque detection repose sur une preuve explicite (pattern present dans la source analysee).

Conception du catalogue :
  - HtmlSignature   : un ou plusieurs patterns cherches dans le HTML brut
                      (comparaison insensible a la casse)
  - HeaderSignature : verification d'un header HTTP par cle et/ou valeur

Pour etendre le catalogue, ajouter une ligne dans la liste correspondante.
Aucune modification de la logique de detection n'est necessaire.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models import TechStack
from app.scraper import ScrapedData


# ---------------------------------------------------------------------------
# Structures de donnees du catalogue de signatures
# ---------------------------------------------------------------------------


@dataclass
class HtmlSignature:
    """
    Signature detectee par presence d'au moins un pattern dans le HTML brut.
    La recherche est toujours insensible a la casse.
    """

    name: str
    patterns: list[str]


@dataclass
class HeaderSignature:
    """
    Signature detectee via un header HTTP de la reponse.

    - header_key : cle du header, en minuscules (ex. 'cf-ray', 'server').
    - patterns   : valeurs a chercher dans la valeur du header.
                   Si la liste est vide, la simple presence de la cle suffit.
    """

    name: str
    header_key: str
    patterns: list[str]


# ---------------------------------------------------------------------------
# Catalogue : Frameworks JavaScript
# ---------------------------------------------------------------------------

_FRAMEWORK_HTML: list[HtmlSignature] = [
    HtmlSignature("Next.js",    ["__next_data__", "/_next/", "next/dist"]),
    HtmlSignature("Nuxt.js",    ["__nuxt", "_nuxt/"]),
    # React detectable sans Next.js (Next.js est detecte separement)
    HtmlSignature("React",      ["data-reactroot", "_reactrootcontainer",
                                  "react.production.min.js", "react-dom.production.min.js",
                                  "__react_fiber"]),
    HtmlSignature("Vue.js",     ["vue.min.js", "__vue__", "data-v-", "/vue/dist/", "createapp("]),
    HtmlSignature("Angular",    ["ng-version=", "angular.min.js", "ng-app=",
                                  "angular/fesm", "/core.mjs"]),
    HtmlSignature("Svelte",     ["__svelte", ".svelte-", "svelte.js"]),
    HtmlSignature("SvelteKit",  ["sveltekit-hydrate", "/__svelte"]),
    HtmlSignature("Gatsby",     ["___gatsby", "gatsby-", "gatsby.js", "gatsby-script"]),
    HtmlSignature("Remix",      ["__remixcontext", "/__remix"]),
    HtmlSignature("Astro",      ["astro-island", "astro-static-slot"]),
    HtmlSignature("Ember.js",   ["ember.min.js", "ember-application", "data-ember-"]),
    HtmlSignature("Alpine.js",  ["cdn.alpinejs.com", "unpkg.com/alpinejs", "x-data="]),
    HtmlSignature("HTMX",       ["htmx.min.js", "htmx.org", "hx-get=", "hx-post="]),
]

_FRAMEWORK_HEADER: list[HeaderSignature] = [
    # Next.js se signale parfois dans X-Powered-By sur Vercel et autres hotes
    HeaderSignature("Next.js", "x-powered-by", ["next.js"]),
]


# ---------------------------------------------------------------------------
# Catalogue : CMS et builders de sites
# ---------------------------------------------------------------------------

_CMS_HTML: list[HtmlSignature] = [
    HtmlSignature("WordPress",   ["/wp-content/", "/wp-includes/", "wp-json"]),
    HtmlSignature("Shopify",     ["cdn.shopify.com", "shopify.theme", "myshopify.com"]),
    HtmlSignature("Webflow",     ["webflow.com", "data-wf-", "js.webflow.com"]),
    HtmlSignature("Wix",         ["static.wixstatic.com", "wix.com/pages"]),
    HtmlSignature("Squarespace", ["squarespace.com", "static1.squarespace"]),
    HtmlSignature("Ghost",       ["ghost.io", "content.ghost.io"]),
    HtmlSignature("Drupal",      ["drupal.js", "/sites/default/files/", "drupal.settings"]),
    HtmlSignature("Joomla",      ["/media/jui/", "/components/com_"]),
    HtmlSignature("Framer",      ["framerusercontent.com"]),
    HtmlSignature("Contentful",  ["ctfassets.net"]),
    HtmlSignature("Prismic",     ["prismic.io", "prismicio"]),
    HtmlSignature("Sanity",      ["cdn.sanity.io"]),
]


# ---------------------------------------------------------------------------
# Catalogue : CDN et hebergement
# ---------------------------------------------------------------------------

_CDN_HTML: list[HtmlSignature] = [
    HtmlSignature("AWS CloudFront", ["cloudfront.net"]),
    HtmlSignature("Fastly",         ["fastly.net"]),
    HtmlSignature("Bunny CDN",      ["b-cdn.net"]),
]

_CDN_HEADER: list[HeaderSignature] = [
    # Cloudflare : deux preuves possibles (presence du header cf-ray OU valeur server)
    HeaderSignature("Cloudflare",     "cf-ray",               []),            # presence seule
    HeaderSignature("Cloudflare",     "server",               ["cloudflare"]),
    HeaderSignature("Vercel",         "x-vercel-id",          []),
    HeaderSignature("Netlify",        "x-nf-request-id",      []),
    HeaderSignature("AWS CloudFront", "x-amz-cf-id",          []),
    HeaderSignature("Fastly",         "x-served-by",          ["cache-"]),
    HeaderSignature("Akamai",         "x-akamai-request-id",  []),
    HeaderSignature("Bunny CDN",      "cdn-pullzone",          []),
    HeaderSignature("Fly.io",         "fly-request-id",        []),
    HeaderSignature("Railway",        "railway-request-id",    []),
]


# ---------------------------------------------------------------------------
# Catalogue : Serveur HTTP (headers "server" et "x-powered-by")
# ---------------------------------------------------------------------------

_SERVER_HEADER: list[HeaderSignature] = [
    HeaderSignature("nginx",      "server",        ["nginx"]),
    HeaderSignature("Apache",     "server",        ["apache"]),
    HeaderSignature("Caddy",      "server",        ["caddy"]),
    HeaderSignature("IIS",        "server",        ["microsoft-iis"]),
    HeaderSignature("Gunicorn",   "server",        ["gunicorn"]),
    HeaderSignature("LiteSpeed",  "server",        ["litespeed"]),
    HeaderSignature("OpenResty",  "server",        ["openresty"]),
    HeaderSignature("Kestrel",    "server",        ["kestrel"]),
    # X-Powered-By : runtime ou langage cote serveur
    HeaderSignature("PHP",        "x-powered-by",  ["php"]),
    HeaderSignature("Express.js", "x-powered-by",  ["express"]),
    HeaderSignature("ASP.NET",    "x-powered-by",  ["asp.net"]),
]


# ---------------------------------------------------------------------------
# Catalogue : Analytics et outils de mesure
# ---------------------------------------------------------------------------

_ANALYTICS_HTML: list[HtmlSignature] = [
    HtmlSignature("Google Analytics 4",         ["googletagmanager.com/gtag/js",
                                                  "gtag('config', 'g-",
                                                  'gtag("config", "g-']),
    HtmlSignature("Google Universal Analytics", ["google-analytics.com/analytics.js",
                                                  "ga('create', 'ua-",
                                                  'ga("create", "ua-']),
    HtmlSignature("Segment",                    ["cdn.segment.com",
                                                  "segment.io/analytics.js",
                                                  "analytics.load("]),
    HtmlSignature("Amplitude",                  ["cdn.amplitude.com",
                                                  "amplitude.com/libs",
                                                  "amplitude.init("]),
    HtmlSignature("Mixpanel",                   ["cdn.mxpnl.com",
                                                  "mixpanel.init(",
                                                  "mixpanel.com/lib"]),
    HtmlSignature("Hotjar",                     ["static.hotjar.com",
                                                  "hjid:", "_hjsettings"]),
    HtmlSignature("Plausible",                  ["plausible.io/js/plausible",
                                                  "plausible.io/js/script"]),
    HtmlSignature("PostHog",                    ["app.posthog.com",
                                                  "posthog.init(",
                                                  "cdn.posthog.com"]),
    HtmlSignature("Heap",                       ["heapanalytics.com",
                                                  "heap.load(",
                                                  "cdn.heapanalytics.com"]),
    HtmlSignature("FullStory",                  ["fullstory.com/s/fs.js",
                                                  "_fs_namespace"]),
    HtmlSignature("Microsoft Clarity",          ["clarity.ms/tag",
                                                  "clarity.ms/collect"]),
    HtmlSignature("Matomo",                     ["matomo.js", "piwik.js",
                                                  "matomo.php"]),
    HtmlSignature("Rudderstack",                ["cdn.rudderlabs.com",
                                                  "rudderstack.com"]),
]


# ---------------------------------------------------------------------------
# Catalogue : Tag managers
# ---------------------------------------------------------------------------

_TAG_MANAGER_HTML: list[HtmlSignature] = [
    HtmlSignature("Google Tag Manager", ["googletagmanager.com/gtm.js",
                                          "googletagmanager.com/ns.html"]),
    HtmlSignature("Tealium",            ["tags.tiqcdn.com", "tealiumiq.com"]),
    HtmlSignature("Adobe Launch",       ["assets.adobedtm.com"]),
    HtmlSignature("Matomo Tag Manager", ["mtm.js"]),
]


# ---------------------------------------------------------------------------
# Catalogue : Outils tiers notables ("other")
# ---------------------------------------------------------------------------

_OTHER_HTML: list[HtmlSignature] = [
    HtmlSignature("Stripe",         ["js.stripe.com", "stripe.com/v3"]),
    HtmlSignature("Intercom",       ["widget.intercom.io", "api.intercom.io"]),
    HtmlSignature("Zendesk",        ["static.zdassets.com"]),
    HtmlSignature("HubSpot",        ["js.hs-scripts.com", "js.hubspot.com"]),
    HtmlSignature("Salesforce",     ["force.com", "pardot.com"]),
    HtmlSignature("reCAPTCHA",      ["google.com/recaptcha", "recaptcha/api.js"]),
    HtmlSignature("hCaptcha",       ["hcaptcha.com/1/api.js"]),
    HtmlSignature("Cloudinary",     ["res.cloudinary.com"]),
    HtmlSignature("LaunchDarkly",   ["launchdarkly-js-client-sdk",
                                      "app.launchdarkly.com"]),
    HtmlSignature("Sentry",         ["browser.sentry-cdn.com",
                                      "sentry.io/api/"]),
    HtmlSignature("Datadog RUM",    ["browser-agent.datadoghq.com",
                                      "datadoghq-browser-agent"]),
    HtmlSignature("Algolia",        ["algoliasearch.js",
                                      "algoliaapis.com"]),
    HtmlSignature("Auth0",          ["cdn.auth0.com", "auth0.js"]),
    HtmlSignature("Okta",           ["cdn.okta.com", "okta-signin-widget"]),
    HtmlSignature("Paddle",         ["cdn.paddle.com/paddle/paddle.js"]),
    HtmlSignature("Chargebee",      ["js.chargebee.com"]),
    HtmlSignature("Lemon Squeezy",  ["lemonsqueezy.com"]),
    HtmlSignature("Twilio",         ["media.twiliocdn.com"]),
]


# ---------------------------------------------------------------------------
# Fonctions de detection internes
# ---------------------------------------------------------------------------


def _match_html(sig: HtmlSignature, html_lower: str) -> bool:
    """Retourne True si au moins un pattern de la signature est present dans le HTML."""
    return any(p.lower() in html_lower for p in sig.patterns)


def _match_header(sig: HeaderSignature, headers: dict[str, str]) -> bool:
    """
    Retourne True si le header existe et, si des patterns sont definis,
    si au moins un pattern est present dans sa valeur (insensible a la casse).
    """
    value = headers.get(sig.header_key, "")
    if not value:
        return False
    # Liste vide = la presence seule du header suffit
    if not sig.patterns:
        return True
    value_lower = value.lower()
    return any(p.lower() in value_lower for p in sig.patterns)


def _collect_html_matches(sigs: list[HtmlSignature], html_lower: str) -> list[str]:
    """Retourne la liste ordonnee et dedupliquee des noms detectes dans le HTML."""
    seen: set[str] = set()
    result: list[str] = []
    for sig in sigs:
        if sig.name not in seen and _match_html(sig, html_lower):
            seen.add(sig.name)
            result.append(sig.name)
    return result


def _collect_header_matches(sigs: list[HeaderSignature], headers: dict[str, str]) -> list[str]:
    """Retourne la liste ordonnee et dedupliquee des noms detectes dans les headers."""
    seen: set[str] = set()
    result: list[str] = []
    for sig in sigs:
        if sig.name not in seen and _match_header(sig, headers):
            seen.add(sig.name)
            result.append(sig.name)
    return result


def _merge_unique(*lists: list[str]) -> list[str]:
    """Fusionne plusieurs listes en preservant l'ordre et en eliminant les doublons."""
    seen: set[str] = set()
    result: list[str] = []
    for lst in lists:
        for item in lst:
            if item not in seen:
                seen.add(item)
                result.append(item)
    return result


# ---------------------------------------------------------------------------
# Fonction principale publique
# ---------------------------------------------------------------------------


def detect_tech_stack(data: ScrapedData) -> TechStack:
    """
    Analyse le HTML et les headers HTTP pour identifier les technologies utilisees.

    Strategies de detection :
    - Signatures dans le HTML brut (scripts src, variables JS, attributs HTML, meta tags)
    - Headers HTTP proprietaires (CDN, serveur, runtime)

    Args:
        data: donnees brutes produites par scraper.scrape().

    Returns:
        TechStack: technologies identifiees par categorie, sans doublons.
                   Une categorie vide indique l'absence de signature reconnue,
                   pas une erreur de detection.
    """
    # Securite defensive : html et headers sont toujours presents mais peuvent etre vides
    html_lower: str = (data["html"] or "").lower()
    headers: dict[str, str] = data["response_headers"] or {}

    # Frameworks JS : HTML + header X-Powered-By (dedupliques)
    frameworks = _merge_unique(
        _collect_html_matches(_FRAMEWORK_HTML, html_lower),
        _collect_header_matches(_FRAMEWORK_HEADER, headers),
    )

    # CMS et builders : HTML uniquement
    cms = _collect_html_matches(_CMS_HTML, html_lower)

    # CDN et hebergement : HTML + headers proprietaires (dedupliques)
    cdn = _merge_unique(
        _collect_html_matches(_CDN_HTML, html_lower),
        _collect_header_matches(_CDN_HEADER, headers),
    )

    # Serveur HTTP : headers "server" et "x-powered-by" uniquement
    server = _collect_header_matches(_SERVER_HEADER, headers)

    # Analytics et trackers de mesure : HTML uniquement
    analytics = _collect_html_matches(_ANALYTICS_HTML, html_lower)

    # Tag managers : HTML uniquement
    tag_managers = _collect_html_matches(_TAG_MANAGER_HTML, html_lower)

    # Outils tiers notables : HTML uniquement
    other = _collect_html_matches(_OTHER_HTML, html_lower)

    return TechStack(
        frameworks=frameworks,
        cdn=cdn,
        cms=cms,
        server=server,
        analytics=analytics,
        tag_managers=tag_managers,
        other=other,
    )
