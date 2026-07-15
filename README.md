# Skill Optimizer

> 让 AI Agent 的 Skill 编写优化过程从「能用」变成「好用」。本项目类似 Claude Code 自带的 skill-creator ，但针对 Grok Build、Kimi Code、MiMo Code 针对性的优化了，确保在每一个适配的平台上都能发挥出最大的作用。

一套跨平台的 **Skill 设计、测试、优化工具包**。包含三个平台专用版本：

**最新更新：v1.1.0 — Prove 层**

**v1.1.0**：共享 **Prove 发版门**（来自 session-digger 工程实践）：`scripts/prove_skill.py` = 结构审计 + 活体/夹具回放 + ship_ready；Failure Pattern 库（F-SUBSTR / F-HARDCODE / F-NO-LIVE…）；`baseline_gate.py` 防回归。三平台 creator 均增加 **Step 8 Prove**，打包前必须过门。

**v1.02**：kimi-skill-creator；Description Trap；7 步评估 Pipeline 等。

| 版本 | 目录 | 平台 | 特色 |
|------|------|------|------|
| **grok-skill-creator** | `grok-skill-creator/` | Grok Build | 紧凑方法论 + 评估流水线 + Prove |
| **kimi-skill-creator** | `kimi-skill-creator/` | Kimi Code | AgentSwarm + whenToUse + Prove |
| **mimo-skill-creator** | `mimo-skill-creator/` | MiMo Code | TDD / compose + Prove |
| **shared prove** | `scripts/` + `references/` | 全平台 | audit · live · baseline_gate |

核心闭环：**Three Gates → Write → Smoke → Eval → Optimize → Prove → Package**。

---

## 项目灵感

Skill Optimizer 的灵感来源于 Claude Code 自带的 `skill-creator`。

在分别使用 Grok Build、Kimi Code 和 MiMo Code 的过程中，我们发现这些 Agent 内置的 skill 创建引导（或类似功能的 skill）水平参差不齐——优化和测试 skill 的工具相当简陋，导致一个 skill 写出来之后需要反复返工：触发不准、内容冗余、缺乏量化验证手段。

于是我决定：**不做通用指南，针对每个 Agent 的实际环境、官方文档和工具接口，分别开发专用版本。** 每个版本都用该平台的原生工具实现完整的「创建 → 测试 → 评估 → 优化」闭环，而不是写一层适配层去抹平差异。

这就是 Skill Optimizer 的定位：**不是一个 skill 教程，只有三个可以直接跑起来的 skill 工程流水线。**

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
                    → Prove 发版门（audit + live）
                    → 改进 → 下一轮
```

### Prove 发版门（v1.1，共享）

结构看着对 ≠ 行为对。打包前：

```bash
cd /path/to/skill-optimizer

# 对人：终端摘要
python3 scripts/prove_skill.py /path/to/your-skill

# 对 CI / 棘轮：JSON + 严格门
python3 scripts/prove_skill.py /path/to/your-skill --json -o /tmp/prove.json
python3 scripts/prove_skill.py /path/to/your-skill --strict

