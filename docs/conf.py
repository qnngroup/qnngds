"""
Shared Sphinx configuration using sphinx-multiproject.

To build each project, the ``PROJECT`` environment variable is used.

.. code:: console

   $ make html  # build default project
   $ PROJECT=dev make html  # build the dev project

for more information read https://sphinx-multiproject.readthedocs.io/.
"""

import os
import sys
from multiproject.utils import get_project

sys.path.insert(0, os.path.abspath(os.path.join('..', 'src')))

extensions = [
    "multiproject",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
]

multiproject_projects = {
    "user": {
        "use_config_file": False,
        "config": {
            "project": "QNNGDS user documentation",
            "html_title": "QNNGDS user documentation",
        },
    },
    "dev": {
        "use_config_file": False,
        "config": {
            "project": "QNNGDS developer documentation",
            "html_title": "QNNGDS developer documentation",
        },
    },
}

docset = get_project(multiproject_projects)

master_doc = "index"
copyright = "QNN group"
version = "0.1.0"
release = version

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.10/", None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}


html_theme = "sphinx_rtd_theme"
html_static_path = ["_static", f"{docset}/_static"]

# Activate autosectionlabel plugin
autosectionlabel_prefix_document = True
