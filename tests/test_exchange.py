import datetime as dt,json,tempfile,unittest,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import exchange
from collect import atomic_json

def xml(date='2026-11-06',usd='1.2',cny='7.2'):
 return f'<Envelope><Cube><Cube time="{date}"><Cube currency="USD" rate="{usd}"/><Cube currency="CNY" rate="{cny}"/></Cube></Cube></Envelope>'.encode()
class ExchangeTest(unittest.TestCase):
 def test_cross_rate_and_weekend_date(self):
  r=exchange.parse_ecb(xml(),dt.date(2026,11,7));self.assertEqual(r['rate'],6);self.assertEqual(r['rate_date'],'2026-11-06')
 def test_bad_future_stale_and_anomalous_rates_rejected(self):
  for body in [xml(date='2026-11-08'),xml(date='2026-10-01'),xml(usd='0'),xml(cny='NaN'),xml(cny='10000')]:
   with self.assertRaises(Exception):exchange.parse_ecb(body,dt.date(2026,11,7))
  with self.assertRaises(ValueError):exchange.parse_ecb(xml(),dt.date(2026,11,7),{'rate':8,'rate_date':'2026-11-06'})
 def test_failed_update_keeps_last_success_timestamp_and_rate(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);previous=exchange.parse_ecb(xml(),dt.date(2026,11,7));previous.update(observed_at='2026-11-06T12:00:00Z',stale=False);atomic_json(root/'data/fx/latest.json',previous)
   with patch.object(exchange.urllib.request,'urlopen',side_effect=TimeoutError('timeout')) as fetch,patch.object(exchange.time,'sleep'):
    r,status=exchange.update(root,dt.datetime(2026,11,7,tzinfo=dt.timezone.utc),atomic_json)
   self.assertEqual(fetch.call_count,3);self.assertEqual(status['status'],'failed');self.assertTrue(r['stale']);self.assertEqual(r['rate'],6);self.assertEqual(r['observed_at'],previous['observed_at']);self.assertEqual(len(list((root/'data/fx/attempts').glob('*.json'))),1)
 def test_first_failure_has_no_fabricated_rate(self):
  with tempfile.TemporaryDirectory() as d,patch.object(exchange.urllib.request,'urlopen',side_effect=TimeoutError()),patch.object(exchange.time,'sleep'):
   r,status=exchange.update(Path(d),dt.datetime(2026,11,7,tzinfo=dt.timezone.utc),atomic_json)
   self.assertIsNone(r);self.assertFalse((Path(d)/'data/fx/latest.json').exists())
 def test_success_preserves_raw_and_multiple_same_date_observations(self):
  import io,gzip,hashlib
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   with patch.object(exchange.urllib.request,'urlopen',side_effect=lambda *args,**kwargs:io.BytesIO(xml())):
    for hour in [10,14]:r,status=exchange.update(root,dt.datetime(2026,11,7,hour,tzinfo=dt.timezone.utc),atomic_json)
   self.assertEqual(len(json.loads((root/'data/fx/history/index.json').read_text())),2)
   self.assertEqual(hashlib.sha256(gzip.decompress((root/status['raw']).read_bytes())).hexdigest(),status['sha256'])
