"""
Safety Rules - Git 操作安全红线
=================================
本文件定义了所有 Agent 必须遵守的安全规则。
在执行任何 Git 操作前，Agent 必须检查该规则表。
"""

# ======================================================================
# ABSOLUTE PROHIBITIONS (绝不执行)
# ======================================================================

BANNED_COMMANDS = [
    "git push --force",
    "git push -f",
    "git reset --hard",
    "git clean -fd",
    "git branch -D",       # 必须用 -d 并确认
    "git push origin :*",   # 删除远程分支
    "rm -rf .git",
]

# ======================================================================
# SENSITIVE FILE PATTERNS (绝不提交)
# ======================================================================

BANNED_FILE_PATTERNS = [
    ".env",
    ".env.local",
    ".env.production",
    "credentials",
    "*.key",
    "*.pem",
    "*.p12",
    "*.pfx",
    "id_rsa*",
    "id_ed25519*",
    "id_ecdsa*",
    "*.keystore",
    "secret*",
    "token*",
    "password*",
    "*.htpasswd",
]

# ======================================================================
# CONFIRMATION REQUIRED (必须用户确认后才能执行)
# ======================================================================

CONFIRM_REQUIRED = [
    ("delete branch", "git branch -d {branch}"),
    ("delete remote branch", "git push origin --delete {branch}"),
    ("force push", "git push --force"),
    ("delete tag", "git tag -d {tag}; git push --delete origin {tag}"),
    ("stash drop", "git stash drop"),
]

# ======================================================================
# PRE-COMMIT CHECKS (提交前必须检查)
# ======================================================================

PRE_COMMIT_CHECKS = """
在执行 git commit 前，必须检查:
1. git diff --cached --name-only 的结果中不包含 BANNED_FILE_PATTERNS 中的文件
2. 如果包含敏感文件，立即中止并警告用户
"""

# ======================================================================
# DEGRADATION RULES (降级策略)
# ======================================================================

DEGRADATION = {
    "gh_not_available": {
        "action": "Skip PR/Release creation, save output to local files only",
        "message": "GitHub CLI (gh) not found. PR/Release features unavailable. Install: https://cli.github.com/",
    },
    "no_remote": {
        "action": "Commit locally only, skip push and PR",
        "message": "No git remote configured. Changes committed locally only.",
    },
    "dirty_tree": {
        "action": "Stash changes before deployment, restore after",
        "message": "Working tree has uncommitted changes. Stashing before deployment.",
    },
}
