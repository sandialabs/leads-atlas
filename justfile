# Run tests using pytest
test *ARGS:
    pytest {{ARGS}}

# Build the package with uv
build:
    uv build

# Run pre-commit checks
pre *ARGS:
    pre-commit run {{ARGS}}

# Remove build artifacts
clean:
    rm -rf build dist docs/_build
    rm -rf src/*.egg-info

# Build documentation with Sphinx
docs:
    sphinx-build --color -b html -d docs/_build/doctrees docs docs/_build/html

# Run doctests in documentation
doctests:
    sphinx-build --color -b doctest -d docs/_build/doctrees docs docs/_build/doctest

# Check documentation links
linkcheck:
    sphinx-build --color -b linkcheck -d docs/_build/doctrees docs docs/_build/linkcheck

# Open the CI config in vim
ci:
    vim {{justfile_directory()}}/.gitlab-ci.yml
