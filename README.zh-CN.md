# narrate

**一行命令，从 git 历史生成发布说明。**

```
pip install changelog-narrate
narrate ohmyzsh/ohmyzsh --from v1.0 --to v2.0
```

`narrate` 从 GitHub 获取你的 commits 和 issues，分析变更内容，生成结构化的 markdown 发布说明——支持纯模板模式（无需 API key）和 AI 模式。零外部依赖，仅用 Python 标准库。

## 快速开始

```bash
# 模板模式 —— 不需要任何 API key
narrate ohmyzsh/ohmyzsh --from HEAD~10 --to HEAD

# 选择模板风格
narrate vercel/next.js --from v14.0 --to v15.0 --template technical

# AI 模式 —— 更丰富的描述
export DEEPSEEK_API_KEY=sk-xxx
narrate facebook/react --from HEAD~20 --to HEAD --template community

# 使用你自己的模型（OpenAI、Ollama，任何兼容 OpenAI 的 API）
export AI_API_KEY=sk-xxx
narrate facebook/react --from HEAD~10 --to HEAD \
  --ai-model gpt-4o \
  --ai-endpoint https://api.openai.com/v1/chat/completions

# 本地 Ollama（无需 API key！）
narrate facebook/react --from HEAD~10 --to HEAD \
  --ai-model llama3 \
  --ai-endpoint http://localhost:11434/v1/chat/completions

# 把原始数据喂给你的编码工具的 AI
#（opencode、Cursor、Claude Code、Codex、Workbuddy 等）
narrate ohmyzsh/ohmyzsh --from HEAD~4 --to HEAD --json-only
```

## 三种使用方式

| 模式 | 需要 API key？ | 原理 |
|------|---------------|------|
| **模板**（默认） | 不需要 | 基于规则的 commit 分类 + markdown 格式化 |
| **AI 模式**（终端） | 需要 `AI_API_KEY` 或 `DEEPSEEK_API_KEY` | 把数据发给兼容 OpenAI 的模型，生成更高质量的文案 |
| **编码工具模式**（--json-only） | 不需要 | 输出原始 JSON → 工具自带的 AI 写 changelog |

### 模板模式（零配置）

开箱即用。自动分类 commits（新功能、修复、破坏性变更），突出社区 issues，从 open issues 生成 roadmap。

```bash
narrate ohmyzsh/ohmyzsh --from HEAD~4 --to HEAD
narrate facebook/react --from v18.0 --to v19.0 --template technical
```

### AI 模式（自带模型）

Narrate 支持任何兼容 OpenAI 的聊天 API。设置 `AI_API_KEY`（或兼容旧版的 `DEEPSEEK_API_KEY`），可选配置模型和 endpoint。

```bash
# DeepSeek（默认）
export DEEPSEEK_API_KEY=sk-xxx
narrate facebook/react --from HEAD~10 --to HEAD

# OpenAI
export AI_API_KEY=sk-xxx
narrate facebook/react --from HEAD~10 --to HEAD \
  --ai-model gpt-4o \
  --ai-endpoint https://api.openai.com/v1/chat/completions

# 本地 Ollama（完全本地运行，无需联网，无需 API key）
# 先执行：ollama pull llama3
# 然后：
export AI_API_KEY=ollama  # Ollama 忽略 key 值，随便填
narrate facebook/react --from HEAD~5 --to HEAD \
  --ai-model llama3 \
  --ai-endpoint http://localhost:11434/v1/chat/completions

# 任何兼容 OpenAI 的提供商
export AI_API_KEY=sk-xxx
narrate owner/repo --from HEAD~10 --to HEAD \
  --ai-model claude-sonnet-4 \
  --ai-endpoint https://api.anthropic.com/v1/chat/completions
```

### 编码工具模式（使用工具自带的 AI）

不需要 API key。Narrate 只做数据采集——从 GitHub 获取 commits/issues，输出结构化 JSON 到 stdout。你的编码工具自带的 AI 负责写 changelog。

**在所有下列工具中用法完全一样：**

- **opencode** — `narrate owner/repo --from HEAD~4 --to HEAD --json-only`
- **Claude Code** — 完全相同的命令
- **Cursor（Composer）** — 完全相同的命令
- **Codex CLI** — 完全相同的命令
- **Workbuddy / Windsurf / 任何 AI 编码工具** — 完全相同的命令

模式永远一样：narrate 采集数据 → 工具 AI 写文案。不需要设置任何环境变量。

```bash
# 在任何工具中的等效操作：narrate 采集，工具 AI 写作
narrate ohmyzsh/ohmyzsh --from HEAD~4 --to HEAD --json-only
```

输出约 300+ 行结构化 JSON 到 stdout——包含 commits（类型、作者、SHA）、open/closed issues、社区亮点、交叉引用。你的编码工具 AI 读取这些数据后生成精美的发布说明。

## 模板风格

| 风格 | 受众 | 适用场景 |
|------|------|----------|
| `community` | 贡献者和用户 | 开源项目，让每个贡献者都感受到被重视 |
| `technical` | 开发者 | 库、SDK、基础设施——精确、关注迁移 |
| `marketing` | 普通受众 | SaaS 产品、新闻通讯、社交媒体公告 |

