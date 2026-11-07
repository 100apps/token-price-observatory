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
