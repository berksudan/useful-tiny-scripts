set shell := ["bash", "-euo", "pipefail", "-c"]

PYTHON_VERSION := "3.14"
VENV_DIR := justfile_directory() / ".venv"

default:
    @just --list

setup:
    #!/usr/bin/env bash
    set -euo pipefail
    rm -rf "{{ VENV_DIR }}"
    uv venv "{{ VENV_DIR }}" --python "{{ PYTHON_VERSION }}"
    echo "export PYTHONPATH={{ justfile_directory() }}/" >> "{{ VENV_DIR }}/bin/activate"
    uv sync --locked
    "{{ VENV_DIR }}/bin/prek" install
    echo "Activate the virtual environment: source {{ VENV_DIR }}/bin/activate"
