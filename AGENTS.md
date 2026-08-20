# AGENTS.md — Guidelines for AI Agents Working on LIBA

## Project Goal
Build a clean, portfolio-ready Django backend for a social book platform,
with good architecture and consistent commit history on GitHub.

## Current Phase
Phase 0 → Project hygiene and proper structure (see Todo.md for details).

## General Rules
- Keep apps focused and single-responsibility (respect `apps/` boundaries)
- Prefer clean, readable code over clever code
- Do not over-engineer early phases
- Prefer simple, direct solutions unless there's a clear reason for complexity
- When suggesting changes, briefly explain why

## Explicit Boundaries (don't build yet)
- No Activity Feed, Community (book clubs), or Notifications until their phase
- No Discovery (search/trending/recommendations) until core + social are stable
- No PostgreSQL before Phase 0 cleanup is done; add it before starting Phase 3 (social)
- No Cart/Order/Payment — this project intentionally stays non-commerce

## Commit Style
Use conventional commits:
- `feat:` new feature
- `fix:` bug fix
- `refactor:` code change with no behavior change
- `chore:` tooling/config/deps
- `docs:` documentation only

## Workflow
- After any significant change, update `Todo.md`
- If project direction or key decisions change, update `Project_info.md`
- Keep this file (`AGENTS.md`) as the single source of truth for rules —
  do not create separate instruction files

## Learning Mode
The owner of this project is using it to actively learn backend/software
architecture, not just to get finished code. Because of this:
- Before implementing any non-trivial change, present the possible approaches
  (at least 2 when relevant) and the trade-offs between them, before picking one
- Don't silently pick "the standard way" — explain briefly why it's standard
  and what you'd give up by choosing an alternative
- Wait for explicit confirmation on the approach before writing code, unless
  the task is trivial (typo fix, formatting, obvious one-way decision)
- Keep these explanations short and practical — this is about decision-making,
  not a full lecture
