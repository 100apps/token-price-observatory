"""ECB daily reference cross-rate: CNY per USD = EUR/CNY / EUR/USD."""
import copy,datetime as dt,gzip,hashlib,json,math,time,urllib.request
from decimal import Decimal
from xml.etree import ElementTree as ET
URL='https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
SOURCE='https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html'

def parse_ecb(body,today,previous=None):
 root=ET.fromstring(body)
 dated=[e for e in root.iter() if e.get('time')]
 if len(dated)!=1:raise ValueError('Expected one ECB observation date')
 node=dated[0];date=dt.date.fromisoformat(node.attrib['time'])
 if not 0<=(today-date).days<=7:raise ValueError('ECB reference date is future or older than seven days')
 entries=[e for e in node if e.get('currency')]
 rates={e.get('currency'):e.get('rate') for e in entries}
 if len(rates)!=len(entries):raise ValueError('Duplicate ECB currency')
 usd,cny=Decimal(rates['USD']),Decimal(rates['CNY'])
 if not usd.is_finite() or not cny.is_finite() or usd<=0 or cny<=0:raise ValueError('Invalid ECB rates')
 rate=float(cny/usd)
 if not math.isfinite(rate) or not 1<rate<20:raise ValueError('Invalid USD/CNY cross-rate')
 if previous:
  if date.isoformat()<previous['rate_date']:raise ValueError('ECB date regressed')
  if abs(rate/previous['rate']-1)>.1:raise ValueError('USD/CNY changed over 10%; manual source review required')
 return dict(base='USD',quote='CNY',rate=rate,rate_date=date.isoformat(),source=SOURCE,feed=URL,method='ECB CNY per EUR / USD per EUR',eur_usd=str(usd),eur_cny=str(cny))

def update(root,now,atomic_json):
 latest=root/'data/fx/latest.json';previous=json.loads(latest.read_text()) if latest.exists() else None
 stamp=now.strftime('%Y-%m-%dT%H-%M-%S.%fZ');status=dict(provider='fx_ecb',url=URL,attempted_at=now.isoformat())
 for attempt in range(3):
  try:
   req=urllib.request.Request(URL,headers={'User-Agent':'TokenAtlas/1.3'})
   with urllib.request.urlopen(req,timeout=30) as response:body=response.read()
   digest=hashlib.sha256(body).hexdigest();raw=root/'data/raw'/digest[:2]/(digest+'.xml.gz');raw.parent.mkdir(parents=True,exist_ok=True)
   if not raw.exists():raw.write_bytes(gzip.compress(body,mtime=0))
   status.update(raw=str(raw.relative_to(root)),sha256=digest)
   record=parse_ecb(body,now.date(),previous);record.update(observed_at=now.isoformat(),stale=False,evidence=dict(raw=status['raw'],sha256=digest))
   atomic_json(root/'data/fx/history'/(stamp+'.json'),record)
   atomic_json(root/'data/fx/history/index.json',sorted([p.name for p in (root/'data/fx/history').glob('*.json') if p.name!='index.json'],reverse=True))
   atomic_json(latest,record)
   return record,{**status,'status':'parsed','fetched_at':now.isoformat(),'count':1}
  except Exception as exc:
   error=str(exc)
   if attempt<2:time.sleep(2*(4**attempt))
 status.update(status='failed',error=error)
 if previous:
  record=copy.deepcopy(previous);record.update(stale=True,last_attempt_at=now.isoformat(),error=error)
  atomic_json(latest,record)
 else:record=None
 atomic_json(root/'data/fx/attempts'/(stamp+'.json'),status)
 return record,status
