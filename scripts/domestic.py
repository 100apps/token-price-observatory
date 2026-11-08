"""Domestic catalogues and explicit market boundaries; never infer location from FX."""
import hashlib,re
from urllib.parse import urlparse

KIMI='https://platform.kimi.com/docs/pricing/chat'
ZHIPU='https://docs.bigmodel.cn/cn/guide/start/pricing.md'
DOMESTIC_HOSTS={
 'bailian':{'bailian.console.aliyun.com'},
 'deepseek':{'api-docs.deepseek.com'},
 'siliconflow':{'siliconflow.cn','www.siliconflow.cn'},
 'minimax':{'platform.minimaxi.com','platform.minimax.cn'},
 'moonshot':{'platform.moonshot.cn','platform.kimi.com'},
 'zhipu':{'docs.bigmodel.cn','bigmodel.cn'},
 'volcengine':{'www.volcengine.com','docs.volcengine.com'},
 'tencent':{'cloud.tencent.com'},
}

def check_origin(provider,url):
 u=urlparse(url);hosts=DOMESTIC_HOSTS.get(provider,set())
 if provider=='bailian':hosts=hosts|{'bailian-cs.console.aliyun.com'}
 if u.scheme!='https' or u.hostname not in hosts:raise ValueError('Domestic source redirected outside approved domestic catalogue')
 if provider=='deepseek' and not u.path.startswith('/zh-cn/'):raise ValueError('DeepSeek requires the Chinese CNY catalogue')
 if provider=='zhipu' and not u.path.startswith('/cn/'):raise ValueError('BigModel requires Chinese mainland catalogue')

def market_policy(rows):
 result=[]
 for r in rows:
  provider=r['provider']
  if provider=='zai':continue  # International GLM catalogue is not domestic BigModel pricing.
  if provider in DOMESTIC_HOSTS:
   u=urlparse(r.get('source',''))
   if r.get('provenance')!='official' or r.get('currency')!='CNY' or u.hostname not in DOMESTIC_HOSTS[provider]:continue
   if provider=='deepseek' and not u.path.startswith('/zh-cn/'):continue
   if provider=='bailian' and r.get('conditions',{}).get('region')!='cn-beijing':continue
   result.append({**r,'pricing_market':'cn','market_label':'中国大陆报价'})
  else:result.append({**r,'pricing_market':'international','market_label':'海外平台报价'})
 return result

def quote(provider,model,a,b,c,source,variant,conditions,notes):
 identity=provider+':cn:'+model+':'+hashlib.sha256(variant.encode()).hexdigest()[:12]
 return dict(id=identity,provider=provider,platform={'moonshot':'月之暗面 Kimi','zhipu':'智谱 BigModel'}[provider],model=model,canonical=model.lower(),currency='CNY',input=a,output=b,cache_read=c,source=source,provenance='official',variant=variant,conditions=conditions,notes=notes)

def kimi(body):
 text=body.decode()
 # The official Chinese page embeds compiled DocTable rows; never execute its JS.
 # Require exact column semantics before reading the first three prices.
 if 'title:`输入`' not in text or 'title:`输出`' not in text or 'children:`缓存命中`' not in text:return []
 result=[]
 pattern=r'children:`(kimi-[a-z0-9.\-]+)`\}\),((?:`¥[\d.]+ / MTok`(?:,|(?=\])))+)'
 for m in re.finditer(pattern,text):
  header=text[text.rfind('columns:[',0,m.start()):m.start()]
  positions=[header.find(t) for t in ['title:`输入`','title:`输出`','children:`缓存命中`']]
  if min(positions)<0 or positions!=sorted(positions):continue
  model=m[1];rates=[float(v) for v in re.findall(r'`¥([\d.]+) / MTok`',m[2])]
  if len(rates) not in (3,5):continue
  conditions=dict(region='中国大陆',unit='CNY / 1 MTok',cache_write_5min=rates[3] if len(rates)==5 else None,cache_write_1h=rates[4] if len(rates)==5 else None)
  variant='国内标准 / '+('高速版' if model.endswith('-highspeed') else '常规版')
  if model.startswith('kimi-k2.'):variant+=' / K2 仅已有用户，计划年底下线'
  notes='国内官网人民币目录；缓存写入、存储和工具调用不包含在三指标估算内。K3 写入 5min/1h 费率见条件；缓存命中不重复收写入费。K2 系列仅面向已有用户，按官方下线公告选择。'
  result.append(quote('moonshot',model.lower(),*rates[:3],KIMI,variant,conditions,notes))
 return result

def zhipu(body):
 text=body.decode();result=[]
 header=None
 for line in text.splitlines():
  line=line.lstrip('> ').strip()
  if not line.startswith('|'):continue
  cells=[x.strip() for x in line.strip('|').split('|')]
  if cells[0]=='模型名称':
   header=cells if all(any(k in h for h in cells) for k in ['输入单价（元/百万 Tokens）','输出单价（元/百万 Tokens）','缓存命中（元/百万 Tokens）']) else None
   continue
  if not header or len(cells)!=len(header) or not re.fullmatch(r'GLM-[A-Za-z0-9.\-]+',cells[0]):continue
  def val(label):
   v=cells[next(i for i,h in enumerate(header) if label in h)]
   return 0 if v=='免费' else float(v) if re.fullmatch(r'\d+(?:\.\d+)?',v) else None
  a,b,c=val('输入单价'),val('输出单价'),val('缓存命中')
  cachetext=cells[next(i for i,h in enumerate(header) if '缓存命中' in h)]
  if a is None or b is None or c is None and cachetext!='不支持':continue
  model=cells[0].lower();variant='中国大陆 / 标准目录 / '+cells[1].replace('\\','')
  r=quote('zhipu',model,a,b,c,ZHIPU,variant,dict(region='中国大陆',context_range=cells[1],headers=header,cells=cells),'智谱国内官网人民币单价；上下文阶梯见条件。缓存存储限时免费，结束后的存储费不含在本估算中；不自动套用 Batch 或未明确资格的促销。')
  r['cache_supported']=cachetext!='不支持';result.append(r)
 return result
