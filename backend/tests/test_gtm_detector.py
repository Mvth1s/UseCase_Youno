"""
Tests unitaires pour gtm_detector.py.

Verifie que les outils de chat, pixels, analytics et pages cles
sont correctement detectes depuis le HTML et les liens internes.
"""

import pytest

from app.scraper import ScrapedData
from app.gtm_detector import detect_gtm_signals


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _data(html: str = "", links: list[str] | None = None) -> ScrapedData:
    return ScrapedData(
        url="https://example.com",
        page_title="",
        meta_description="",
        og_title="",
        og_description="",
        favicon_url=None,
        html=html,
        internal_links=links or [],
        response_headers={},
    )


# ---------------------------------------------------------------------------
# Outils de chat
# ---------------------------------------------------------------------------


def test_detects_intercom():
    result = detect_gtm_signals(_data(html="widget.intercom.io/widget/abc"))
    assert "Intercom" in result.chat_tools


def test_detects_drift():
    result = detect_gtm_signals(_data(html='<script src="https://js.drift.com/drift.js">'))
    assert "Drift" in result.chat_tools


def test_detects_crisp():
    result = detect_gtm_signals(_data(html='<script src="https://client.crisp.chat/l.js">'))
    assert "Crisp" in result.chat_tools


def test_detects_tawkto():
    result = detect_gtm_signals(_data(html='<script src="https://embed.tawk.to/abc/default">'))
    assert "Tawk.to" in result.chat_tools


def test_no_chat_tool_when_html_empty():
    result = detect_gtm_signals(_data())
    assert result.chat_tools == []


# ---------------------------------------------------------------------------
# Pixels publicitaires
# ---------------------------------------------------------------------------


def test_detects_meta_pixel():
    result = detect_gtm_signals(_data(html="fbq('init', '123456789')"))
    assert "Meta Pixel" in result.ad_pixels


def test_detects_linkedin_insight_tag():
    result = detect_gtm_signals(_data(html="var _linkedin_partner_id = '1234';"))
    assert "LinkedIn Insight Tag" in result.ad_pixels


def test_detects_google_ads():
    result = detect_gtm_signals(_data(html="gtag('config', 'AW-12345')"))
    assert "Google Ads" in result.ad_pixels


def test_detects_twitter_ads():
    result = detect_gtm_signals(_data(html='<script src="https://static.ads-twitter.com/uwt.js">'))
    assert "Twitter/X Ads" in result.ad_pixels


def test_detects_bing_ads():
    result = detect_gtm_signals(_data(html="window.uetq = window.uetq || [];"))
    assert "Bing Ads" in result.ad_pixels


def test_no_ad_pixels_when_html_empty():
    result = detect_gtm_signals(_data())
    assert result.ad_pixels == []


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


def test_detects_ga4():
    result = detect_gtm_signals(_data(html='<script src="https://www.googletagmanager.com/gtag/js">'))
    assert "Google Analytics 4" in result.analytics_tools


def test_detects_segment():
    result = detect_gtm_signals(_data(html="analytics.load('abc123')"))
    assert "Segment" in result.analytics_tools


def test_detects_amplitude():
    result = detect_gtm_signals(_data(html="amplitude.init('key')"))
    assert "Amplitude" in result.analytics_tools


def test_detects_mixpanel():
    result = detect_gtm_signals(_data(html="mixpanel.init('token')"))
    assert "Mixpanel" in result.analytics_tools


def test_detects_hotjar():
    result = detect_gtm_signals(_data(html="hjid:1234567, hjsv:6, _hjsettings"))
    assert "Hotjar" in result.analytics_tools


def test_detects_posthog():
    result = detect_gtm_signals(_data(html="posthog.init('key', {api_host:'https://app.posthog.com'})"))
    assert "PostHog" in result.analytics_tools


# ---------------------------------------------------------------------------
# Page pricing (detection via liens internes)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("link", [
    "/pricing", "/plans", "/tarifs", "/price", "/subscription", "/upgrade",
])
def test_detects_pricing_page_from_link(link):
    result = detect_gtm_signals(_data(links=[f"https://example.com{link}"]))
    assert result.has_pricing_page is True


def test_no_pricing_page_when_no_matching_link():
    result = detect_gtm_signals(_data(links=["https://example.com/about", "https://example.com/blog"]))
    assert result.has_pricing_page is False


# ---------------------------------------------------------------------------
# Formulaire demo (lien OU texte CTA)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("link", [
    "/demo", "/request-demo", "/book-a-demo", "/schedule-demo",
])
def test_detects_demo_from_link(link):
    result = detect_gtm_signals(_data(links=[f"https://example.com{link}"]))
    assert result.has_demo_form is True


@pytest.mark.parametrize("cta", [
    "Book a Demo", "Get a Demo", "Request a Demo",
    "See it in action", "Start for free",
])
def test_detects_demo_from_cta_text(cta):
    result = detect_gtm_signals(_data(html=f'<a href="/demo">{cta}</a>'))
    assert result.has_demo_form is True


def test_demo_detection_is_case_insensitive():
    result = detect_gtm_signals(_data(html="BOOK A DEMO"))
    assert result.has_demo_form is True


def test_no_demo_when_no_signal():
    result = detect_gtm_signals(_data(html="<p>Contactez-nous</p>"))
    assert result.has_demo_form is False


# ---------------------------------------------------------------------------
# Page careers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("link", [
    "/careers", "/jobs", "/hiring", "/join-us", "/open-positions",
])
def test_detects_careers_from_link(link):
    result = detect_gtm_signals(_data(links=[f"https://example.com{link}"]))
    assert result.has_careers_page is True


def test_no_careers_when_no_matching_link():
    result = detect_gtm_signals(_data(links=["https://example.com/team"]))
    assert result.has_careers_page is False


# ---------------------------------------------------------------------------
# Cas limites
# ---------------------------------------------------------------------------


def test_empty_data_returns_all_empty():
    result = detect_gtm_signals(_data())
    assert result.chat_tools == []
    assert result.ad_pixels == []
    assert result.analytics_tools == []
    assert result.has_pricing_page is False
    assert result.has_demo_form is False
    assert result.has_careers_page is False


def test_no_duplicates_in_chat_tools():
    html = "widget.intercom.io app.intercom.com intercomsettings"
    result = detect_gtm_signals(_data(html=html))
    assert result.chat_tools.count("Intercom") == 1


def test_detection_case_insensitive_for_html():
    result = detect_gtm_signals(_data(html="CDN.SEGMENT.COM"))
    assert "Segment" in result.analytics_tools
