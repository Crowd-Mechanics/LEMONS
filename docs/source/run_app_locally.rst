.. _installation_guide_app:

Run the app locally
===================

To set up, follow these steps after downloading the repository from `GitHub <https://github.com/Crowd-Mechanics/LEMONS>`__:

**1. Environment setup**

To install the latest development version, clone or download the full repository from
`GitHub <https://github.com/Crowd-Mechanics/LEMONS>`__. Then, from the root directory of the project,  create a virtual environment and install all required Python
dependencies using `uv <https://docs.astral.sh/uv/>`__:

.. code-block:: bash

   python -m pip install --upgrade pip
   pip install uv
   uv sync


**2. Launch the app**

Start the app with the following command:

.. code-block:: bash

   uv run streamlit run src/streamlit_app/app/app.py

