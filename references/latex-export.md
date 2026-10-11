# LaTeX 导出

本 skill 产出的**每一份 PDF**，不论学科或是否有公式，均须先生成 `.tex`，再用 XeLaTeX 或 LuaLaTeX 实际编译，且**一律黑底白字**：页面底色为黑、文字为白，标题、公式、表格框线与导图连线同用白色系（`\pagecolor{black}` 配合 `\color{white}`；导图中原本的 `black!NN` 改为 `white!NN`，圆点的 `fill=white` 改为 `fill=black`）。**例外**：每日课程的“宽松排版型”与错题本要打印出来手写作答，改用白底黑字（`\pagecolor{white}` 配合 `\color{black}`，导图颜色反向翻回 `black!NN`、圆点 `fill=white`）；渲染脚本已按 `--layout loose` 与 `--kind errors` 自动切换两种主题，其余 PDF 一律黑底白字。知识清单、备考计划等主文件的最终 PDF 放在科目或比赛文件夹顶层；每日课程 PDF 放在各自的 `每日学习/D001-YYYY-MM-DD` 文件夹。对应 `.tex` 放在同级 `源文件` 子目录，保持同名以便重编译。**源文件里的公式必须写成 LaTeX 数学模式**：行内用 `$...$`、独立成行用 `$$...$$`；下标写 `A_1`、上标写 `A^c`、星号上标写 `\mu^{\ast}`（可测集类与教材一致写作 `\mathcal{A}^{\ast}`）。渲染脚本会转义数学模式之外的文字，所以裸写 `A_1` 只会印出下划线——这是本 skill 最常见、也最容易漏掉的排版错误。材料里若已有裸下标，渲染前先运行 [`scripts/normalize_math.py`](../scripts/normalize_math.py) 批量改写，再用 [`scripts/scan_math.py`](../scripts/scan_math.py) 确认残留为 0；不得使用网页打印、Word 导出、ReportLab 等其他方式替代编译。若编译器不可用，先排查或安装，仍不可用时明确告知 PDF 尚未完成，不输出来源不明的 PDF。

工作区的 [`scripts/render_study_pdf.py`](../scripts/render_study_pdf.py) 可把本 skill 常用的 Markdown（标题、段落、列表、表格、粗体、链接和 `$...$`／`$$...$$` 公式）转成 XeLaTeX 文档，并按文档类型自动选定配色主题：知识清单、备考计划、每日课程紧凑版用黑底白字，每日课程宽松版与错题本用白底黑字的打印版（导图线条随之在白色系与黑色系之间切换）。它从一个 JSON 文件读取导图信息：顶层分别以 `knowledge`、`plan`、`day` 为键，每项有 `title`、`headline`、`tagline`／`groups`／`date_range`／`footnote` 和六个 `nodes`；每个节点有 `title` 与 `lines`，`knowledge` 与 `day` 的节点各给三行，`plan` 的第 1 行作日期、其余作细节，第 6 个节点作复盘回路。如果材料含脚本未支持的 Markdown，先扩展转换逻辑或直接编写 `.tex`，不得丢失正文。

```text
python scripts/normalize_math.py 科目/每日学习/D001-YYYY-MM-DD/源文件/今日课程.md
python scripts/scan_math.py 科目/每日学习/D001-YYYY-MM-DD/源文件/今日课程.md
python scripts/render_study_pdf.py 科目/每日学习/D001-YYYY-MM-DD/源文件/今日课程.md 科目/每日学习/D001-YYYY-MM-DD/源文件/今日课程-紧凑.tex --kind day --layout compact --map-config 科目/每日学习/D001-YYYY-MM-DD/源文件/导图.json
python scripts/render_study_pdf.py 科目/每日学习/D001-YYYY-MM-DD/源文件/今日课程.md 科目/每日学习/D001-YYYY-MM-DD/源文件/今日课程-宽松.tex --kind day --layout loose --map-config 科目/每日学习/D001-YYYY-MM-DD/源文件/导图.json
python scripts/compile_study_pdf.py 科目/每日学习/D001-YYYY-MM-DD/源文件/今日课程-紧凑.tex 科目/每日学习/D001-YYYY-MM-DD/今日课程-紧凑.pdf
python scripts/compile_study_pdf.py 科目/每日学习/D001-YYYY-MM-DD/源文件/今日课程-宽松.tex 科目/每日学习/D001-YYYY-MM-DD/今日课程-宽松.pdf
```

[`scripts/normalize_math.py`](../scripts/normalize_math.py) 在渲染之前运行，把 Markdown 里裸写的下标、上标与星号上标整体改写为数学模式（`µ_1(A) = µ_2(A)` 会连运算符一起进入数学模式，`µ*` 写成 `\mu^{\ast}`、`A*` 写成 `\mathcal{A}^{\ast}`）。它不动已有的 `$...$`、反引号代码段与 Markdown 链接，并且是幂等的，重复执行不会二次改动；可加 `--dry-run` 先看改动量，或用 `--report` 输出报告。[`scripts/scan_math.py`](../scripts/scan_math.py) 是配套自查，列出数学模式之外仍裸写的下标与上标，输出必须为空；有输出就按缺陷处理，不要带着它交付 PDF。注意导图 JSON 的文字不走数学模式（渲染脚本会转义那里的 `$`），所以导图里不要写 `L^r` 这类记号，改用文字表述。

对知识清单和备考计划分别使用 `--kind knowledge`、`--kind plan`。每日课程每个核心方法用 `## 单元 N...` 标题，脚本使单元另起一页；单元包含一题完整例题和其举一反三。将独立填步题、变式题放在 `### 举一反三` 下，混合题放在 `## 独立练习` 下，使用 `**A1.**` 一类题号；脚本只给这些题目留作答空白，例题不留白。若某题需要长证明或作图，按实际解答量调整空白高度。答案应有单独的二级标题，并位于全部独立练习之后。

错题本用 --kind errors 渲染，不需要导图 JSON；不制作思维导图、独立封面或其他非正题内容，首页直接进入第一条错题。每条错题采用“错题 N”二级标题，第二条起另起一页；复做题置于“再做一题”三级标题下，答案集中放在后部的二级标题。复做记录用 LaTeX 数学模式的 `$\square$` 表示可手写勾选的空方框，每个日期提供独立做对、订正后做对、未做对等选项；不要预勾选模拟记录。错题本与每日课程的宽松版都是白底黑字的打印版，使用 `--layout loose` 得到带作答区的那一种。正文排版：黑底白字的版本用白色系线条，白底黑字的打印版（宽松版、错题本）用黑色系线条；两者都保持宽页边距、较舒展的行距和段距；表格优先不用竖线，留足行高。核心例题和错题记录都不要在同页堆叠，题干与步骤保持在一起，避免标题落在页尾。紧凑版也保留阅读所需空白；两个版本只在独立题的作答区有差异。编译器源文件应能在本机重新编译成同一内容的 PDF。

编译脚本实际调用 XeLaTeX 两遍，用临时 ASCII 文件名避开 Windows 上中文日志文件名写入失败；若要使用 LuaLaTeX，可传 --compiler lualatex。源文件应为自包含的 LaTeX 文档。检查日志中的缺字与越界警告，渲染 PDF 的每一页检查中文、公式、导图、表格和作答空白；同时确认 `scan_math.py` 的输出为空（源码里没有裸写的下标与上标），并抽查若干数学密集页，核对下标、上标、求和号上下限与大括号是否与教材排法一致。紧凑版和宽松版必须出自同一份课程文本，核对题目及答案完整一致。
