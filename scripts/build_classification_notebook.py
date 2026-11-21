"""Build and execute TP4 notebook using the same conventions as TP1-TP3."""
import re
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'eda/classification_tp4.py').read_text(encoding='utf-8')
parts=re.split(r'(?m)^# %%([^\n]*)\n',source)
cells=[]
for marker,content in zip(parts[1::2],parts[2::2]):
    cells.append(nbformat.v4.new_markdown_cell(re.sub(r'(?m)^# ?', '',content).strip())
                 if 'markdown' in marker else nbformat.v4.new_code_cell(content.strip()))
nb=nbformat.v4.new_notebook(cells=cells,metadata={
    'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
    'language_info':{'name':'python','version':'3.12'}})
NotebookClient(nb,timeout=1200,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}}).execute()
nbformat.write(nb,ROOT/'eda/classification_tp4.ipynb')
print('Notebook TP4 executado e salvo.')
