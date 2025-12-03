Contributing
============

Thanks for your interest in contributing! This guide covers:

- The :ref:`general-procedure` for contributing to the project
- How to set up and test the :ref:`Python wrapper <python-wrapper>` and the :ref:`mechanical layer <cpp-mechanical-layer>`
- What happens in :ref:`the continous integration <continuous-integration>` when you open a pull request
- How :ref:`to report an issue <reporting-issues>`

.. _general-procedure:

General procedure
-----------------

The ``master`` branch is protected: direct pushes are not allowed.
All changes must go through a pull request (PR). Here is how you should proceed:

1. On GitHub, fork the repository to create your own copy.
2. Clone your fork to your local machine, preferably on macOS or Ubuntu. On Windows, extra care is needed because the continuous integration does not run on Windows.
3. Create a new branch from ``master``::

      git checkout master
      git pull
      git checkout -b feature/short-description

4. Set up the required Python and C++ environments (:ref:`detailed below <python-wrapper>`).
5. Make your changes.
6. Run the hooks defined in the ``.pre-commit-config.yaml`` file::

      uv run pre-commit run --all-files

7. Run the mechanical layer tests::

      cd tests/mechanical_layer
      ./run_mechanical_tests.sh
      cd ../..

8. Commit your changes.
9. Push your branch::

      git push -u origin feature/short-description

10. Open a pull request on GitHub targeting ``master``. The configured checks (:ref:`detailed below <continuous-integration>`) will run automatically and their status will appear on the PR.

A PR is ready to merge when:

- All automated checks are green (pre-commit.ci checks and GitHub Actions CI).
- The code has been reviewed and approved by at least one collaborator.
- The commit history is reasonably clean.

There are two main types of checks:

- **Style and quality checks**, which enforce formatting, coding conventions, documentation rules, and basic static analysis.
- **Functional checks**, which run tests to ensure the expected behavior is correct.

.. _python-wrapper:

Working on the Python wrapper
------------------------------

To work on the Python wrapper:

1. Install Python (version 3.13 or later).
2. Install and configure the `uv <https://docs.astral.sh/uv/>`__ package manager to set up the Python virtual environment with all required dependencies::

      python -m pip install --upgrade pip
      pip install uv pre-commit
      uv sync

   This creates and manages a virtual environment for you and installs all dependencies (including development dependencies).
3. You can then modify the Python code as needed.
4. Before committing, run in the repository root::

      uv run pre-commit run --all-files --skip clang-tidy,clang-format,cpplint

   Here ``--skip`` is used to avoid running the C++-related hooks locally when you are only modifying Python code, which saves time.

.. _cpp-mechanical-layer:

Working on the C++ mechanical layer
------------------------------------

To work on the C++ part, you need a working C++ toolchain. On macOS this includes LLVM/Clang and CMake. The C++ mechanical layer has its own build and test workflow:

1. You first need to build the C++ project. From the repository root, run::

      cd src/mechanical_layer
      cmake -H. -Bbuild -DBUILD_SHARED_LIBS=ON
      cmake --build build
      cd ../..

2. Modify the code as you want.
3. Run mechanical layer pre-commit hooks and tests. The tests depend on the Python wrapper, so you must set up the required Python virtual environment as explained above. Then, from the repository root::

      uv run pre-commit run --all-files
      cd tests/mechanical_layer
      ./run_mechanical_tests.sh

4. Additionally, you may want to visualize the outputs of the mechanical Layer tests::

      ./make_tests_videos.sh

   The generated videos are stored in ``/test/mechanical_layer/movies/``.

.. _continuous-integration:

Continuous Integration (CI)
----------------------------

For every pull request targeting ``master``, two categories of automated checks run on both ``macos-latest`` and ``ubuntu-latest`` runners.

Pre-commit checks (via pre-commit.ci service)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The pre-commit.ci service runs most of the hooks defined in ``.pre-commit-config.yaml``, including for example:

- Spell checking (`codespell <https://github.com/codespell-project/codespell>`__)
- Python formatting and linting (`ruff, ruff-format <https://github.com/astral-sh/ruff-pre-commit>`__)
- Python type checking (`mypy <https://github.com/pre-commit/mirrors-mypy>`__)
- Python docstring validation (`numpydoc-validation <https://github.com/numpy/numpydoc>`__)
- Notebook checks and upgrades (`nbqa-ruff, nbqa-pyupgrade <https://github.com/nbQA-dev/nbQA>`__)
- Shell formatting (`shfmt <https://github.com/maxwinterstein/shfmt-py>`__)
- C/C++ formatting and style checks (`clang-format <https://github.com/pocc/pre-commit-hooks>`__, `cpplint <https://github.com/cpplint/cpplint>`__)

Some more complex hooks are skipped here and are handled instead by GitHub Actions (see below).

GitHub Actions workflow
~~~~~~~~~~~~~~~~~~~~~~~~

On each pull request, GitHub Actions runs the following steps:

1. Check out the repository.
2. Install LLVM and Graphviz (on macOS).
3. Install the latest Doxygen.
4. Set up Python, install ``uv``, and synchronize dependencies.
5. Install the pre-commit hook.
6. Build the C++ mechanical layer with CMake.
7. Run selected pre-commit hooks:

   - ``check-copyright`` (verify that the copyright headers are present and correctly formatted using the ``.check-copyright.sh`` script.)
   - `clang-tidy <https://github.com/pocc/pre-commit-hooks>`__
   - ``uv-pytest`` (Python configuration tests via the `pytest <https://docs.pytest.org/en/stable/>`__ package)
   - ``test-notebooks`` (Jupyter notebook tests via the local shell script ``.check-notebooks.sh``, only on ``macos-latest`` runner)
   - ``check-doxygen`` (C++ documentation tests via the local shell script ``.check-doxygen.sh``)

8. Run the mechanical layer tests.

All of these checks must succeed before the PR can be merged.

.. _reporting-issues:

Reporting issues and proposing changes
---------------------------------------

If you are unsure about something, open an issue and describe:

- The problem you are trying to solve.
- The proposed solution.
- Any open design questions (for example, API changes or performance implications).

Maintainers can then provide early feedback before you invest too much time in a particular direction.
