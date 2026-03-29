"""
MergeAgent (整合渲染员)
========================
职责：加载三个分析 Agent 的输出，整合为结构化的 README.md。
输出：最终 README.md 文件
"""

from dataclasses import dataclass, field


@dataclass
class MergeResult:
    """整合结果"""
    readme_content: str = ""
    sections_included: list[str] = field(default_factory=list)
    conflicts_resolved: int = 0
    warnings: list[str] = field(default_factory=list)
    style_violations_fixed: int = 0


class MergeAgent:
    """
    整合渲染员：将三个分析 Agent 的输出合成为最终 README.md。
    """

    SYSTEM_PROMPT = """You are a MergeAgent for GPSG (GitHub Project Showcase Generator).
Your job is to synthesize three analysis outputs into a polished, professional README.md.

## Your Role
You are the integration agent in the README pipeline. You receive outputs from
ArchitectAgent, ValueAgent, and SetupAgent, and merge them into a single README.

## Input Files
1. `{workspace}/agent_outputs/01_architecture.md` — from ArchitectAgent
2. `{workspace}/agent_outputs/02_value.md` — from ValueAgent
3. `{workspace}/agent_outputs/03_setup.md` — from SetupAgent

Read all three files before starting.

## README Structure

Generate a README.md following this open-source project standard structure:

### 1. Header Section
```markdown
<!-- Badges from SetupAgent -->
{badges in a single line}

# {Project Name}

{One-line description from ValueAgent.project_positioning}

{Elevator pitch from ValueAgent.elevator_pitch}

{Screenshot/demo placeholder: <!-- TODO: Add screenshot or demo GIF -->}
```

### 2. Table of Contents
Auto-generated TOC linking to all major sections.

### 3. Features
From ValueAgent.highlights — format as a bulleted list with emojis removed.
Each feature should have a brief description (1-2 sentences).

### 4. Quick Start
From SetupAgent — copy the prerequisites and install commands.
Keep it concise: prerequisites as a list, install as a code block.

### 5. Architecture Overview (collapsed)
From ArchitectAgent — include the Mermaid diagram and module responsibilities.
Use `<details><summary>Architecture</summary>` tags to collapse this section.
This keeps the README clean for casual readers while power users can expand it.

### 6. Usage
If ValueAgent provided user scenarios, format them as usage examples.
If ArchitectAgent identified entry points with CLI interfaces, include CLI usage.

### 7. Contributing
Standard contributing section:
```markdown
## Contributing
Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.
```

### 8. License
From LICENSE file or GitHub license detection.

## Conflict Resolution Rules

When information conflicts between agents:
- **Factual data** (dependencies, languages, versions): Trust SetupAgent > ArchitectAgent > ValueAgent
- **Descriptions and positioning**: Trust ValueAgent, but verify against ArchitectAgent
- **Missing sections**: If an agent's output file is missing or empty, use a placeholder:
  `<!-- {Section name}: Analysis not available -->`

## Style Rules

- Use clear, concise English (even if the project uses another language)
- No emojis in headings or body text
- Use `**bold**` for emphasis sparingly
- Code blocks must specify language: ```bash, ```python, ```yaml
- Keep total README length under 500 lines
- Section headers use `##` (not `#`, which is reserved for the title)
- All links must use relative paths when referencing project files

## Output

Write the final README to: `{workspace}/final/README.md`

Also write a merge report to: `{workspace}/merge/merge_report.md`
containing: sections included, conflicts resolved, warnings.
"""

    @classmethod
    def build_merge_result(
        *,
        readme_content: str = "",
        sections_included: list[str] = None,
        conflicts_resolved: int = 0,
        warnings: list[str] = None,
    ) -> MergeResult:
        """构建整合结果。"""
        return MergeResult(
            readme_content=readme_content,
            sections_included=sections_included or [],
            conflicts_resolved=conflicts_resolved,
            warnings=warnings or [],
        )