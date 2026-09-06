"""Sphinx configuration for the DataForge documentation.

Build with ``make docs`` (or ``uv run sphinx-build -b html docs docs/_build/html``).
"""

from importlib.metadata import version as package_version

# -- Project information -----------------------------------------------------

project = "DataForge"
author = "AdnanBoxwala"
copyright = "2026, AdnanBoxwala"

# Read the version from the installed package so it can never drift from
# pyproject.toml.
release = package_version("dataforge")
version = release

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",  # pull docstrings out of the package
    "sphinx.ext.autosummary",  # generate summary tables of members
    "sphinx.ext.napoleon",  # understand Google-style docstrings
    "sphinx.ext.viewcode",  # link each documented object to its source
    "sphinx.ext.intersphinx",  # link to Python and numpy docs
    "sphinx_autodoc_typehints",  # render type hints as parameter types
    "myst_parser",  # allow Markdown alongside reStructuredText
]

templates_path = ["_templates"]
exclude_patterns = ["_build"]

# Accept both formats: narrative pages are Markdown, API pages are reST because
# autodoc directives read more naturally there.
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# -- Autodoc -----------------------------------------------------------------

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "description"
autosummary_generate = True

# Docstrings are Google style, per the project's conventions.
napoleon_google_docstring = True
napoleon_numpy_docstring = False
# Render "Attributes:" as :ivar: rather than separate object descriptions, which
# otherwise collide with the fields autodoc already emits for a dataclass.
napoleon_use_ivar = True

# -- Intersphinx -------------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}

# -- HTML output -------------------------------------------------------------

html_theme = "furo"
html_title = f"DataForge {release}"
html_static_path: list[str] = []
