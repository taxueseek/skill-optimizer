# Skill Optimizer

> 让 AI Agent 的 Skill 从「能用」变成「好用」。

一套跨平台的 **Skill 设计、测试、优化工具包**。包含三个平台专用版本：

| 版本 | 目录 | 行数 | 平台 | 特色 |
|------|------|------|------|------|
| **grok-skill-creator** | `grok-skill-creator/` | 270 行 | Grok Build | 紧凑方法论 + 评估流水线 + Description Trap |
| **kimi-skill-creator** | `kimi-skill-creator/` | 265 行 | Kimi Code | AgentSwarm 批量并发 + arguments 参数化 + whenToUse |
| **mimo-skill-creator** | `mimo-skill-creator/` | 248 行 | MiMo Code | TDD 驱动 + compose 生态集成 + 合理化表格 |

三个版本共享同一套核心方法论（Three Gates → Capture Intent → Write → Test → Grade → Optimize），但深度适配各自平台的工具链和运行模型。

---

## 项目灵感

Skill Optimizer 的灵感来源于 Claude Code 自带的 `skill-creator`。

在分别使用 Grok Build、Kimi Code 和 MiMo Code 的过程中，我们发现这些 Agent 内置的 skill 创建引导（或类似功能的 skill）水平参差不齐——优化和测试 skill 的工具相当简陋，导致一个 skill 写出来之后需要反复返工：触发不准、内容冗余、缺乏量化验证手段。

于是我们决定：**不做通用指南，针对每个 Agent 的实际环境、官方文档和工具接口，分别开发专用版本。** 每个版本都用该平台的原生工具实现完整的「创建 → 测试 → 评估 → 优化」闭环，而不是写一层适配层去抹平差异。

这就是 Skill Optimizer 的定位：**不是又一个 skill 教程，而是三个可以直接跑起来的 skill 工程流水线。**

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
- Description Optimization 指定 `LongCat-2.0-Preview` 模型，60/40 train/test split

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

### Grok Build

```
将 grok-skill-creator/ 目录复制到 ~/.grok/skills/ 下即可使用。
输入 /grok-skill-creator 触发。
```

### Kimi Code

```
将 kimi-skill-creator/ 目录复制到 ~/.kimi-code/skills/ 下即可使用。
输入 /skill:kimi-skill-creator 触发。
```

### MiMo Code

```
将 mimo-skill-creator/ 目录复制到 MiMo Code 的 skills/ 目录下即可使用。
输入 /new-skill 触发。
```

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
