# bilibili-sub-md —— Bilibili 批量字幕下载器

一键批量下载 Bilibili 视频字幕，自动识别视频链接、多 P 视频、UP 主合集与收藏夹，输出为干净 Markdown / SRT / TXT。基于 Bilibili Obsidian Clipper 插件的字幕抓取逻辑复刻。

---

## 解决什么痛点

**以前是这样的：**

- 想精读一个 B 站教程，只能开着视频反复暂停、抄字幕
- 收藏夹里存了 50 个学习视频，想批量整理字幕，只能一个个点进去复制
- UP 主的系列课程有 20 集，要一集集手动下载字幕
- AI 生成的学习笔记没有原文对照，想提取字幕做成 Obsidian 笔记
- 不同视频的字幕语言不统一，有的只有 AI 字幕，有的只有人工字幕

**现在是这样的：**

- 粘贴一个 BV 号、一个合集链接或一整页链接，回车即下载
- 自动识别 UP 主合集、频道系列、收藏夹，一键展开所有视频
- 多 P 视频自动按分 P 标题分别保存
- 输出格式可选 Markdown（Obsidian 友好）、SRT（剪辑可用）、TXT（纯文本）
- 按语言优先级智能选择字幕：中文 > 英文 > AI 字幕

**适合谁用：**

- **知识整理者 / Obsidian 用户** —— 把 B 站教程字幕归档为可搜索的 Markdown
- **内容学习者** —— 精读技术课程、语言学习、讲座内容
- **视频创作者** —— 批量获取参考视频字幕，做选题分析和脚本整理
- **AI 训练数据收集者** —— 批量获取带时间轴的字幕语料

---

## 核心功能

| 功能 | 解决什么问题 |
|------|-------------|
| **批量多链接粘贴** | 一次复制 20 个视频链接，空行结束即可批量下载 |
| **播放列表自动展开** | UP 主合集、频道系列、收藏夹链接自动提取所有视频 |
| **多 P 视频自动拆分** | 一个 BV 号含多个分 P 时，按 P 标题分别保存 |
| **智能字幕选择** | 按中文 → 英文 → AI 字幕的优先级自动选择最佳轨道 |
| **三格式输出** | Markdown（带时间戳）、SRT（剪辑可用）、TXT（纯文本） |
| **并发限速下载** | 默认 3 并发 + 1~2.5 秒随机延迟，防 B 站反爬 |
| **失败隔离** | 单个视频失败不中断整体任务，最后汇总报告 |
| **播放列表子文件夹** | 每个播放列表自动创建子文件夹，归档清晰 |

---

## 安装方法

### 环境要求

- Python 3.10+

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/decai335335-debug/bilibili-sub-md.git
cd bilibili-sub-md

# 2. 创建虚拟环境
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
```

### 修改默认输出目录（可选）

打开 `config.py`，把 `DEFAULT_OUTPUT_DIR` 改成你的 Obsidian 仓库路径：

```python
DEFAULT_OUTPUT_DIR = Path("E:/Obsidian/主仓库/11-subtitles/bilibili")
```

---

## 使用方法

### 场景一：批量粘贴链接下载（最常用）

**什么时候用**：在浏览器里打开了一堆 B 站视频，想全部下载字幕。

```bash
python main.py download -i
```

1. 不输入参数，使用交互模式
2. 逐行粘贴链接，**输入空行结束**：
   ```
   > https://www.bilibili.com/video/BV1xx411c7mD
   > https://www.bilibili.com/video/BV1yy411c7nE
   > https://space.bilibili.com/123456/channel/collectiondetail?sid=789
   >
   ```
3. 按提示确认输出目录和格式（直接回车用默认）
4. 等待下载完成，打开输出目录查看 `.md` / `.srt` / `.txt` 文件

### 场景二：命令行直接下载单个视频

```bash
python main.py download "https://www.bilibili.com/video/BV1xx411c7mD"
```

### 场景三：下载 UP 主合集

```bash
python main.py download "https://space.bilibili.com/123456/channel/collectiondetail?sid=789"
```

播放列表内所有视频的字幕会下载到以合集名称命名的子文件夹中。

### 场景四：下载多 P 视频的全部分 P（功能 B）

**什么时候用**：一个 BV 号下包含多个分 P（如课程系列），想把所有分 P 的字幕一次性下载到以视频标题命名的文件夹。

```bash
python main.py download "https://www.bilibili.com/video/BV1Ra5K61EQ4" --all-parts
```

会自动：
1. 识别该视频共有多少个分 P
2. 创建以视频标题命名的子文件夹（如 `麻省理工_如何用AI做任何事_Mit_How_To_Ai_Almost_Anything_Spring_2026/`）
3. 下载所有分 P 的字幕，文件名包含分 P 标题

**交互模式下的 A/B 选择**：

在交互模式下粘贴多 P 视频链接时，程序会询问：

```
? 视频 '【麻省理工】如何用Ai做任何事 ...'（BV1Ra5K61EQ4）共有 12 个分 P。
  [A] 只下载第 1 P（默认）
  [B] 下载全部 12 个分 P，保存到 '麻省理工_如何用AI做任何事.../' 文件夹
