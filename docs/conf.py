import os
import sys
from importlib.metadata import version

sys.path.insert(0, os.path.abspath(os.path.join("..", "src")))

extensions = [
    "sphinx_copybutton",
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.viewcode",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathbase",
]

autodoc_member_order = "bysource"

napoleon_google_docstring = True
napoleon_use_param = False
napoleon_use_rtype = False
napoleon_include_init_with_doc = False
napoleon_attr_annotations = True

pygments_style = "sphinx"
todo_include_todos = True


autodoc_type_aliases = (
    {
        "DeviceFactory": "ComponentFactory",
        "DeviceSpec": "DeviceSpec",
        "CrossSectionFactory": "CrossSectionFactory",
        "CrossSectionSpec": "CrossSectionSpec",
        "LayerSpec": "LayerSpec",
        "LayerSpecs": "LayerSpecs",
    },
)


project = "qnngds"

master_doc = "index"
copyright = "QNN group"
version = version("qnngds")
release = version

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.10/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}

html_theme = "sphinx_rtd_theme"

# Activate autosectionlabel plugin
autosectionlabel_prefix_document = True
