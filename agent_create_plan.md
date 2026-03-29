我来为你编写 **Claude Code `plan` 模式专用提示词**，采用详细的步骤分解格式，让 Claude 能够自主规划、执行并追踪多智能体工作流。

---

## Claude Code `plan` 模式配置

### 文件结构
```
.claude/
├── plan/
│   ├── gpsg-master-plan.md      # 主计划入口
│   ├── phases/
│   │   ├── phase-01-orchestrator.md   # Phase 1: 意图解析与调度
│   │   ├── phase-02-parallel-analysis.md # Phase 2: 三 Agent 并行
│   │   ├── phase-03-arbitration.md      # Phase 3: 整合仲裁
│   │   ├── phase-04-visualization.md    # Phase 4: 视觉渲染
│   │   └── phase-05-deployment.md       # Phase 5: Git 部署
│   └── subplans/
│       ├── architect-subplan.md   # ArchitectAgent 内部子计划
│       ├── value-subplan.md       # ValueAgent 内部子计划
│       └── setup-subplan.md       # SetupAgent 内部子计划
└── tools/
    └── plan-checkpoint.json       # 计划执行状态检查点
```

---

### 主计划入口: `.claude/plan/gpsg-master-plan.md`

```markdown
# GPSG Master Plan
# Claude Code plan 模式主计划
# 触发: 用户输入 gpsg generate 命令

## 计划元数据
```yaml
plan_id: gpsg-master-v3
version: "3.0-git-native"
estimated_duration: "5-8 minutes"
parallel_phases: [2]  # Phase 2 支持并行
critical_path: [1, 3, 4, 5]  # 必须顺序执行的 phases
rollback_point: phase_01  # 失败时可回滚到的阶段
```

## 执行摘要
本计划将自主完成 GitHub 项目主页的生成与部署，无需用户干预中间步骤。

## 阶段概览

| Phase | 名称 | Agent | 输入 | 输出 | 模式 | 超时 |
|:---|:---|:---|:---|:---|:---|:---|
| 1 | 意图解析与调度 | OrchestratorAgent | 用户命令 | execution_plan.json + style_guide.md | 顺序 | 60s |
| 2 | 并行分析 | Architect + Value + Setup | Git 仓库 + style_guide | 3x .md 文件 | 并行 | 120s |
| 3 | 整合仲裁 | OrchestratorAgent | 3x .md | content_bundle.yaml | 顺序 | 60s |
| 4 | 视觉渲染 | VisualAgent | content_bundle.yaml | README.md | 顺序 | 60s |
| 5 | Git 部署 | GitExecutor | README.md | commit/PR | 顺序 | 60s |

## 前置检查清单
执行 Phase 1 前必须验证:

- [ ] 当前目录是 Git 仓库 (`.git/` 存在)
- [ ] 有写权限 (非裸仓库)
- [ ] `gh` CLI 已安装 (用于 PR 创建) 或标记为本地模式
- [ ] 磁盘空间 > 100MB (用于 .gpsg/ 工作目录)

## 全局状态变量
```yaml
state:
  git_status: null      # CLEAN | DIRTY | MERGING | ...
  strategy: null        # feature-branch | direct-commit | stash-and-go
  style_guide: null     # 路径
  execution_plan: null  # 路径
  agent_outputs: []     # [architect, value, setup] 输出路径
  content_bundle: null  # 路径
  final_readme: null    # 路径
  deploy_result: null   # commit hash / PR url
  errors: []            # 累积错误
  warnings: []            # 非致命警告
```

## 阶段跳转逻辑
```python
def next_phase(current, result):
    if current == 1 and result.ok:
        return 2  # 进入并行分析
    elif current == 2:
        if all_agents_success(result.outputs):
            return 3
        elif partial_success(result.outputs):
            state.warnings.append("Partial agent output")
            return 3  # 继续，但标记警告
        else:
            return ROLLBACK  # 重试 Phase 2 或中止
    elif current == 3 and result.conflicts == 0:
        return 4
    elif current == 3 and result.conflicts > 0:
        if result.auto_resolved:
            return 4
        else:
            return 3  # 原地重试，打回 Agent 补全
    elif current == 4 and result.ok:
        return 5
    elif current == 5:
        if result.deployed:
            return SUCCESS
        elif result.retryable:
            return 5  # 重试部署
        else:
            return FAILURE  # 需手动处理
