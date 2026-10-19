# Initial implementation decisions

## Constrained planning before arbitrary SQL

The initial live agent produces a typed intent and scope. SQL is compiled from the metric contract, then independently validated before execution. This makes unsupported questions explicit and eliminates target-grain joins from the model's responsibilities. It is narrower than the proposed arbitrary text-to-SQL agent. MCP supports ad hoc SQL through the same validator. Expand live SQL generation only after benchmark and semantic validation coverage are adequate.

## Session state in PostgreSQL

Conversation scope is persisted in `app.sessions`; LangGraph executes each bounded turn. A transaction-scoped advisory lock serializes concurrent turns from a session. Full graph checkpoint/resume is not implemented yet. The frontend uses an HTTP-only opaque cookie, with the server overwriting client-supplied session IDs.

## Reporting scope

Initial periods: Q3 2026, Q2 2026, YTD 2026 and FY 2025. All measures use synthetic reporting USD. The current generator uses fixed rep assignments and no launches; additional scenario realism remains future work.

## Evaluation boundary

The 60-case initial benchmark exercises guided mode with independent Python aggregation for revenue and targets. It covers conversation follow-ups, explicit refusals and clarification. It does not measure a live LLM, does not establish broad natural-language accuracy, and is not a held-out model comparison. Add frozen development/test splits before tuning model prompts.

## Local development

A dedicated PostgreSQL cluster runs on port 55433, web on 3031 and API on 8031. No existing database was altered. Runtime data and credentials are ignored by Git. For long-term use, move runtime storage out of a synced Drive folder onto local storage or managed PostgreSQL.
