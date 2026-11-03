"""Prepare/review or apply a narrow integration into the existing local portal.

Never restarts a service or migrates the production database. Existing edits are preserved.
"""
import argparse
import ast
import difflib
import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--okul',type=Path,default=ROOT.parent/'okul')
parser.add_argument('--apply',action='store_true')
args=parser.parse_args();okul=args.okul.resolve()
files={name:(okul/name).read_text() for name in ['app.py','db.py','scripts/geri_al.py','templates/ogretmen/ana.html']}
new=files.copy()
schema=(ROOT/'backend/schema.sql').read_text()
if 'atlas_session' not in files['db.py']:
 tree=ast.parse(files['db.py'])
 assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='GOCLER' for t in n.targets))
 version=len(assignment.value.elts)+1
 migration=f'SEMA_V{version}'
 lines=files['db.py'].splitlines(keepends=True)
 lines.insert(assignment.end_lineno-1,f'    {migration},\n')
 lines.insert(assignment.lineno-1,f'# Farabi Atlas: teacher-owned classroom results; no XP changes.\n{migration} = """\n{schema}"""\n\n')
 new['db.py']=''.join(lines)
 new['scripts/geri_al.py']=files['scripts/geri_al.py'].replace('GERI = {',f'GERI = {{\n    {version}: """\nDROP TABLE IF EXISTS atlas_session;\n""",',1)
if '# Farabi Atlas integration' not in files['app.py']:
 new['app.py']+='\n\n# Farabi Atlas integration — same origin, existing teacher authentication.\nimport sys as _atlas_sys\n_atlas_sys.path.insert(0, '+repr(str(ROOT))+')\nfrom backend.server import install as _atlas_install\n_atlas_install(app)\n'
if 'href="/kure/"' not in files['templates/ogretmen/ana.html']:
 text=files['templates/ogretmen/ana.html']
 block='{% if ATLAS_ETKIN is defined and ATLAS_ETKIN %}\n<section class="kart"><h2>Farabi Atlas</h2><p>Türkiye ve dünya haritalarıyla sınıfta coğrafya ve tarih etkinlikleri.</p><p><a class="tus ikincil" href="/kure/">Harita laboratuvarını aç</a></p></section>\n{% endif %}\n'
 # Insert inside the template's content block, never outside the inherited page.
 match=re.search(r'{%\s*block\s+icerik\s*%}',text)
 if not match:match=re.search(r'{%\s*block\s+content\s*%}',text)
 if not match:raise SystemExit('Teacher content block not found; integration aborted.')
 new['templates/ogretmen/ana.html']=text[:match.end()]+'\n'+block+text[match.end():]
for name in new:
 if name.endswith('.py'):ast.parse(new[name])
 if new[name]!=files[name]:print(''.join(difflib.unified_diff(files[name].splitlines(keepends=True),new[name].splitlines(keepends=True),fromfile=name,tofile=name)))
if args.apply:
 backup=Path('/tmp')/('atlas-portal-backup-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
 for name,text in new.items():
  if text==files[name]:continue
  dest=backup/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(okul/name,dest)
  # Detect concurrent edits before touching a shared file.
  if (okul/name).read_text()!=files[name]:raise SystemExit('Concurrent edit detected; stopped: '+name)
  (okul/name).write_text(text)
 print('Integration prepared. Original files:',backup)
else:print('Review only; no portal files changed.')
