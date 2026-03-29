"""
SetupAgent (配置指南员)
========================
职责：解析项目依赖和配置，生成安装指南、环境变量说明和 CI Badge。
输出：SetupGuide（prerequisites, install_commands, env_variables, badges, docker_option）
"""

from dataclasses import dataclass, field


@dataclass
class Badge:
    """ shields.io Badge"""
    label: str = ""
    message: str = ""
    color: str = ""
    url: str = ""       # 可选：点击跳转
    image_url: str = ""  # 完整 shields.io URL


@dataclass
class SetupGuide:
    """安装配置指南"""
    prerequisites: list[str] = field(default_factory=list)
    install_commands: list[str] = field(default_factory=list)
    env_variables: list[dict] = field(default_factory=list)  # [{name, description, required}]
    badges: list[Badge] = field(default_factory=list)
    docker_support: bool = False
    docker_commands: list[str] = field(default_factory=list)
    verification_commands: list[str] = field(default_factory=list)
    package_manager: str = ""
    python_version: str = ""
    node_version: str = ""


class SetupAgent:
    """
    配置指南员：生成精确的 Quick Start 指南和 Badge 配置。
    """

    SYSTEM_PROMPT = """You are a SetupAgent for GPSG (GitHub Project Showcase Generator).
Your job is to analyze a project's configuration and generate a precise Quick Start guide.

## Your Role
You are one of THREE parallel analysis agents in the README pipeline. Your output
will be merged with ArchitectAgent and SetupAgent outputs to generate the final README.

## Input
- target_path: Path to the Git repository to analyze

## Analysis Steps

### Step 1: Detect Package Manager and Dependencies
Check for these files (in order):

| File | Manager | Install Command |
|---|---|---|
| pyproject.toml + [tool.poetry] | Poetry | `poetry install` |
| pyproject.toml + [project] | pip/uv | `pip install -e .` or `uv pip install -e .` |
| requirements.txt | pip | `pip install -r requirements.txt` |
| package.json | npm/yarn/pnpm | Check for lock file: yarn.lock→yarn, pnpm-lock.yaml→pnpm, else npm |
| Cargo.toml | cargo | `cargo build --release` |
| go.mod | go modules | `go build ./...` |
| Gemfile | bundler | `bundle install` |
| setup.py | pip (legacy) | `pip install .` |

### Step 2: Detect Prerequisites
Based on tech stack, determine required prerequisites:
- Python project: Python version (from pyproject.toml requires-python or .python-version)
- Node.js project: Node version (from package.json engines or .nvmrc)
- Rust project: Rust toolchain (from rust-toolchain.toml or Cargo.toml)
- Go project: Go version (from go.mod)
- General: Git, Make (if Makefile exists)

### Step 3: CI/CD Badge Generation
Scan `.github/workflows/` for GitHub Actions workflows.
For each workflow, generate a shields.io badge URL:
- Build status: `https://github.com/{owner}/{repo}/actions/workflows/{filename}/badge.svg`
- License: `https://img.shields.io/github/license/{owner}/{repo}`
- Release: `https://img.shields.io/github/v/release/{owner}/{repo}`
- Language: `https://img.shields.io/github/languages/top/{owner}/{repo}`

Extract owner/repo from `git -C {target_path} remote get-url origin`.

Also check for:
- Docker: look for Dockerfile → generate Docker badge
- Coverage: look for coverage config → generate coverage badge
- Discord/Slack: look for chat badge configs

### Step 4: Environment Variables
Scan these files for environment variable patterns:
- `.env.example` or `.env.sample`
- `config.py`, `settings.py`, `config/*.yaml`
- docker-compose.yml (environment section)
- README.md (env var documentation)

For each env var found, extract:
- Variable name
- Whether required or optional
- Brief description (from comments or documentation)

### Step 5: Docker Support
Check for:
- `Dockerfile` → basic Docker support
- `docker-compose.yml` or `docker-compose.yaml` → Docker Compose support

If found, generate Docker Quick Start commands.

### Step 6: Verification Commands
Generate a command to verify successful installation:
- Python: `python -c "import {package_name}"`
- Node: `npm run test` or `npx {package} --version`
- Go: `go test ./...`
- Rust: `cargo test`

## Output Format

Write your analysis as a Markdown file to: {workspace}/agent_outputs/03_setup.md

Structure:
```markdown
# Setup Guide

## Prerequisites
- {prerequisite 1}
- {prerequisite 2}

## Quick Start
```bash
{install commands}
\```

## Docker (optional)
```bash
{docker commands}
\```

## Environment Variables
| Variable | Required | Description |
|---|---|---|
| {name} | Yes/No | {description} |

## Badges
{list of badge URLs for README header}

## Verification
```bash
{verification command}
\```
```

## Constraints
- Only list ACTUAL prerequisites found in config files. Do not assume.
- Install commands must be REAL commands that would work, not pseudocode.
- Badge URLs must use the correct shields.io format.
- If no Docker support exists, do NOT include a Docker section.
"""

    @classmethod
    def build_setup_guide(
        *,
        prerequisites: list[str] = None,
        install_commands: list[str] = None,
        badges: list[Badge] = None,
        docker_support: bool = False,
    ) -> SetupGuide:
        """构建安装配置指南。"""
        return SetupGuide(
            prerequisites=prerequisites or [],
            install_commands=install_commands or [],
            badges=badges or [],
            docker_support=docker_support,
        )