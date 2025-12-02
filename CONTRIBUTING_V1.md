# Contributing to This Project

Thanks for your interest in contributing! This document explains the development workflow, how to run checks and tests, and what is expected in a pull request.


## Branching and pull requests

The `master` branch is protected: direct pushes are not allowed.
All changes must go through a pull request (PR).

1. On GitHub, Fork the repository to create your own copy.
2. Clone your fork to your local machine.
3. Create a new branch from `master`:
   ```bash
   git checkout master
   git pull
   git checkout -b feature/short-description
   ```
4. Make your changes and commit them.
5. Push your branch:
   ```bash
   git push -u origin feature/short-description
   ```

6. Open a pull request on GitHub targeting `master`. The configured checks will run automatically and their status will appear on the PR.

A PR is ready to merge when:

- All automated checks are green (pre-commit checks and GitHub Actions CI).
- The code has been reviewed and approved by at least one collaborator.
- The commit history is reasonably clean (rebased if necessary).

There are two main types of checks:

- **Style and quality checks**, which enforce formatting, coding conventions, documentation rules, and basic static analysis.
- **Functional checks**, which run tests to ensure the behavior and results are correct.

---

## Development environment

The project combines C++, Python, shell scripts, and Jupyter notebooks.
The CI currently uses macOS with LLVM, Doxygen, Graphviz, and Python 3.10. Python dependencies are managed with the [uv](https://docs.astral.sh/uv/) package manager.

You can work with a more recent Python locally (for example, Python 3.13), but ensure that everything still passes under Python 3.10 if relevant.

---

## Working on the Python code

To work on the Python code:

1. Install Python (version 3.10 or later).
2. Install and configure `uv` and `pre-commit`:
   ```
   python -m pip install --upgrade pip
   pip install uv pre-commit
   uv sync --extra dev
   ```
   This creates and manages a virtual environment for you and installs all dependencies (including development dependencies).

3. Install the git hook (once per clone):
   ```
   uv run pre-commit install
   ```

You can then modify the Python code as needed. Before committing, run in the repository root:

```
uv run pre-commit run --all-files
```

To run a single hook (useful when iterating on a specific issue), for example:

```
uv run pre-commit run ruff --all-files
uv run pre-commit run mypy --all-files
```

---

## Working on the C++ mechanical layer

To work on the C++ part, you need a working C++ toolchain. On macOS this includes LLVM/Clang (for `clang-format` and `clang-tidy`) and CMake.

The C++ “mechanical layer” has its own build and test workflow. In CI, the heavy steps (such as video generation) are separated from the fast automated tests to keep feedback quick.

### Building the C++ project

From the repository root:

```
cd src/mechanical_layer
cmake -H. -Bbuild -DBUILD_SHARED_LIBS=ON
cmake --build build
cd ../..
```

This creates the `build` directory used by `clang-tidy` and by the C++ tests.

### Running mechanical layer tests

From the repository root:

```
cd tests/mechanical_layer
./run_mechanical_tests.sh
cd ../..
```

Please run these tests locally before opening a PR that touches the mechanical layer.

---

## Continuous Integration (CI)

On each pull request targeting `master`, two categories of automation run:

### Pre-commit checks (via CI service)

The pre-commit service runs most of the hooks defined in `.pre-commit-config.yaml`, including for example:

- Python formatting and linting (`ruff`, `ruff-format`)
- Type checking (`mypy`)
- Docstring validation (`numpydoc-validation`)
- C/C++ formatting and style checks (`clang-format`, `cpplint`)
- Spell checking (`codespell`)
- Shell formatting (`shfmt`)
- Notebook checks and upgrades (`nbqa-ruff`, `nbqa-pyupgrade`)
- Copyright header checks

Some heavier hooks are skipped here and are handled instead by GitHub Actions (see below).

### GitHub Actions workflow

On each pull request, GitHub Actions runs the following steps:

1. Check out the repository.
2. Install LLVM and Graphviz (on macOS).
3. Install the latest Doxygen.
4. Set up Python 3.10, install `uv`, and synchronize dependencies with `uv sync --extra dev`.
5. Install the pre-commit hook (`uv run pre-commit install`).
6. Build the C++ mechanical layer with CMake.
7. Run selected pre-commit hooks:
   - `clang-tidy`
   - `uv-pytest` (Python configuration tests)
   - `test-notebooks`
   - `check-doxygen`
8. Run the mechanical layer tests:
   ```
   cd ./tests/mechanical_layer
   ./run_mechanical_tests.sh
   cd ../..
   ```

All of these checks must succeed before the PR can be merged.

---

## Reporting issues and proposing changes

If you are unsure about an approach, open an issue or a draft pull request and describe:

- The problem you are trying to solve.
- The proposed solution.
- Any open design questions (for example, API changes or performance implications).

Maintainers can then provide early feedback before you invest too much time in a particular direction.
