"""Turn collector crashes into explicit health reports without publishing partial prices."""
import datetime as dt,json,traceback
import collect as collector

def run():
 root=collector.ROOT;latest=root/'data/latest.json';index=root/'data/history/index.json'
 saved={p:p.read_bytes() if p.exists() else None for p in [latest,index]}
 hp=root/'data/health.json';prior_health=json.loads(hp.read_text()) if hp.exists() else {}
 try:return collector.main()
 except Exception as exc:
  for path,content in saved.items():
   if content is not None:
    tmp=path.with_suffix('.recovery');tmp.write_bytes(content);tmp.replace(path)
   elif path.exists():path.unlink()
  now=dt.datetime.now(dt.timezone.utc).isoformat();hp=root/'data/health.json'
  previous=prior_health
  prices=json.loads(saved[latest]) if saved[latest] else {}
  health=dict(attempted_at=now,last_success_at=previous.get('last_success_at',prices.get('collected_at')),status='failed',fresh_official_quotes=0,failed_sources=['collector'],review_warnings=0,sources=[],error=type(exc).__name__+': '+str(exc)[:500])
  collector.atomic_json(hp,health)
  collector.atomic_json(root/'data/attempts'/(dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H-%M-%S.%fZ')+'.json'),health)
  traceback.print_exc();return False
if __name__=='__main__':raise SystemExit(0 if run() else 2)
