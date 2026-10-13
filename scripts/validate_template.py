"""Check observable layout/side-effect invariants of the compiled fixture.
Run with the bundled Python containing pdfplumber and pypdf, after latexmk.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,re,argparse,subprocess,shutil
import pdfplumber
from pypdf import PdfReader

parser=argparse.ArgumentParser(description='Compile and inspect the packaged four-page template case.')
parser.add_argument('--build-dir',type=Path,required=True)
args=parser.parse_args()
root=args.build_dir.expanduser().resolve();root.mkdir(parents=True,exist_ok=True)
skill=Path(__file__).resolve().parents[1]
base=(skill/'assets/template.tex').read_text(encoding='utf-8')
start=re.search(r'^\\begin\{document\}',base,re.M)
if not start:raise SystemExit('Template document body missing')
body=(skill/'assets/validation-body.tex').read_text(encoding='utf-8')
(root/'bilingual-layout-validation.tex').write_text(base[:start.start()]+body,encoding='utf-8')
shutil.copyfile(skill/'assets/test-figure.png',root/'test-figure.png')
try:
 with (root/'build.console').open('w',encoding='utf-8') as output:
  build=subprocess.run(['latexmk','-xelatex','-halt-on-error','-interaction=nonstopmode','bilingual-layout-validation.tex'],cwd=root,stdout=output,stderr=subprocess.STDOUT)
except FileNotFoundError:raise SystemExit('latexmk/XeLaTeX unavailable')
if build.returncode:raise SystemExit('Compile failed; inspect '+str(root/'build.console'))
pdf=root/'bilingual-layout-validation.pdf'
log=(root/'bilingual-layout-validation.log').read_text()
aux=(root/'bilingual-layout-validation.aux').read_text()
source=(root/'bilingual-layout-validation.tex').read_text()
checks=[]
def check(name,passed,detail):
 checks.append({'check':name,'passed':bool(passed),'detail':detail})

check('Compile diagnostics',not re.search(r'^!|Overfull|undefined references|multiply defined|LaTeX Warning',log,re.M),'Final compilation has no errors, overfull boxes, unresolved references or repeated labels.')
routes=dict(re.findall(r'CASE\|([^|\n]+)\|([^\n]+)',log))
check('Side-effect routing',all(routes.get(x)=='fixed' for x in ['FOOTNOTE','LABEL','COUNTER','FIGURE','TABLE']),str(routes))
actual=int(re.search(r'VALIDATION-PROBE-RUNS=(\d+)',log)[1])
check('Exactly-once counter calls',actual==6,f'Expected 6 calls, observed {actual}.')
labels=re.findall(r'\\newlabel\{([^}]+)\}',aux)
check('No duplicate label writes',all(c==1 for c in Counter(labels).values()),f'{len(labels)} unique writes.')

reader=PdfReader(pdf)
named=reader.named_destinations
with pdfplumber.open(pdf) as textdoc:
 texts=[p.extract_text() for p in textdoc.pages]
alltext='\n'.join(texts)
check('Four-page fixture',len(reader.pages)==4,f'{len(reader.pages)} pages.')
check('Two real footnotes, no duplicates',all(alltext.count(x)==1 for x in ['FOOTNOTE-EN-ONCE','FOOTNOTE-ZH-ONCE']),'Both footnote payloads occur once.')
fndests=[n for n in named if n.startswith('Hfootnote.')]
check('Footnote targets separated by language',len(fndests)==2 and any('column0' in n for n in fndests) and any('column1' in n for n in fndests),str(fndests))
links=[];missing=[]
for p in reader.pages:
 for ref in p.get('/Annots',[]):
  a=ref.get_object()
  if a.get('/Subtype')!='/Link':continue
  action=a.get('/A')
  if action and action.get('/S')=='/GoTo':
   d=action.get('/D');links.append(str(d))
   if isinstance(d,str) and d not in named:missing.append(str(d))
check('All internal links resolve',not missing,f'{len(links)} links; missing targets: {missing}.')
check('Figure, table and theorem targets in both columns',all(f'{kind}:1:{lang}' in named and f'{kind}:1:{lang}' in links for kind in ['figure','table','theorem'] for lang in ['en','zh']),'Forward links to six object/language targets resolve.')
check('Equation references target actual numbered displays',all(re.search(r'\\newlabel\{eq:long:'+lang+r'\}',aux) for lang in ['en','zh']) and '(1)' in alltext,'Both language labels exist and source number 1 is visible.')

cross={k:int(v) for k,v in re.findall(r'\\newlabel\{(cross:[^}]+)\}\{\{[^}]*\}\{(\d+)\}',aux)}
check('Both theorem statements span pages',all(cross.get(f'cross:start:{lang}',999)<cross.get(f'cross:end:{lang}',0) for lang in ['en','zh']),str(cross))
body=source[source.index('\\begin{document}'):]
span=body[body.index('\\hypertarget{theorem:1:en}'):body.index('\\typeout{VALIDATION-PROBE-RUNS')]
check('Final formulas stay inside the theorem pair',span.count('\\end{formaltheoremen}')==1 and span.count('\\end{formaltheoremzh}')==1 and all(re.search(r'\\end\{equation\*\}\\phantomsection\\label\{cross:end:'+lang+r'\}\s*\\end\{formaltheorem'+lang+r'\}',span) for lang in ['en','zh']),'Final formulas precede the matching formal-environment ends; the outer pair closes afterward.')
check('No added paragraph break before displays',not re.search(r'\\par\s*\\begin\{(?:equation\*?|align\*?)\}',body),'No explicit paragraph break immediately before display environments.')

with pdfplumber.open(pdf) as doc:
 p1,p2,p3=doc.pages[:3]
 left=25/25.4*72;gap=36/25.4*72;col=(p1.width-2*left-gap)/2;right=left+col+gap
 def hit(page,text):
  hs=page.search(text)
  assert hs,f'Missing text: {text}'
  return hs[0]
 title=hit(p1,'Bilingual Layout Validation')
 zh_title=hit(p1,'双栏翻译排版验证案例')
 centered=hit(p1,'1 Centered heading');zh_centered=hit(p1,'1 居中标题')
 check('Centered titles in both columns',all(abs((h['x0']+h['x1'])/2-center)<1 for h,center in [(title,left+col/2),(zh_title,right+col/2),(centered,left+col/2),(zh_centered,right+col/2)]),'Document and section titles are centered to within 1 PDF point.')
 check('Left-aligned headings',abs(hit(p1,'2 Figure and translated table')['x0']-left)<.5 and abs(hit(p1,'2 图片与双栏表格')['x0']-right)<.5,'Left headings start at their column edges.')
 check('Same raster figure shown twice',len(p1.images)==2 and p1.images[0]['name']==p1.images[1]['name'],'One image asset is drawn once in each column.')
 check('Translated tables preserve numeric values',all(alltext.count(x)==2 for x in ['0.120','0.081','0.043']) and '基准模型' in alltext and 'Baseline' in alltext,'Three result rows have unchanged numbers in both languages.')
 en=hit(p2,'A subsequent paragraph');zh=hit(p2,'有 TeX 原文时')
 ensize=en['chars'][0]['size'];zhsize=zh['chars'][0]['size']
 check('TeX-mode English indent 1.5em',abs(en['x0']-left-1.5*ensize)<.5,f'Indent {en["x0"]-left:.3f} bp, font {ensize:.3f} bp.')
 check('TeX-mode Chinese indent 2em at selected size',abs(zh['x0']-right-2*zhsize)<.5,f'Indent {zh["x0"]-right:.3f} bp, font {zhsize:.3f} bp.')
 check('English first paragraph after heading is flush',abs(hit(p2,'First heading paragraph')['x0']-left)<.5,'Explicit first-paragraph rule is applied.')
 check('PDF-only mode has no indentation in either column',abs(hit(p2,'For a PDF-only source')['x0']-left)<.5 and abs(hit(p2,'只有 PDF 原文时')['x0']-right)<.5,'Both paragraphs begin at their column edges.')
 headers=[hit(p3,r'Theorem\s+1\.'),hit(p3,r'定理\s*1\.')]
 check('Theorem labels are black',all(c.get('non_stroking_color') in [None,(0,),(0,0,0),0] for h in headers for c in h['chars']),'Both statement title labels use black text.')
 overlap=[]
 for ref in reader.pages[2].get('/Annots',[]):
  a=ref.get_object()
  if a.get('/Subtype')!='/Link':continue
  x0,y0,x1,y1=map(float,a['/Rect']);top=p3.height-y1;bottom=p3.height-y0
  for h in headers:
   if x0<h['x1'] and x1>h['x0'] and top<h['bottom'] and bottom>h['top']:overlap.append(str(a))
 check('No self-links over theorem labels',not overlap,'No link annotation intersects either statement title.')
 closing='，。；：！？、）》」』】'
 outside=[(i+1,c['text']) for i,p in enumerate(doc.pages) for c in p.chars if c['text'].strip() and (c['x0']<left-.7 or (c['x1']>p.width-left+.7 and not (c['text'] in closing and c['x0']<p.width-left+.7 and c['x1']<p.width-left+c['size'])))]
 check('Text stays within margins allowing CJK closing punctuation',not outside,f'Outside-margin non-punctuation characters: {outside[:5]}. CJK closing-punctuation advance boxes may hang; rendered pages are reviewed separately.')

result={'passed':sum(c['passed'] for c in checks),'total':len(checks),'checks':checks}
(root/'validation-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
lines=['# 正式模板回归检查','',f'{result["passed"]}/{result["total"]} checks passed.','',
'副作用块必须固定字号；间接包含副作用的宏应显式 mode=fixed。',
'脚注保持 pair 末端模式；自动检查不替代逐页渲染查看。','', '| Check | Result | Evidence |','|---|---|---|']
for c in checks:lines.append('| '+c['check']+' | '+('PASS' if c['passed'] else 'FAIL')+' | '+c['detail'].replace('|',' / ')+' |')
(root/'validation-report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(f'{result["passed"]}/{result["total"]} checks passed')
for c in checks:
 if not c['passed']:print('FAIL:',c['check'],c['detail'])
if result['passed']!=result['total']:raise SystemExit(1)
