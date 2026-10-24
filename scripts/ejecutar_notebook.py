"""Ejecuta el respaldo con el Python de uv y exporta HTML con resultados incrustados."""
from pathlib import Path
import os
import sys
import asyncio

ROOT = Path(__file__).resolve().parents[1]
for name, folder in {
    'MPLCONFIGDIR':'/tmp/admisiones-matplotlib',
    'IPYTHONDIR':'/tmp/admisiones-ipython',
    'JUPYTER_RUNTIME_DIR':'/tmp/admisiones-jupyter-runtime',
    'JUPYTER_CONFIG_DIR':'/tmp/admisiones-jupyter-config',
    'JUPYTER_DATA_DIR':'/tmp/admisiones-jupyter-data',
}.items():
    os.environ.setdefault(name,folder)
    Path(os.environ[name]).mkdir(parents=True,exist_ok=True)
os.environ.setdefault('LC_ALL','C.UTF-8')

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter
from jupyter_client.kernelspec import KernelSpecManager

# Kernelspec temporal: usa el mismo intérprete que ejecuta este script.
kernel_root=Path('/tmp/admisiones-kernels')
kernel_dir=kernel_root/'admisiones-uv'
kernel_dir.mkdir(parents=True,exist_ok=True)
import json
(kernel_dir/'kernel.json').write_text(json.dumps({
    'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
    'display_name':'Python del proyecto uv','language':'python',
}))
manager=KernelSpecManager(kernel_dirs=[str(kernel_root)])
path=ROOT/'notebooks/01_respaldo_informe_descriptivo.ipynb'
nb=nbformat.read(path,as_version=4)
nbformat.validate(nb)
client=NotebookClient(nb,timeout=300,kernel_name='admisiones-uv',
                      resources={'metadata':{'path':str(ROOT)}},
                      allow_errors=False)
from jupyter_client import AsyncKernelManager
client.km=AsyncKernelManager(kernel_name='admisiones-uv',kernel_spec_manager=manager)
try:
    client.execute()
except Exception:
    nbformat.write(nb,path)
    raise
finally:
    if client.km is not None and client.km.has_kernel:
        asyncio.run(client.km.shutdown_kernel(now=True))
nb.metadata.kernelspec={'display_name':'Python del proyecto uv','language':'python','name':'python3'}
nbformat.write(nb,path)
exporter=HTMLExporter()
exporter.exclude_input_prompt=True
exporter.exclude_output_prompt=True
html,_=exporter.from_notebook_node(nb)
html_path=ROOT/'reports/01_respaldo_informe_descriptivo.html'
html_path.write_text(html,encoding='utf-8')
code_cells=[cell for cell in nb.cells if cell.cell_type=='code']
assert all(cell.execution_count is not None for cell in code_cells)
assert not any(output.output_type=='error' for cell in code_cells for output in cell.outputs)
print('Notebook ejecutado:',path)
print('Celdas de código ejecutadas:',len(code_cells))
print('HTML:',html_path)
