"""Streamlit Community Cloud entrypoint for VNStockLab."""

from pathlib import Path
from runpy import run_path

run_path(str(Path(__file__).with_name("app.py")), run_name="__main__")
