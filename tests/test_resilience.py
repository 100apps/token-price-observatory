import contextlib,io,json,tempfile,unittest,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect,refresh
from should_collect import should_collect
class ResilienceTest(unittest.TestCase):
 def setup_tree(self,root):
  (root/'data/history').mkdir(parents=True)
  (root/'data/latest.json').write_text(json.dumps({'collected_at':'2026-11-06T01:00:00Z','models':[{'id':'old'}]}))
  (root/'data/history/index.json').write_text('[]')
 def test_all_failed_preserves_latest_and_timestamp(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.setup_tree(root);before=(root/'data/latest.json').read_bytes()
   snapshot=dict(collected_at='2026-11-07T02:00:00Z',models=[dict(provenance='official',stale=True,observed_at='2026-11-06T01:00:00Z')],sources=[dict(provider='openai',status='failed')])
   with patch.object(collect,'ROOT',root):result=collect.save_result(snapshot,'attempt',{'last_success_at':'2026-11-06T01:00:00Z'})
   self.assertFalse(result);self.assertEqual((root/'data/latest.json').read_bytes(),before)
   h=json.loads((root/'data/health.json').read_text());self.assertEqual(h['status'],'failed');self.assertEqual(h['last_success_at'],'2026-11-06T01:00:00Z');self.assertTrue((root/'data/attempts/attempt.json').exists())
 def test_partial_failure_publishes_healthy_quotes_and_failed_status(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.setup_tree(root)
   snapshot=dict(collected_at='2026-11-07T02:00:00Z',models=[dict(id='new',provenance='official',stale=False,observed_at='2026-11-07T02:00:00Z')],sources=[dict(provider='openai',status='parsed'),dict(provider='deepseek',status='failed')])
   with patch.object(collect,'ROOT',root):result=collect.save_result(snapshot,'attempt',{})
   self.assertTrue(result);self.assertEqual(json.loads((root/'data/latest.json').read_text())['models'][0]['id'],'new')
   h=json.loads((root/'data/health.json').read_text());self.assertEqual(h['status'],'degraded');self.assertEqual(h['failed_sources'],['deepseek'])
 def test_collector_crash_rolls_back_partial_latest_and_reports_failure(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.setup_tree(root);before=(root/'data/latest.json').read_bytes()
   def crash():
    (root/'data/latest.json').write_text('{broken');raise RuntimeError('simulated disk/parse crash')
   with patch.object(collect,'ROOT',root),patch.object(collect,'main',side_effect=crash),contextlib.redirect_stderr(io.StringIO()):self.assertFalse(refresh.run())
   self.assertEqual((root/'data/latest.json').read_bytes(),before)
   self.assertEqual(json.loads((root/'data/health.json').read_text())['status'],'failed')
 def test_index_write_failure_does_not_advance_latest(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.setup_tree(root);before=(root/'data/latest.json').read_bytes()
   snapshot=dict(collected_at='now',models=[dict(provenance='official',observed_at='now')],sources=[])
   with patch.object(collect,'ROOT',root),patch.object(collect,'atomic_json',side_effect=OSError('disk full')):
    with self.assertRaises(OSError):collect.save_result(snapshot,'attempt',{})
   self.assertEqual((root/'data/latest.json').read_bytes(),before)
 def test_backup_schedule_retries_missing_failed_old_updates(self):
  today='2026-11-07';good={'last_success_at':today+'T02:23:00Z','failed_sources':[]}
  self.assertFalse(should_collect('schedule','23 6 * * *',good,today))
  for h in [{},{**good,'failed_sources':['openai']},{**good,'last_success_at':'2026-11-06T02:23:00Z'}]:self.assertTrue(should_collect('schedule','23 6 * * *',h,today))
  self.assertTrue(should_collect('workflow_dispatch','',good,today))
  self.assertTrue(should_collect('schedule','23 2 * * *',good,today))

class PublishRecoveryTest(unittest.TestCase):
 def test_concurrent_push_keeps_remote_code_and_all_captured_history(self):
  import os,subprocess
  import publish_data
  def git(cwd,*args):return subprocess.run(['git',*args],cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  with tempfile.TemporaryDirectory() as d:
   base=Path(d);remote=base/'remote.git';work=base/'work';other=base/'other'
   git(base,'init','--bare',str(remote));git(base,'clone',str(remote),str(work));git(work,'checkout','-b','main')
   git(work,'config','user.name','test');git(work,'config','user.email','test@example.com')
   (work/'scripts').mkdir();(work/'data/history').mkdir(parents=True)
   (work/'scripts/refresh.py').write_text("from pathlib import Path\nPath('data/latest.json').write_text('{\"regenerated\":true}')\n")
   (work/'data/latest.json').write_text('{}');git(work,'add','.');git(work,'commit','-m','initial');git(work,'push','-u','origin','main')
   git(base,'clone','--branch','main',str(remote),str(other));git(other,'config','user.name','other');git(other,'config','user.email','other@example.com')
   (other/'remote-code.txt').write_text('must survive');git(other,'add','.');git(other,'commit','-m','concurrent code update');git(other,'push')
   (work/'data/history/captured.json').write_text('{"evidence":"preserve"}');(work/'data/latest.json').write_text('{"old_candidate":true}')
   cwd=Path.cwd()
   try:
    os.chdir(work)
    with patch.dict(os.environ,{'GITHUB_ACTIONS':'true'}),patch.object(publish_data,'run',side_effect=lambda *args,check=True:subprocess.run(args,check=check,stdout=subprocess.PIPE,stderr=subprocess.PIPE)):
     publish_data.publish()
   finally:os.chdir(cwd)
   self.assertTrue((work/'remote-code.txt').exists());self.assertTrue((work/'data/history/captured.json').exists())
   self.assertEqual(json.loads((work/'data/latest.json').read_text()),{'regenerated':True})
   self.assertEqual(git(work,'rev-parse','HEAD').stdout,git(work,'rev-parse','origin/main').stdout)
