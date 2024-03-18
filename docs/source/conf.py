# Configuration file for the Sphinx documentation builder.

# -- Project information

project = 'qnngds'
copyright = '2024, QNN group'
author = 'QNN group'

release = '0.1'
version = '0.1.0'

import sys 
import os
sys.path.insert(0, os.path.abspath(os.path.join('..', '..', 'src')))
sys.path.insert(0, os.path.abspath('..'))


# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon'
]

autodoc_member_order = 'bysource'

napoleon_google_docstring = True
napoleon_use_param = False
napoleon_use_rtype = False
napoleon_include_init_with_doc = False
napoleon_attr_annotations = True


intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_rtd_theme'

# -- Options for EPUB output
epub_show_urls = 'footnote'