```

## 失败恢复策略
| 失败阶段 | 自动动作 | 用户提示 |
|:---|:---|:---|
| Phase 1 | 重试 1 次，检查意图解析 | "请澄清项目类型" |
| Phase 2 (单 Agent 失败) | 其他 Agent 继续，失败 Agent 输出占位符 | "X Agent 超时，使用简化输出" |
| Phase 2 (全失败) | 回滚到 Phase 1，检查 Git 状态 | "无法分析代码库，请检查路径" |
| Phase 3 (冲突不可解) | 生成冲突报告，暂停等待用户 | "请裁决: X 与 Y 矛盾" |
| Phase 4 | 使用纯文本模板，跳过美化 | "渲染失败，输出基础格式" |
| Phase 5 (推送失败) | 自动 pull --rebase 重试 3 次 | "远程冲突，请手动同步" |

## 结束条件
- SUCCESS: `deploy_result` 包含有效 commit hash 或 PR URL
- FAILURE: 生成 `.gpsg/resume.json`，用户可 `--continue` 恢复

## 启动命令
当检测到用户输入匹配 `gpsg generate.*` 时，加载本计划并执行 Phase 1。
```

---

### Phase 1: 意图解析与调度 `.claude/plan/phases/phase-01-orchestrator.md`

```markdown
# Phase 1: 意图解析与调度
# Agent: OrchestratorAgent
# 模式: 顺序执行 (阻塞)

## 目标
将用户自然语言输入转化为结构化执行计划和强制风格规范。

## 输入
- 用户命令字符串 (如: `gpsg generate . --intent="医疗 RL 临床落地" --template=research`)
- 当前工作目录文件列表
- Git 仓库基本信息 (remote url, 当前 branch)

## 详细步骤

### Step 1.1: 解析命令行参数
```python
# 提取结构化参数
args = parse_command(user_input)

extracted:
  source: "."  # 或 URL
  intent: "医疗 RL 临床落地"
  template: "research"  # 默认: generic
  urgent: false
  strategy: null  # 由后续 Git 状态决定
  constraints:
    max_length: null  # 从 template 推断
    highlights: []     # 从 intent 关键词提取
```

### Step 1.2: 推断项目特征
```python
# 扫描文件树，确定项目类型
files = list_dir(".", depth=2)

detections:
  language: detect_language(files)  # python | javascript | rust | ...
  has_docker: exists("Dockerfile")
  has_ci: exists(".github/workflows/")
  has_docs: exists("docs/") or exists("mkdocs.yml")
  is_monorepo: exists("pnpm-workspace.yaml") or multiple_package_files
```

### Step 1.3: 映射意图到 StyleGuide
```python
# 选择或生成风格指南
style_key = f"{args.template}-{detections.language}"
style_guide_path = f".claude/tools/style-guides/{style_key}.yaml"

if not exists(style_guide_path):
    style_guide_path = generate_dynamic_style(args.intent, detections)
    # 基于意图关键词动态生成

# 加载并定制
style_guide = load_yaml(style_guide_path)
style_guide.custom_highlights = extract_keywords(args.intent)
```

### Step 1.4: 诊断 Git 状态
```python
# 完整 Git 健康检查
git_state = {
    "is_repo": check_git_repo(),
    "current_branch": git_branch(),
    "is_dirty": len(git_status()) > 0,
    "untracked_files": git_status(untracked=True),
    "behind_count": git_behind_remote(),
    "ahead_count": git_ahead_remote(),
    "is_merging": exists(".git/MERGE_HEAD"),
    "is_rebasing": exists(".git/rebase-merge"),
    "head_detached": git_rev_parse() not in git_branches(),
    "remote_url": git_remote_url(),
    "default_branch": git_default_branch(),  # main or master
}

