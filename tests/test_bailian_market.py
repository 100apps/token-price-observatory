import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import bailian_market
class BailianMarketTest(unittest.TestCase):
 def test_http_200_login_response_is_not_a_successful_price(self):
  with self.assertRaisesRegex(ValueError,'要求登录'):bailian_market.parse(json.dumps({'code':'ConsoleNeedLogin','message':'请登录','successResponse':False}))
 def test_unknown_discount_schema_is_rejected_instead_of_guessing(self):
  with self.assertRaises(ValueError):bailian_market.parse(json.dumps({'success':True,'price':1,'discount':.1}))
 def test_request_is_read_only_catalog_and_has_no_account_token(self):
  request=bailian_market.request()
  self.assertIn('listFoundationModels',request.full_url)
  self.assertNotIn('sec_token',request.data.decode());self.assertNotIn('Cookie',request.headers)

class PublicCatalogTest(unittest.TestCase):
 def data(self):return json.loads((Path(__file__).parent/'fixtures/bailian-public.json').read_text())
 def rows(self):return bailian_market.parse(json.dumps(self.data()))
 def test_actual_deepseek_cli_market_rates_and_cache_not_usd(self):
  rs=[r for r in self.rows() if r['model']=='deepseek-v4.1-flash'];self.assertEqual(len(rs),2)
  self.assertEqual([(r['input'],r['output'],r['cache_read']) for r in rs],[(1,4,.1),(2,8,.2)]);self.assertTrue(all(r['currency']=='CNY' and not r['calculation_blocked'] for r in rs))
 def test_context_thinking_and_batch_are_separate_quotes(self):
  rs=[r for r in self.rows() if r['model']=='qwen-plus' and r['conditions']['context_range']=='输入<=128k']
  realtime=[r for r in rs if r['conditions']['mode'].startswith('实时')];self.assertEqual([r['output'] for r in realtime],[2,8])
  batch=[r for r in rs if r['conditions']['mode']=='Batch File'][0];self.assertEqual((batch['input'],batch['output']),(.4,1));self.assertFalse(batch['cache_supported']);self.assertIsNone(batch['cache_read'])
 def test_batch_chat_half_price_applied_once_and_no_cache_discount(self):
  rs=[r for r in self.rows() if r['model']=='qwen-plus' and r['conditions']['context_range']=='输入<=128k' and r['conditions']['mode']=='Batch Chat·限时5折']
  self.assertEqual(len(rs),1);self.assertEqual((rs[0]['input'],rs[0]['output']),(.4,1));self.assertFalse(rs[0]['cache_supported'])
 def test_bad_unit_and_missing_promotion_evidence_rejected(self):
  with self.assertRaises(ValueError):bailian_market.unit_price({'price':1,'priceUnit':'每张'})
  with self.assertRaises(ValueError):bailian_market.unit_price({'price':1,'priceUnit':'每百万tokens','discount':.3})
  data=self.data();data.pop('batch_chat_doc');rs=bailian_market.parse(json.dumps(data));self.assertFalse(any('Batch Chat' in r['variant'] for r in rs))
 def test_incomplete_capture_rejected(self):
  data=self.data();data['total']+=1
  with self.assertRaises(ValueError):bailian_market.parse(json.dumps(data))

 def test_already_discounted_catalog_values_are_not_discounted_twice(self):
  data=self.data()
  for page in data['pages']:
   for group in bailian_market.unwrap(page)['list']:
    for model in group.get('items',[]):
     for r in model.get('multiPrices') or [model]:
      for p in r.get('prices',[]):
       if p.get('type','').endswith('_batch_chat'):p['price']=str(float(p['price'])*.5)
  self.assertFalse(any('Batch Chat' in r['variant'] for r in bailian_market.parse(json.dumps(data))))
