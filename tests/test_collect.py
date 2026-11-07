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
