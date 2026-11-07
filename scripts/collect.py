"""Public, keyless price collection. Never replace failed data with invented rates."""
import argparse, concurrent.futures, datetime as dt, gzip, hashlib, json, re, time, urllib.request
from pathlib import Path
from lxml import html
from quality import validate_batch, review_batch
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
 'openrouter':'https://openrouter.ai/api/v1/models',
 'bailian':'https://help.aliyun.com/zh/model-studio/model-pricing',
 'community':'https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json',
 'openai':'https://developers.openai.com/api/docs/pricing',
 'anthropic':'https://platform.claude.com/docs/en/about-claude/pricing',
 'gemini':'https://ai.google.dev/gemini-api/docs/pricing',
 'deepseek':'https://api-docs.deepseek.com/quick_start/pricing.md',
 'moonshot':'https://platform.moonshot.cn/docs/pricing/chat',
 'zhipu':'https://docs.bigmodel.cn/cn/guide/models/text',
 'zai':'https://docs.z.ai/guides/overview/pricing',
 'volcengine':'https://www.volcengine.com/docs/82379/1544106',
 'siliconflow':'https://siliconflow.cn/pricing',
 'tencent':'https://cloud.tencent.com/document/product/1729/97731',
 'minimax':'https://platform.minimaxi.com/docs/guides/pricing-paygo',
 'mistral':'https://mistral.ai/pricing',
 'xai':'https://docs.x.ai/docs/models',
 'together_ai':'https://www.together.ai/pricing',
 'deepinfra':'https://api.deepinfra.com/models/list',
 'fireworks_ai':'https://fireworks.ai/pricing',
 'bedrock':'https://aws.amazon.com/bedrock/pricing/',
 'azure':'https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/'
}
NAMES={'openai':'OpenAI','anthropic':'Anthropic','gemini':'Google Gemini','deepseek':'DeepSeek','moonshot':'月之暗面 Kimi','zhipu':'智谱','volcengine':'火山方舟','siliconflow':'硅基流动','tencent':'腾讯混元','minimax':'MiniMax','zai':'智谱 Z.ai','bailian':'阿里云百炼','openrouter':'OpenRouter'}
def number(v):
 try:
  n=float(v)
  return n if 0<=n<1e12 else None
 except (ValueError,TypeError):return None

def canonical(s):
 # Exact version identifiers only; do not conflate aliases or differently quantized models.
 return s.lower().split('/')[-1].replace('anthropic.','').replace('meta-llama.','')

def row(provider,model,inp,out,cache=None,**kw):
 return dict(id=provider+':'+model+':'+str(kw.get('variant','standard')),provider=provider,platform=NAMES.get(provider,provider),model=model,canonical=canonical(model),currency='USD',input=inp,output=out,cache_read=cache,source=SOURCES.get(provider),provenance='official',variant='standard',**kw)

def openrouter(data):
 result=[]
 for m in data['data']:
  if 'text' not in m.get('architecture',{}).get('output_modalities',['text']):continue
  p=m.get('pricing',{});a,b=number(p.get('prompt')),number(p.get('completion'))
  if a is None or b is None:continue
  r=row('openrouter',m['id'],a*1e6,b*1e6, None if number(p.get('input_cache_read')) is None else float(p['input_cache_read'])*1e6)
  r.update(context=m.get('context_length'),name=m.get('name'),conditions={k:v for k,v in p.items() if k not in ['prompt','completion','input_cache_read']},source='https://openrouter.ai/'+m['id']);result.append(r)
 return result

def grid(table):
 occupied={};rows=[]
 for ri,tr in enumerate(table.xpath('./thead/tr|./tbody/tr|./tr')):
  vals={c:v for (r,c),v in occupied.items() if r==ri};c=0
  for cell in tr.xpath('./th|./td'):
   while c in vals:c+=1
   val=' '.join(cell.text_content().split());rs=int(cell.get('rowspan','1'));cs=int(cell.get('colspan','1'))
   for rr in range(ri,ri+rs):
    for cc in range(c,c+cs):occupied[rr,cc]=val
   vals.update({cc:val for cc in range(c,c+cs)});c+=cs
  rows.append([vals.get(i,'') for i in range(max(vals,default=-1)+1)])
 return rows

