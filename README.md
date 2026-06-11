# Skill Optimizer

> 让 AI Agent 的 Skill 从「能用」变成「好用」。

一套跨平台的 **Skill 设计、测试、优化工具包**。包含两个平台专用版本：

| 版本 | 目录 | 行数 | 平台 | 特色 |
|------|------|------|------|------|
| **grok-skill-creator** | `grok-skill-creator/` | 309 行 | Grok Build | 紧凑方法论 + 7 个 Python 脚本 + eval-viewer |
| **mimo-skill-creator** | `mimo-skill-creator/` | 370 行 | MiMo Code | TDD 驱动 + actor 工具集成 + 批量并发控制 |

两个版本共享同一套核心方法论（Three Gates → Capture Intent → Write → Test → Grade → Optimize），但深度适配各自平台的工具链和运行模型。

---

## 解决什么问题

写一个 Skill 容易，写一个**好的**Skill 难：

- **触发不准**：description 写不好，该用的时候没用，不该用的时候误触
- **内容冗余**：SKILL.md 塞了太多 Agent 已经知道的常识，浪费 token
- **缺乏验证**：写完不知道到底有没有用，全靠感觉
- **迭代低效**：改完不知道比上一版好还是差

Skill Optimizer 把 Skill 设计变成**可测试、可量化、可迭代**的工程流程。

---

## 核心方法论

```
Three Gates（该不该写）
    → Capture Intent（要做什么）
        → Write SKILL.md（怎么写）
            → Test & Grade（测一下）
                → Optimize Description（触发更准）
                    → Iterate（循环到满意）
```

### Three Gates — 该不该写

每个 Skill 开始前过三关，任一为否就停：

1. **没有这个 Skill，结果会更差吗？** 如果 Agent 本身就能搞定，没必要加 Skill
2. **用户会用超过五次吗？** 一次性自动化不如直接写脚本
3. **Agent 本身就会吗？** 别给 Agent 解释它已经知道的事

### 写完后 — 怎么验证

```
创建测试用例（10-20 个，7:2:1 比例）
    → 并行跑 with-skill + baseline
        → 评分（grading.json）
            → 聚合对比（benchmark.json）
                → 分析模式（analyzer）
                    → 改进 → 下一轮
```

---

## 两个版本的差异

### grok-skill-creator（Grok Build）

- **309 行**，极致紧凑，同样的方法论用更少的 token 传达
- 7 个 Python 脚本：`quick_validate.py`（预检）、`aggregate_benchmark.py`（聚合）、`package_skill.py`（打包）、`generate_report.py`（报告）、`utils.py`（工具函数）
- `eval-viewer/` — 自包含 HTML 浏览器审阅页面，零依赖
- `agents/` — grader、comparator、analyzer 三个子代理指令
- `references/schemas.md` — 完整 JSON Schema 定义
- 描述优化依赖 Grok 原生 `spawn_subagent`，无需额外脚本

### mimo-skill-creator（MiMo Code）

- **370 行**，TDD 驱动——「没看过 Agent 失败，就不知道 Skill 教的对不对」
- 深度集成 MiMo Code 的 `actor` 工具（`spawn`/`run` 两种模式）
- 明确的**批量并发控制**：4-6 并发，分批执行，不一次性全部发射
- **控制器负责持久化**：subagent 不写磁盘，主代理收到 `actor-notification` 后立即落盘
- 12 条 Never + 8 条 Always 的 Red Flags 清单
- 7 步创建流程（含 Validate + Quick Smoke Test）

---

## 快速开始

### Grok Build

```
将 grok-skill-creator/ 目录复制到 ~/.grok/skills/ 下即可使用。
输入 /grok-skill-creator 触发。
```

### MiMo Code

```
将 mimo-skill-creator/ 目录复制到 MiMo Code 的 skills/ 目录下即可使用。
输入 /new-skill 触发。
```

---

## 技能表

### grok-skill-creator 包含的脚本

| 文件 | 功能 |
|------|------|
| `scripts/quick_validate.py` | 预检：frontmatter 格式、命名规范、description 长度 |
| `scripts/aggregate_benchmark.py` | 聚合：grading.json → benchmark.json/md（mean±stddev + delta） |
| `scripts/package_skill.py` | 打包：目录 → .skill 文件（zip） |
| `scripts/generate_report.py` | 报告：description 优化迭代的 HTML 可视化 |
| `scripts/utils.py` | 工具：parse_skill_md() 共享解析器 |
| `eval-viewer/generate_review.py` | 审阅器：自包含 HTML 浏览器审阅页面 |
| `agents/grader.md` | 评分代理指令 |
| `agents/comparator.md` | 盲评代理指令 |
| `agents/analyzer.md` | 分析代理指令 |

### mimo-skill-creator 包含的脚本

无额外脚本。所有功能通过 MiMo Code 的 `actor` 工具 + `bash` 执行 Python 内联脚本实现。

---

## 设计哲学

1. **先验证，后交付**：每个 Skill 必须经过 with-skill vs without-skill 的对比测试
2. **Token 即成本**：Grok 版 309 行 vs 行业平均 500+ 行，同样的信息更少的 token
3. **平台原生优先**：不写适配层，直接用平台提供的工具（`spawn_subagent` / `actor`）
4. **可量化**：pass_rate、time、tokens 三个维度，mean ± stddev，delta 一目了然
5. **迭代有终点**：用户满意 / 反馈全正 / 进度停滞，三者满足其一即停

---

## 版本历史

| 版本 | 更新 | 日期 |
|------|------|------|
| v1.0 | 初始发布：grok-skill-creator + mimo-skill-creator | 2026-06 |

---

## 许可证

MIT License
