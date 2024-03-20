# File: docs/user/conf.py

release = '0.1'
version = '0.1.0'

import sys 
import os
sys.path.insert(0, os.path.abspath(os.path.join('..', '..', 'src')))


extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
]

autodoc_member_order = 'bysource'

napoleon_google_docstring = True
napoleon_use_param = False
napoleon_use_rtype = False
napoleon_include_init_with_doc = False
napoleon_attr_annotations = True
