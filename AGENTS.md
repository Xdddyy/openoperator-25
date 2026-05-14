# AGENTS.md

## Workflow Summary / 工作流速查表

| Workflow | Name | Best used for | Example command |
|---|---|---|---|
| Workflow A | Read-Only Analysis | Understanding project structure, code logic, call chains, or root causes without editing files. | Use Workflow A: Analyze the current project structure and main call chain in read-only mode. Do not modify files. |
| Workflow B | Plan First, Then Wait | Getting a safe implementation plan before any code changes. | Use Workflow B: Analyze this issue and propose an implementation plan. Do not modify code directly. |
| Workflow C | Implement With Review | Normal feature implementation or bug fixing with code changes and final review. | Use Workflow C: Analyze and implement this feature, then ask reviewer to review the git diff. |
| Workflow D | Debug and Fix | Handling errors, failed commands, test failures, API errors, or runtime exceptions. | Use Workflow D: Diagnose and fix this error, then ask reviewer to review the changes. |
| Workflow E | Review Only | Reviewing current `git diff`, selected files, or provided code without modifying anything. | Use Workflow E: Review the current git diff only. Do not modify files. |
| Workflow F | Research Then Plan | Checking external documentation, API behavior, library usage, or compatibility before planning. | Use Workflow F: Research the relevant documentation first, then propose an implementation plan. Do not modify code directly. |
| Workflow G | Refactor Safely | Refactoring a module or component while preserving existing behavior. | Use Workflow G: Safely refactor this module while preserving behavior, then review the diff. |
| Workflow H | Add Tests | Adding or improving tests for an existing feature or bug fix. | Use Workflow H: Add tests for this feature and run the relevant test commands. |
| Workflow I | Local Bridge / Provider Debugging | Debugging OpenCode, uvicorn bridge, model routing, API keys, base URLs, SSL, or streaming issues. | Use Workflow I: Debug the OpenCode local uvicorn bridge failure. Do not expose keys. |
| Workflow J | Quick Small Change | Very small, low-risk changes that do not require a full planning stage. | Use Workflow J: Make this small change, then ask reviewer to review the diff. |

---

## MCP Server Tools / MCP 工具总表

All MCP server tools available to this project should be recorded in this section. These tools are part of the normal agent workflow. When a workflow encounters a file type, data source, or task that matches one of these tools, the agent should automatically use the appropriate MCP tool instead of asking the user to perform manual preprocessing.

| MCP Server | Tool | Best used for | Auto-use condition | Output / constraint |
|---|---|---|---|---|
| `pdf-tools` | `pdf_to_text` | Convert PDF documents into text for downstream analysis. | Automatically use when a workflow needs to read, summarize, analyze, or extract information from a `.pdf` file. | Save extracted text under `docs_extracted/`; do not modify the original PDF. |
| `pdf-tools` | `read_text_preview` | Quickly preview extracted `.txt` or `.md` files. | Automatically use after text extraction, or when a large text document only needs an initial inspection. | Return a bounded preview first; use normal file reading for deeper analysis if needed. |
| `image-tools` | `read_image` | Read and extract text/OCR content from image files (`.jpg`, `.png`, `.gif`, `.bmp`, etc.). | Automatically use when the user references an image file and the model cannot natively view images. | Extract visual content as text description; do not modify the original image. |

## MCP Auto Invocation Rule

MCP tools are workflow tools, not separate manual steps.

When executing any workflow:

1. Check whether the task matches an available MCP tool.
2. If a matching MCP tool exists and the operation is read-only or produces a safe derived artifact, use it automatically.
3. Do not ask the user to manually convert, preprocess, or inspect files when an MCP tool can do it.
4. Do not claim that a file cannot be read before checking relevant MCP tools.
5. Save generated derived artifacts under a clearly named project subdirectory such as `docs_extracted/`.
6. Never modify original source documents unless explicitly requested.
7. For tools that may modify source files, delete files, call external services, or perform costly operations, ask the user first.
8. After using an MCP tool, continue the selected workflow using the generated or returned artifact.

---

This file defines how OpenCode agents should work in this project.

---

## Workflow Usage

The user may choose one of the workflows above by name. When a workflow is selected, follow the corresponding role sequence and constraints.

---

## Workflow A: Read-Only Analysis

**只读分析：用于理解项目结构、调用链、错误原因或设计逻辑，不修改文件。**

Use this workflow when the user only wants to understand the project, code structure, error cause, or design logic.

Role sequence:

1. `planner`

Rules:

- Do not edit files.
- Do not run destructive commands.
- Inspect only relevant files.
- Explain the project structure, call chain, or root cause clearly.
- End with a concise conclusion and optional next steps.

Example user command:

```text
Use Workflow A: analyze the current project structure and main call chain without modifying files.
```

---

## Workflow B: Plan First, Then Wait

**先规划后等待：用于高风险或不确定任务，先给方案，等用户确认后再实现。**

Use this workflow when the user wants a safe implementation plan before any code change.

Role sequence:

1. `planner`
2. Stop and wait for user confirmation.

