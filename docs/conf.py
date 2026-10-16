"""Sphinx configuration for the ETRM & Energy Trading Glossary."""

project = "ETRM & Energy Trading Glossary"
author = "Roman Denysenko"
copyright = "2026, Roman Denysenko"
release = "1.0"

extensions = [
    "myst_parser",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_design",
]

myst_enable_extensions = ["colon_fence", "deflist", "fieldlist"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_title = "ETRM & Energy Trading Glossary"
html_short_title = "ETRM Glossary"

html_css_files = ["custom.css"]

html_theme_options = {
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 3,
    "includehidden": True,
    "titles_only": False,
    "prev_next_buttons_location": "both",
}

html_sidebars = {
    "**": ["globaltoc.html", "relations.html", "searchbox.html"],
}

# Autosection labels let us cross-reference generated pages,
# e.g. :ref:`glossary-s_2`
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 3

# Fail on broken references — Documentation-as-Code
nitpicky = False
suppress_warnings = ["myst.header"]