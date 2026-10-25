from pathlib import Path
import re
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
parts = re.split(r"(?m)^# %%([^\n]*)\n", (ROOT / "eda" / "eda_tp2.py").read_text(encoding="utf-8"))
cells = []
for marker, content in zip(parts[1::2], parts[2::2]):
    if "markdown" in marker:
        cells.append(nbformat.v4.new_markdown_cell(re.sub(r"(?m)^# ?", "", content).strip()))
    else:
        cells.append(nbformat.v4.new_code_cell(content.strip()))
cells.append(nbformat.v4.new_code_cell('from IPython.display import Image, display\nfor name in ["04_heatmap.png", "05_scatter.png", "06_hypothesis_violin.png"]:\n    display(Image(filename=str(OUT / "figures" / name)))'))
notebook = nbformat.v4.new_notebook(cells=cells, metadata={"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}})
NotebookClient(notebook, timeout=180, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}}).execute()
nbformat.write(notebook, ROOT / "eda" / "eda_tp2.ipynb")
print("TP2 notebook executed:", len(cells), "cells")
