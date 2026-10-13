# 双栏模板接口与边界

复制 assets/template.tex 到论文 output 目录，替换示例正文，保留中文注释参数区。实例中修改参数，不修改安装的 skill 资产。模板为一个独立 .tex，图片为独立资源，不能将其伪称为无依赖单文件文档。

默认 A3 横版、英文左栏/中文右栏；左右 25 mm，上下 24 mm，栏间 36 mm；BodyFontBP=11，中文候选为基础字号加 0–1.5 bp，步长 .25 bp；正常正文，行距倍率 1.3，无页眉、居中页码，链接色 #167D8D。

## 输入类型与段落

- 用户确有原 TeX：设 `\SourceHasTeXtrue`。中文两字宽，英文 1.5em，英文标题后首段不缩进。
- 用户只有 PDF：保持 `\SourceHasTeXfalse`。两栏普通段落零缩进；MinerU/Luna 产生数学 TeX 不改变实际输入类型。
- 首行缩进在当前字号选择后计算；不要使用在旧字体下提前求值的固定长度。

普通段落开头原有的纯排版 `\indent` / `\noindent` 等，应按块的 first/continued 和输入类型规范化；不能让原排版命令覆盖这里的固定规则。数学字体宏不属于这类命令。

普通段落用：

```tex
\begin{textpair}[id=u0010,first]
英文段落
\switchcolumn
中文段落
\end{textpair}
```

`first` 只取消英文标题后首段缩进。`continued` 表示原段落的续接文字，两栏均不额外缩进。`keep=3` 等值只为开头预留行数，不阻止长块跨页。

`mode=auto` 默认只用于安全普通文字；`mode=fixed` 明确禁止试排。模板对显式脚注、标签、锚点、计数器、图注/图片、环境等做第二道检测，转固定字号。任意宏的间接副作用无法穷尽检测，Sol 必须按块类型正确分派；不要用自动试排处理未知宏。引用宏本身无新增目标，可以在安全段落中使用。

## 标题、定理与公式

`\papertitle[center|left]{英文}{中文}`；`\phead` / `\psubhead` 同样接受对齐参数。各级编号使用原论文文字。PDF 决定对齐，字号/颜色沿用本模板。

结构块用 `pair`，可选参数为开头保护行数。完整定理示例：

```tex
\begin{pair}[\StatementKeepLines]
\hypertarget{bpt:u0012:en}{}
\begin{formaltheoremen}{\StatementNumber{Theorem}{2}}
英文完整陈述及其公式
\end{formaltheoremen}
\switchcolumn
\hypertarget{bpt:u0012:zh}{}
\begin{formaltheoremzh}{\StatementNumber{定理}{2}}
中文完整陈述及其公式
\end{formaltheoremzh}
\end{pair}
```

定义用 formaldefinitionen/zh；其他定理类按原文样式选现有组件并保留原名称和编号。模板不自动生成定理编号。末尾公式必须在对应 formal 环境内，不能被移入下一个 pair。证明按原自然段分块，不默认把整篇长证明锁成一块。

定理类环境之外的行间公式用 equationpair；不在 equation/align 等前添加 `\par` 或空白段落。未编号公式用星号环境，原编号公式明确保留 tag。多行组保持 aligned/align 等逻辑结构，宽公式优先做数学上合理的换行。

`\NumberedLink{目标}{名称}{原编号}` 用于正文提及；名称黑色，数字主题色。`\EqRef{目标}{原编号}` 输出带括号的数字链接。目标按对象 ID 与语言区分，不能仅凭原数字认定归属。

## 图表与脚注

图和表各用一个固定字号 pair，在每栏放对应内容和图注。优先非浮动的 minipage + includegraphics/tabular 等，防止两栏各自浮动而失去对应。图片不能翻译时两栏同一资源，图注仍翻译；宽度/高度需适应栏宽并保留比例。图表编号显式保留，语言目标独立。

长表不能塞进不可分页的 minipage；也不要把普通 longtable 直接塞进 paracol。必要时按完整行组拆成连续表格块、重复表头并保持原号及对象归属，逐页核验缺行。此行为需要针对实际表格验证，不宣称合成短表覆盖所有长表。

脚注使用固定块；可用 `\SourceFootnote{原标记}{内容}`，两栏保留原标记而内部目标分离。原脚注可以翻译，过程疑点不能变成译稿脚注。当前已验证脚注跟随对应 pair 末端排出，不承诺整页物理底部定位。

## 编译及交付

单文件、无额外资源的稿件优先内置 compile_latex_document；多文件/图片项目用 XeLaTeX/latexmk，运行目录正确指向 output，保留最后一次成功生成的 PDF。原文预览与译稿分别编译。不要在编译失败后交付旧 PDF 冒充最新结果。

检查无未解析引用、重复标签/目标及可见溢出。逐页渲染看中文、数学、图片、脚注、标题与分页；CJK 标点全字宽框可能包含边缘空白，位置检查需结合实际图像，不能只根据字框判定溢出。

已验证的四页案例位于这台机器的 `/Users/1tianpang/Zotero/output/pdf/bilingual-layout-validation/`；skill 本身不依赖该绝对路径。正式模板更改后重跑相应案例。宏间接副作用、复杂长表或特殊文档类仍需针对真实输入核验。

维护时可运行 `scripts/validate_template.py --build-dir /临时或工作目录/template-check`，依赖 latexmk/XeLaTeX、pdfplumber、pypdf。它用当前模板和打包的合成正文生成四页案例，检查副作用、链接、跨页和几何；随后仍需逐页渲染。案例图片是人工模拟数据，不是任何论文的实验结果。
