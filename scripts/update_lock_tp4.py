"""Extend the previous dependency lock with only the required Agents SDK closure."""
import importlib.metadata as metadata
from pathlib import Path
import subprocess
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT=Path(__file__).resolve().parents[1]
original=subprocess.run(['git','show','HEAD:requirements-lock.txt'],cwd=ROOT,capture_output=True,text=True,check=True).stdout
locked={canonicalize_name(Requirement(line).name) for line in original.splitlines() if line.strip() and not line.startswith('#')}
visited=set()
extra=[]
def visit(name):
    normalized=canonicalize_name(name)
    if normalized in visited:return
    visited.add(normalized)
    distribution=metadata.distribution(name)
    if normalized not in locked:
        pin=f'{distribution.metadata["Name"]}=={distribution.version}'
        if normalized=='pywin32':pin+='; sys_platform == "win32"'
        extra.append(pin)
    for raw in distribution.requires or []:
        requirement=Requirement(raw)
        if requirement.marker is None or requirement.marker.evaluate({'extra':''}):visit(requirement.name)
visit('openai-agents')
text=original.rstrip()+'\n\n# TP4: required Agents SDK dependencies (without optional integrations)\n'+'\n'.join(sorted(extra,key=str.lower))+'\n'
(ROOT/'requirements-lock.txt').write_text(text,encoding='utf-8')
print('SDK dependency additions:',len(extra))
