"""Public catalog gateway used by official bailian-cli 2.8.4 (no token required).
Reference: modelstudioai/cli packages/core/src/console/{gateway,models}.ts.
"""
import datetime as dt,hashlib,json,math,urllib.parse,urllib.request
from decimal import Decimal
MARKET='https://bailian.console.aliyun.com/cn-beijing/model/market'
API='zeldaHttp.dashscopeModel./zelda/api/v1/modelCenter/listFoundationModels'
ENDPOINT='https://bailian-cs.console.aliyun.com/cli/api.json?'+urllib.parse.urlencode({'action':'BroadScopeAspnGateway','product':'sfm_bailian','api':API})
BATCH_DOC='https://docs.bailian.console.aliyun.com/zh/model-studio/openai-compatible-batch-chat.md'
CLI_SOURCE='https://github.com/modelstudioai/cli/blob/cadc301d078f0fd1f2c56f7bf94f32c55bbb055d/packages/core/src/console/gateway.ts'
def request(page=1):
 payload={'Api':API,'V':'1.0','Data':{'input':{'pageNo':page,'pageSize':50,'name':'','providers':[],'inferenceProviders':[],'features':[],'group':True,'capabilities':[],'contextWindows':[],'queryPrice':True,'queryPermissions':True,'queryApplyStatus':True,'queryActivationStatus':True,'queryQpmInfo':True,'supports':{'inference':True}},'cornerstoneParam':{'protocol':'V2','console':'ONE_CONSOLE','productCode':'p_efm','switchUserType':3,'consoleSite':'BAILIAN_ALIYUN'}}}
 return urllib.request.Request(ENDPOINT,data=urllib.parse.urlencode({'params':json.dumps(payload),'region':'cn-beijing'}).encode(),headers={'Accept':'*/*','Content-Type':'application/x-www-form-urlencoded','User-Agent':'TokenAtlas/1.7'})
def unwrap(data):
 if data.get('code')=='ConsoleNeedLogin' or data.get('successResponse') is False:raise ValueError('百炼市场要求登录或公开目录接口不可用')
 d=data.get('data',data)
 if 'DataV2' in d:d=d['DataV2'].get('data',d['DataV2'])
 d=d.get('data',d)
 if not isinstance(d.get('list'),list) or not isinstance(d.get('total'),int):raise ValueError('Unknown Bailian catalog envelope')
 return d

def fetch():
 pages=[];expected=None
 for page in range(1,101):
  with urllib.request.urlopen(request(page),timeout=40) as response:raw=json.load(response)
  d=unwrap(raw)
  if expected is None:expected=d['total']
  if d['total']!=expected:raise ValueError('Bailian catalog total changed during pagination; retry')
  pages.append(raw)
  if page>=math.ceil(expected/50):break
  if not d['list']:raise ValueError('Premature empty Bailian page')
 groups=[g for p in pages for g in unwrap(p)['list']]
 if len(groups)!=expected or len({g['model'] for g in groups})!=expected:raise ValueError('Incomplete or duplicate Bailian catalog pages')
 try:
  with urllib.request.urlopen(BATCH_DOC,timeout=30) as response:batch_doc=response.read().decode()
 except Exception:batch_doc=''
 return json.dumps({'batch_chat_doc':batch_doc,'batch_chat_doc_url':BATCH_DOC,'format':'bailian-cli-public-v1','cli_reference':CLI_SOURCE,'region':'cn-beijing','total':expected,'pages':pages},ensure_ascii=False).encode()

def unit_price(p,allow_batch_discount=False):
 unit=p.get('priceUnit');factor={'每百万tokens':1,'每千tokens':1000,'千tokens':1000,'千Token':1000}.get(unit)
 if factor is None or p.get('currency','CNY')!='CNY':raise ValueError('Unsupported currency or token unit')
 # A discount badge alone does not establish whether price is before/after discount.
 discount=Decimal(str(p.get('discount',1)))
 if discount!=1 and not (allow_batch_discount and discount==Decimal('.5')):raise ValueError('Discount semantics require separate verification')
 n=Decimal(str(p['price']))*factor*discount
 if not n.is_finite() or n<0:raise ValueError('Invalid market token rate')
 return float(n)

