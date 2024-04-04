import os
import sys
from multiproject.utils import get_project

sys.path.insert(0, os.path.abspath(os.path.join('..', 'src')))

extensions = [
    "multiproject",
    # "sphinx_copybutton",
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
]

autodoc_member_order = 'bysource'

napoleon_google_docstring = True
napoleon_use_param = False
napoleon_use_rtype = False
napoleon_include_init_with_doc = False
napoleon_attr_annotations = True

pygments_style = 'sphinx'
todo_include_todos = True

# multiproject_projects = {
#     "user": {
#         "use_config_file": False,
#         "config": {
#             "project": "qnngds",
#             "html_title": "qnngds-user",
#         },
#     },
#     "dev": {
#         "use_config_file": False,
#         "config": {
#             "project": "qnngds",
#             "html_title": "qnngds-developer",
#         },
#     },
# }

multiproject_projects = {
   "user": {},
   "dev": {},
}


current_project = get_project(multiproject_projects)

locale_dirs = [f"{current_project}/locale/"]

if current_project == "user":
    extensions += ['sphinx.ext.napoleon']
    project = "qnngds"
elif current_project == "dev":
    project = "qnngds-dev"

master_doc = "index"
copyright = "QNN group"
version = "0.1.0"
release = version

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.10/", None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}

html_theme = "sphinx_rtd_theme"

# Activate autosectionlabel plugin
autosectionlabel_prefix_document = True
