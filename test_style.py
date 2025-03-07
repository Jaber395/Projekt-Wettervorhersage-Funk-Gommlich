import pytest
import tinycss2
import os


def test_css_file_exists():
    """Test that the CSS file exists"""
    assert os.path.exists('style.css')


def test_css_file_syntax():
    """Test that the CSS file has valid syntax"""
    with open('style.css', 'r', encoding='utf-8') as f:
        css_content = f.read()

    # Parse the CSS content
    stylesheet = tinycss2.parse_stylesheet(css_content)

    # Filter out comments
    rules = [rule for rule in stylesheet if rule.type != 'comment']

    # Check if parsing was successful (no syntax errors)
    assert len(rules) > 0, "CSS file should contain valid rules"


def test_essential_selectors_exist():
    """Test that essential selectors are present in the CSS"""
    with open('style.css', 'r', encoding='utf-8') as f:
        css_content = f.read()

    # List of essential selectors that should be present
    essential_selectors = [
        'body',
        '.header',
        '.container',
        '.section_wrapper',
        '.section',
        '.section_search',
        '.section_results',
        '.button',
        'table'
    ]

    for selector in essential_selectors:
        assert selector in css_content, f"CSS should contain the '{selector}' selector"


def test_color_scheme_consistency():
    """Test that the color scheme is consistent"""
    with open('style.css', 'r', encoding='utf-8') as f:
        css_content = f.read()

    # Check for primary color usage
    primary_color = '#004d99'
    assert primary_color in css_content, "Primary color should be used in the CSS"

    # Count occurrences to ensure it's used multiple times (consistency)
    assert css_content.count(primary_color) >= 3, "Primary color should be used consistently"
