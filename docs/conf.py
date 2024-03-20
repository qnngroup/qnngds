# File: docs/conf.py

# -- Project information

project = 'qnngds'
copyright = '2024, QNN group'
author = 'QNN group'

extensions = [
   "multiproject",
   # Your other extensions.
   "sphinx.ext.intersphinx",
   "sphinx.ext.autosectionlabel",
]

multiproject_projects = {
    "user": {
        "path": "user",
    },
    "dev": {
        "use_config_file": False,
        "config": {
            "project": "QNNGDS developer documentation",
            "html_title": "QNNGDS developer documentation",
            "path": "dev",
        },
    },
}

# Common options.
html_theme = "sphinx_rtd_theme"
epub_show_urls = 'footnote'

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']