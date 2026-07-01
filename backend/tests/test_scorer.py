"""
Tests unitaires pour scorer.py.

Verifie que les 8 facteurs ponderees produisent les bons points
et que le score global est correctement assemble et clampe.
"""

import pytest

from app.models import CompanyProfile, GtmSignals, TechStack
from app.scorer import compute_score


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _profile(**kwargs) -> CompanyProfile:
    defaults = {"name": "Acme", "description": "", "sector": "", "estimated_size": "", "audience": ""}
    return CompanyProfile(**{**defaults, **kwargs})


def _gtm(**kwargs) -> GtmSignals:
    defaults = {
        "chat_tools": [], "ad_pixels": [], "analytics_tools": [],
        "has_pricing_page": False, "has_demo_form": False, "has_careers_page": False,
    }
    return GtmSignals(**{**defaults, **kwargs})


def _tech(**kwargs) -> TechStack:
    defaults = {"frameworks": [], "cdn": [], "cms": [], "server": [], "analytics": [], "tag_managers": [], "other": []}
    return TechStack(**{**defaults, **kwargs})


def _points(score, name: str) -> int:
    return next(f.points for f in score.factors if f.name == name)


# ---------------------------------------------------------------------------
# Facteur 1 : Audience B2B
# ---------------------------------------------------------------------------


def test_audience_b2b_gives_25():
    score = compute_score(_profile(audience="B2B"), _tech(), _gtm())
    assert _points(score, "Audience B2B") == 25


def test_audience_mixed_gives_12():
    score = compute_score(_profile(audience="mixed"), _tech(), _gtm())
    assert _points(score, "Audience B2B") == 12


def test_audience_b2c_gives_0():
    score = compute_score(_profile(audience="B2C"), _tech(), _gtm())
    assert _points(score, "Audience B2B") == 0


def test_audience_empty_gives_0():
    score = compute_score(_profile(audience=""), _tech(), _gtm())
    assert _points(score, "Audience B2B") == 0


# ---------------------------------------------------------------------------
# Facteur 2 : Analytics avances
# ---------------------------------------------------------------------------


def test_analytics_zero_advanced_gives_0():
    score = compute_score(_profile(), _tech(), _gtm(analytics_tools=["Google Analytics 4"]))
    assert _points(score, "Analytics avances (Segment, Amplitude, Mixpanel...)") == 0


def test_analytics_one_advanced_gives_9():
    score = compute_score(_profile(), _tech(), _gtm(analytics_tools=["Segment"]))
    assert _points(score, "Analytics avances (Segment, Amplitude, Mixpanel...)") == 9


def test_analytics_two_advanced_gives_12():
    score = compute_score(_profile(), _tech(), _gtm(analytics_tools=["Segment", "Amplitude"]))
    assert _points(score, "Analytics avances (Segment, Amplitude, Mixpanel...)") == 12


def test_analytics_three_plus_gives_15():
    score = compute_score(_profile(), _tech(), _gtm(analytics_tools=["Segment", "Amplitude", "Mixpanel"]))
    assert _points(score, "Analytics avances (Segment, Amplitude, Mixpanel...)") == 15


def test_analytics_ga4_only_not_counted_as_advanced():
    score = compute_score(_profile(), _tech(), _gtm(analytics_tools=["Google Analytics 4", "Hotjar"]))
    assert _points(score, "Analytics avances (Segment, Amplitude, Mixpanel...)") == 0


# ---------------------------------------------------------------------------
# Facteur 3 : Page pricing
# ---------------------------------------------------------------------------


def test_pricing_page_present_gives_12():
    score = compute_score(_profile(), _tech(), _gtm(has_pricing_page=True))
    assert _points(score, "Page pricing presente") == 12


def test_pricing_page_absent_gives_0():
    score = compute_score(_profile(), _tech(), _gtm(has_pricing_page=False))
    assert _points(score, "Page pricing presente") == 0


# ---------------------------------------------------------------------------
# Facteur 4 : Pixels publicitaires B2B
# ---------------------------------------------------------------------------


def test_ad_pixels_linkedin_gives_8():
    score = compute_score(_profile(), _tech(), _gtm(ad_pixels=["LinkedIn Insight Tag"]))
    assert _points(score, "Pixels publicitaires B2B (LinkedIn, Google Ads, Bing)") == 8


def test_ad_pixels_google_gives_6():
    score = compute_score(_profile(), _tech(), _gtm(ad_pixels=["Google Ads"]))
    assert _points(score, "Pixels publicitaires B2B (LinkedIn, Google Ads, Bing)") == 6


