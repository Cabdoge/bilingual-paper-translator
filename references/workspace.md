# 工作目录和阶段数据

新任务：`python scripts/create_workspace.py --output /绝对路径/论文双语 --pdf /原文.pdf [--tex /原文.tex]`。至少提供一种输入。仅 TeX 时省略 --pdf，随后在原文副本中取得预览。脚本不复制完整源项目；所需正文、书目及图片依赖由 Sol 定向暂存。续译使用已有目录，不重新初始化。

目录：source/ 原文与必要依赖，extraction/ 解析，batches/ 分派与反馈，translations/ 子代理结果，output/ 最终 .tex/PDF/图片；根目录有 manifest.json、units.jsonl、terminology.json、progress.json、review.md。所有路径以所在工作目录为基础，保留源文件哈希。

## units.jsonl

每行一个稳定块。`id` 唯一且非空，续改保留已有身份；`kind` 为 paragraph/heading/statement/equation/figure/table/bibliography/other；`en` 为已核验英文 LaTeX；`source` 保存 PDF 页码或 TeX 定位，不能只用生成稿页码。

按需增加 `first` / `continued`、原编号、对齐、模式、对象归属等排版信息。不能把独立 display 塞进普通 paragraph，不能把一条完整陈述拆成多个 statement。数学内容及其编号在源块中保持稳定；翻译前记录 `source_hash` 为 UTF-8 en 字符串的 SHA-256。

## terminology.json 与批次

根对象为 `version`（从 1 开始的整数）及 `entries`。条目记录 english、translation 或 retain、person，以及按需的上下文/别名。这是当前论文的术语表，不是整个 skill 共享并污染所有论文的全局词典。

每个 batches/*.json 文件包含 `id`、`unit_ids`、`glossary_version`；其余字段可保存背景、符号定义及任务说明。每个 assigned ID 只属于一个初始分派；定向返工可另记 attempt，不能把两份结果悄悄叠加。

translations/*.jsonl 每行：

```json
{"id":"u0010","source_hash":"英文 en 的 SHA-256","glossary_version":1,"zh":"中文 LaTeX","notes":[]}
```

记录 source_hash 与 version 用于识别来源变化，不证明数学正确。Sol 可为纯公式/英文书目直接复制产生对应结果，无需让 Luna 重写。术语版本升级后，Sol 定向修正受影响块，复核完成再更新当前结果版本；保留旧批次文件作记录，translations/ 只放每块当前选定结果，旧结果移入批次归档。

## progress.json

根对象包含 `stage` 及 `units`；units 按 ID 映射状态，如：

```json
{"stage":"translating","units":{"u0010":{"status":"reviewed","source_hash":"英文哈希","glossary_version":1}}}
```

状态根据真实结果设置；reviewed 只在 Sol 完成内容复核后写入。notes 与独立 review.md 记录疑点及处理，编译成功不自动把块升级为 reviewed。

`check_workspace.py /工作目录` 检查当前已交付结果与源块一致；加 `--complete` 要求每块有译文且已复核。该检查只在阶段交接或实际修改后重跑，不为未解决语义问题反复刷检查。

`check_document.py --tex /稿件.tex --log /编译.log --pdf /稿件.pdf` 检查可观察的结构/编译/跳转问题，依赖 pypdf。PDF 中原文、数学和图像仍要由 Sol 查看。生成过程不能修改只读的 en 或源文件来迁就检查器。