# 确定执行策略
if git_state.is_merging or git_state.is_rebasing:
    strategy = "ABORT"  # 不安全，必须暂停
elif args.urgent and git_state.current_branch == git_state.default_branch:
    strategy = "DIRECT_COMMIT" if confirm_user() else "ABORT"
elif git_state.is_dirty:
    strategy = "STASH_AND_PROCEED"
elif git_state.behind_count > 10:
    strategy = "PULL_REBASE_FIRST"
else:
    strategy = "FEATURE_BRANCH_PR"
```

### Step 1.5: 生成执行计划
```python
execution_plan = {
    "run_id": f"gpsg-{timestamp()}",
    "triggered_by": user_input,
    "strategy": strategy,
    "style_guide": style_guide_path,
    "phases": [
        {
            "phase": 2,
            "mode": "parallel",
            "agents": [
                {"name": "ArchitectAgent", "subplan": "architect-subplan.md", "timeout": 120},
                {"name": "ValueAgent", "subplan": "value-subplan.md", "timeout": 120},
                {"name": "SetupAgent", "subplan": "setup-subplan.md", "timeout": 120},
            ],
            "fallback": "sequential_with_timeout_extension"
        },
        {
            "phase": 3,
            "mode": "sequential",
            "agent": "OrchestratorAgent",
            "task": "arbitration",
            "timeout": 60
        },
        # ... Phase 4, 5
    ],
    "checkpoints": [
        {"after": 2, "save_state": true},  # 保存 Agent 输出
        {"after": 4, "save_state": true},  # 保存最终 README
    ]
}
```

### Step 1.6: 持久化状态
```python
# 创建 .gpsg/ 工作目录
mkdir(".gpsg/agent_outputs", exist_ok=True)
mkdir(".gpsg/merge", exist_ok=True)
mkdir(".gpsg/final", exist_ok=True)
mkdir(".gpsg/audit", exist_ok=True)

# 写入文件
write_json(".gpsg/execution_plan.json", execution_plan)
write_yaml(".gpsg/git_state.json", git_state)
copy(style_guide_path, ".gpsg/style_guide_active.yaml")

# 创建检查点
write_json(".gpsg/plan_checkpoint.json", {
    "phase": 1,
    "status": "completed",
    "outputs": [
        ".gpsg/execution_plan.json",
        ".gpsg/git_state.json", 
        ".gpsg/style_guide_active.yaml"
    ],
    "next_phase": 2
})
```

## 输出文件
| 文件 | 格式 | 说明 |
|:---|:---|:---|
| `.gpsg/execution_plan.json` | JSON | 完整执行计划，包含所有 phases |
| `.gpsg/git_state.json` | JSON | Git 状态快照 |
| `.gpsg/style_guide_active.yaml` | YAML | 激活的风格指南 |
| `.gpsg/plan_checkpoint.json` | JSON | 检查点，用于恢复 |

## 成功标准
- [ ] `execution_plan.json` 有效且可解析
- [ ] `strategy` 已确定 (非 ABORT)
- [ ] `style_guide_active.yaml` 存在且包含必需字段
- [ ] 检查点文件写入成功

## 失败处理
若 `strategy == "ABORT"`：
1. 输出诊断报告 (Git 状态冲突详情)
2. 提供恢复命令 (如 `git merge --abort`)
3. 生成 `.gpsg/abort_reason.json`
4. 计划终止，提示用户解决后重试
```

---

### Phase 2: 并行分析 `.claude/plan/phases/phase-02-parallel-analysis.md`

