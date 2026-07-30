# LEADS-Atlas

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-blue?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![ruff](https://img.shields.io/badge/format-ruff-blue?logo=ruff)](https://github.com/astral-sh/ruff)
[![pytest](https://img.shields.io/badge/testing-pytest-blue?logo=pytest)]()
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)]()

Data loaders for PyTorch using VTK data using PyVista as a backend.

# Quickstart

To install `LEADS-Atlas` into your Python environment
```sh
python -m pip install .
```

To check that the installation worked, print the library version in a terminal
```sh
$ python -m leads_atlas --version
leads-atlas 0.1.0
```

# Features

This software is in very early alpha, as a proof of concept, the initial requrements are listed below

```text
Software Requirements: v0.1

1. Read a single exodus file into pyvista
2. Extract a masked grid with pyvista (focus on 2D)
    1. 3 tensor containing fields, and mask
    2. Coordinates of image data
3. Timestep pairs for autoregressive training

Repository Requirements: v0.1
1. Documentation page
2. CI/CD Pipeline configured
```

# Developing Workflow

## Actions

Various actions, such as testing, building docs, and more are coordinated using  the `just` tool. To install, refer to the [project's documentation](https://github.com/casey/just).

An overview of the available actions are shown below
```text
$ just --list
Available recipes:
    build      # Build the package with uv
    ci         # Open the CI config in vim
    clean      # Remove build artifacts
    docs       # Build documentation with Sphinx
    doctests   # Run doctests in documentation
    linkcheck  # Check documentation links
    pre *ARGS  # Run pre-commit checks
    test *ARGS # Run tests using pytest
```

## Development Setup

1. [Setting up `uv`](#python-environments-with-uv)
2. [Install `ruff`](#installing-ruff)
3. [Install `pre-commit`](#installing-pre-commit-optional) (optional)
4. [Install `just`](#install-just)
5. [Install `LEADS-Atlas`](#install-leads-atlas)


## Python Environments with `uv`

`LEADS-Atlas` is tested across multiple Python versions (3.11+), `uv` is used to manage multiple these environments.

To install `uv`, follow the instructions from the [official documentation](https://docs.astral.sh/uv/getting-started/installation/) for your platform

## Installing `ruff`

`ruff` is an incredibly fast linter and formatter for python projects, to install run:

```sh
uv tool install ruff
```

## Installing `pre-commit` (optional)

`pre-commit` helps run scripts before committing code to ensure certain guarantees about formatting, security, etc.

Using `pre-commit` is often a personal preference. For this reason it is optional for local development, as the associated checks will be checked before merging.

To install:

```sh
uv tool install pre-commit
```

To install pre-commit hooks:
```sh
pre-commit install
```

Or, if you want to remove local pre-commits

```sh
pre-commit uninstall
```

## Install `just`

Just is a command runner for repositories. Install following the  [official instructions](https://github.com/casey/just).

## Install `LEADS-Atlas`

Create a python virtual environment for development using `uv` (recommended)

```sh
uv venv
source .venv/bin/activate
uv pip install -e .[test,docs]
```
