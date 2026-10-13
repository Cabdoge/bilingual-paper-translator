#!/usr/bin/env python3
"""Initialize a new paper workspace; never overwrite sources or an existing run."""
import argparse,hashlib,json,shutil
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--output',type=Path,required=True)
 p.add_argument('--pdf',type=Path)
 p.add_argument('--tex',type=Path)
 a=p.parse_args()
 if not (a.pdf or a.tex):p.error('provide --pdf or --tex')
 sources={}
 for kind,path in [('pdf',a.pdf),('tex',a.tex)]:
  if path:
   path=path.expanduser().resolve()
   if not path.is_file() or path.suffix.lower()!='.'+kind:p.error(f'invalid {kind} source: {path}')
   sources[kind]=path
 out=a.output.expanduser().resolve()
 if out.exists():p.error(f'output exists; resume it instead: {out}')
 template=Path(__file__).resolve().parents[1]/'assets/template.tex'
 if not template.is_file():p.error('template asset missing')
 out.mkdir(parents=True)
 for d in ['source','extraction','batches','translations','output']: (out/d).mkdir()
 manifest={'source_type':'tex' if a.tex else 'pdf','sources':{},'models':{'sol':{'model':'gpt-6.1-sol','reasoning_effort':'high'},'luna':{'model':'gpt-6-luna','reasoning_effort':'xhigh'}},'version_check':'pending' if len(sources)==2 else 'single-source','parallel_limit':3}
 for kind,src in sources.items():
  dest=out/'source'/('original.'+kind);shutil.copyfile(src,dest)
  digest=hashlib.sha256(src.read_bytes()).hexdigest()
  if hashlib.sha256(dest.read_bytes()).hexdigest()!=digest:raise RuntimeError('source-copy checksum mismatch')
  manifest['sources'][kind]={'original_path':str(src),'copy':'source/'+dest.name,'sha256':digest}
 for name,obj in [('manifest.json',manifest),('terminology.json',{'version':1,'entries':[]}),('progress.json',{'stage':'initialized','units':{}})]:
  (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (out/'units.jsonl').write_text('',encoding='utf-8')
 (out/'review.md').write_text('# 校对记录\n\n按原 PDF 页码、pair ID、疑点、处理结果和状态记录。\n',encoding='utf-8')
 text=template.read_text(encoding='utf-8')
 if a.tex:text=text.replace('\\SourceHasTeXfalse % 有原 TeX 时改成 SourceHasTeXtrue','\\SourceHasTeXtrue % 实际输入包含原 TeX',1)
 (out/'output/translation.tex').write_text(text,encoding='utf-8')
 print(json.dumps({'workspace':str(out),'source_type':manifest['source_type'],'sources':list(sources)},ensure_ascii=False))
if __name__=='__main__':main()