```markdown
# Phase 2: 并行分析
# Agents: ArchitectAgent + ValueAgent + SetupAgent
# 模式: 并行执行 (非阻塞，独立超时)

## 目标
三个 Agent 同时分析代码库，分别产出技术架构、价值卖点、配置指南。

## 并行架构

```
┌─────────────────────────────────────────────────────────┐
│                    Phase 2 协调器                        │
│  (轻量级调度，监控进度，处理超时)                          │
└─────────────┬─────────────────────────────┬─────────────┘
              │                             │
    ┌─────────▼─────────┐         ┌─────────▼─────────┐
    │  ArchitectAgent   │         │   ValueAgent      │
    │  子计划: architect │         │   子计划: value   │
    │  超时: 120s        │         │   超时: 120s       │
    │  输出: 01_architecture.md    │   输出: 02_value.md │
    └─────────┬─────────┘         └─────────┬─────────┘
              │                             │
              └─────────────┬───────────────┘
                            │
                  ┌─────────▼─────────┐
                  │   SetupAgent      │
                  │   子计划: setup   │
                  │   超时: 120s       │
                  │   输出: 03_setup.md │
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌─────────────────┐
                  │  协调器聚合结果  │
                  │  标记完成/超时/失败│
                  └─────────────────┘
```

## 协调器逻辑

```python
def run_parallel_agents(agents, global_timeout=120):
    results = {}
    pending = set(a.name for a in agents)
    
    for agent in agents:
        # 非阻塞启动
        results[agent.name] = launch_subplan(agent.subplan, timeout=agent.timeout)
    
    # 监控循环
    while pending:
        for name in list(pending):
            status = check_subplan(name)
            
            if status == "completed":
                pending.remove(name)
                results[name].status = "success"
                results[name].output_path = get_output_path(name)
                
            elif status == "timeout":
                pending.remove(name)
                results[name].status = "timeout"
                results[name].output_path = generate_placeholder(name)
                log_warning(f"{name} timeout, using placeholder")
                
            elif status == "failed":
                pending.remove(name)
                results[name].status = "failed"
                results[name].error = get_error_log(name)
        
        if not pending:
            break
            
        sleep(1)
    
    # 评估整体结果
    success_count = sum(1 for r in results.values() if r.status == "success")
    
    if success_count == 3:
        return PhaseResult(status="success", outputs=results)
    elif success_count >= 1:
        return PhaseResult(status="partial", outputs=results, warning="Some agents failed/timeout")
    else:
        return PhaseResult(status="failure", outputs=results, error="All agents failed")
```

## 子计划启动规范

每个 Agent 子计划接收:

```yaml
subplan_input:
  execution_plan: ".gpsg/execution_plan.json"  # 完整计划上下文
  style_guide: ".gpsg/style_guide_active.yaml"   # 强制风格
  git_state: ".gpsg/git_state.json"             # Git 状态
  agent_specific:
    entry_points: [...]  # 由协调器预分析的关键文件
    focus_areas: [...]   # 基于意图的重点关注区域
```

每个 Agent 子计划产出:

```yaml
subplan_output:
  status: "success" | "timeout" | "failed"
  output_file: ".gpsg/agent_outputs/0N_{agent_name}.md"
  metadata:
    word_count: 0
    sections_generated: []
    git_queries_made: 0
    warnings: []
```

## 检查点更新

Phase 2 完成后更新:

```json
{
  "phase": 2,
  "status": "completed",
  "agent_results": {
    "ArchitectAgent": {"status": "success", "output": "01_architecture.md"},
    "ValueAgent": {"status": "success", "output": "02_value.md"},
    "SetupAgent": {"status": "timeout", "output": "03_setup_placeholder.md"}
  },
  "next_phase": 3,
  "warnings": ["SetupAgent timeout, simplified output used"]
}
```

## 输出文件
- `.gpsg/agent_outputs/01_architecture.md`
- `.gpsg/agent_outputs/02_value.md`
- `.gpsg/agent_outputs/03_setup.md` (或占位符)

## 成功标准
- [ ] 至少 2 个 Agent 成功完成
- [ ] 输出文件存在于指定目录
- [ ] 文件符合基础 Markdown 格式
```

---

### ArchitectAgent 子计划 `.claude/plan/subplans/architect-subplan.md`

```markdown
# Subplan: ArchitectAgent
# 父阶段: Phase 2
# 超时: 120 秒

## 目标
生成技术架构白皮书章节，包含依赖图、模块职责、技术选型原因。

## 执行步骤

### Step 1: Git 历史挖掘 (20s)
```python
# 加载输入
style_guide = load_yaml("{{style_guide}}")
git_state = load_json("{{git_state}}")

