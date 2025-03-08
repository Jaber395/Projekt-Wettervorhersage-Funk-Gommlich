import pytest
import tinycss2
import os
import re


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
        'table',
        '.button_search',
        '.button:hover',
        '.button-container',
        '.input-field',
        '.input-date',
        '.section_date',
        'label',
        '.results_table_wrapper',
        '.results_table_wrapper2',
        'thead',
        'tbody',
        'th',
        'td',
        'tr',
        'tr:nth-child(even)',
        '.container_charts',
        '.chart',
        '.table-button',
        '.table-button:hover',
        '.button.active',
        '.station-button',
        '.station-button:hover',
        '#loadingOverlay',
        '.loader',
        '@keyframes spin'
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

    # Check for hover color
    hover_color = '#003366'
    assert hover_color in css_content, "Hover color should be used in the CSS"


def test_responsive_layout():
    """Test that there are responsive layout features"""
    with open('style.css', 'r', encoding='utf-8') as f:
        css_content = f.read()

    # Check for flex layouts
    assert 'display: flex' in css_content, "CSS should use flex layouts"
    assert 'flex-direction' in css_content, "CSS should use flex direction"

    # Check for responsive width settings
    assert 'width: 100%' in css_content, "CSS should have responsive width settings"
    assert 'max-height' in css_content, "CSS should use max-height for container limitations"


def test_scrollable_elements():
    """Test that scrollable elements are properly defined"""
    with open('style.css', 'r', encoding='utf-8') as f:
        css_content = f.read()

    # Check for overflow settings
    assert 'overflow-y: auto' in css_content, "CSS should define vertical scrolling"
    assert 'overflow: hidden' in css_content, "CSS should use overflow: hidden where appropriate"


def test_animation_definitions():
    """Test that animations are properly defined"""
    with open('style.css', 'r', encoding='utf-8') as f:
        css_content = f.read()

    # Check for keyframes definition
    assert '@keyframes spin' in css_content, "CSS should define keyframes for animations"
    assert 'animation:' in css_content, "CSS should use animation property"

    # Check animation content
    assert 'transform: rotate(0deg)' in css_content, "Animation should include rotation transform"
    assert 'transform: rotate(360deg)' in css_content, "Animation should include full rotation"


def test_shadow_and_visual_effects():
    """Test that visual effects like shadows are defined"""
    with open('style.css', 'r', encoding='utf-8') as f:
        css_content = f.read()

    # Check for box-shadow
    assert 'box-shadow:' in css_content, "CSS should define box-shadows"
    assert 'border-radius:' in css_content, "CSS should use border-radius for rounded corners"


def test_loading_overlay():
    """Test that loading overlay is properly defined"""
    with open('style.css', 'r', encoding='utf-8') as f:
        css_content = f.read()

    # Check loading overlay properties
    assert '#loadingOverlay' in css_content, "CSS should define a loading overlay"
    assert 'position: fixed' in css_content, "Loading overlay should use fixed positioning"
    assert 'z-index:' in css_content, "Loading overlay should have a z-index"


def test_table_styling():
    """Test that tables are styled correctly"""
    with open('style.css', 'r', encoding='utf-8') as f:
        css_content = f.read()

    # Check table styling
    assert 'table' in css_content, "CSS should style tables"
    assert 'th' in css_content, "CSS should style table headers"
    assert 'td' in css_content, "CSS should style table cells"
    assert 'tr:nth-child(even)' in css_content, "CSS should use zebra striping for tables"
    assert 'position: sticky' in css_content, "CSS should use sticky positioning for table headers"
