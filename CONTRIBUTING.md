# Contributing to This Project

Thanks for your interest in contributing! This document explains the development workflow, how to run checks and tests, and what is expected in a pull request.



## Branching and pull requests

The `master` branch is protected: direct pushes are not allowed.
All changes must go through a pull request (PR).

1. Click Fork on GitHub to create your own copy under your account.
2. Clone your GitHub repository to your local machine to be able to make changes
3. Create a new branch from `master`:
   ```
   git checkout master
   git pull
   git checkout -b feature/short-description
   ```
4. Make your changes and commit them.
5. Push your branch:
   ```
   git push -u origin feature/short-description
   ```
6. Open a pull request on GitHub targeting `master`. GitHub will run the configured checks and show their status in the PR.

A PR is ready to merge when:
- All automated checks are green (CI pre-commit hooks and CI github actions hooks and tests).
- The code has been reviewed and approved by at least one of the collaborators.
- The history is reasonably clean.

There are mainly to type of check that are performed: some for maintaining the coding style quality and readability and those to test the functions used and if the obtained result is the desired one.

## Development environment

The project combines C++, Python, shell scripts, and Jupyter notebooks. The CI uses macOS with LLVM, Doxygen, Graphviz, and Python 3.10. The python dependencies are managed with the python package [uv](https://docs.astral.sh/uv/).



### Modify the python codes

To work on the python code, you need
1. install python ici la version 3.13 ou plus
2. to Create and activate a virtual environment using [uv](https://docs.astral.sh/uv/>) to manage dependencies efficiently:

```bash
python -m pip install --upgrade pip
pip install uv
uv sync
```



You can modify the code then as you mwant and before commiting, run on the root directory

```bash
uv run pre-commit run --all-files
```

To run a single hook (useful when iterating on a specific issue):

```
uv run pre-commit run ruff --all-files
uv run pre-commit run clang-format --all-files
```


To improve the C++ code you need, to setup the right C++ environment (LLMV on macOS)
The C++ “mechanical layer” has its own build and test workflow. CI separates fast automated tests from video generation to keep feedback quick.

### Building the C++ project

From the repository root:

```
cd src/mechanical_layer
cmake -H. -Bbuild -DBUILD_SHARED_LIBS=ON
cmake --build build
cd ../..
```

This creates the `build` directory used by `clang-tidy` and the C++ tests.

### Running mechanical layer tests

From the repository root:

```
cd tests/mechanical_layer
./run_mechanical_tests.sh
cd ../..
```

Please run these tests locally before opening a PR that touches the mechanical layer.


---

## CI: what runs on GitHub

On each pull request targeting `master`,
Ci-precommit runs :
1. ruff
2. codespell to ...
3. etc

GitHub Actions run:

1. Checkout of the repository.
2. Installation of LLVM and Graphviz (macOS).
3. Installation of the latest Doxygen.
4. Python setup (3.10), `uv` installation, and dependency sync with `uv sync --extra dev`.
5. Installation of the pre-commit hook (`uv run pre-commit install`).
6. C++ build of the mechanical layer.
7. Pre-commit hooks for:
   - `clang-tidy`
   - `uv-pytest` (configuration tests)
   - `test-notebooks`
   - `check-doxygen`
8. Mechanical layer tests via `./tests/mechanical_layer/run_mechanical_tests.sh`.

All these checks must succeed before the PR can be merged.

---

## Reporting issues and proposing changes

If you are unsure about an approach, open an issue or a draft pull request and describe:

- The problem you are trying to solve.
- The proposed solution.
- Any open design questions (API changes, performance implications, etc.).

Maintainers can then provide early feedback before you invest too much time in a particular direction.



