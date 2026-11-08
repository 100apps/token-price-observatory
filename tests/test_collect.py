import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collect import bailian,openrouter,grid,number
from lxml import html
class CollectTest(unittest.TestCase):
 def test_rowspan(self):
  t=html.fromstring('<table><tr><td rowspan="2">model</td><td>1</td></tr><tr><td>2</td></tr></table>')
  self.assertEqual(grid(t),[['model','1'],['model','2']])
 def test_no_invented_or_negative_rates(self):
  self.assertIsNone(number(-1));self.assertIsNone(number('n/a'));self.assertIsNone(number(float('nan')))
 def test_openrouter_cache_units_and_modality(self):
  rs=openrouter({'data':[{'id':'a/b','pricing':{'prompt':'.000002','completion':'.000008','input_cache_read':'0'}},{'id':'image','architecture':{'output_modalities':['image']},'pricing':{'prompt':'1','completion':'1'}}]})
  self.assertEqual(len(rs),1);self.assertEqual(rs[0]['input'],2);self.assertEqual(rs[0]['cache_read'],0)
 def test_bailian_does_not_guess_when_html_changes(self):
  self.assertEqual(bailian('<html>not a pricing table</html>'),[])
if __name__=='__main__':unittest.main()

class OfficialPricingTest(unittest.TestCase):
 def test_peak_offpeak_not_merged(self):
  from collect import deepseek
  body=b'''| MODEL | MODEL | MODEL | deepseek-flash(1) | deepseek-v4-pro |
| PRICING(2) | 1M INPUT TOKENS / (CACHE HIT) | OFF-PEAK | $0.003 | $0.022 |
| PRICING(2) | 1M INPUT TOKENS / (CACHE MISS) | OFF-PEAK | $0.15 | $0.66 |
| PRICING(2) | 1M OUTPUT TOKENS | OFF-PEAK | $0.6 | $1.98 |
| PRICING(2) | 1M INPUT TOKENS / (CACHE HIT) | PEAK | $0.006 | $0.044 |
| PRICING(2) | 1M INPUT TOKENS / (CACHE MISS) | PEAK | $0.3 | $1.32 |
| PRICING(2) | 1M OUTPUT TOKENS | PEAK | $1.2 | $3.96 |'''
  rs=deepseek(body);self.assertEqual(len(rs),4);self.assertEqual(rs[0]['input'],.15);self.assertEqual(rs[1]['input'],.3);self.assertEqual(rs[0]['cache_read'],.003)
 def test_bailian_thinking_modes_and_region(self):
  body='''<h2>千问</h2><h4>北京</h4><table><tr><th rowspan="2">模型 ID</th><th rowspan="2">输入单价（每百万Token）</th><th colspan="2">输出单价（每百万Token）</th></tr><tr><th>非思考模式</th><th>思考模式</th></tr><tr><td>qwen-plus</td><td>0.8元</td><td>2元</td><td>8元</td></tr></table>'''
  rs=bailian(body);self.assertEqual(len(rs),2);self.assertEqual([r['output'] for r in rs],[2,8]);self.assertIn('北京',rs[0]['variant']);self.assertNotEqual(rs[0]['id'],rs[1]['id'])
 def test_deepinfra_cents_not_dollars(self):
  from collect import deepinfra
  import json
  rs=deepinfra(json.dumps([dict(model_name='x/y',type='text-generation',pricing=dict(type='tokens',cents_per_input_token=.00002,cents_per_output_token=.00004,rate_per_input_token_cached=.1))]).encode())
  self.assertAlmostEqual(rs[0]['input'],.2);self.assertAlmostEqual(rs[0]['cache_read'],.02)

