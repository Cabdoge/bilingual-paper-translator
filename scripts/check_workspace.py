#!/usr/bin/env python3
"""Read-only stage checks; does not certify semantic translation quality."""
import argparse,hashlib,json
from pathlib import Path

KINDS={'paragraph','heading','statement','equation','figure','table','bibliography','other'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('workspace',type=Path);p.add_argument('--complete',action='store_true');a=p.parse_args()
 root=a.workspace.expanduser().resolve();errors=[]
 def read_json(path):
  try:return json.loads(path.read_text(encoding='utf-8'))
  except (OSError,ValueError) as e:errors.append(f'{path.name}: {e}');return {}
 def rows(path):
  try:lines=path.read_text(encoding='utf-8').splitlines()
  except OSError as e:errors.append(str(e));return []
  result=[]
  for n,line in enumerate(lines,1):
   if not line.strip():continue
   try:r=json.loads(line)
   except ValueError as e:errors.append(f'{path.name}:{n}: {e}');continue
   if not isinstance(r,dict):errors.append(f'{path.name}:{n}: object expected');continue
   result.append(r)
  return result
 terms=read_json(root/'terminology.json');progress=read_json(root/'progress.json');manifest=read_json(root/'manifest.json')
 if not isinstance(terms,dict):errors.append('terminology must be an object');terms={}
 if not isinstance(progress,dict):errors.append('progress must be an object');progress={}
 if not isinstance(manifest,dict):errors.append('manifest must be an object');manifest={}
 version=terms.get('version')
 if type(version) is not int or version<1:errors.append('invalid glossary version')
 if manifest.get('source_type') not in {'tex','pdf'}:errors.append('invalid actual input type')
 units={}
 for r in rows(root/'units.jsonl'):
  uid=r.get('id');en=r.get('en')
  if not isinstance(uid,str) or not uid.strip():errors.append('empty/non-string unit ID');continue
  if uid in units:errors.append(f'duplicate unit ID: {uid}');continue
  if r.get('kind') not in KINDS:errors.append(f'{uid}: unknown kind')
  if not isinstance(en,str) or not en.strip():errors.append(f'{uid}: empty/non-string English block');continue
  digest=hashlib.sha256(en.encode('utf-8')).hexdigest()
  if 'source_hash' in r and r['source_hash']!=digest:errors.append(f'{uid}: stored English hash changed')
  if not isinstance(r.get('source'),dict) or not r['source']:errors.append(f'{uid}: source location missing')
  units[uid]=digest
 results={}
 for path in sorted((root/'translations').glob('*.jsonl')):
  for r in rows(path):
   uid=r.get('id')
   if not isinstance(uid,str):errors.append(f'{path.name}: invalid result ID');continue
   if uid in results:errors.append(f'duplicate active result: {uid}')
   results[uid]=r
   if uid not in units:errors.append(f'unknown result ID: {uid}');continue
   if r.get('source_hash')!=units[uid]:errors.append(f'{uid}: stale/wrong source hash')
   if r.get('glossary_version')!=version:errors.append(f'{uid}: stale glossary version')
   if not isinstance(r.get('zh'),str) or not r['zh'].strip():errors.append(f'{uid}: empty Chinese result')
   if not isinstance(r.get('notes'),list):errors.append(f'{uid}: notes must be a list')
 states=progress.get('units',{})
 if not isinstance(states,dict):errors.append('progress.units must be an object');states={}
 for uid,state in states.items():
  if uid not in units:errors.append(f'unknown progress ID: {uid}');continue
  if not isinstance(state,dict):errors.append(f'{uid}: invalid progress record');continue
  if state.get('status')=='reviewed':
   if uid not in results:errors.append(f'{uid}: reviewed without selected translation')
   if state.get('source_hash')!=units[uid] or state.get('glossary_version')!=version:errors.append(f'{uid}: reviewed state is stale')
 if a.complete:
  if not units:errors.append('no source units; empty workspace is not complete')
  for uid in units:
   if uid not in results:errors.append(f'{uid}: missing translation')
   if not isinstance(states.get(uid),dict) or states[uid].get('status')!='reviewed':errors.append(f'{uid}: not reviewed by Sol')
 for kind,entry in manifest.get('sources',{}).items():
  if not isinstance(entry,dict):errors.append(f'{kind}: invalid source metadata');continue
  name=entry.get('copy')
  if not isinstance(name,str):errors.append(f'{kind}: missing source-copy path');continue
  copy=(root/name).resolve()
  if not copy.is_relative_to(root):errors.append(f'{kind}: source copy outside workspace');continue
  if not copy.is_file() or hashlib.sha256(copy.read_bytes()).hexdigest()!=entry.get('sha256'):errors.append(f'{kind}: source copy changed or missing')
 print(json.dumps({'units':len(units),'translated':len(results),'glossary_version':version,'complete_check':a.complete,'errors':errors},ensure_ascii=False,indent=2))
 return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