# 改动前后对比（拒绝变差）
python3 scripts/prove_skill.py /path/to/your-skill --json -o /tmp/before.json
# ... 编辑 skill ...
python3 scripts/prove_skill.py /path/to/your-skill --json -o /tmp/after.json
python3 scripts/baseline_gate.py --baseline /tmp/before.json --current /tmp/after.json
```

| 脚本 | 作用 |
|------|------|
| `scripts/skill_audit.py` | 结构 / description trap / 硬编码路径 |
| `scripts/live_replay.py` | 跑 `scripts/verify.sh` 或 pytest |
| `scripts/prove_skill.py` | 合并审计 + 活体 → `ship_ready` |
| `scripts/baseline_gate.py` | 基线棘轮 |
| `scripts/failure_patterns.py` | F-* 模式目录 |
| `references/prove-pipeline.md` | 政策说明 |
| `references/failure-patterns.md` | 模式手册 |

目标 skill 建议提供 `scripts/verify.sh`（真实检查 exit 0）或 `tests/`。无夹具时 prove 可过 audit，但会标 **F-NO-LIVE / dry_run**。

---

## v1.02 更新内容

v1.0 发布后，基于实际使用反馈和 Claude Code 版 skill-creator 的参照分析，做了大幅重构：

### 新增 Kimi Code 版本

新增 `kimi-skill-creator/`（265 行），覆盖 Kimi Code 特有的 `Agent`、`AgentSwarm`、`AskUserQuestion` 工具，以及 `arguments` 参数化、`whenToUse` 触发场景、`type: flow` 手动触发等原生机制。

### 三个版本共同吸收的改进

| 改进 | 旧版 | 新版 |
|------|------|------|
| **Description Trap** | 无 | 明确指出 description 总结 workflow 会导致模型走捷径跳过 body，附 ❌/✅ 对比 |
| **Skill 类型分类** | 无 | Discipline/Technique/Pattern/Reference 四种类型给不同写作框架 |
| **Bulletproofing 合理化表格** | 无 | Excuse → Reality 对照表，堵住「这次不一样」的借口 |
| **5 Common Failures** | 散落各处 | 集中成排障手册，可快速扫描 |
| **评估 Pipeline** | 简单测试描述 | 完整 7 步流水线（test cases → paired runs → persist → grade → aggregate → analyze → present） |
| **平台原生工具** | 部分依赖通用描述 | 深度适配各平台（Grok 的 `spawn_subagent` / Kimi 的 `AgentSwarm` / MiMo 的 `task`） |

### 行数变化

| 版本 | v1.0 | v1.02 | 变化 |
|------|------|-------|------|
| grok-skill-creator | 309 行 | 270 行 | -12.6% |
| mimo-skill-creator | 370 行 | 248 行 | -33.0% |
| kimi-skill-creator | — | 265 行 | 新增 |

更少的行数，更多的信息。压缩靠的是把教程体换成手册体、散落的建议汇成表格、重复的说明合并到流程里。

---

## 三个版本的差异

### grok-skill-creator（Grok Build）

- **270 行**，极致紧凑
- 深度适配 Grok 的 `spawn_subagent` 原生能力
- 内置 `agents/`（grader、comparator、analyzer）+ `scripts/`（aggregate_benchmark、quick_validate、eval-viewer）
- `references/schemas.md` — 完整 JSON Schema 定义
- Description Optimization 可指定模型，60/40 train/test split

### kimi-skill-creator（Kimi Code）

- **265 行**，Kimi Code 原生工具全覆盖
- `Agent`（单任务）和 `AgentSwarm`（批量并发）两种执行模式
- `arguments` 参数化：`$target`、`$mode` 在 body 中直接引用
- `whenToUse` 字段：中文友好的触发场景描述
- `type: flow` + `disableModelInvocation: true`：精细控制自动触发 vs 手动触发
- `AskUserQuestion` 结构化反馈收集

### mimo-skill-creator（MiMo Code）

- **248 行**，三个版本中最紧凑
- 深度集成 MiMo Code 的 `task` 工具（`spawn`/`run` 两种模式）
- `compose:` 生态引用（`compose:tdd`、`compose:verify`、`compose:ask`、`compose:plan`）
- 明确的批量并发控制：4-6 并发，分批执行
- **控制器负责持久化**：subagent 不写磁盘，主代理收到 `actor-notification` 后立即落盘

---

## 快速开始

输入 `/grok-skill-creator` 或 `/skill:kimi-skill-creator` 或 `/new-skill`，描述你要创建的 Skill。系统自动走完「Three Gates → Write → Test → Grade → Optimize」全流程。

**最常见的用法：**

```
/grok-skill-creator 帮我写一个自动分析股票基金的 skill
/skill:kimi-skill-creator 我想做一个小红书标题优化的 skill
/new-skill 帮我创建一个 PDF 处理的 skill
```

**不用记命令。** 说「帮我写个 skill」+ 描述场景，触发对应的 Skill Creator。

---

## 安装

### Grok Build

```
npx -y skills add taxueseek/skill-optimizer -g
```

安装后 Skill 文件在 `~/.grok/skills/` 目录下。

### Kimi Code

将 `kimi-skill-creator/` 目录复制到 `~/.kimi-code/skills/` 下即可：

```
cp -r kimi-skill-creator ~/.kimi-code/skills/
```

### MiMo Code

将 `mimo-skill-creator/` 目录复制到 MiMo Code 的 `skills/` 目录下：

```
cp -r mimo-skill-creator <mimocode-skills-dir>/
```

### 手动安装（通用）

```
git clone https://github.com/taxueseek/skill-optimizer.git
# 将对应平台的 skill 目录复制到 Agent 的 skills/ 目录下
```

---

## 更新

### 通过 `npx skills add` 安装的用户

重新运行一次即可。安装和更新用的是同一条命令：

```
npx -y skills add taxueseek/skill-optimizer -g
```

### 手动安装的用户

```
cd <skill-optimizer-dir> && git pull
```

---

## 技能表（3 个）

| 斜杠命令 | 功能 | 平台 | 版本 |
|---------|------|------|------|
| `/grok-skill-creator` | Skill 创建 + 评估优化 + Description 调优 | Grok Build | v1.02 |
| `/skill:kimi-skill-creator` | Skill 创建 + AgentSwarm 批量评估 + arguments 参数化 | Kimi Code | v1.02 |
| `/new-skill` | Skill 创建 + TDD 驱动 + compose 生态集成 | MiMo Code | v1.02 |

### grok-skill-creator 包含的脚本

| 文件 | 功能 |
|------|------|
| `scripts/quick_validate.py` | 预检：frontmatter 格式、命名规范、description 长度 |
| `scripts/aggregate_benchmark.py` | 聚合：grading.json → benchmark.json/md（mean±stddev + delta） |
| `scripts/package_skill.py` | 打包：目录 → .skill 文件（zip） |
| `eval-viewer/generate_review.py` | 审阅器：自包含 HTML 浏览器审阅页面 |
| `agents/grader.md` | 评分代理指令 |
| `agents/comparator.md` | 盲评代理指令 |
| `agents/analyzer.md` | 分析代理指令 |

### kimi-skill-creator 包含的脚本

无额外脚本。所有功能通过 Kimi Code 的 `Agent`、`AgentSwarm`、`AskUserQuestion` 工具实现。

### mimo-skill-creator 包含的脚本

无额外脚本。所有功能通过 MiMo Code 的 `task` 工具 + `bash` 执行 Python 内联脚本实现。

---

## 工作流联动

三个 Skill Creator 共享同一套闭环，但平台差异导致执行方式不同：

```
创建 SKILL.md
    → Smoke Test（2 个 subagent，with vs without）
        → 评估 Pipeline（10-20 个测试用例，with-skill vs baseline）
            → 评分 + 聚合 → Benchmark
                → 分析模式 → 改进 SKILL.md
                    → Description Optimization → 重新评估
                        → 满意 → 打包 .skill
