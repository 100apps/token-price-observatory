"""Reject broken deployment artifacts before Pages can replace a working site."""
import gzip,json,math
from pathlib import Path

def validate(root):
 for f in ['index.html','style.css','app.js','calc.mjs','quality.mjs','url-state.mjs','data/latest.json','data/health.json','data/history/index.json']:
  if not (root/f).is_file():raise ValueError('Missing deploy file: '+f)
 current=json.loads((root/'data/latest.json').read_text())
 if not current.get('models'):raise ValueError('No current prices')
 ids=set()
 for r in current['models']:
  if r['id'] in ids:raise ValueError('Duplicate quote ID')
  ids.add(r['id'])
  for key in ['input','output','cache_read']:
   v=r[key]
   if key=='cache_read' and v is None:continue
   if not isinstance(v,(int,float)) or not math.isfinite(v) or v<0:raise ValueError('Invalid rate')
 for name in json.loads((root/'data/history/index.json').read_text()):
  if Path(name).name!=name:raise ValueError('Invalid snapshot path')
  p=root/'data/history'/name
  snapshot=json.loads(gzip.decompress(p.read_bytes()) if name.endswith('.gz') else p.read_bytes())
  if not snapshot.get('models'):raise ValueError('Empty snapshot')
 health=json.loads((root/'data/health.json').read_text())
 if health.get('status') not in ['ok','degraded','failed']:raise ValueError('Invalid health status')
 print('Deployment files, prices, history and health validated')
if __name__=='__main__':validate(Path(__file__).resolve().parents[1])