def bailian(body):
 doc=html.fromstring(body);result=[];seen=set()
 for ti,t in enumerate(doc.xpath('//table')):
  headings=t.xpath('preceding::*[self::h2 or self::h3 or self::h4]')
  stack={}
  for h in headings:
   level=int(h.tag[1]);stack={k:v for k,v in stack.items() if k<level};stack[level]=' '.join(h.text_content().split())
  section=' / '.join(stack.values())
  g=grid(t)
  if not g:continue
  headers=g[0]
  if not any('每百万' in v for v in headers):continue
  ic=next((i for i,h in enumerate(headers) if '输入单价' in h),None)
  ocs=[i for i,h in enumerate(headers) if '输出单价' in h]
  if ic is None or not ocs:continue
  for cells in g[1:]:
   if len(cells)<=max(ocs):continue
   model=re.match(r'([a-zA-Z][a-zA-Z0-9_.:/-]+)',cells[0])
   a=re.match(r'^([\d.]+)\s*元(?:$|缓存命中输入)',cells[ic])
   cache=re.search(r'缓存命中输入[：:]\s*([\d.]+)\s*元',cells[ic])
   if not (model and a):continue
   for oc in ocs:
    b=re.fullmatch(r'([\d.]+)\s*元',cells[oc])
    if not b:continue
    subheader=g[1][oc] if len(ocs)>1 and len(g)>1 else ''
    conditions=section+' | '+' | '.join(cells[1:ic])+(' | '+subheader if subheader else '')
    signature=(model[1],conditions,a[1],b[1])
    if signature in seen:continue
    seen.add(signature)
    r=row('bailian',model[1],float(a[1]),float(b[1]),float(cache[1]) if cache else None)
    r.update(currency='CNY',variant=conditions,id='bailian:'+hashlib.sha256(repr(signature[:2]).encode()).hexdigest()[:18],conditions=dict(section=section,headers=headers,cells=cells,output_mode=subheader),notes='地区、上下文阶梯与模式见本行条件；未解析缓存折扣时按普通输入计费。')
    result.append(r)
 return result

def community(data):
 result=[]
 for model,p in data.items():
  if not isinstance(p,dict) or p.get('mode') not in ['chat','completion']:continue
  provider=p.get('litellm_provider')
  if provider not in SOURCES or provider in ['community','bailian','openrouter']:continue
  if p.get('deprecation_date','9999') < dt.date.today().isoformat():continue
  a,b=number(p.get('input_cost_per_token')),number(p.get('output_cost_per_token'))
  if a is None or b is None:continue
  r=row(provider,model,a*1e6,b*1e6, None if number(p.get('cache_read_input_token_cost')) is None else p['cache_read_input_token_cost']*1e6)
  r.update(provenance='community',catalog=SOURCES['community'],source=p.get('source') if str(p.get('source','')).startswith('https://') else SOURCES[provider],conditions={k:v for k,v in p.items() if any(s in k for s in ['cost','pricing','region'])},notes='社区目录报价，官方页面已另行归档，未逐项自动核验。阶梯/Batch/Flex/优先级等条件见详情，不自动套用。',context=p.get('max_input_tokens'));result.append(r)
 return result

