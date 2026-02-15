"""LEMON project documentation build configuration file."""

# Configuration file for the Sphinx documentation builder.
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys

# Add the source directory to sys.path so Sphinx can find the modules
sys.path.insert(0, os.path.abspath("../../src"))
sys.path.insert(0, os.path.abspath("../../tests/configuration"))
sys.path.insert(0, os.path.abspath("../../tests/mechanical_layer"))
smartquotes = False

os.environ["KIVY_NO_ARGS"] = "1"  # Disable Kivy's argument parsing
os.environ["KIVY_NO_CONFIG"] = "1"  # Disable Kivy config checks during docs build
os.environ["KIVY_NO_CONSOLELOG"] = "1"  # Disable Kivy console logging during docs build

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "lemons"
copyright = "%Y, The LEMONS project"
author = "Oscar Maxime Alexandre"
# release = "1.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.todo",  # Support for TODO comments
    "sphinx.ext.viewcode",  # Add links to highlighted source code
    "sphinx.ext.autodoc",  # Automatically document modules/classes/functions
    "sphinx.ext.napoleon",  # Support for NumPy/Google style docstrings
    "sphinx_autodoc_typehints",  # Render type hints as links in docs
    "sphinx.ext.intersphinx",  # Link to external documentation (e.g., Python)
    "nbsphinx",  # Support for Jupyter notebooks
    "myst_parser",
    "sphinx.ext.mathjax",
    "nbsphinx_link",  # Optional: Linking to external notebooks
    "breathe",  # For C++ documentation via Doxygen
    "exhale",  # For generating API documentation from C++ code
]

templates_path = ["_templates"]
# exclude_patterns = []  # List of patterns to ignore when looking for source files
language = "en"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"  # Use the Read the Docs theme
html_static_path = ["_static"]  # Path to custom static files (e.g., CSS)
html_css_files = ["custom.css"]  # Custom CSS file for styling
html_logo = "_static/logo/logo_doc.png"  # Logo for the documentation

suppress_warnings = ["config.cache", "duplicate_declaration.cpp"]

# -- Napoleon settings -------------------------------------------------------
napoleon_use_param = True  # Enable parameter type annotations in docstrings

# -- Intersphinx settings ----------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),  # Link to Python standard library docs
    "shapely": ("https://shapely.readthedocs.io/en/stable/", None),  # Link to Shapely documentation
    "plotly": ("https://plotly.com/python-api-reference/", None),  # Link to Plotly documentation
    "numpy": ("https://numpy.org/doc/stable/", None),  # Link to NumPy documentation
    "kivy": ("https://kivy.org/doc/stable/", None),  # Link to Kivy documentation
}

# -- Autodoc settings --------------------------------------------------------
autodoc_default_options = {
    "members": True,  # Include all members of the module/class
    "undoc-members": True,  # Include undocumented members
    "private-members": False,  # Exclude private members (those starting with _)
}

autodoc_typehints = "description"  # Show type hints in the description section of the docstring
autodoc_member_order = "bysource"  # Order members by their source code order
autodoc_mock_imports = ["kivy"]


# -- Exhale configuration ----------------------------------------------------

exhale_args = {
    "containmentFolder": "./api",  # Folder to contain the generated API documentation
    "rootFileName": "library_root.rst",  # Name of the root file
    "rootFileTitle": "Mechanical layer (C++)",  # Title for the root file
    "doxygenStripFromPath": os.path.abspath(os.path.join("..", "..", "src", "mechanical_layer")),  # Relative to conf.py's location
    "createTreeView": True,  # Create a tree view of the API
    "exhaleExecutesDoxygen": True,  # Execute Doxygen to generate XML files
    "exhaleDoxygenStdin": "INPUT=../../src/mechanical_layer/src ../../src/mechanical_layer/include",  # Input directory for Doxygen
}

# -- Breathe configuration ---------------------------------------------------

breathe_projects = {"mechanical_layer": os.path.abspath("../doxy_files/xml")}
breathe_default_project = "mechanical_layer"
