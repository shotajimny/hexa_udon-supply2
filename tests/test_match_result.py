import contextlib,io,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from match_result import MatchResultReporter

class MatchResultTests(unittest.TestCase):
 def test_saved_actual_state_rejection_and_cli(self):
  source={'map':{'width':2,'height':1,'cells':[[0,0]]},'spots':[{'pos':1,'brand':7,'stocks':1}],'daySteps':[2,2]}
  events=[{'type':'day','day':0,'agents':[{'kind':0,'pos':0,'fuel':10}],'traffics':[]},{'type':'post','endpoint':'/','day':0,'payload':[[2]],'body':'{"revision":1}'},{'type':'post','endpoint':'/','day':0,'payload':[[99]],'body':'{"revision":-1}'}]
  with tempfile.TemporaryDirectory() as root,contextlib.redirect_stdout(io.StringIO()):
   reporter=MatchResultReporter(source,events,root)
   self.assertFalse(reporter.update()['complete'])
   events.append({'type':'day','day':1,'agents':[{'kind':0,'pos':1,'fuel':9}],'traffics':[]})
   stats=reporter.update(completed=True)
   self.assertEqual(stats['total_count'],2)
   self.assertEqual(stats['cumulative_types'],2)
   self.assertEqual(stats['missing_brands'],[])
   file=reporter.directory/'match.json';saved=json.loads(file.read_text());self.assertEqual(saved['events'],events)
   output=subprocess.check_output([sys.executable,'match_result.py',str(file)],text=True)
   self.assertIn('合計獲得数: 2',output)
 def test_mismatched_real_position_is_not_complete(self):
  source={'map':{'width':2,'height':1,'cells':[[0,0]]},'spots':[{'pos':1,'brand':7,'stocks':1}],'daySteps':[2,2]}
  events=[{'type':'day','day':0,'agents':[{'kind':0,'pos':0}],'traffics':[]},{'type':'post','endpoint':'/','day':0,'payload':[[2]],'body':'{"revision":1}'},{'type':'day','day':1,'agents':[{'kind':0,'pos':0}],'traffics':[]}]
  with tempfile.TemporaryDirectory() as root,contextlib.redirect_stdout(io.StringIO()) as out:
   stats=MatchResultReporter(source,events,root).update(completed=True)
   self.assertFalse(stats['complete']);self.assertIsNone(stats['missing_brands']);self.assertIn('判定できません',out.getvalue())

if __name__=='__main__':unittest.main()