class QualityTest(unittest.TestCase):
 def quote(self,**kwargs):
  from collect import row
  return {**row('openai','test',2,8,.2),**kwargs}
 def test_schema_zero_and_cache(self):
  from quality import validate_batch
  self.assertEqual(len(validate_batch([self.quote(cache_read=0)])),1)
  for change in [dict(input=float('inf')),dict(output=-1),dict(input=None),dict(input=True),dict(currency='unknown')]:
   with self.assertRaises(ValueError):validate_batch([self.quote(**change)])
 def test_quarantine_large_changes_currency_and_conflicts(self):
  from quality import validate_batch
  before=self.quote()
  for change in [dict(input=2000000),dict(input=0),dict(output=80),dict(currency='CNY')]:
   with self.assertRaises(ValueError):validate_batch([self.quote(**change)],[before])
  with self.assertRaises(ValueError):validate_batch([before,self.quote(input=3)])
 def test_partial_parse_failure_count(self):
  from quality import validate_batch
  old=[self.quote(id=str(i)) for i in range(20)]
  with self.assertRaises(ValueError):validate_batch(old[:5],old)
 def test_bailian_identity_survives_real_price_changes(self):
  tpl='<h2>千问</h2><h3>Plus</h3><h4>北京</h4><table><tr><th>模型</th><th>输入单价（每百万Token）</th><th>输出单价（每百万Token）</th></tr><tr><td>qwen-plus</td><td>{}元</td><td>8元</td></tr></table>'
  self.assertEqual(bailian(tpl.format('1'))[0]['id'],bailian(tpl.format('2'))[0]['id'])
 def test_ambiguous_price_cells_rejected(self):
  from collect import official_tables
  doc='<table><tr><th>Model</th><th>Input</th><th>Output</th></tr><tr><td>model</td><td>$1 $2 promotional</td><td>$8</td></tr></table>'
  self.assertEqual(official_tables('openai',doc),[])

class OfficialGoldenTest(unittest.TestCase):
 def fixture(self,key):return (Path(__file__).parent/'fixtures'/(key+'.txt')).read_bytes()
 def test_real_official_openai_prices(self):
  from collect import official_tables
  rows=official_tables('openai',self.fixture('openai'));r=next(r for r in rows if r['model']=='gpt-6-astra')
  self.assertEqual((r['currency'],r['input'],r['output'],r['cache_read']),('USD',10,50,1))
 def test_real_official_anthropic_prices(self):
  from collect import official_tables
  rows=official_tables('anthropic',self.fixture('anthropic'));r=next(r for r in rows if r['model']=='claude-fable-5-1')
  self.assertEqual((r['input'],r['output'],r['cache_read']),(10,50,.25))
 def test_real_official_deepseek_prices(self):
  from collect import deepseek
  rows=deepseek(self.fixture('deepseek'));r=next(r for r in rows if r['id']=='deepseek:deepseek-flash:PEAK')
  self.assertEqual((r['input'],r['output'],r['cache_read']),(.3,1.2,.006))
 def test_real_siliconflow_cny_and_time_periods(self):
  from collect import siliconflow
  rows=siliconflow(self.fixture('siliconflow'))
  self.assertEqual(len(rows),2)
  self.assertEqual((rows[0]['currency'],rows[0]['input'],rows[0]['output'],rows[0]['cache_read']),('CNY',2,8,.04))
  self.assertEqual((rows[1]['input'],rows[1]['output'],rows[1]['cache_read']),(1,4,.02))

class QuarantineTest(unittest.TestCase):
 def test_only_changed_or_missing_quote_is_quarantined(self):
  from collect import row
  from quality import review_batch
  a=row('openai','a',2,8,.2);b=row('openai','b',3,9,.3);c=row('openai','removed',4,10)
  for r in [a,b,c]:r.update(observed_at='2026-11-06T00:00:00Z')
  rows,warnings=review_batch([{**a,'input':200},b],[a,b,c])
  self.assertEqual(len(warnings),2);self.assertEqual(rows[0]['input'],2);self.assertTrue(rows[0]['stale']);self.assertEqual(rows[0]['observed_at'],a['observed_at']);self.assertFalse(rows[1].get('stale',False));self.assertTrue(rows[2]['stale'])


class DecimalScalingTest(unittest.TestCase):
 def test_normalization_preserves_source_currency_and_exact_decimal_rate(self):
  from collect import openrouter,community,deepinfra
  import json
  rs=openrouter({'data':[{'id':'test','pricing':{'prompt':'0.0000004','completion':'0.00000219','input_cache_read':'0.000000044'}}]})
  self.assertEqual((rs[0]['currency'],rs[0]['input'],rs[0]['output'],rs[0]['cache_read']),('USD',.4,2.19,.044))
  rs=community({'deepseek/test':{'mode':'chat','litellm_provider':'deepseek','input_cost_per_token':4e-7,'output_cost_per_token':2.19e-6,'cache_read_input_token_cost':4.4e-8}})
  self.assertEqual((rs[0]['input'],rs[0]['output'],rs[0]['cache_read']),(.4,2.19,.044))
  rs=deepinfra(json.dumps([dict(model_name='test',type='text-generation',pricing=dict(type='tokens',cents_per_input_token=.00002,cents_per_output_token=.00004,rate_per_input_token_cached=.1))]).encode())
  self.assertEqual((rs[0]['currency'],rs[0]['input'],rs[0]['output'],rs[0]['cache_read']),('USD',.2,.4,.02))