def parse(body):
 data=json.loads(body)
 if data.get('format')!='bailian-cli-public-v1':unwrap(data);raise ValueError('Expected complete paginated market capture')
 groups=[g for p in data['pages'] for g in unwrap(p)['list']]
 if len(groups)!=data['total']:raise ValueError('Incomplete market capture')
 result=[]
 batch_active='其最终费用为实时调用价格的 50%' in data.get('batch_chat_doc','') and '已结束' not in data.get('batch_chat_doc','')
 for group in groups:
  for m in group.get('items',[]):
   if m.get('offlineAt'):continue
   modalities=m.get('modalities',m.get('inferenceMetadata',{}))
   if 'Text' not in modalities.get('output',modalities.get('response_modality',[])):continue
   ranges=m.get('multiPrices') or [{'rangeName':'无单独上下文阶梯','prices':m.get('prices',[])}]
   for rg in ranges:
    prices=rg.get('prices',[])
    bands=list(dict.fromkeys(p.get('timeBand','standard') for p in prices))
    for band in bands:
     selected=[p for p in prices if p.get('timeBand','standard')==band]
     for mode,inp,out,cache in [('实时推理','input_token','output_token','input_token_cache'),('实时推理·思考','thinking_input_token','thinking_output_token','thinking_input_token_cache'),('Batch File','input_token_batch','output_token_batch',None),('Batch File·思考','thinking_input_token_batch','thinking_output_token_batch',None),('Batch Chat·限时5折','input_token_batch_chat','output_token_batch_chat',None),('Batch Chat·思考·限时5折','thinking_input_token_batch_chat','thinking_output_token_batch_chat',None)]:
      entries={}
      for p in selected:
       key=p.get('type')
       if key in entries and entries[key]!=p:raise ValueError('Conflicting market type')
       entries[key]=p
      if inp not in entries or out not in entries:continue
      batch_chat=mode.startswith('Batch Chat')
      if batch_chat:
       bases=['thinking_input_token','thinking_output_token'] if inp.startswith('thinking_') else ['input_token','output_token']
       if not batch_active or any(Decimal(str(entries[k].get('discount',1)))!=Decimal('.5') for k in [inp,out]):continue
       if any(base not in entries or Decimal(str(entries[k]['price']))!=Decimal(str(entries[base]['price'])) or entries[k]['priceUnit']!=entries[base]['priceUnit'] for k,base in zip([inp,out],bases)):continue
      try:
       a,b=unit_price(entries[inp],batch_chat),unit_price(entries[out],batch_chat);c=unit_price(entries[cache]) if cache and cache in entries else None
      except (ValueError,ArithmeticError,KeyError):continue
      label={'standard':'普通时段','offpeak':'闲时','peak':'忙时'}.get(band)
      if label is None:continue
      variant='北京 / '+mode+' / '+label+' / '+rg.get('rangeName','未标注上下文范围')
      identity=(m['model'],variant,m.get('inferenceProvider'),m.get('serviceSites'))
      result.append(dict(id='bailian:market:'+hashlib.sha256(repr(identity).encode()).hexdigest()[:18],provider='bailian',platform='阿里云百炼',model=m['model'],canonical=m['model'].lower().split('/')[-1],currency='CNY',input=a,output=b,cache_read=c,source=MARKET,provenance='official',variant=variant,pricing_basis='market_catalog',calculation_blocked=False,cache_supported=not mode.startswith('Batch'),conditions=dict(region='cn-beijing',service_sites=m.get('serviceSites'),inference_provider=m.get('inferenceProvider'),context_range=rg.get('rangeName'),time_band=band,mode=mode,batch_promotion_source=BATCH_DOC if batch_chat else None,discount_applied=.5 if batch_chat else 1,prices=selected,doc_url=m.get('docUrl')),notes='百炼公开模型市场当前报价；非账号结算价。忙闲时、上下文与 Batch 条件分别展示；套餐/领券优惠、显式缓存写入和工具费用不自动套用。Batch 不支持缓存；Batch Chat 限时5折仅在目录折扣字段与当日抓取的官方规则同时成立时计算，不叠加到其他模式。'))
 return result
