"""Optimistic push; regenerate on the latest code after a concurrent branch update.
Only used in disposable Actions checkouts. Preserve every captured history/raw file.
"""
import os,shutil,subprocess,tempfile
from pathlib import Path

def run(*args,check=True):return subprocess.run(args,check=check)

def publish():
 if os.environ.get('GITHUB_ACTIONS')!='true':raise RuntimeError('Run only in disposable GitHub Actions checkout')
 run('git','config','user.name','github-actions[bot]')
 run('git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
 for attempt in range(3):
  run('git','add','data')
  if run('git','diff','--cached','--quiet',check=False).returncode==0:return
  run('git','commit','-m','data: daily price snapshot and update health')
  if run('git','push','origin','HEAD:main',check=False).returncode==0:return
  if attempt==2:raise RuntimeError('Push rejected three times; keep deployed site; retained run artifact contains data')
  # Recollect with newest code/baseline instead of resolving generated-price conflicts by guessing.
  with tempfile.TemporaryDirectory() as backup:
   for name in ['history','raw','attempts','fx']:
    if Path('data',name).exists():shutil.copytree(Path('data',name),Path(backup,name))
   run('git','fetch','origin','main')
   run('git','reset','--hard','origin/main')
   for name in ['history','raw','attempts','fx']:
    src=Path(backup,name)
    if src.exists():
     for f in src.rglob('*'):
      if not f.is_file() or f.name in ['index.json','latest.json']:continue
      target=Path('data',name,f.relative_to(src));target.parent.mkdir(parents=True,exist_ok=True)
      if not target.exists():shutil.copy2(f,target)
  # Exit 2 is the intentional all-sources-failed result: health still gets committed.
  result=run('python','scripts/refresh.py',check=False)
  if result.returncode not in (0,2):raise RuntimeError('Collector crashed after concurrent push')
if __name__=='__main__':publish()