# 提取近期演进
recent_commits = git_log(max_count=50, format="hash|author|date|message")

# 识别重构热点
refactor_commits = filter(recent_commits, 
    lambda c: any(kw in c.message for kw in ["refactor", "migrate", "rewrite"]))
```

### Step 2: 代码结构扫描 (40s)
```python
# 生成文件树（排除标准目录）
file_tree = list_dir(".", recursive=True, 
    exclude=["node_modules", ".git", "__pycache__", "*.pyc", ".venv"])

# 识别技术栈
config_files = find(["pyproject.toml", "package.json", "Cargo.toml", "setup.py"])
tech_stack = parse_tech_stack(config_files)

# 提取入口点
entry_points = find(["__main__.py", "cli.py", "main.py", "app.py", "index.js"])
for ep in entry_points[:3]:  # 限制前 3 个，避免过度分析
    imports = parse_imports(ep)
    dependency_graph.add_node(ep, imports)
```

### Step 3: 架构图生成 (30s)
```python
# 生成 Mermaid 图
mermaid_code = generate_mermaid(dependency_graph, type="flowchart")

# 验证语法 (简单检查)
if not validate_mermaid(mermaid_code):
    mermaid_code = generate_fallback_text_graph(dependency_graph)
```

### Step 4: 内容合成 (25s)
```python
# 按 StyleGuide 模板渲染
content = render_template("architect-research",  # 基于 style_guide 选择模板
    tech_stack=tech_stack,
    dependency_graph=dependency_graph,
    mermaid_code=mermaid_code,
    refactor_history=refactor_commits[:5],  # 最近 5 次重构
    maintainers=extract_maintainers(git_blame, threshold=0.5)
)

# 风格强制检查
violations = check_style_compliance(content, style_guide)
if violations:
    content = auto_fix(content, violations)
```

### Step 5: 输出 (5s)
```python
write_file("{{output_path}}", content)
write_json("{{metadata_path}}", {
    "word_count": len(content.split()),
    "sections": ["Tech Stack", "Architecture Diagram", "Module Responsibilities"],
    "git_queries": len(recent_commits) + len(refactor_commits),
    "warnings": [] if not violations else [f"Auto-fixed: {v}" for v in violations]
})
```

## 失败降级
若任何步骤超时:
- Step 2 超时 → 使用简化文件树，标注 "Partial analysis due to timeout"
- Step 3 超时 → 跳过 Mermaid，使用文本列表
- Step 4 超时 → 输出原始模板，标注 "Template output, customization skipped"

## 输出
- 文件: `.gpsg/agent_outputs/01_architecture.md`
- 元数据: `.gpsg/agent_outputs/01_architecture.meta.json`
```

---

### ValueAgent 子计划 `.claude/plan/subplans/value-subplan.md`

```markdown
# Subplan: ValueAgent
# 父阶段: Phase 2
# 超时: 120 秒

## 目标
提取项目价值卖点，生成用户视角的价值主张。

## 执行步骤

### Step 1: 项目叙事挖掘 (30s)
```python
# 版本标签分析
tags = git_tag_list()
release_pattern = analyze_release_pattern(tags)  # 稳定版 vs 快速迭代

# Commit 主题聚类
recent = git_log(since="3 months ago")
themes = cluster_commits(recent, categories=["feature", "perf", "fix", "docs"])
dominant_theme = max(themes, key=lambda x: x.count)
```

### Step 2: 用户信号提取 (40s)
```python
# Issue 模板分析
if exists(".github/ISSUE_TEMPLATE/"):
    templates = read_dir(".github/ISSUE_TEMPLATE/")
    pain_points = extract_problem_statements(templates)

# Changelog 分析
if exists("CHANGELOG.md"):
    changelog = parse_changelog()
    recent_changes = changelog.releases[0].changes if changelog.releases else []
