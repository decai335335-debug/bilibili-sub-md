# bilibili-sub-md 批量字幕下载工具开发 —— 任务总结

**任务类型**：工具链开发（Python CLI + 网络爬虫 + 跨平台兼容性）  
**执行时间**：2025-06-08  
**执行者**：Kimi Code CLI（DDC1018 用户协作）  
**任务状态**：已完成，核心功能可用，已推送到 GitHub  
**预估耗时**：2 小时  
**实际耗时**：约 4 小时（因多轮兼容性问题调试）

---

## 一、任务概述

### 1.1 背景与动机

用户在日常学习中大量使用 Bilibili 学习技术课程和讲座，希望像整理 YouTube 字幕一样，把 B 站视频字幕批量下载到 Obsidian 笔记库中。已有 Chrome 插件 [Bilibili Obsidian Clipper](https://github.com/haixiong1997/Bilibili-Obsidian-Clipper) 支持单个视频抓取，但缺乏批量能力。用户需要一个命令行工具，支持混合粘贴视频链接和播放列表链接，自动下载字幕并归档。

### 1.2 任务目标

1. 创建一个 Python CLI 工具 `bilibili-sub-md`
2. 支持单个视频、多 P 视频、UP 主合集、频道系列、收藏夹的批量处理
3. 输出 Markdown / SRT / TXT 三种格式
4. 自动识别播放列表并创建子文件夹
5. 智能选择字幕语言（中文 > 英文 > AI 字幕）
6. 解决"有字幕按钮但 API 返回空"的登录态问题
7. 推送到 GitHub 仓库

### 1.3 约束条件

- Python 3.10+，Windows PowerShell 为主要运行环境
- 基于 Bilibili 公开 API（复刻 BOC 插件调用链）
- 必须兼容 Windows GBK 控制台输出
- 必须处理 B 站 API 的登录态差异
- 用户对命令行和 PowerShell 不太熟悉，需要极低使用门槛

---

## 二、成果交付

### 2.1 核心成果

| 成果项 | 状态 | 说明 |
|--------|------|------|
| 项目骨架搭建 | 完成 | main.py + config.py + models.py + core/ 四模块 |
| URL 解析器 | 完成 | 支持 BV 号、分 P、合集、系列、收藏夹识别 |
| Bilibili API 封装 | 完成 | 视频元数据、字幕轨道列表、字幕 JSON 下载 |
| 格式转换器 | 完成 | Markdown（带 YAML frontmatter）、SRT、TXT |
| 并发下载调度 | 完成 | ThreadPoolExecutor + 随机延迟 |
| Cookie / SESSDATA 支持 | 完成 | 支持 --cookie 参数和 BILI_COOKIE 环境变量 |
| 交互模式优化 | 完成 | 无参数时默认进入交互模式，直接输入链接 |
| run.ps1 启动脚本 | 完成 | PowerShell 脚本，自动提示输入 SESSDATA |
| GitHub 仓库推送 | 完成 | https://github.com/decai335335-debug/bilibili-sub-md |
| README + DEV_LOG | 完成 | 按通用模板完整撰写 |

### 2.2 数据概览

| 指标 | 数值 |
|------|------|
| GitHub 提交次数 | 7 次 |
| 核心 Python 文件 | 7 个 |
| 修复的 bug 数量 | 5 个 |
| 测试验证的视频 | 3 个（BV1dM411U7qK、BV1KmGv63EAa、BV1agH8zCE1V） |
| 支持的播放列表类型 | 4 种（合集、系列、收藏夹、稍后再看规划中） |
| 输出格式 | 3 种（md / srt / txt） |

---

## 三、完整迭代/踩坑记录

### 迭代 1：初始项目创建

- **尝试**：一次性创建完整项目结构，参考 yt-sub-md 的架构
- **结果**：成功，代码结构清晰，语法检查通过，GitHub 仓库创建并推送
- **教训**：复用已验证的架构模式能显著降低设计成本

### 迭代 2：VideoPage 导入缺失（运行时 NameError）

- **问题**：用户首次运行时报 `NameError: name 'VideoPage' is not defined`
- **根因**：`core/downloader.py` 中 `_get_page_for_url` 函数的类型注解使用了 `VideoPage`，但文件顶部没有从 `models` 导入
- **修复**：补充 `from models import VideoPage`
- **教训**：类型注解也会在运行时被解析，不能只关注运行时使用的类

### 迭代 3：asyncio 与 PowerShell / IDE 的事件循环冲突

- **问题**：在 PowerShell 中运行 `python main.py` 时，`asyncio.run()` 报错：`asyncio.run() cannot be called from a running event loop`
- **根因**：某些运行环境（如通过 VS Code 启动的 PowerShell）已经存在一个事件循环，`asyncio.run()` 不允许嵌套调用
- **尝试 1**：检测 `asyncio.get_running_loop()` 并用 `run_until_complete()` 回退
- **尝试 2**：引入 `nest_asyncio` 补丁
- **最终修复**：彻底弃用 asyncio，改用 `concurrent.futures.ThreadPoolExecutor`。
  - 对于 IO 密集型 HTTP 请求，线程池完全够用
  - 消除了事件循环兼容性问题
  - 代码更简单，调试更容易
- **教训**：不要为了技术炫技而选择 asyncio；对于同步 IO 库（requests），线程池往往是更稳妥的选择

### 迭代 4：默认进入交互模式

- **问题**：用户运行 `python main.py` 后直接退出，提示"请提供 URL 或使用 --interactive"
- **根因**：原设计假设用户会主动加 `-i` 参数，但用户期望"双击运行就能输入"
- **修复**：当没有 URL 参数时，默认调用 `_prompt_links()` 进入交互模式
- **教训**：命令行工具的默认行为应该符合最小 Surprise 原则，用户最不费力的操作路径应该是最佳路径

### 迭代 5：播放列表 / 字幕需要登录 Cookie

- **问题**：用户确认视频有"字幕"按钮，但工具返回"该视频暂无可用字幕"
- **根因**：Bilibili 的部分 AI 生成字幕和大会员内容，未登录用户调用 API 时返回空字幕列表
- **验证**：用用户的 SESSDATA 测试，未登录时 `Tracks count: 0`，登录后 `Tracks count: 1`（ai-zh）
- **修复**：
  - 添加 `--cookie` 命令行参数
  - 添加 `BILI_COOKIE` / `BILIBILI_SESSDATA` 环境变量支持
  - 在 `core/metadata.py` 中实现 `set_cookie()`，让后续所有 API 请求自动带 Cookie
- **教训**：爬虫工具必须把"登录态"作为一等公民设计，不能假设公开 API 能返回完整数据

### 迭代 6：PowerShell 脚本编码问题

- **问题**：`run.ps1` 脚本在 PowerShell 中运行时报"字符串缺少终止符"
- **根因**：
  1. 文件以 UTF-8 无 BOM 编码保存，PowerShell 默认用 ANSI/GBK 解析中文，导致引号匹配失败
  2. `$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")` 参数格式不被支持
- **修复**：
  1. 用 Python 将文件重写为 `utf-8-sig`（带 BOM）
  2. `ReadKey` 改为 `Read-Host`
- **教训**：Windows PowerShell 对 UTF-8 无 BOM 脚本的支持很差，中文脚本必须保存为 UTF-8 with BOM

### 迭代 7：Cookie 的 latin-1 编码错误

- **问题**：用户设置 Cookie 后下载失败：`latin-1 codec can't encode characters in position 50-53`
- **根因**：用户通过 PowerShell `Read-Host` 复制粘贴 SESSDATA 时，可能带入了零宽空格、全角空格或其他不可见 Unicode 字符。requests 库在构造 HTTP header 时要求所有 header 值必须是 latin-1 编码（0-255），Unicode 字符会触发编码错误
- **修复**：
  - `set_cookie()` 增加严格清理：strip、移除换行制表符、剥离 `SESSDATA=` 前缀、过滤非安全字符
  - `build_headers()` 中对 cookie 值再做一层 latin-1 安全检查
- **教训**：永远不要信任用户从剪贴板粘贴的字符串，必须做防御性清洗

---

## 四、偏差分析

### 4.1 时间偏差

| 阶段 | 预估 | 实际 | 偏差 | 原因 |
|------|------|------|------|------|
| 初始项目开发 | 1h | 1.5h | +50% | 需要完整复刻 BOC 插件 API 逻辑 |
| 兼容性调试 | 0.5h | 2h | +300% | PowerShell + Windows 编码 + asyncio 三重问题 |
| Cookie 与登录态 | 0.5h | 0.5h | 0% | 一次性解决，方案清晰 |

### 4.2 关键偏差详解

**最大偏差：兼容性调试耗时远超预期**

- **Why 1**：为什么兼容性调试花了 2 小时？
  - 因为问题不在 Python 代码本身，而在 Python 与 Windows PowerShell 的交互层
- **Why 2**：为什么没有预见到 PowerShell 的问题？
  - 开发环境是 Git Bash，测试时用的是 bash 管道输入，没有覆盖用户真实的 PowerShell 交互场景
- **Why 3**：为什么测试场景不完整？
  - 早期假设"能跑通就行"，没有从用户实际使用路径出发设计测试用例
- **系统级根因**：测试策略缺乏"端到端用户旅程"覆盖，过度依赖开发者的理想环境

---

## 五、复盘框架（混合模式：KPT + 5Why）

### 5.1 Keep（保持）

1. **架构复用**：参考 yt-sub-md 的模块化设计（extractor / metadata / downloader / formatter），新项目快速落地
2. **API 复刻**：基于已验证的 Bilibili Obsidian Clipper 插件 API 调用链，避免从零踩坑
3. **快速迭代**：小步快跑，每修复一个问题立即提交并推送，用户能实时看到进展

### 5.2 Problem（问题）

1. **未做跨平台测试**：开发在 Git Bash，用户使用 PowerShell，编码和事件循环问题直到用户运行才暴露
2. **高估 asyncio 的普适性**：在 Windows / PowerShell 环境下 asyncio 事件循环管理比预期复杂
3. **对用户输入的信任**：SESSDATA 复制粘贴时带入不可见字符，没有第一时间做防御性清洗
4. **Cookie 支持设计滞后**：应该在初始设计就把登录态作为一等公民，而不是事后补丁

### 5.3 Try（尝试）

1. 未来任何面向 Windows 用户的 Python 脚本，首版就加入 UTF-8 with BOM 的 `.ps1` 启动脚本
2. 任何涉及 HTTP header 的用户输入，必须做 ASCII / latin-1 安全过滤
3. 涉及剪贴板输入的场景，默认做不可见字符清理
4. 爬虫类工具首版就必须考虑登录态设计（cookie 参数 + 环境变量 + 使用说明）

### 5.4 严重问题深度分析

**问题：同样的"编码/兼容性"问题反复出现**

- 迭代 3：asyncio 与 PowerShell 事件循环冲突
- 迭代 6：PowerShell 脚本 UTF-8 编码问题
- 迭代 7：Cookie 中不可见字符导致 latin-1 编码错误

**5Why 根因分析**：

- Why 1：为什么反复出现编码/兼容性问题？
  - 因为开发环境和用户环境不一致（Git Bash vs PowerShell，UTF-8 vs GBK）
- Why 2：为什么没有在开发阶段覆盖用户环境？
  - 因为测试策略只验证了"功能正确"，没有验证"用户路径正确"
- Why 3：为什么用户路径缺失？
  - 因为没有把"用户怎么打开程序、怎么粘贴、怎么输入"纳入验收标准
- 系统级根因：**验收标准只关注代码行为，不关注人机交互的完整链路**

**责任**：开发侧。应该在首版就定义"用户第一次双击运行能成功"作为验收条件。

---

## 六、经验沉淀与复用指南

### 6.1 核心经验清单

| 问题场景 | 具体表现 | 正确处理方式 | 错误处理方式（反模式） | 来源 |
|---------|---------|-------------|---------------------|------|
| Windows 中文 PowerShell 脚本 | 字符串缺少终止符、乱码 | 保存为 UTF-8 with BOM | 保存为 UTF-8 无 BOM | 迭代 6 |
| Python CLI 在 PowerShell 中运行 | asyncio.run 报事件循环冲突 | 改用 ThreadPoolExecutor | 强行用 nest_asyncio 或 asyncio 复杂化 | 迭代 3 |
| 用户从剪贴板粘贴长字符串 | HTTP header 报 latin-1 编码错误 | strip + 过滤非安全字符 | 直接原样使用 | 迭代 7 |
| 视频网站爬虫 | 有内容但 API 返回空 | 立即设计 Cookie / 登录态支持 | 假设公开 API 返回完整数据 | 迭代 5 |
| 命令行工具默认行为 | 用户忘记加参数 | 无参数时进入交互模式 | 直接退出并报错 | 迭代 4 |

### 6.2 可复用的方法论/原则

**原则 1：用户路径即验收标准**

- 定义：一个工具不仅要"功能正确"，还要"用户第一次按直觉操作就能成功"
- 适用场景：任何面向非技术用户的 CLI / 脚本工具
- 本次验证：迭代 4（默认交互模式）和迭代 6（run.ps1 脚本）都验证了这一点

**原则 2：防御性输入清洗**

- 定义：任何来自剪贴板、命令行、环境变量的外部输入，都必须经过清洗才能进入网络请求或文件系统
- 适用场景：爬虫、API 客户端、文件重命名工具
- 本次验证：迭代 7 的 Cookie 清洗

**原则 3：同步 IO 优先线程池**

- 定义：当依赖库本身是同步的（如 requests），不要为了 async 而 async，ThreadPoolExecutor 更简单可靠
- 适用场景：Python 网络爬虫、批量下载工具
- 本次验证：迭代 3 从 asyncio 迁移到 ThreadPoolExecutor 后所有兼容性问题消失

### 6.3 反模式清单

| 反模式 | 为什么错误 | 正确替代 | 本次任务中的代价 |
|--------|-----------|---------|----------------|
| UTF-8 无 BOM 的 PowerShell 脚本 | PowerShell 默认用 ANSI/GBK 解析，中文引号匹配失败 | UTF-8 with BOM | 迭代 6 额外 30 分钟调试 |
| asyncio.run() 不加环境检测 | 某些环境已有事件循环，会报冲突 | ThreadPoolExecutor 或检测 loop | 迭代 3 额外 40 分钟调试 |
| 直接信任剪贴板输入 | 可能带入零宽字符、全角空格 | strip + 字符集过滤 | 迭代 7 额外 20 分钟调试 |
| 爬虫工具首版不考虑登录态 | 大量内容对未登录用户隐藏 | 首版就支持 cookie 参数 | 迭代 5 导致返工，需要修改多处 |

### 6.4 工具/技巧速查

| 场景 | 工具/命令 | 作用 | 备注 |
|------|----------|------|------|
| Python 文件转 UTF-8 BOM | `open(f, 'w', encoding='utf-8-sig')` | 让 PowerShell 正确解析中文 | 读取时无需特殊处理 |
| 检测字符串是否全 ASCII | `all(ord(c) < 128 for c in s)` | 快速检查用户输入安全性 | 适用于 header、文件名等 |
| PowerShell 设置临时环境变量 | `$env:NAME=value"` | 当前会话有效 | 关闭窗口后失效 |
| 检查 cookie 清理效果 | `print([ord(c) for c in cookie])` | 发现异常 Unicode 字符 | 零宽字符 ord 值通常在 8203-8207 |
| 批量下载限速 | `time.sleep(random.uniform(1.0, 2.5))` + Semaphore | 防 API 限流 | 根据目标网站调整延迟 |
| 快速查看文件编码 | `file filename` (Git Bash) | 确认是否为 UTF-8 with BOM | Windows 下可用 WSL/Git Bash |

---

## 七、后续行动（SMART）

| 行动项 | 具体描述 | 衡量标准 | 截止时间 | 负责人 |
|--------|---------|---------|---------|--------|
| 验证 run.ps1 在用户环境稳定运行 | 用户在纯 PowerShell 中运行 3 次以上无报错 | 连续 3 次成功下载 | 2025-06-09 | 用户 |
| 补充单元测试 | 为 extractor、metadata、downloader 添加 pytest 覆盖 | 核心函数测试覆盖率 > 70% | 2025-06-15 | 开发者 |
| 支持更多播放列表类型 | 稍后再看、UP 主全部投稿、搜索结果页 | 新增 2 种以上播放列表识别 | 2025-06-20 | 开发者 |
| 双语字幕合并 | 同时下载中英文字幕并生成对照 Markdown | 输出文件包含双语段落 | 2025-06-25 | 开发者 |
| 更新 README 使用视频/截图 | 为 Cookie 获取流程添加截图指引 | README 中新增 3 张步骤截图 | 2025-06-12 | 开发者 |

---

## 八、设计原理/核心决策摘要

### 决策 1：为什么复刻 Bilibili Obsidian Clipper 的 API 逻辑？

- **选项 A**：从头研究 B 站 API
- **选项 B**：使用 yt-dlp
- **选项 C**：复刻 BOC 插件调用链 ✅
- **理由**：BOC 插件已经验证稳定，有完整的字幕选择和时长校验逻辑，复刻成本最低，风险最小。

### 决策 2：为什么用 ThreadPoolExecutor 而不是 asyncio？

- **选项 A**：asyncio + asyncio.to_thread
- **选项 B**：ThreadPoolExecutor ✅
- **理由**：依赖库 requests 是同步的，asyncio 的收益有限，而 PowerShell / Windows 环境下事件循环管理复杂。ThreadPoolExecutor 更简单、兼容、可调试。

### 决策 3：为什么默认进入交互模式？

- **理由**：用户最不费力的操作路径就是"双击运行 → 粘贴链接 → 回车"。命令行工具应该降低门槛，而不是要求用户记住参数。

### 决策 4：为什么 Cookie 支持同时提供参数、环境变量、交互式脚本三种入口？

- **理由**：不同用户有不同的使用习惯。高级用户喜欢用命令行参数，日常用户喜欢用双击脚本，自动化场景喜欢用环境变量。三者并存覆盖所有场景。

---

## 九、附录

### 9.1 技术栈/环境

- Python 3.11.9
- requests 2.34.2
- typer 0.9+
- rich 13.0+
- pydantic 2.0+
- Windows PowerShell + Git Bash 混合开发环境

### 9.2 文件位置

```
E:\git项目\Codex\bilibili-sub-md\
├── main.py              # CLI 入口
├── config.py            # 全局配置 + build_headers
├── models.py            # Pydantic 数据模型
├── run.ps1              # PowerShell 启动脚本
├── requirements.txt     # 依赖
├── README.md            # 用户文档
├── DEV_LOG.md           # 开发日志
└── core/
    ├── extractor.py     # URL 解析
    ├── metadata.py      # Bilibili API + Cookie 管理
    ├── downloader.py    # 字幕下载与保存
    └── formatter.py     # Markdown / SRT / TXT 转换
```

GitHub 仓库：`https://github.com/decai335335-debug/bilibili-sub-md`

### 9.3 已知限制

1. **稍后再看未支持**：需要额外处理登录态和专用 API
2. **部分会员视频**：即使带 Cookie，大会员专属内容仍可能受限
3. **极长播放列表**：B 站 API 分页拉取，目前没有断点续传
4. **Windows 控制台中文乱码**：不影响功能，仅影响显示

### 9.4 完整踩坑记录表

| # | 问题 | 根因 | 修复 | 耗时 |
|---|------|------|------|------|
| 1 | VideoPage NameError | 缺少导入 | 补充 import | 5 min |
| 2 | asyncio 事件循环冲突 | PowerShell 已有 loop | 改用 ThreadPoolExecutor | 40 min |
| 3 | 无参数直接退出 | 默认行为不友好 | 默认进入交互模式 | 10 min |
| 4 | 有字幕但 API 为空 | 未登录 | 添加 Cookie 支持 | 30 min |
| 5 | run.ps1 编码错误 | UTF-8 无 BOM | 改为 UTF-8 with BOM | 30 min |
| 6 | Cookie latin-1 错误 | 剪贴板带入不可见字符 | 防御性清洗 | 20 min |

---

## 质量红线自检

- [x] 诚实记录失败：包含 6 次失败/返工记录
- [x] 具体可量化：提交次数、文件数、测试视频数、耗时均有数据
- [x] 迭代记录完整：每次尝试 → 失败原因 → 最终修复
- [x] 根因到系统层面：从"PowerShell 报错"追到"测试策略缺乏用户路径覆盖"
- [x] SMART 后续行动：5 项行动均有具体描述、衡量标准和截止时间
- [x] 经验沉淀可复用：6.1-6.4 模块完整，每个教训均上升到通用经验
