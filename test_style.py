import pytest
import re
import os

# Path to the CSS file
CSS_FILE = 'style.css'


def read_css_file():
    """Read the CSS file and return its content."""
    if not os.path.exists(CSS_FILE):
        pytest.fail(f"CSS file not found: {CSS_FILE}")

    with open(CSS_FILE, 'r', encoding='utf-8') as f:
        return f.read()


def test_file_exists():
    """Test that the CSS file exists."""
    assert os.path.exists(CSS_FILE), f"CSS file not found: {CSS_FILE}"


def test_valid_css_structure():
    """Test that the CSS file has a valid structure (opening and closing braces match)."""
    css_content = read_css_file()

    # Count opening and closing braces
    opening_braces = css_content.count('{')
    closing_braces = css_content.count('}')

    assert opening_braces == closing_braces, f"Mismatched braces: {opening_braces} opening vs {closing_braces} closing"


def test_root_variables_exist():
    """Test that the :root variables are defined."""
    css_content = read_css_file()

    # Check if :root exists
    assert ":root {" in css_content, "Root variables block not found"

    # Check that all required variables exist
    required_variables = [
        "--color-primary",
        "--color-primary-dark",
        "--color-background",
        "--color-white",
        "--color-text",
        "--color-border",
        "--color-hover",
        "--color-overlay"
    ]

    for var in required_variables:
        assert var in css_content, f"Required variable not found: {var}"


def test_essential_selectors_exist():
    """Test that essential selectors exist in the CSS."""
    css_content = read_css_file()

    essential_selectors = [
        "body",
        ".header",
        ".container",
        ".section-wrapper",
        ".section",
        ".section-search",
        ".section-results",
        "h2",
        ".button",
        ".input-field",
        "table",
        "th",
        "td",
        "#map",
        ".chart"
    ]

    for selector in essential_selectors:
        # Modified pattern to find selectors even if they're part of grouped rules
        # This will match selectors followed by either a comma, a space+{, or a newline+{
        pattern = rf"{re.escape(selector)}(\s*{{|\s*,|,\s*|\n)"
        assert re.search(pattern, css_content), f"Essential selector not found: {selector}"


def test_responsive_elements():
    """Test that there are responsive elements in the CSS."""
    css_content = read_css_file()

    # Check for media queries or flex layouts
    has_responsive_elements = "@media" in css_content or "display: flex" in css_content

    assert has_responsive_elements, "No responsive elements found (no @media queries or flex layouts)"


def test_animation_exists():
    """Test that animations are defined in the CSS."""
    css_content = read_css_file()

    # Check for keyframes
    has_keyframes = "@keyframes" in css_content

    assert has_keyframes, "No animations (@keyframes) found"


def test_color_consistency():
    """Test that colors are consistent and use variables."""
    css_content = read_css_file()

    # Count variable usage
    var_usage_count = css_content.count("var(--color")

    # Count direct color usage (hex, rgb, rgba)
    direct_color_pattern = r'#[0-9a-fA-F]{3,8}|rgba?\([^)]+\)'
    direct_color_matches = re.findall(direct_color_pattern, css_content)

    # Some direct color usage is acceptable (like in the :root definition)
    # but we expect most colors to use variables
    assert var_usage_count > len(direct_color_matches) / 2, "Color variables are not used consistently"


def test_no_important_flags():
    """Test that !important is not overused."""
    css_content = read_css_file()

    important_count = css_content.count("!important")

    # A few !important flags might be necessary, but too many indicate poor CSS structure
    assert important_count <= 3, f"Too many !important flags found: {important_count}"


def test_class_naming_convention():
    """Test that class naming follows a consistent convention."""
    css_content = read_css_file()

    # Extract all class names
    class_pattern = r'\.([\w-]+)'
    class_names = re.findall(class_pattern, css_content)

    # Check if they follow kebab-case convention
    for name in class_names:
        assert '-' in name or len(name) == 1 or name.islower(), f"Class name doesn't follow kebab-case: {name}"
