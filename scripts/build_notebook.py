"""Build and execute the notebook equivalent to eda.py."""
import re
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "eda" / "eda.py").read_text(encoding="utf-8")
parts = re.split(r"(?m)^# %%([^\n]*)\n", source)
cells = []
for marker, content in zip(parts[1::2], parts[2::2]):
    if "markdown" in marker:
        content = re.sub(r"(?m)^# ?", "", content).strip()
        cells.append(nbformat.v4.new_markdown_cell(content))
    else:
        cells.append(nbformat.v4.new_code_cell(content.strip()))
cells.append(nbformat.v4.new_markdown_cell("## Gráficos gerados\nFonte: recorte CLINC150, elaboração própria com Pandas/Matplotlib."))
cells.append(nbformat.v4.new_code_cell('from IPython.display import Image, display\nfor name in ["01_histogram.png", "02_categories.png", "03_boxplot.png"]:\n    display(Image(filename=str(OUT / "figures" / name)))'))
notebook = nbformat.v4.new_notebook(cells=cells, metadata={
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12"}})
client = NotebookClient(notebook, timeout=180, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}})
client.execute()
nbformat.write(notebook, ROOT / "eda" / "eda.ipynb")
print("Notebook executed:", len(cells), "cells")