请选择 [A/B]:
```

输入 `B` 即可下载全部分 P。

如果只想下载某一个特定分 P，在 URL 中加上 `?p=N`：
```bash
python main.py download "https://www.bilibili.com/video/BV1Ra5K61EQ4?p=3"
```

### 场景五：指定输出格式和语言

```bash
# 输出 SRT 格式
python main.py download BV1xx411c7mD --format srt

# 优先下载英文字幕
python main.py download BV1xx411c7mD --lang en

# 指定输出目录和并发数
python main.py download BV1xx411c7mD -o ./output -w 5
```

### 场景六：带 Cookie 下载（需要登录的字幕）

**什么时候用**：视频明明有"字幕"按钮，但工具提示"暂无可用字幕"。这通常是因为该字幕需要登录才能通过 API 获取（如部分 AI 生成字幕或大会员专享字幕）。

**获取 SESSDATA 的方法**：

1. 用浏览器打开 `https://www.bilibili.com` 并登录账号
2. 按 `F12` 打开开发者工具 → 切换到 **Application / 应用** 标签
3. 左侧选择 **Cookies → https://www.bilibili.com**
4. 找到 `SESSDATA` 这一项，复制它的**值**（是一串字母和数字，不含 `SESSDATA=`）

**运行命令**：

```bash
python main.py download "https://www.bilibili.com/video/BV1dM411U7qK" --cookie "你的SESSDATA值"
```

或在交互模式下：

```bash
python main.py download --cookie "你的SESSDATA值" -i
```

如果你更喜欢先设置环境变量再进入交互模式（避免每次粘贴很长的 SESSDATA）：

**Windows PowerShell:**
```powershell
$env:BILI_COOKIE="你的SESSDATA值"
python main.py download -i
```

**Windows CMD:**
```cmd
set BILI_COOKIE=你的SESSDATA值
python main.py download -i
```

**macOS / Linux:**
```bash
export BILI_COOKIE="你的SESSDATA值"
python main.py download -i
```

> ⚠️ **安全提示**：SESSDATA 相当于你的登录凭证，不要把它分享到公开仓库或发给他人。建议只在本地命令行中使用。

### 支持的 URL 格式

| URL 类型 | 示例 | 说明 |
|---------|------|------|
| 单个视频 | `https://www.bilibili.com/video/BV1xx411c7mD` | 支持自动识别多 P |
| 分 P 视频 | `https://www.bilibili.com/video/BV1xx411c7mD?p=3` | 只下载指定 P |
| UP 主合集 | `https://space.bilibili.com/123456/channel/collectiondetail?sid=789` | 自动展开所有视频 |
| 频道系列 | `https://space.bilibili.com/123456/channel/seriesdetail?sid=789` | 自动展开所有视频 |
| 收藏夹 | `https://www.bilibili.com/list/ml1234567` | 自动展开所有视频 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| CLI 框架 | Typer |
| 终端 UI | Rich（进度条、表格） |
| 网络请求 | requests |
| 数据校验 | Pydantic v2 |
| 异步并发 | asyncio + Semaphore |

---

## 文件结构

