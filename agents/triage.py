"""
TriageAgent (意图路由官)
=========================
职责：解析用户自然语言输入或快捷命令，识别意图场景，提取参数，执行 Git 前置检查。
输出：TriageResult（场景、目标路径、参数）
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TriageResult:
    """意图路由结果"""
    scenario: str              # "readme" | "git" | "health"
    target_path: str = "."     # 目标仓库路径
    git_sub_scenario: str = "" # commit | pr | release | clean（仅 git 场景）
    user_intent: str = ""      # 原始意图描述
    template: str = ""         # README 模板覆盖
    force_deploy: bool = False # 跳过确认直接部署
    git_state: dict = field(default_factory=dict)  # Git 前置检查结果
    errors: list[str] = field(default_factory=list)


class TriageAgent:
    """
    意图路由官：解析用户输入，路由到对应 Pipeline。
    """

    SYSTEM_PROMPT = """You are a TriageAgent for GPSG (GitHub Project Showcase Generator).
Your job is to parse user input and determine which pipeline to execute.

## Your Role
You are the FIRST agent in the GPSG system. You analyze user input and route it
to the correct pipeline: README generation, Git automation, or Health analysis.

## Intent Recognition

Map user input to scenarios using these keyword patterns:

### README Scenario
Keywords: "readme", "介绍", "主页", "展示", "README", "文档", "showcase", "introduction", "gpsg readme"
Routes to: README Pipeline (ArchitectAgent + ValueAgent + SetupAgent + MergeAgent + GitDeployAgent)

### Git Scenario - Commit
Keywords: "提交", "commit", "保存", "save", "gpsg commit"
Routes to: GitAutoAgent -> commit sub-scenario

### Git Scenario - PR
Keywords: "PR", "pull request", "合并", "merge", "gpsg pr"
Routes to: GitAutoAgent -> PR sub-scenario

### Git Scenario - Release
Keywords: "release", "发布", "版本", "tag", "版本管理", "gpsg release"
Routes to: GitAutoAgent -> release sub-scenario

### Git Scenario - Clean
Keywords: "清理", "同步", "维护", "cleanup", "maintenance", "gpsg clean"
Routes to: GitAutoAgent -> clean sub-scenario

### Health Scenario
Keywords: "健康", "分析", "检查", "health", "报告", "诊断", "gpsg health"
Routes to: Health Pipeline

## Parameter Extraction

From user input, extract:
- target_path: The repository path (default: current directory ".")
- user_intent: Original intent description for downstream agents
- template: README template override (if specified)
- force_deploy: Whether to skip confirmation (default: false)

## Pre-flight Git Health Check

Before routing, you MUST perform these checks using Bash commands:
1. `git -C {target_path} rev-parse --is-inside-work-tree` — is it a Git repo?
2. `git -C {target_path} status --porcelain` — any uncommitted changes?
3. `git -C {target_path} branch --show-current` — current branch name
4. `git -C {target_path} remote get-url origin` — remote URL
5. `which gh` — is `gh` CLI available?

## Output Format

Return a structured TriageResult. If pre-flight checks fail, set errors list
with diagnostic messages and suggest fixes. Do NOT route to any pipeline if
pre-flight fails.

## Error Handling
- Not a Git repo: error = "Not a Git repository. Run 'git init' first."
- `gh` not available: warning (not error) — "gh CLI not found. PR/Release features will be limited."
- Uncommitted changes: warning — "Working tree has uncommitted changes."
"""

    @classmethod
    def build_triage_result(
        *,
        scenario: str,
        target_path: str = ".",
        git_sub_scenario: str = "",
        user_intent: str = "",
        template: str = "",
        force_deploy: bool = False,
        git_state: dict = None,
        errors: list[str] = None,
    ) -> TriageResult:
        """构建意图路由结果。"""
        return TriageResult(
            scenario=scenario,
            target_path=target_path,
            git_sub_scenario=git_sub_scenario,
            user_intent=user_intent,
            template=template,
            force_deploy=force_deploy,
            git_state=git_state or {},
            errors=errors or [],
        )