Installation guide
==================

You can try the Streamlit application online at `https://lemons.streamlit.app/ <https://lemons.streamlit.app/>`_. It lets you generate a crowd and download the corresponding configuration files, which you can then use to run the simulation locally via the Python wrapper that calls the underlying C++ library.


Python wrapper
--------------

To use the Python wrapper locally (e.g., to run simulations, plot the crowd scene and get statistics as shown
in the :ref:`tutorials <tutorials_config_files>`), install the package with pip:

.. code-block:: bash

   python -m pip install --upgrade pip
   python -m pip install lemons-crowd


Development version (from source)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install the latest development version, clone or download the full repository from
`GitHub <https://github.com/Crowd-Mechanics/LEMONS>`__. Then create a virtual environment and install all required Python
dependencies using `uv <https://docs.astral.sh/uv/>`__:

.. code-block:: bash

   python -m pip install --upgrade pip
   pip install uv
   uv sync --locked --all-extras --dev

You can then launch the streamlit app locally with the following command:

.. code-block:: bash

   uv run streamlit run src/streamlit_app/app/app.py


C++ library (CrowdMechanics)
----------------------------

The C++ code used to run the crowd simulation is intended to be installed as a shared library. Alternatively, you can
vendor the sources and headers into your own project and compile everything together. The steps below describe the
recommended shared-library installation workflow.

Dependencies
~~~~~~~~~~~~

This project uses ``cmake`` as its build system. Make sure you have a recent version installed; you can download it from the `official site <https://cmake.org/download/>`_.

Building the library
~~~~~~~~~~~~~~~~~~~~

After downloading the repository from `GitHub <https://github.com/Crowd-Mechanics/LEMONS>`__, build the
``CrowdMechanics`` shared library from the ``src/mechanical_layer`` directory.

Linux / macOS:

.. code-block:: bash

   cmake -H. -Bbuild -DBUILD_SHARED_LIBS=ON
   cmake --build build

Windows (command line):

.. code-block:: bash

   cmake -Bbuild -DBUILD_SHARED_LIBS=ON ^
     -DCMAKE_CXX_COMPILER=/name/of/C++/compiler ^
     -DCMAKE_C_COMPILER=/name/of/C/compiler ^
     -DCMAKE_MAKE_PROGRAM=/name/of/make/program ^
     -G "Name of Makefile generator"

If you specify tool paths explicitly, ensure they are available in your ``PATH`` environment variable, or provide
absolute paths to the executables.