Rules:

- Do not edit files.
- Do not run modification commands.
- Identify relevant files.
- Explain the root cause.
- Provide a minimal implementation plan.
- Explicitly list which files would be changed.
- Wait for user approval before using `coder`.

Example user command:

```text
Use Workflow B: analyze this issue and produce a modification plan without directly changing code.
```

---

## Workflow C: Implement With Review

**实现并审查：用于常规开发任务，先规划，再编码，最后审查 diff。**

Use this workflow for normal coding tasks where code modification is expected.

Role sequence:

1. `planner`
2. `coder`
3. `reviewer`

Rules:

- `planner` first analyzes the task and proposes a minimal plan.
- `coder` implements only the approved or clearly necessary changes.
- `coder` should keep changes small and scoped.
- `reviewer` reviews `git diff` after implementation.
- Final response must include:
  - files changed
  - why they were changed
  - verification performed
  - remaining risks or manual checks

Example user command:

```text
Use Workflow C: analyze and implement this feature, then ask reviewer to review the git diff.
```

---

## Workflow D: Debug and Fix

**定位并修复：用于报错、测试失败、API 错误或运行时异常，先定位原因再修复。**

Use this workflow when there is an error log, failing command, test failure, API error, or runtime exception.

Role sequence:

1. `debugger`
2. `planner`
3. `coder`
4. `reviewer`

Rules:

- `debugger` first analyzes the error and identifies the likely cause.
- `debugger` may suggest diagnostic commands, but should explain them before running.
- `planner` converts the diagnosis into a minimal fix plan.
- `coder` applies the fix.
- `reviewer` reviews the final diff.
- Do not guess if the issue can be verified with a focused command.

Example user command:

```text
Use Workflow D: diagnose this error, fix it, and ask reviewer to review the final diff.
```

---

## Workflow E: Review Only

**只审查：用于提交前检查或代码质量审查，不产生新的代码修改。**

Use this workflow when the user only wants code review and does not want modifications.

Role sequence:

1. `reviewer`

Rules:

- Do not edit files.
- Review current `git diff`, selected files, or provided code.
- Focus on:
  - correctness
  - maintainability
  - security
  - compatibility
  - regression risk
  - unintended changes
- Provide actionable comments.
- Do not rewrite the code unless explicitly requested.

Example user command:

```text
Use Workflow E: review the current git diff without modifying files.
```

---

## Workflow F: Research Then Plan

**先查资料再规划：用于需要查外部文档、API 行为、框架用法或兼容性的问题。**

Use this workflow when external documentation, API behavior, framework usage, or library compatibility needs to be checked.

Role sequence:

1. `researcher`
2. `planner`
3. Stop and wait for user confirmation.

Rules:

- `researcher` checks relevant documentation or references.
- `researcher` must not edit files.
- `planner` summarizes findings and proposes an implementation plan.
- Do not implement until the user confirms.

Example user command:

```text
Use Workflow F: check relevant documentation, then propose an implementation plan without changing code.
```

---

## Workflow G: Refactor Safely

**安全重构：用于重构模块或整理结构，要求保持原有行为不变。**

Use this workflow for refactoring tasks.

Role sequence:

1. `planner`
2. `coder`
3. `debugger`
4. `reviewer`

Rules:

- `planner` identifies the current structure and refactoring scope.
- Refactor only the requested area.
- Preserve public behavior.
- Do not introduce unrelated style changes.
- `coder` applies small incremental changes.
- `debugger` runs or suggests focused verification.
- `reviewer` checks whether behavior was preserved.

Example user command:

```text
Use Workflow G: refactor this module safely, preserve behavior, and review the final diff.
```

---

## Workflow H: Add Tests

**补充测试：用于为功能、bug 修复或边界行为补充测试，并验证测试质量。**

Use this workflow when adding or improving tests.

Role sequence:

1. `planner`
2. `coder`
3. `debugger`
4. `reviewer`

Rules:

- `planner` identifies the behavior that should be tested.
- `coder` adds minimal focused tests.
- `debugger` runs the relevant test command or explains why it cannot run.
- `reviewer` checks whether tests are meaningful and not brittle.

Example user command:

```text
Use Workflow H: add focused tests for this feature and run the relevant tests.
```

---

## Workflow I: Local Bridge / Provider Debugging

**本地 bridge / provider 排错：用于 OpenCode、uvicorn bridge、模型路由、key、base URL、SSL、streaming 等问题。**

Use this workflow for OpenCode, uvicorn bridge, model provider, API key, base URL, model routing, or streaming issues.

Role sequence:

1. `debugger`
2. `planner`
3. `coder`
4. `reviewer`

Rules:

- First determine whether the issue is:
  - local bridge authentication
  - upstream API key
  - base URL
  - endpoint path
  - model name
  - SSL verification
  - request schema
  - response parsing
  - streaming behavior
- Never print real API keys.
- Check whether the model is allowed by the local bridge whitelist.
- Use focused curl commands when useful.
- If code changes are needed, keep them minimal.
- `reviewer` must check that GPT, Claude, and unsupported-model behavior are not broken.

