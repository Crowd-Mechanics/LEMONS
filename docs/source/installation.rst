Installation guide
==================

You can try out the Streamlit application online at this `link <https://lemons.streamlit.app/>`_, generate your own crowd, download the corresponding configuration files, and run the crowd simulation locally.

If you want to use the Streamlit application locally, you can install it and use it following the advanced tutorial :ref:`installation_guide_app`.

The C++ code (to run the crowd simulation) is intended to be installed as a shared library. Alternatively, you can include all sources and headers directly in your own code and compile everything together. Below, we detail the originally intended installation method.

Dependencies
------------

This project uses ``cmake`` as the build system. Please ensure you have a recent version installed. You can download it from the `official site <https://cmake.org/download/>`_.

Building the Library
--------------------

After downloading the repository from `GitHub <https://github.com/odufour7/LEMONS.git>`__, you can build the ``CrowdMechanics`` library as a shared library in the ``mechanical_layer`` directory by running the following commands on Linux or macOS:

.. code-block:: console

    cmake -H. -Bbuild -DBUILD_SHARED_LIBS=ON
    cmake --build build


If you're using Windows and want to build with the command line, you may have to supply additional information in the first command:

.. code-block:: console

    cmake -Bbuild -DBUILD_SHARED_LIBS=ON -DCMAKE_CXX_COMPILER=/name/of/C++/compiler -DCMAKE_C_COMPILER=/name/of/C/compiler -DCMAKE_MAKE_PROGRAM=/name/of/make/program -G "Name of Makefile generator"

In that case, please also make sure that the paths to all the mentioned programs are in the ``PATH`` environment variable, or supply the absolute paths to them.
