#!/usr/bin/env python3
"""Check final compile diagnostics, label writes and PDF GoTo destinations."""
import argparse,json,re
from collections import Counter
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for key in ['tex','log','pdf']:p.add_argument('--'+key,type=Path,required=True)
 p.add_argument('--aux',type=Path);a=p.parse_args();errors=[]
 for file in [a.tex,a.log,a.pdf]:
  if not file.is_file():errors.append(f'missing file: {file}')
 if errors:print(json.dumps({'errors':errors}));return 1
 text=a.tex.read_text(encoding='utf-8');log=a.log.read_text(encoding='utf-8',errors='replace')
 for pattern,label in [(r'^!','TeX error'),(r'Overfull','overfull box'),(r'Missing character','missing glyph'),(r'undefined references|Reference .* undefined','unresolved reference'),(r'multiply defined|duplicate destination|destination.*already','duplicate label/target')]:
  if re.search(pattern,log,re.M|re.I):errors.append(label)
 if not re.search(r'Output written on',log):errors.append('log does not show a completed compilation')
 start=re.search(r'^\s*\\begin\{document\}',text,re.M)
 if not start:errors.append('document body missing')
 else:
  body=re.sub(r'(?<!\\)%[^\n]*','',text[start.end():])
  if re.search(r'\\par\s*\\begin\{(?:equation\*?|align\*?)\}',body):errors.append('extra paragraph immediately before a display')
 aux=a.aux or a.log.with_suffix('.aux')
 if aux.is_file():
  counts=Counter(re.findall(r'\\newlabel\{([^}]+)\}',aux.read_text(encoding='utf-8',errors='replace')))
  errors.extend('duplicate aux label: '+k for k,n in counts.items() if n>1)
 try:from pypdf import PdfReader
 except ImportError:print(json.dumps({'errors':errors+['pypdf unavailable; use bundled document/PDF Python runtime']}));return 1
 try:
  reader=PdfReader(a.pdf);named=reader.named_destinations;count=0
  for page in reader.pages:
   for ref in page.get('/Annots',[]):
    obj=ref.get_object();action=obj.get('/A')
    if obj.get('/Subtype')=='/Link' and action and action.get('/S')=='/GoTo':
     count+=1;dest=action.get('/D')
     if isinstance(dest,str) and dest not in named:errors.append('missing link target: '+dest)
  names=[]
  def walk(node):
   if hasattr(node,'get_object'):node=node.get_object()
   arr=node.get('/Names',[]);names.extend(str(arr[i]) for i in range(0,len(arr),2))
   for kid in node.get('/Kids',[]):walk(kid)
  root=reader.trailer['/Root'].get('/Names')
  if root:
   root=root.get_object()
   if root.get('/Dests'):walk(root['/Dests'])
  errors.extend('duplicate named destination: '+k for k,n in Counter(names).items() if n>1)
  print(json.dumps({'pages':len(reader.pages),'internal_links':count,'named_destinations':len(named),'errors':errors},ensure_ascii=False,indent=2))
 except Exception as e:print(json.dumps({'errors':errors+[f'PDF inspection failed: {e}']}));return 1
 return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