Example user command:

```text
Use Workflow I: debug why OpenCode cannot call the local uvicorn bridge without exposing keys.
```

---

## Workflow J: Quick Small Change

**快速小修改：用于非常小、低风险、目标明确的修改，若范围扩大则切换到 Workflow C。**

Use this workflow for very small, low-risk changes.

Role sequence:

1. `coder`
2. `reviewer`

Rules:

- Only use this workflow when the change is clearly small.
- `coder` should explain the intended change before editing.
- `reviewer` checks the final diff.
- If the task is not actually small, switch to Workflow C.

Example user command:

```text
Use Workflow J: make this small change and ask reviewer to check the diff.
```

---

## Workflow Selection Rule

If the user explicitly names a workflow, follow that workflow.

If the user does not name a workflow:

- Use Workflow A for explanation-only questions.
- Use Workflow B when the task is unclear or risky.
- Use Workflow C for normal implementation tasks.
- Use Workflow D for errors, failures, and exceptions.
- Use Workflow E for review-only requests.
- Use Workflow F when external documentation is needed.
- Use Workflow I for model provider, API bridge, OpenCode, or local uvicorn issues.

When uncertain, choose the safer workflow and start with `planner`.

---

## Project Working Principle

For any non-trivial task, do not directly modify files. First understand the project structure, identify the relevant files, explain the cause of the problem, then propose a minimal implementation plan.

Use the configured agents according to their roles:

- `planner`: analyze the project, inspect relevant files, and produce an implementation plan. Do not modify files.
- `coder`: implement approved changes by editing files and running focused verification commands.
- `debugger`: investigate errors, inspect logs, run diagnostic commands, and propose fixes.
- `reviewer`: review code changes for correctness, maintainability, security, compatibility, and regressions. Do not modify files.
- `researcher`: search documentation or external references when needed. Do not modify files.

The current OpenCode configuration maps these roles to different models:

- `planner`, `debugger`, and `researcher` use DeepSeek directly.
- `coder` uses GPT through the local uvicorn bridge.
- `reviewer` uses Claude through the local uvicorn bridge.

---

## Default Workflow

For complex coding tasks, follow this workflow:

1. Use `planner` first.
   - Read the project structure and relevant files.
   - Identify the root cause or design problem.
   - Produce a concise plan.
   - Do not modify files.

2. Use `coder` only after the plan is clear.
   - Modify only the necessary files.
   - Keep patches small and reviewable.
   - Explain what will be changed before editing.
   - Do not rewrite unrelated code.

3. Use `debugger` when there are errors.
   - Inspect logs, stack traces, command output, and configuration.
   - Suggest focused verification commands.
   - Ask before running commands that may take time or change state.
   - Do not guess when the issue can be verified.

4. Use `reviewer` before final completion.
   - Review `git diff`.
   - Check for unintended changes.
   - Check security, compatibility, maintainability, and regression risks.
   - Do not modify files directly.

5. Summarize the final result.
   - State what changed.
   - State what was verified.
   - State what still needs manual confirmation, if any.

---

## Safety Rules

Never expose, print, copy, summarize, or modify real API keys or secrets.

Do not read these files unless explicitly instructed:

- `.env`
- `.env.*`
- files containing API keys, tokens, passwords, credentials, or private keys

Do not run destructive commands unless explicitly requested by the user. This includes:

```bash
rm -rf
sudo
git reset --hard
git clean -fd
chmod -R
chown -R
```

Do not push code automatically:

```bash
git push
```

Always ask before:

- editing files
- installing packages
- running long commands
- modifying configuration files
- changing model/provider routing
- deleting files
- changing environment variables
- running commands outside the current project directory

---

## File Editing Rules

When modifying files:

- Change the smallest necessary scope.
- Preserve the existing project structure.
- Preserve naming conventions and code style.
- Do not introduce unrelated refactors.
- Do not change public behavior unless the task requires it.
- Do not silently remove existing features.
- Do not modify generated files unless necessary.
- After editing, inspect the diff.

Before final response, run or suggest:

```bash
git status
git diff
```

---

## Debugging Rules

When debugging a failure, check in this order:

1. Reproduce the error.
2. Identify the failing command, endpoint, file, or function.
3. Inspect the minimal relevant code path.
4. Check environment variables and configuration names without revealing secret values.
5. Check request path, model name, base URL, API type, and response parsing.
6. Propose the smallest fix.
7. Verify the fix with a focused command.

For model provider or bridge issues, check:

1. API key existence, not the raw key value.
2. Base URL.
3. Endpoint path.
4. Model name.
5. Request body schema.
6. Response body schema.
7. Streaming vs non-streaming behavior.
8. SSL verification settings.
9. Local bridge authentication.
10. Upstream provider routing.

---

## Response Style

When responding, be concise but complete.

For code changes, include:

- files changed
- reason for each change
- verification performed
- remaining risks or manual checks

Do not over-explain obvious code. Focus on the decisions that matter.

---
