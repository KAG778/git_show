"""
Git Helpers - 可复用的 Git 操作命令参考
========================================
本文件不是可执行代码，而是 Agent 可引用的 Git 命令片段。
Agent 在 SYSTEM_PROMPT 中可以引用这些命令模式。
"""

# ======================================================================
# Pre-flight Checks
# ======================================================================

GIT_IS_REPO = "git -C {path} rev-parse --is-inside-work-tree"
GIT_STATUS = "git -C {path} status --porcelain"
GIT_CURRENT_BRANCH = "git -C {path} branch --show-current"
GIT_DEFAULT_BRANCH = "git -C {path} symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'"
GIT_REMOTE_URL = "git -C {path} remote get-url origin"
GIT_BEHIND_COUNT = "git -C {path} rev-list --count HEAD..@{upstream}"

# ======================================================================
# Commit Analysis
# ======================================================================

GIT_LOG_RECENT = "git -C {path} log --oneline -20"
GIT_LOG_SINCE = "git -C {path} log --oneline --since='3 months ago'"
GIT_LOG_DIFF_MAIN = "git -C {path} log {default_branch}..HEAD --oneline"
GIT_DIFF_STAGED = "git -C {path} diff --staged --stat"
GIT_DIFF_UNSTAGED = "git -C {path} diff --stat"

# ======================================================================
# Tag & Release
# ======================================================================

GIT_TAG_LIST = "git -C {path} tag --sort=-creatordate"
GIT_LATEST_TAG = "git -C {path} describe --tags --abbrev=0"
GIT_LOG_SINCE_TAG = "git -C {path} log {latest_tag}..HEAD --oneline"

# ======================================================================
# Branch Operations
# ======================================================================

GIT_LIST_BRANCHES = "git -C {path} branch -a"
GIT_LIST_MERGED = "git -C {path} branch --merged {default_branch}"
GIT_CREATE_BRANCH = "git -C {path} checkout -b {branch_name}"
GIT_CHECKOUT = "git -C {path} checkout {branch_name}"

# ======================================================================
# Deploy Operations
# ======================================================================

GIT_ADD = "git -C {path} add {files}"
GIT_COMMIT = "git -C {path} commit -m {message}"
GIT_PUSH = "git -C {path} push -u origin {branch_name}"
GIT_STASH_PUSH = "git -C {path} stash push -m {message}"
GIT_STASH_POP = "git -C {path} stash pop"

# ======================================================================
# PR & Release (via gh CLI)
# ======================================================================

GH_CREATE_PR = "gh pr create --repo {owner}/{repo} --title {title} --body {body}"
GH_CREATE_RELEASE = "gh release create {tag} --title {title} --notes {notes} --repo {owner}/{repo}"
GH_PR_VIEW = "gh pr view {pr_number} --repo {owner}/{repo}"

# ======================================================================
# Owner/Repo Extraction
# ======================================================================

# Extract owner/repo from remote URL
# Works for: https://github.com/owner/repo.git or git@github.com:owner/repo.git
EXTRACT_OWNER_REPO = """
remote_url=$(git -C {path} remote get-url origin)
echo "$remote_url" | sed -E 's|.+(github.com[:/])([^/]+)/([^/.]+)(\\.git)?|\\2/\\3|'
"""
