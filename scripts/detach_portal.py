"""Remove only Atlas changes; preserve pre-existing portal edits and current school data."""
import ast
import re
import shutil
import sqlite3
import subprocess
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PORTAL=ROOT.parent/'okul'
ORIGINAL=Path('/tmp/atlas-portal-backup-20261101-220039')
FILES=['app.py','db.py','scripts/geri_al.py','templates/ogretmen/ana.html']
prepared={}
for name in FILES:
 current=(PORTAL/name).read_text()
 if name=='app.py':
  current=current.split('\n\n# Farabi Atlas integration — same origin, existing teacher authentication.')[0]+'\n'
 elif name=='db.py':
  current=re.sub(r'# Farabi Atlas: teacher-owned classroom results; no XP changes\.\nSEMA_V39 = """.*?"""\n\n','',current,flags=re.S)
  current=current.replace('    SEMA_V39,\n','')
 elif name=='scripts/geri_al.py':
  current=current.replace('    39: """\nDROP TABLE IF EXISTS atlas_session;\n""",\n','')
 else:
  current=re.sub(r'{% if ATLAS_ETKIN is defined and ATLAS_ETKIN %}\n.*?{% endif %}\n\n','',current,count=1,flags=re.S)
 if current.rstrip()!=(ORIGINAL/name).read_text().rstrip():
  raise SystemExit('Concurrent portal changes found; refusing wholesale restore: '+name)
 prepared[name]=(ORIGINAL/name).read_bytes()
 for_check=prepared[name].decode()
 if name.endswith('.py'):ast.parse(for_check)

source=PORTAL/'veri/okul.db'
backup=ROOT/'var'/('portal-detach-'+datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')+'.db')
# Back up the CURRENT database, never restore an old school-wide snapshot.
with sqlite3.connect(source) as c,sqlite3.connect(backup) as dest:
 c.backup(dest)
 version=c.execute('PRAGMA user_version').fetchone()[0]
 if version!=39:raise SystemExit('Unexpected portal schema version; stopped safely: '+str(version))
 count=c.execute('SELECT COUNT(*) FROM atlas_session').fetchone()[0]
 if count:raise SystemExit('Atlas results exist; archive/move them before detaching.')
subprocess.run(['sudo','-n','systemctl','stop','farabi-okul'],check=True)
try:
 with sqlite3.connect(source) as c:
  c.execute('BEGIN IMMEDIATE')
  c.execute('DROP TABLE atlas_session')
  c.execute('PRAGMA user_version=38')
  c.commit()
  assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 for name,data in prepared.items():(PORTAL/name).write_bytes(data)
finally:subprocess.run(['sudo','-n','systemctl','start','farabi-okul'],check=True)
print('Portal restored byte-for-byte to pre-Atlas files; pre-existing V38 preserved. School data retained; integrity ok.')
print('Rollback safety backup:',backup.name)
