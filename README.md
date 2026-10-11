# Good Learning（个人自用）

一个用于 AI agent 的学习与备考 skill：根据考纲、教材、真题和可用时间建立知识清单、备考计划与每日课程，再依据真实作答整理错题并调整后续安排

## 能做什么

- 分别制作知识清单和备考计划，保留知识点编号、验收标准及来源
- 按零基础或复习模式生成自成体系的每日课程，包括例题、变式、混合练习与逐步答案
- 根据用户的实际作答制作错题本；演示错误会标为模拟，不计入真实掌握状态
- 为当日复盘绘制 SVG 思维导图，可选生成 PNG 预览
- 通过 XeLaTeX 或 LuaLaTeX 编译课程、清单、计划和错题本 PDF；科目目录存放知识清单和备考计划 PDF，每日课程按日期独立成夹；各文件夹顶层只放最终 PDF，Markdown、`.tex` 和其他源文件放在对应的 `源文件` 子目录
- PDF 的公式以 LaTeX 数学模式排版、与教材排法一致，下标与上标不会被印成下划线：渲染前用 `normalize_math.py` 规范化，交付前用 `scan_math.py` 自查

## 输出目录

```text
科目或比赛/
├── 知识清单.pdf
├── 备考计划.pdf
├── 源文件/
└── 每日学习/
    └── D001-YYYY-MM-DD/
        ├── D001-紧凑排版型.pdf
        ├── D001-宽松排版型.pdf
        └── 源文件/  课程文本、LaTeX、配置与当日学习记录
```

后续课程按真实学习进度逐日建立，用户提交作答或错题后更新对应日期的记录，并调整尚未完成的学习任务

## 安装

以codex为示例：把仓库克隆或复制为 Codex skills 目录下的 `good-learning` 文件夹，重启 Codex 或重新加载 skills 后即可使用

```text
~/.codex/skills/good-learning/SKILL.md
```

示例请求：

```text
我准备参加一项数学竞赛，每天能学三小时，请帮我制定知识清单和备考计划
我是零基础，开始今天的学习
这里是我的作答，请核对并制作错题本
根据今天的知识和错题绘制总结思维导图
```

## 运行环境

- Python 3.10 或更新版本
- PDF：XeLaTeX 或 LuaLaTeX，以及 `ctex`、`amsmath`、`tikz` 等常用 LaTeX 宏包
- 总结图 PNG：Pillow，使用 `pip install -r requirements.txt` 安装
- 总结图 SVG：只需 Python 标准库
- 生成 PNG 时需提供中文字体；脚本可自动查找常见字体，也可用 `--font` 和 `--bold-font` 指定

## 脚本

```text
scripts/normalize_math.py        渲染前把裸写的下标、上标与星号上标改写为 LaTeX 数学模式（幂等）
scripts/scan_math.py             自查：列出数学模式之外仍裸写的下标与上标，输出应为空
scripts/render_study_pdf.py      常用 Markdown → LaTeX
scripts/compile_study_pdf.py     LaTeX → PDF
scripts/render_summary_map.py    JSON → SVG，可选 PNG
```

公式一律写成 LaTeX 数学模式（行内 `$...$`、独立成行 `$$...$$`），下标写 `A_1`、上标写 `A^c`。渲染脚本会转义数学模式之外的文字，裸写 `A_1` 只会印出下划线；材料里若已有裸下标，渲染前先跑 `normalize_math.py`，再用 `scan_math.py` 确认为 0

```text
python scripts/normalize_math.py 科目/源文件/知识清单.md --report 规范化报告.txt
python scripts/scan_math.py 科目/源文件/知识清单.md
```

总结图输入为 JSON，包含 `eyebrow`、`title`、`subtitle`、`status`、`description`、`core_label`、`core_title`、`core_subtitle`、`core_foot`、`workload`、`error_count`、`legend`、`note_legend`、`footer`，以及 4—6 个 `branches`；每个分支填写 `side`、`category`、`title`、`rule`、`detail`，如有错题再填写 `error.number`、`error.label`、`error.mistake`、`error.fix`；无错题时填写 `check` 与 `check_fix`

```text
python scripts/render_summary_map.py examples/summary-map.json summary.svg --png summary.png
```

具体工作流程见 [SKILL.md](SKILL.md)，设计与资料检索规则见 [references](references)

## 内容边界

仓库只包含 skill 指令和生成脚本，不包含教材、历年试卷、用户作答或生成的个人学习文件；使用资料时请核对来源与授权

## 来源与修改

本仓库是 [yoli-mi/good-learning-skill](https://github.com/yoli-mi/good-learning-skill) 的修改版，在上游基础上增加了：

- `scripts/normalize_math.py` 与 `scripts/scan_math.py`：把 Markdown 里裸写的下标、上标与星号上标规范化为 LaTeX 数学模式，并提供自查
- 「源文件里的公式必须写成 LaTeX 数学模式」这条规则，以及对应的验收要求
- 按文档类型切换配色主题：知识清单、备考计划与每日课程紧凑版为黑底白字；每日课程宽松版与错题本改为白底黑字，便于打印手写作答

上游的提交历史与作者署名一并保留

## 许可证

[MIT](LICENSE)，原始版权归 yoli-mi 所有