def official_tables(provider,body):
 doc=html.fromstring(body);result=[]
 for ti,t in enumerate(doc.xpath('//table')):
  if provider=='anthropic' and ti!=0:continue
  g=grid(t)
  header_idx=next((i for i,r in enumerate(g[:3]) if 'Input' in r and 'Output' in r),None)
  if header_idx is None:continue
  headers=g[header_idx]
  if any(v in headers for v in ['Training','Modality']):continue
  ic,oc=headers.index('Input'),headers.index('Output')
  mc=next((i for i,v in enumerate(headers) if v in ['Name','Model','Model configuration']),None)
  if mc is None:continue
  cachec=next((i for i,v in enumerate(headers) if v in ['Cached input','Hits and refreshes']),None)
  variants=[n.get('data-value') for n in t.iterancestors() if n.get('data-value')]
  variant=variants[0] if variants else 'standard'
  table_variant=variant
  for cells in g[header_idx+1:]:
   if len(cells)<=max(ic,oc):continue
   def money(v):
    m=re.fullmatch(r'\$([\d.]+)(?:\s*/\s*MTok)?(?:for prompts (?:up to|over) [\d,]+ tokens)?',v)
    return float(m[1]) if m else None
   a,b=money(cells[ic]),money(cells[oc])
   if a is None or b is None:continue
   model=cells[mc]
   if provider=='anthropic':
    m=re.match(r'Claude (Fable|Opus|Sonnet|Haiku|Mythos) (\d+(?:\.\d+)?)',model)
    if not m:continue
    model='claude-'+m[1].lower()+'-'+m[2].replace('.','-')
   cache=money(cells[cachec]) if cachec is not None else None
   context_note=re.sub(r'^\$[\d.]+(?:\s*/\s*MTok)?','',cells[ic]).strip()
   variant=table_variant+(' | '+context_note if context_note else '')
   r=row(provider,model,a,b,cache);r.update(variant=variant,id=provider+':'+model+':'+variant,conditions=dict(zip(headers,cells)),notes='官方表格直采；单次上下文、缓存写入与服务等级条件见详情。附加费用未计入。')
   result.append(r)
 return result

def deepseek(body):
 text=body.decode();lines=[[c.strip() for c in l.strip().strip('|').split('|')] for l in text.splitlines() if l.strip().startswith('|')]
 header=next((l for l in lines if l[0]=='MODEL'),None)
 if not header:return []
 result=[]
 rule=' '.join(l for l in text.splitlines() if l.startswith('(2)'))
 for col in range(3,len(header)):
  model=re.sub(r'\(\d+\)','',header[col]).strip()
  for period in ['OFF-PEAK','PEAK']:
   prices={}
   for l in lines:
    if len(l)<=col or l[0]!='PRICING(2)' or l[2]!=period:continue
    m=re.fullmatch(r'\$([\d.]+)',l[col])
    if m:prices[l[1]]=float(m[1])
   if len(prices)!=3:continue
   a=next(v for k,v in prices.items() if 'MISS' in k);b=next(v for k,v in prices.items() if 'OUTPUT' in k);cache=next(v for k,v in prices.items() if 'HIT' in k)
   r=row('deepseek',model,a,b,cache);r.update(id='deepseek:'+model+':'+period,variant='闲时 OFF-PEAK' if period=='OFF-PEAK' else '忙时 PEAK',conditions=dict(period=period,schedule=rule),notes=rule);result.append(r)
 return result

def deepinfra(body):
 result=[]
 for m in json.loads(body):
  p=m.get('pricing') or {}
  if m.get('type')!='text-generation' or p.get('type')!='tokens' or m.get('deprecated') or m.get('replaced_by'):continue
  a,b=number(p.get('cents_per_input_token')),number(p.get('cents_per_output_token'))
  if a is None or b is None:continue
  # This API reports cents per token. Cached rate is a multiplier, not cents.
  cache_rate=number(p.get('rate_per_input_token_cached'))
  r=row('deepinfra',m['model_name'],a*10000,b*10000,None if cache_rate is None else a*10000*cache_rate)
  r.update(source='https://deepinfra.com/'+m['model_name'],conditions=p,context=m.get('max_tokens'),notes='按官方模型 API 的美分/token换算为美元/百万 token；量化：'+str(m.get('quantization')));result.append(r)
 return result

def siliconflow(body):
 result=[];doc=html.fromstring(body)
 for node in doc.xpath('//*[starts-with(@id,"pricing-row-text-")]'):
  anchors=node.xpath('./div[1]/a[@title]')
  if not anchors:continue
  model=anchors[0].get('title');cells=node.xpath('./div')[1:]
  if len(cells)%3:continue
  for offset in range(0,len(cells),3):
   group=cells[offset:offset+3];rates=[];conditions=[]
   for cell in group:
    spans=cell.xpath('./span');value=' '.join(spans[-1].text_content().split()) if spans else ''
    m=re.fullmatch(r'¥\s*([\d.]+)',value)
    rates.append(float(m[1]) if m else 0 if value=='免费' else None)
    conditions.append(' '.join(spans[0].text_content().split()) if spans else '')
   if rates[0] is None or rates[1] is None:continue
   variant=conditions[0] or 'standard'
   r=row('siliconflow',model,*rates);r.update(currency='CNY',id='siliconflow:'+model+':'+variant,variant=variant,conditions=conditions,notes='官网价格页面直采；费用时段与上下文范围见条件。时区未自动推断，请核对官网。');result.append(r)
 return result