```

### Step 3: 差异化分析 (30s, 最佳 effort)
```python
# 尝试 GitHub API 扫描竞品 (若 token 可用)
try:
    competitors = github_search(topic=infer_topic(), sort="stars", limit=3)
    differentiation = compare_features(extract_our_features(), competitors)
except (NoTokenError, APIError):
    differentiation = null
    warning = "GitHub API unavailable, differentiation analysis skipped"
```

### Step 4: 价值叙事合成 (15s)
```python
content = render_template("value-research",
    value_proposition=generate_elevator_pitch(themes, pain_points),
    highlights=extract_highlights(themes, recent_changes, 3),  # Top 3
    differentiation_table=differentiation,
    user_scenarios=extract_scenarios(pain_points),
    evidence_links=collect_issue_references(pain_points)
)

# 强制检查: 所有声称必须有证据
claims = extract_claims(content)
for claim in claims:
    if not has_evidence(claim):
        mark_as_opinion(claim)  # 添加 "我们相信..." 前缀或移除
```

### Step 5: 输出 (5s)
```python
write_file("{{output_path}}", content)
```

## 输出
- 文件: `.gpsg/agent_outputs/02_value.md`
```

---

### SetupAgent 子计划 `.claude/plan/subplans/setup-subplan.md`

```markdown
# Subplan: SetupAgent
# 父阶段: Phase 2
# 超时: 120 秒

## 目标
生成精确的 Quick Start 指南和 Badge 配置。

## 执行步骤

### Step 1: 配置解析 (40s)
```python
# 检测并解析配置文件
configs = []
for filename in ["pyproject.toml", "package.json", "Cargo.toml", "environment.yml"]:
    if exists(filename):
        content = parse_file(filename)  # 自动检测格式
        configs.append({"file": filename, "content": content})

# 提取依赖
deps = merge_dependencies(configs)  # 跨配置文件合并

# 检测环境管理器
env_manager = detect_env_manager(configs)  # pip/conda/poetry/npm/cargo
```

### Step 2: CI/CD 解析 (30s)
```python
# 扫描 workflow 文件
workflows = list_dir(".github/workflows/") if exists(".github/workflows/") else []

badges = []
for wf in workflows:
    badge = generate_shields_badge(wf)  # 生成 shields.io URL
    badges.append(badge)

# 检测 Docker
docker_support = exists("Dockerfile") or exists("docker-compose.yml")
```

### Step 3: 指令生成 (35s)
```python
# 多平台指令
install_cmds = {
    "bash": generate_bash_install(env_manager, deps),
    "powershell": generate_powershell_install(env_manager, deps),
    "zsh": generate_zsh_install(env_manager, deps)
}

# 环境变量扫描
env_vars = scan_env_vars([".env.example", "config.py", "settings.py"])

# 验证命令
verify_cmds = generate_verification(env_manager)
```

### Step 4: 合成 (10s)
```python
content = render_template("setup-research",
    prerequisites=extract_prerequisites(configs),
    install_commands=install_cmds,
    env_variables=env_vars,
    badges=badges,
    docker_option=docker_support,
    verification=verify_cmds
)
```

### Step 5: 输出 (5s)
```python
write_file("{{output_path}}", content)
```

## 输出
- 文件: `.gpsg/agent_outputs/03_setup.md`
```

---

### Phase 3-5 概要

由于篇幅，以下提供核心逻辑框架：

**Phase 3: 整合仲裁** `.claude/plan/phases/phase-03-arbitration.md`
```markdown
# Phase 3: 整合仲裁
# Agent: OrchestratorAgent (仲裁模式)

## 输入
- `01_architecture.md`
- `02_value.md` 
- `03_setup.md`
- `style_guide_active.yaml`

## 仲裁流程
1. 加载三份输出，解析为结构化块
2. 检测冲突:
   - 事实矛盾: 数值不一致 (如依赖数量)
   - 风格偏离: 禁用词、语气不符
   - 内容缺失: StyleGuide 要求的必需章节
3. 裁决规则:
   - 客观数据: SetupAgent > ArchitectAgent > ValueAgent
   - 主观描述: ValueAgent 优先，但需证据支撑
4. 生成 `content_bundle.yaml`:
   ```yaml
   sections:
     - id: "introduction"
       source: "02_value.md:elevator_pitch"
       content: "..."
     - id: "architecture"
       source: "01_architecture.md:full"
       fold: true  # 根据 StyleGuide
   conflicts_resolved: 2
   auto_fixed: 1
   manual_review_required: 0
   ```

## 输出
- `.gpsg/merge/content_bundle.yaml`
```

