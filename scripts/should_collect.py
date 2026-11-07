"""Backup schedule retries only if today's normal update failed or did not run."""
import datetime as dt,json,os
from pathlib import Path

def should_collect(event,schedule,health,today):
 if event!='schedule' or schedule!='23 6 * * *':return True
 return not (health.get('status')!='failed' and health.get('last_success_at','') and health['last_success_at'][:10]==today and not health.get('failed_sources'))
if __name__=='__main__':
 p=Path('data/health.json')
 try:health=json.loads(p.read_text())
 except (OSError,ValueError):health={}
 result=should_collect(os.environ.get('EVENT',''),os.environ.get('SCHEDULE',''),health,dt.date.today().isoformat())
 with open(os.environ['GITHUB_OUTPUT'],'a') as f:f.write('collect='+str(result).lower()+'\n')