def test_ad_pixels_bing_gives_3():
    score = compute_score(_profile(), _tech(), _gtm(ad_pixels=["Bing Ads"]))
    assert _points(score, "Pixels publicitaires B2B (LinkedIn, Google Ads, Bing)") == 3


def test_ad_pixels_linkedin_and_google_capped_at_12():
    # 8 + 6 = 14, plafonné à 12
    score = compute_score(_profile(), _tech(), _gtm(ad_pixels=["LinkedIn Insight Tag", "Google Ads"]))
    assert _points(score, "Pixels publicitaires B2B (LinkedIn, Google Ads, Bing)") == 12


def test_ad_pixels_empty_gives_0():
    score = compute_score(_profile(), _tech(), _gtm(ad_pixels=[]))
    assert _points(score, "Pixels publicitaires B2B (LinkedIn, Google Ads, Bing)") == 0


# ---------------------------------------------------------------------------
# Facteur 5 : Formulaire demo
# ---------------------------------------------------------------------------


def test_demo_form_present_gives_10():
    score = compute_score(_profile(), _tech(), _gtm(has_demo_form=True))
    assert _points(score, "Formulaire demo / Contact sales") == 10


def test_demo_form_absent_gives_0():
    score = compute_score(_profile(), _tech(), _gtm(has_demo_form=False))
    assert _points(score, "Formulaire demo / Contact sales") == 0


# ---------------------------------------------------------------------------
# Facteur 6 : Chat client
# ---------------------------------------------------------------------------


def test_chat_tool_present_gives_10():
    score = compute_score(_profile(), _tech(), _gtm(chat_tools=["Intercom"]))
    assert _points(score, "Outil de chat client (Intercom, Drift, Crisp...)") == 10


def test_chat_tool_absent_gives_0():
    score = compute_score(_profile(), _tech(), _gtm(chat_tools=[]))
    assert _points(score, "Outil de chat client (Intercom, Drift, Crisp...)") == 0


# ---------------------------------------------------------------------------
# Facteur 7 : Taille entreprise
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("size,expected", [
    ("PME 50-500",             8),
    ("ETI 500-5000",           6),
    ("startup <50",            4),
    ("grande entreprise >5000", 2),
    ("",                        0),
])
def test_company_size_points(size, expected):
    score = compute_score(_profile(estimated_size=size), _tech(), _gtm())
    assert _points(score, "Taille entreprise (cible PME/ETI)") == expected


# ---------------------------------------------------------------------------
# Facteur 8 : Stack tech moderne
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("framework", ["Next.js", "React", "Vue.js", "Angular", "Svelte"])
def test_modern_framework_gives_8(framework):
    score = compute_score(_profile(), _tech(frameworks=[framework]), _gtm())
    assert _points(score, "Stack tech moderne (Next.js, React, Vue.js...)") == 8


def test_no_modern_framework_gives_0():
    score = compute_score(_profile(), _tech(frameworks=["jQuery"]), _gtm())
    assert _points(score, "Stack tech moderne (Next.js, React, Vue.js...)") == 0


# ---------------------------------------------------------------------------
# Score global
# ---------------------------------------------------------------------------


def test_perfect_b2b_saas_score():
    """Profil ideal : tous les signaux B2B au maximum."""
    score = compute_score(
        _profile(audience="B2B", estimated_size="PME 50-500"),
        _tech(frameworks=["Next.js"]),
        _gtm(
            chat_tools=["Intercom"],
            ad_pixels=["LinkedIn Insight Tag", "Google Ads"],
            analytics_tools=["Segment", "Amplitude", "Mixpanel"],
            has_pricing_page=True,
            has_demo_form=True,
        ),
    )
    assert score.score == 100


def test_pure_b2c_no_signals_score_is_zero():
    """Profil B2C sans aucun signal : score nul."""
    score = compute_score(_profile(audience="B2C"), _tech(), _gtm())
    assert score.score == 0


def test_score_clamped_between_0_and_100():
    score = compute_score(_profile(), _tech(), _gtm())
    assert 0 <= score.score <= 100


def test_score_has_8_factors():
    score = compute_score(_profile(), _tech(), _gtm())
    assert len(score.factors) == 8


def test_label_ideal_when_score_80_plus():
    score = compute_score(
        _profile(audience="B2B", estimated_size="PME 50-500"),
        _tech(frameworks=["Next.js"]),
        _gtm(
            chat_tools=["Intercom"],
            ad_pixels=["LinkedIn Insight Tag"],
            analytics_tools=["Segment", "Amplitude", "Mixpanel"],
            has_pricing_page=True,
            has_demo_form=True,
        ),
    )
    assert score.score >= 80
    assert score.label == "Cible ideale B2B SaaS"
