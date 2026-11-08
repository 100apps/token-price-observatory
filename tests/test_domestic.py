import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import domestic,collect
class DomesticPolicyTest(unittest.TestCase):
 def q(self,provider,currency,source,**kw):return dict(provider=provider,currency=currency,source=source,provenance='official',**kw)
 def test_domestic_quotes_cannot_be_replaced_with_usd_or_international_sites(self):
  rows=[self.q('minimax','USD','https://platform.minimax.io/docs/guides/pricing'),self.q('moonshot','USD','https://platform.moonshot.ai/docs/pricing'),self.q('zai','USD','https://docs.z.ai/guides/overview/pricing'),self.q('zhipu','CNY',domestic.ZHIPU),self.q('deepseek','CNY','https://api-docs.deepseek.com/quick_start/pricing.md'),self.q('openrouter','USD','https://openrouter.ai/api/v1/models')]
  rs=domestic.market_policy(rows);self.assertEqual([r['provider'] for r in rs],['zhipu','openrouter']);self.assertEqual([r['pricing_market'] for r in rs],['cn','international'])
 def test_domestic_community_usd_is_not_relabelled_as_cny(self):
  d={f'{p}/test':dict(mode='chat',litellm_provider=p,input_cost_per_token=1e-6,output_cost_per_token=2e-6) for p in [*domestic.DOMESTIC_HOSTS,'zai','openai']}
  rs=collect.community(d);self.assertEqual([r['provider'] for r in rs],['openai']);self.assertEqual(rs[0]['currency'],'USD')
 def test_reject_unapproved_redirect_even_when_url_looks_chinese(self):
  with self.assertRaises(ValueError):domestic.check_origin('minimax','https://platform.minimax.io/zh/pricing')
  with self.assertRaises(ValueError):domestic.check_origin('deepseek','https://api-docs.deepseek.com/quick_start/pricing.md')
  domestic.check_origin('moonshot',domestic.KIMI)
  domestic.check_origin('minimax','https://platform.minimax.cn/docs/pricing/overview')
  domestic.check_origin('siliconflow','https://www.siliconflow.cn/pricing')
 def test_kimi_actual_chinese_table_and_price_column_order(self):
  b=Path(__file__).with_name('fixtures').joinpath('kimi-cn.txt').read_bytes();rs=domestic.kimi(b)
  self.assertEqual(len(rs),6);r=next(r for r in rs if r['model']=='kimi-k3.1-pro');self.assertEqual((r['currency'],r['input'],r['output'],r['cache_read']),('CNY',13,68,1.3));self.assertEqual(r['conditions']['cache_write_1h'],26)
  self.assertEqual(domestic.kimi(b.replace('¥'.encode(),b'$')),[])
  self.assertEqual(domestic.kimi(b.replace('title:`输入`'.encode(),'title:`TEMP`'.encode()).replace('title:`输出`'.encode(),'title:`输入`'.encode()).replace('title:`TEMP`'.encode(),'title:`输出`'.encode())),[])
 def test_bigmodel_native_cny_contexts_and_non_token_exclusion(self):
  rs=domestic.zhipu(Path(__file__).with_name('fixtures').joinpath('zhipu-cn.txt').read_bytes());self.assertEqual(len(rs),44)
  r=next(r for r in rs if r['model']=='glm-5.3');self.assertEqual((r['currency'],r['input'],r['output'],r['cache_read']),('CNY',8,28,2))
  self.assertEqual(len([r for r in rs if r['model']=='glm-5.1']),2);self.assertEqual(len({r['id'] for r in rs}),44)
  self.assertFalse(any(r['model'] in ['glm-tts','cogvideox-3'] for r in rs))
