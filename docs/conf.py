# docs/conf.py
# zlmdb documentation configuration - modernized for 2025
import os
import sys
from datetime import datetime

# -- Path setup --------------------------------------------------------------
sys.path.insert(0, os.path.abspath("../src"))

# monkey-patch txaio so that we can "use" both twisted *and* asyncio,
# at least at import time
import txaio


def use_tx():
    "monkey-patched for doc-building"
    from txaio import tx

    txaio._use_framework(tx)


def use_aio():
    "monkey-patched for doc-building"
    from txaio import aio

    txaio._use_framework(aio)


txaio.use_twisted = use_tx
txaio.use_asyncio = use_aio

# -- Project information -----------------------------------------------------
project = "zlmdb"
author = "The WAMP/Autobahn/Crossbar.io OSS Project"
copyright = f"2018-{datetime.now():%Y}, typedef int GmbH (Germany)"
language = "en"

# Get version from the package
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
with open(os.path.join(base_dir, "src", "zlmdb", "_version.py")) as f:
    exec(f.read())  # defines __version__

version = release = __version__  # noqa

# -- General configuration ---------------------------------------------------
extensions = [
    # MyST Markdown support
    "myst_parser",

    # Core Sphinx extensions
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.ifconfig",
    "sphinx.ext.doctest",
    "sphinx.ext.inheritance_diagram",

    # Modern UX extensions
    "sphinx_design",
    "sphinx_copybutton",
    "sphinxext.opengraph",
    "sphinxcontrib.images",
    "sphinxcontrib.spelling",

    # API documentation
    "autoapi.extension",
]

# Source file suffixes (both RST and MyST Markdown)
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# The master toctree document
master_doc = "index"

# Exclude patterns
exclude_patterns = ["_build", "README.md"]

# -- MyST Configuration ------------------------------------------------------
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "tasklist",
    "attrs_block",
    "attrs_inline",
    "smartquotes",
    "linkify",
]
myst_heading_anchors = 3

# -- AutoAPI Configuration ---------------------------------------------------
autoapi_type = "python"
autoapi_dirs = ["../src/zlmdb"]
autoapi_add_toctree_entry = True
autoapi_keep_files = False              # Cleaner RTD builds
autoapi_generate_api_docs = True
autoapi_options = [
    "members",
    "undoc-members",
    "private-members",
    "special-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]
autoapi_ignore = [
    "*/_version.py",
    "*/test_*.py",
    "*/*_test.py",
    "*/conftest.py",
]
autoapi_python_use_implicit_namespaces = True
autoapi_member_order = "alphabetical"   # Predictable ordering

# -- Intersphinx Configuration -----------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "twisted": ("https://docs.twisted.org/en/stable/", None),
    "txaio": ("https://txaio.readthedocs.io/en/latest/", None),
    "autobahn": ("https://autobahn.readthedocs.io/en/latest/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}
intersphinx_cache_limit = 5

# -- HTML Output (Furo Theme) ------------------------------------------------
html_theme = "furo"
html_title = f"{project} {release}"

# Furo theme options with Noto fonts and Autobahn subarea colors
html_theme_options = {
    # Source repository links
    "source_repository": "https://github.com/crossbario/zlmdb/",
    "source_branch": "master",
    "source_directory": "docs/",

    # Noto fonts and Autobahn Medium Blue (#027eae) accent color
    "light_css_variables": {
        "font-stack": "'Noto Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "font-stack--monospace": "'Noto Sans Mono', SFMono-Regular, Menlo, Consolas, monospace",
        "color-brand-primary": "#027eae",
        "color-brand-content": "#027eae",
    },
    "dark_css_variables": {
        "font-stack": "'Noto Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "font-stack--monospace": "'Noto Sans Mono', SFMono-Regular, Menlo, Consolas, monospace",
        "color-brand-primary": "#027eae",
        "color-brand-content": "#027eae",
    },
}

# Logo and favicon (synced from autobahn-python by `just sync-images`)
html_logo = "_static/img/autobahn_logo_blue.svg"
html_favicon = "_static/favicon.ico"

# Static files
html_static_path = ["_static"]
html_css_files = [
    # Load Noto fonts from Google Fonts
    "https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;600;700&family=Noto+Sans+Mono:wght@400;500&display=swap",
]

# -- sphinxcontrib-images Configuration --------------------------------------
images_config = {
    "override_image_directive": True,
    "default_image_width": "80%",
}

# -- Spelling Configuration --------------------------------------------------
spelling_lang = "en_US"
spelling_word_list_filename = "spelling_wordlist.txt"
spelling_show_suggestions = True

# -- OpenGraph (Social Media Meta Tags) -------------------------------------
ogp_site_url = "https://zlmdb.readthedocs.io/en/latest/"

# -- Miscellaneous -----------------------------------------------------------
todo_include_todos = True
add_module_names = False
autosectionlabel_prefix_document = True
pygments_style = "sphinx"
pygments_dark_style = "monokai"
