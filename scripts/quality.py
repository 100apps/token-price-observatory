"""Fail closed for implausible data; do not auto-approve surprising price changes."""
import math
RATE_FIELDS=('input','output','cache_read')
def validate_batch(rows,old=()):
 if not rows:raise ValueError('No prices parsed')
 seen={}
 for r in rows:
  if r.get('currency') not in ('USD','CNY'):raise ValueError('Unsupported or missing currency')
  if not str(r.get('source','')).startswith('https://'):raise ValueError('Missing HTTPS source')
  for k in RATE_FIELDS:
   v=r.get(k)
   if v is None and k=='cache_read':continue
   if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1e6:raise ValueError('Invalid per-million rate: '+k)
  if r['id'] in seen and any(r[k]!=seen[r['id']][k] for k in RATE_FIELDS):raise ValueError('Conflicting duplicate quote: '+r['id'])
  seen[r['id']]=r
 previous={r['id']:r for r in old}
 if len(previous)>=10 and len(seen)<len(previous)*.7:raise ValueError('Quote count dropped more than 30%; review source structure')
 for key,r in seen.items():
  before=previous.get(key)
  if not before:continue
  if r['currency']!=before['currency']:raise ValueError('Currency changed: '+key)
  for field in RATE_FIELDS:
   a,b=before.get(field),r[field]
   if a is None or b is None:continue
   if (a==0)!=(b==0) or (a and abs(b/a-1)>.5):raise ValueError('Price changed over 50% or crossed zero; manual review required: '+key+' / '+field)
 return list(seen.values())

def review_batch(rows,old=()):
 """Quarantine individual changed/missing quotes without blocking unrelated models."""
 rows=validate_batch(rows)
 previous={r['id']:r for r in old}
 if len(previous)>=10 and len(rows)<len(previous)*.7:raise ValueError('Quote count dropped more than 30%; review source structure')
 result=[];warnings=[];present=set()
 for r in rows:
  present.add(r['id']);before=previous.get(r['id'])
  try:validate_batch([r],[before] if before else [])
  except ValueError as e:
   warnings.append(str(e));r={**before,'stale':True,'quality_issue':str(e)}
  result.append(r)
 for key,r in previous.items():
  if key not in present:
   issue='Quote no longer parsed; archived until confirmed removed: '+key
   warnings.append(issue);result.append({**r,'stale':True,'quality_issue':issue})
 return result,warnings
