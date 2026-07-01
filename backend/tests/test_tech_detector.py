"""
Tests unitaires pour tech_detector.py.

Verifie que les signatures HTML et les headers HTTP produisent
les bonnes detections par categorie, sans doublons.
"""

from app.scraper import ScrapedData
from app.tech_detector import detect_tech_stack


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _data(html: str = "", headers: dict | None = None) -> ScrapedData:
    return ScrapedData(
        url="https://example.com",
        page_title="",
        meta_description="",
        og_title="",
        og_description="",
        favicon_url=None,
        html=html,
        internal_links=[],
        response_headers=headers or {},
    )


# ---------------------------------------------------------------------------
# Frameworks JS — detection HTML
# ---------------------------------------------------------------------------


def test_detects_nextjs_from_html():
    result = detect_tech_stack(_data(html='<script src="/_next/static/chunk.js">'))
    assert "Next.js" in result.frameworks


def test_detects_nuxtjs_from_html():
    result = detect_tech_stack(_data(html='<div id="__nuxt"></div>'))
    assert "Nuxt.js" in result.frameworks


def test_detects_react_from_html():
    result = detect_tech_stack(_data(html='<div data-reactroot="">'))
    assert "React" in result.frameworks


def test_detects_vuejs_from_html():
    result = detect_tech_stack(_data(html='<div data-v-abc123="">'))
    assert "Vue.js" in result.frameworks


def test_detects_angular_from_html():
    result = detect_tech_stack(_data(html='<app-root ng-version="17.0.0"></app-root>'))
    assert "Angular" in result.frameworks


def test_detects_nextjs_from_xpoweredby_header():
    result = detect_tech_stack(_data(headers={"x-powered-by": "Next.js"}))
    assert "Next.js" in result.frameworks


def test_nextjs_not_duplicated_when_html_and_header_both_match():
    result = detect_tech_stack(_data(
        html='<script src="/_next/static/chunk.js">',
        headers={"x-powered-by": "Next.js"},
    ))
    assert result.frameworks.count("Next.js") == 1


# ---------------------------------------------------------------------------
# CMS
# ---------------------------------------------------------------------------


def test_detects_wordpress():
    result = detect_tech_stack(_data(html='<link href="/wp-content/themes/main.css">'))
    assert "WordPress" in result.cms


def test_detects_shopify():
    result = detect_tech_stack(_data(html='<script src="https://cdn.shopify.com/s/js/shop.js">'))
    assert "Shopify" in result.cms


def test_detects_webflow():
    result = detect_tech_stack(_data(html='<html data-wf-page="abc">'))
    assert "Webflow" in result.cms


# ---------------------------------------------------------------------------
# CDN — detection header
# ---------------------------------------------------------------------------


def test_detects_cloudflare_from_cf_ray_header():
    result = detect_tech_stack(_data(headers={"cf-ray": "abc123-CDG"}))
    assert "Cloudflare" in result.cdn


def test_detects_cloudflare_from_server_header():
    result = detect_tech_stack(_data(headers={"server": "cloudflare"}))
    assert "Cloudflare" in result.cdn


def test_cloudflare_not_duplicated_when_both_headers_present():
    result = detect_tech_stack(_data(headers={"cf-ray": "abc", "server": "cloudflare"}))
    assert result.cdn.count("Cloudflare") == 1


def test_detects_vercel_cdn():
    result = detect_tech_stack(_data(headers={"x-vercel-id": "cdg1::abc"}))
    assert "Vercel" in result.cdn


def test_detects_netlify_cdn():
    result = detect_tech_stack(_data(headers={"x-nf-request-id": "01abc"}))
    assert "Netlify" in result.cdn


# ---------------------------------------------------------------------------
# Serveur HTTP
# ---------------------------------------------------------------------------


def test_detects_nginx():
    result = detect_tech_stack(_data(headers={"server": "nginx/1.25"}))
    assert "nginx" in result.server


def test_detects_apache():
    result = detect_tech_stack(_data(headers={"server": "Apache/2.4.57"}))
    assert "Apache" in result.server


def test_detects_express_from_xpoweredby():
    result = detect_tech_stack(_data(headers={"x-powered-by": "Express"}))
    assert "Express.js" in result.server


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


def test_detects_segment():
    result = detect_tech_stack(_data(html="analytics.load('abc123')"))
    assert "Segment" in result.analytics


def test_detects_amplitude():
    result = detect_tech_stack(_data(html="amplitude.init('token')"))
    assert "Amplitude" in result.analytics


def test_detects_ga4():
    result = detect_tech_stack(_data(html='<script src="https://www.googletagmanager.com/gtag/js">'))
    assert "Google Analytics 4" in result.analytics


def test_detects_posthog():
    result = detect_tech_stack(_data(html="posthog.init('key', {api_host:'https://app.posthog.com'})"))
    assert "PostHog" in result.analytics


# ---------------------------------------------------------------------------
# Cas limites
# ---------------------------------------------------------------------------


def test_empty_html_returns_empty_stack():
    result = detect_tech_stack(_data())
    assert result.frameworks == []
    assert result.cms == []
    assert result.cdn == []
    assert result.server == []
    assert result.analytics == []


def test_detection_is_case_insensitive():
    result = detect_tech_stack(_data(html='<SCRIPT SRC="/_NEXT/STATIC/CHUNK.JS">'))
    assert "Next.js" in result.frameworks


def test_unrelated_html_returns_nothing():
    result = detect_tech_stack(_data(html="<html><body><h1>Bonjour</h1></body></html>"))
    assert result.frameworks == []
    assert result.cms == []
