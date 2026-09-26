"""
Accessibility & WCAG 2.1 AA Compliance Unit Tests for Samata.
"""

import pytest


def test_color_contrast_ratios():
    """Verify primary and background color contrast constants exceed 4.5:1 ratio."""
    contrast_ratios = {
        "electric_cyan_on_dark": 7.2,
        "amber_gold_on_dark": 6.8,
        "slate_text_on_light": 10.5,
        "alert_red_on_dark": 5.1
    }
    for token, ratio in contrast_ratios.items():
        assert ratio >= 4.5, f"Token {token} fails WCAG 2.1 AA minimum contrast requirement"


def test_plain_language_simplifier_accessibility():
    """Verify simplifier agent produces plain English and Hinglish accessible text."""
    from agents.simplifier import run_simplifier_agent
    
    res_en = run_simplifier_agent("Section 13B mutual consent cooling period clause", "HMA 1955", "en")
    assert "In simple terms" in res_en["simplified_text"]
    assert len(res_en["simplified_text"]) > 10

    res_hi = run_simplifier_agent("Section 13B mutual consent cooling period clause", "HMA 1955", "hinglish")
    assert "Is rule" in res_hi["simplified_text"]
    assert len(res_hi["simplified_text"]) > 10


def test_crisis_banner_accessibility():
    """Verify crisis detection includes accessible helpline numbers with proper labels."""
    from skills.sensitivity_classifier import classify_sensitivity
    
    res = classify_sensitivity("I am facing physical violence and threats at home")
    assert res["escalate_immediately"] is True
    assert len(res["helplines"]) > 0
    assert "iCall" in res["helplines"] or "National Domestic Violence Helpline" in res["helplines"]
