#!/usr/bin/env python3
"""Apply emotion_primary + content_pillar batch results to obs files."""
import json, os, re
from pathlib import Path

REPO = Path(__file__).parent.parent
LOGS = REPO / 'logs'

def load_key():
    env = Path.home() / '.abraham_env'
    for line in env.read_text().splitlines():
        if line.startswith('OPENAI_API_KEY=') or line.startswith('OPENAI_KEY='):
            os.environ['OPENAI_API_KEY'] = line.split('=',1)[1].strip().strip('"').strip("'")
            return
load_key()
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.openai_client import make_client  # B258: bounded timeout/retries
client = make_client()

state = json.loads((LOGS / 'emotion_pillar_state.json').read_text())
batch_id = state['batch_id']
cid_map = json.loads(Path(state['cid_map_file']).read_text())

b = client.batches.retrieve(batch_id)
rc = b.request_counts
print(f'Batch {batch_id}: status={b.status} completed={getattr(rc,"completed",0)}/{getattr(rc,"total",0)}')
if b.status != 'completed':
    print('Not done yet — run again later.'); raise SystemExit(0)

raw = client.files.content(b.output_file_id).text
results = [json.loads(l) for l in raw.strip().splitlines() if l.strip()]

written = errors = 0
for r in results:
    cid = r.get('custom_id','')
    obs_path = Path(cid_map.get(cid,''))
    if not obs_path.exists(): continue
    try:
        content = r.get('response',{}).get('body',{}).get('choices',[{}])[0].get('message',{}).get('content','')
        content = re.sub(r'^```[a-z]*\n?','',content.strip())
        content = re.sub(r'\n?```$','',content.strip())
        parsed = json.loads(content)
        d = json.loads(obs_path.read_text())
        changed = False
        for field in ['emotion_primary','content_pillar','content_pillar_confidence']:
            if not d.get(field) and field in parsed:
                d[field] = parsed[field]; changed = True
        if changed:
            obs_path.write_text(json.dumps(d, indent=2, ensure_ascii=False)); written += 1
    except: errors += 1

print(f'Applied: {written} obs updated | {errors} errors')