```

**Grok Build**：`spawn_subagent` 原生并发，`scripts/` 目录预置 benchmark 聚合和打包脚本。

**Kimi Code**：`AgentSwarm` 批量并发测试，`AskUserQuestion` 收集结构化反馈，`Bash` 内联 Python 聚合 benchmark。

**MiMo Code**：`task` 工具 spawn/run 并发，4-6 并发分批执行，主代理负责持久化所有结果。

---

## 设计哲学

1. **先验证，后交付**：每个 Skill 必须经过 with-skill vs without-skill 的对比测试
2. **Token 即成本**：三个版本都控制在 300 行以内，同样的信息更少的 token
3. **平台原生优先**：不写适配层，直接用平台提供的工具
4. **可量化**：pass_rate、time、tokens 三个维度，mean ± stddev，delta 一目了然
5. **迭代有终点**：用户满意 / 反馈全正 / 进度停滞，三者满足其一即停

---

## 版本历史

| 版本 | 更新 | 日期 |
|------|------|------|
| v1.02 | 新增 kimi-skill-creator；grok/mimo 两版大幅重构（Description Trap、Skill 类型分类、Bulletproofing、评估 Pipeline、5 Common Failures） | 2026-06 |
| v1.0 | 初始发布：grok-skill-creator + mimo-skill-creator | 2026-06 |

---

## 许可证

MIT License