```
bilibili-sub-md/
├── main.py              # CLI 入口（typer），交互逻辑和批量调度
├── config.py            # 全局配置：输出目录、API 地址、并发、重试
├── models.py            # Pydantic 数据模型：VideoMeta、SubtitleResult、DownloadResult
├── requirements.txt     # Python 依赖
├── README.md            # 用户文档
├── DEV_LOG.md           # 开发日志
└── core/                # 核心引擎
    ├── __init__.py
    ├── extractor.py     # Bilibili URL 解析：BV 号、分 P、播放列表识别
    ├── metadata.py      # Bilibili API 获取元数据和字幕列表
    ├── downloader.py    # 字幕下载主逻辑：语言选择、文件保存
    └── formatter.py     # 字幕格式转换：Markdown / SRT / TXT
```

---

## 常见问题

**Q: 运行时报 "无法获取视频信息"？**

A: 可能是 B 站 API 限流或 BV 号无效。检查网络连接，稍等几分钟后重试。如果频繁请求，建议调低并发数 `-w 1`。

**Q: 为什么有些视频显示"暂无可用字幕"？**

A: 本工具仅支持获取有字幕轨的视频。B 站视频必须满足以下之一：UP 主上传了外挂字幕、B 站提供了 AI 自动生成字幕、视频本身带了 CC 字幕。你可以在播放器里查看是否有「字幕」按钮。

**Q: 如何只下载某个分 P 的字幕？**

A: 在 URL 中加上 `?p=N` 参数，例如：
```bash
python main.py download "https://www.bilibili.com/video/BV1xx411c7mD?p=3"
```

**Q: 下载的 Markdown 文件在 Obsidian 里怎么查看？**

A: 输出文件采用标准 Markdown 语法，包含 YAML frontmatter（标题、BV 号、字幕语言、是否为 AI 字幕）。直接用 Obsidian 打开即可，时间戳用反引号包裹，方便复制和搜索。

**Q: 能下载 4K 视频的弹幕吗？**

A: 不能。本工具专注于字幕（subtitle），不支持弹幕（danmaku）。

**Q: 可以下载会员专享视频的字幕吗？**

A: 不能。B 站 API 对会员视频有限制，未登录状态下无法获取。

---

## 未来开发路线图 (Roadmap)

**当前状态：v0.1.0 —— 核心批量下载流程可用，支持单个视频、多 P、合集、收藏夹。**

### 近期（v0.2.0）

- **Cookie 支持** —— 允许用户配置 SESSDATA，下载需要登录才能查看的字幕和稍后再看列表
- **CSV 报告导出** —— 批量下载后生成 `_download_report.csv`，方便筛选失败项重试
- **断点续传** —— 记录已下载的 BV 号，重复运行时跳过已成功的任务

> 为什么优先做：批量下载几百个视频时，网络波动导致部分失败是常态，断点续传和报告能大幅减少重复工作。

### 中期（v0.3.x ~ v0.4.x）

- **更多播放列表类型** —— 支持稍后再看、搜索结果页、UP 主全部投稿
- **自动翻译字幕合并** —— 同时下载中英文字幕，生成双语对照 Markdown
- **AI 字幕质量标记** —— 在文件名或 frontmatter 中标记 `is_ai: true`，提醒用户校对
- **GUI 桌面版** —— 基于 PyQt 提供可视化界面，方便非程序员使用

> 为什么现在做：中期目标是把"从 B 站批量获取字幕"这个单点能力扩展成"多语言字幕整理工作站"。

### 长期愿景

- **方向**：成为中文互联网视频内容学习者的标准工具，覆盖 B 站 + 其他主流视频平台
- **生态位**：不做视频下载器，而是专注"字幕获取与知识整理"这一垂直场景
- **社区化**：开放字幕解析规则，让社区可以适配新的平台或 API 变化

### 如何参与

- **有需求？** 提交 [Issue](../../issues) 并打上 `enhancement` 标签
- **想贡献代码？** 查看 [good first issue](../../issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
- **有播放列表适配经验？** 欢迎提交 PR 扩展 `core/extractor.py` 的识别规则

---

## 更新日志

### v0.1.0（当前版本）

- Bilibili URL 解析：BV 号、分 P、合集、系列、收藏夹
- Bilibili API 获取视频元数据和字幕轨道列表
- 自动选择最佳字幕语言（中文 > 英文 > AI 字幕）
- 输出 Markdown / SRT / TXT 三种格式
- 多 P 视频自动按分 P 拆分保存
- 播放列表自动展开并创建子文件夹
- 批量交互式链接输入
- 并发限速下载与失败隔离