def minimax(body):
 result=[];doc=html.fromstring(body)
 for ti,t in enumerate(doc.xpath('//table')):
  g=grid(t)
  if not g or not ('输入价格' in ''.join(g[0]) and '输出价格' in ''.join(g[0]) and '缓存读取' in ''.join(g[0])):continue
  # Discounted multi-price cells are left unparsed rather than guessing current prices.
  for cells in g[1:]:
   if len(cells)!=4:continue
   m=re.match(r'(MiniMax-[A-Za-z0-9.\-]+)',cells[0]);rates=[number(v) for v in cells[1:]]
   if not m or any(v is None for v in rates):continue
   r=row('minimax',m[1],*rates);r.update(currency='CNY',conditions=cells);result.append(r)
 return result

def atomic_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 temp=path.with_suffix(path.suffix+'.tmp')
 temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 temp.replace(path)

def save_result(snapshot,stamp,previous_health):
 """Commit the latest pointer last; failed attempts never advance price freshness."""
 fresh=[r for r in snapshot['models'] if r['provenance']=='official' and not r.get('stale') and r.get('observed_at')==snapshot['collected_at']]
 failed=[s['provider'] for s in snapshot['sources'] if s['status']=='failed']
 warnings=sum(len(s.get('warnings',[])) for s in snapshot['sources'])
 health=dict(attempted_at=snapshot['collected_at'],last_success_at=snapshot['collected_at'] if fresh else previous_health.get('last_success_at'),status='failed' if not fresh else 'degraded' if failed or warnings else 'ok',fresh_official_quotes=len(fresh),failed_sources=failed,review_warnings=warnings,sources=snapshot['sources'])
 if not fresh:
  atomic_json(ROOT/'data/attempts'/(stamp+'.json'),health)
  atomic_json(ROOT/'data/health.json',health)
  return False
 history=ROOT/'data/history';history.mkdir(parents=True,exist_ok=True)
 encoded=(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n').encode()
 target=history/(stamp+'.json.gz');temp=target.with_suffix('.tmp')
 temp.write_bytes(gzip.compress(encoded,mtime=0));temp.replace(target)
 index=sorted([p.name for p in history.iterdir() if p.name.endswith(('.json','.json.gz')) and p.name!='index.json'],reverse=True)
 atomic_json(history/'index.json',index)
 # Only fully staged snapshots become current. health is separate from price data.
 latest=ROOT/'data/latest.json';temp=latest.with_suffix('.tmp');temp.write_bytes(encoded);temp.replace(latest)
 atomic_json(ROOT/'data/health.json',health)
 return True

def main(accepted=None):
 accepted=accepted or {}
 now=dt.datetime.now(dt.timezone.utc);stamp=now.strftime('%Y-%m-%dT%H-%M-%S.%fZ');rawdir=ROOT/'data/raw'/stamp;rawdir.mkdir(parents=True)
 previous=json.loads((ROOT/'data/latest.json').read_text()) if (ROOT/'data/latest.json').exists() else {'models':[]}
 health_path=ROOT/'data/health.json'
 previous_health=json.loads(health_path.read_text()) if health_path.exists() else {'last_success_at':previous.get('collected_at')}
 statuses=[];payloads={}
 def fetch(item):
  key,url=item
  for attempt in range(3):
   try:
    req=urllib.request.Request(url,headers={'User-Agent':'TokenPriceObservatory/1.0 (+https://github.com/100apps/token-price-observatory)'})
    with urllib.request.urlopen(req,timeout=45) as r:body=r.read();final=r.url
    ext='json' if key in ['openrouter','community','deepinfra'] else 'md' if key=='deepseek' else 'html';digest=hashlib.sha256(body).hexdigest();path=ROOT/'data/raw'/digest[:2]/(digest+'.'+ext+'.gz');path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():path.write_bytes(gzip.compress(body,mtime=0))
    return key,body,dict(provider=key,url=url,final_url=final,status='archived',sha256=hashlib.sha256(body).hexdigest(),raw=str(path.relative_to(ROOT)),fetched_at=now.isoformat())
   except Exception as e:
    if attempt==2:return key,None,dict(provider=key,url=url,status='failed',error=str(e)[:250],attempted_at=now.isoformat())
    time.sleep(2*(4**attempt))
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for key,body,status in pool.map(fetch,SOURCES.items()):statuses.append(status);payloads[key]=body
 models=[]
 for key,parser in [('openrouter',lambda b:openrouter(json.loads(b))),('bailian',bailian),('siliconflow',siliconflow),('minimax',minimax),('deepseek',deepseek),('deepinfra',deepinfra),('openai',lambda b:official_tables('openai',b)),('anthropic',lambda b:official_tables('anthropic',b)),('community',lambda b:community(json.loads(b)))]:
  status=next(s for s in statuses if s['provider']==key)
  try:
   if payloads[key] is None:raise ValueError(status.get('error','fetch failed'))
   parsed=parser(payloads[key])
   baseline=[r for r in previous['models'] if (r['provenance']=='community' if key=='community' else r['provider']==key and r['provenance']=='official')]
   if key in accepted:
    if accepted[key]!=status['sha256']:raise ValueError('Reviewed source SHA-256 does not match current document')
    baseline=[];status['reviewed_sha256']=accepted[key]
   parsed,warnings=review_batch(parsed,baseline)
   if warnings:status['warnings']=warnings
   for r in parsed:
    if not r.get('stale'):r.update(observed_at=now.isoformat(),stale=False,evidence=dict(raw=status['raw'],sha256=status['sha256'],url=status['url']))
   models+=parsed;status.update(status='parsed',count=len(parsed))
  except Exception as e:
   status.update(status='failed',error=str(e))
   old=[r for r in previous['models'] if (r['provenance']=='community' if key=='community' else r['provider']==key and r['provenance']=='official')]
   if not old:
    # A new parser can still recover a historical successful document after an outage.
    archives=sorted((ROOT/'data/history').glob('*.json*'),reverse=True)
    for archive in archives[:30]:
     if archive.name=='index.json':continue
     try:
      past=json.loads(gzip.decompress(archive.read_bytes()) if archive.name.endswith('.gz') else archive.read_bytes())
      evidence=next((s for s in past['sources'] if s['provider']==key and s.get('raw')),None)
      if not evidence:continue
      raw=ROOT/evidence['raw'];body=gzip.decompress(raw.read_bytes()) if raw.name.endswith('.gz') else raw.read_bytes()
      old=validate_batch(parser(body))
      for r in old:r.update(observed_at=evidence['fetched_at'])
      if old:
       status.update(fallback_observed_at=evidence['fetched_at'],fallback_raw=evidence['raw']);break
     except Exception:continue
   for r in old:r['stale']=True
   models+=old
 # An archived document is evidence, not a verified structured price.
 official_pairs={(r['provider'],r['canonical']) for r in models if r['provenance']=='official' and not r.get('stale')}
 models=[r for r in models if r['provenance']=='official' or (r['provider'],r['canonical']) not in official_pairs]
 unique={r['id']:r for r in models};snapshot=dict(schema_version=1,collector_version='1.1.0',collected_at=now.isoformat(),models=list(unique.values()),sources=statuses)
 saved=save_result(snapshot,stamp,previous_health)
 print(json.dumps({'models':len(unique),'sources':statuses},ensure_ascii=False))
 if any(s['status']=='failed' or s.get('warnings') for s in statuses):print('::warning::Prices quarantined or sources failed; inspect data/health.json')
 return saved
if __name__=='__main__':
 cli=argparse.ArgumentParser()
 cli.add_argument('--accept-source',action='append',default=[],metavar='PROVIDER=SHA256',help='After manual official-source review, accept only this exact document digest')
 args=cli.parse_args()
 accepted={}
 for value in args.accept_source:
  key,sep,digest=value.partition('=')
  if not sep or key not in SOURCES or not re.fullmatch('[a-f0-9]{64}',digest):cli.error('Expected known PROVIDER=SHA256')
  accepted[key]=digest
 raise SystemExit(0 if main(accepted) else 2)