## 输出示例

```markdown
# ohmyzsh master

**4** commits · **2** issues resolved · **4** contributors
2026-07-05 to 2026-07-07 · 6 files · +55 -3

### New: complete route rule actions
[#13848](https://github.com/ohmyzsh/ohmyzsh/pull/13848) by @ishaanlabs-gg

## What's Next

- **[High Priority]** XDG Base Directory support (#9543) — 39 reactions
- **[In Discussion]** Auto-update custom plugins (#9512) — 25 reactions
```

所有中间 JSON 产物都会写入 `references/` 目录，方便检查和调试。

## 安装

```bash
pip install changelog-narrate
```

需要 Python 3.10+。无外部依赖（仅用标准库）。

或者直接从源码运行：

```bash
git clone https://github.com/1knownothing/changelog-narrate.git
cd changelog-narrate
python -m narrate --help
```

## 选项

```
usage: narrate [-h] --from FROM_REF --to TO_REF [--template {community,technical,marketing}]
               [--output OUTPUT] [--skip-quality] [--print] [--json-only]
               [--ai-model AI_MODEL] [--ai-endpoint AI_ENDPOINT]
               repo

positional arguments:
  repo                  owner/name 格式（如 ohmyzsh/ohmyzsh）

options:
  --from FROM_REF       起始引用（HEAD~4、v1.0、master@{7day}）
  --to TO_REF           目标引用（HEAD、master、v2.0）
  --template TEMPLATE   输出风格：community（默认）、technical、marketing
  --output, -o          输出目录（默认：references/）
  --skip-quality        跳过质量校验
  --print               将 markdown 打印到 stdout
  --json-only           ANALYZE 步骤后停止，输出 JSON 供编码工具的 AI 使用
  --ai-model AI_MODEL   AI 模型名称（默认：deepseek-chat）。
                        仅在设置了 AI_API_KEY 或 DEEPSEEK_API_KEY 时生效。
  --ai-endpoint AI_ENDPOINT
                        兼容 OpenAI 的 endpoint URL。
                        默认：https://api.deepseek.com/v1/chat/completions
                        例如：
                          https://api.openai.com/v1/chat/completions
                          http://localhost:11434/v1/chat/completions（Ollama）
```

### 环境变量

| 变量 | 用途 |
|------|------|
| `GITHUB_TOKEN` / `GH_TOKEN` | 提高 GitHub API 频率限制（5000 req/h vs 60） |
| `AI_API_KEY` | 任意兼容 OpenAI 的 AI 提供商的 API key |
| `DEEPSEEK_API_KEY` | 旧版 AI_API_KEY 别名（AI_API_KEY 未设置时使用） |

## 工作原理

```
PARSE_INPUT  →  COLLECT_DATA  →  ANALYZE  →  WRITER  →  FORMATTER  →  QUALITY_CHECK
  (引用)        (GitHub API)    (分类)     (模板/AI)   (markdown)    (校验)
```

每一步都会将输出写入 references 目录，可以从任意阶段检查和恢复。

### 管道详解

1. **PARSE_INPUT** — 校验引用，保存编排器状态
2. **COLLECT_DATA** — 从 GitHub REST API 获取 comparison、commits、open/closed issues
3. **ANALYZE** — 丰富 commits（解析 conventional commit），交叉引用 issues，计算社区影响力评分。`--json-only` 在此步骤停止。
4. **WRITER** — 执行模板写入器（基于规则）或 AI 写入器（如果设置了 `AI_API_KEY`）。AI 写入失败会自动回退到模板。
5. **FORMATTER** — 从结构化数据组装 markdown
6. **QUALITY_CHECK** — 校验输出的完整性，标记缺失部分和占位文本

### 写回 GitHub Release

你可以将格式化的 markdown 通过 GitHub CLI 发布：

```bash
narrate owner/repo --from v1.0 --to v2.0 --print > release.md
gh release create v2.0 --notes-file release.md
```

## GitHub Action

发布 Release 时自动生成发布说明。可在 [Actions Marketplace](https://github.com/marketplace/actions/changelog-narrate) 找到。

### 用法

```yaml
# .github/workflows/release-notes.yml
on:
  release:
    types: [published]
jobs:
  generate:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: 1knownothing/changelog-narrate@v1
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
```

之后在 GitHub 创建 Release → 发布说明自动生成并写入。

### Action 输入

| 输入 | 默认值 | 说明 |
|------|--------|------|
| `token` | `github.token` | 具备 release 写入权限的 token |
| `template` | `community` | 模板风格 |
| `from-ref` | 自动检测 | 上一个 tag 或 commit SHA |
| `to-ref` | `GITHUB_REF_NAME` | 发布 tag 或 commit SHA |

## 路线图

- [x] PyPI 发布
- [x] GitHub Action — 发布 Release 时自动生成发布说明
- [ ] 多仓库支持

## 为什么用 narrate？

好的发布说明能建立社区。它们把 commits 列表变成一个故事，让用户感到被关注，让贡献者感到被重视。`narrate` 处理机械的部分——数据获取、分类、格式化——让你专注于真正重要的事：理解用户需要知道什么。

## 许可证

MIT