**Phase 4: 视觉渲染** `.claude/plan/phases/phase-04-visualization.md`
```markdown
# Phase 4: 视觉渲染
# Agent: VisualAgent

## 输入
- `content_bundle.yaml`
- `style_guide_active.yaml`

## 步骤
1. 加载 Jinja2 模板 (基于 style_guide.template_id)
2. 渲染各章节，应用折叠策略
3. 生成 shields.io Badge URL
4. 插入占位图标记 (<!-- TODO: GIF -->)
5. 生成 TOC (目录)
6. 验证: 链接检查、移动端宽度检查
7. 输出 `.gpsg/final/README.md`
```

**Phase 5: Git 部署** `.claude/plan/phases/phase-05-deployment.md`
```markdown
# Phase 5: Git 部署
# Agent: GitExecutor

## 输入
- `.gpsg/final/README.md`
- `execution_plan.json` (含 strategy)
- `git_state.json` (原始状态)

## 部署流程 (strategy = FEATURE_BRANCH_PR)
1. 若 git_state.dirty: `git stash push -m "GPSG auto-stash"`
2. `git checkout -b gpsg/readme-refresh-{timestamp}`
3. `cp .gpsg/final/README.md ./README.md`
4. `git add README.md`
5. `git commit -S -m "docs: regenerate README with GPSG"`
6. `git push -u origin HEAD`
7. `gh pr create --title "docs: README refresh" --body-file .gpsg/pr_description.md`
8. 若之前有 stash: `git stash pop`

## 输出
- `.gpsg/deploy_result.json`:
  ```json
  {
    "success": true,
    "strategy": "feature-branch-pr",
    "branch": "gpsg/readme-refresh-20260329",
    "commit_hash": "abc123",
    "pr_url": "https://github.com/user/repo/pull/123",
    "stash_restored": true
  }
  ```
```

---

### 检查点与恢复机制 `.claude/tools/plan-checkpoint.json`

```json
{
  "checkpoint_format_version": "1.0",
  "resume_capability": true,
  "states": [
    {
      "phase": 1,
      "files": [".gpsg/execution_plan.json", ".gpsg/git_state.json", ".gpsg/style_guide_active.yaml"],
      "resume_command": "claude --plan .claude/plan/phases/phase-02-parallel-analysis.md --input-from-checkpoint"
    },
    {
      "phase": 2,
      "files": [".gpsg/agent_outputs/*.md", ".gpsg/agent_outputs/*.meta.json"],
      "resume_command": "claude --plan .claude/plan/phases/phase-03-arbitration.md --input-from-checkpoint"
    },
    {
      "phase": 3,
      "files": [".gpsg/merge/content_bundle.yaml"],
      "resume_command": "claude --plan .claude/plan/phases/phase-04-visualization.md --input-from-checkpoint"
    },
    {
      "phase": 4,
      "files": [".gpsg/final/README.md"],
      "resume_command": "claude --plan .claude/plan/phases/phase-05-deployment.md --input-from-checkpoint"
    }
  ],
  "failure_recovery": {
    "default_action": "pause_and_report",
    "auto_retry": ["git_push"],  # 推送失败自动重试
    "max_retries": 3
  }
}
```

### 3. 监控执行
Claude 将:
1. 显示 Phase 进度条
2. 每个 Step 完成后更新检查点
3. 并行 Phase 显示 Agent 状态面板
4. 失败时提供恢复选项

### 4. 中断恢复
若执行中断，下次启动:
```bash
claude --continue  # 自动读取 .gpsg/plan_checkpoint.json
```

--