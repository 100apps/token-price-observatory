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
