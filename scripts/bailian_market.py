"""Read the market's own catalog endpoint; never substitute list prices for offers.
No authentication material is stored or sent. A login response is a failed quote fetch.
"""
import json,urllib.parse,urllib.request
MARKET='https://bailian.console.aliyun.com/cn-beijing/model/market'
API='zeldaHttp.dashscopeModel./zelda/api/v1/modelCenter/listFoundationModels'
ENDPOINT='https://bailian.console.aliyun.com/data/api.json?'+urllib.parse.urlencode({'action':'BroadScopeAspnGateway','product':'Beebot-inner','api':API})
def request():
 payload={'Api':API,'V':'1.0','Data':{'input':{'pageNo':1,'pageSize':30,'group':True,'queryPermissions':False,'queryApplyStatus':False,'queryActivationStatus':False,'supports':{'inference':True}},'cornerstoneParam':{}}}
 return urllib.request.Request(ENDPOINT,data=urllib.parse.urlencode({'params':json.dumps(payload),'region':'cn-beijing'}).encode(),headers={'Content-Type':'application/x-www-form-urlencoded','Referer':MARKET,'User-Agent':'TokenAtlas/1.5'})
def parse(body):
 data=json.loads(body)
 if data.get('code')=='ConsoleNeedLogin' or data.get('successResponse') is False:
  raise ValueError('百炼市场要求登录；活动价、优惠资格与有效期未核验，禁止用文档原价代算')
 # Until a real successful response and its discount semantics can be checked, fail closed.
 raise ValueError('百炼市场尚无已验证的活动价数据结构；禁止把标价或未知折扣用于计算')
