.. _installation_guide_app:

Run the app locally
===================

To set up, follow these steps after downloading the repository from `GitHub <https://github.com/Crowd-Mechanics/LEMONS>`__:

**1. Environment setup**

Create and activate a Python virtual environment using `uv <https://docs.astral.sh/uv/>`__ to manage dependencies efficiently:

.. code-block:: bash

   python -m pip install --upgrade pip
   pip install uv
   uv sync --locked --all-extras --dev


**2. Launch the app**

Start the app with the following command:

.. code-block:: bash

   uv run streamlit run src/streamlit_app/app/app.py

