# Margin Copilot: policy-agent

Margin Copilot policy agent: answers from the pricing policies the signed-in user may read, with citations such as `PP-04 §3.2`.

Part of **Margin Copilot**, a secure multi-agent pricing assistant on Azure, built as a personal learning project.

**Start here:** [margin-copilot/docs](https://github.com/margin-copilot/docs) explains how the whole system works and how the repos fit together.

## Contract

- A2A JSON-RPC at `/` (`SendMessage`), agent card at `/.well-known/agent-card.json`.
- Every call except the card needs a bearer token addressed to this service, with scope `access_as_user`, from an app on `ALLOWED_CALLERS`. In practice that's the orchestrator's OBO token, which carries the user's `groups` claim (this app registration requests it).
- The reply is one data part in the shared `AgentReply` contract: `{"answer": "...", "refusal": null, "citations": ["PP-04 §3.2"]}`. A failure is a JSON-RPC error with the fixed message `policy-agent failed`.
- Skill `policies`:
  - The service reads every clause the caller's groups may read from AI Search: `group_ids/any(...)` on the validated token's groups, and never test fixtures. Group IDs must be GUIDs before they reach the filter.
  - gpt-5-mini (Microsoft Foundry, reasoning effort medium) answers from those clauses only.
  - Code keeps only citations of clauses it handed the model, and sets the refusal: `no_data` when no clause covers the question, `no_access` when the token's group list overflowed (fail closed).

## Configuration

Names in `.env.example`. `ADAPTERS=azure|fake` (no default). Azure mode needs every one of: `TENANT_ID`, `CLIENT_ID` (this app registration), `AZURE_CLIENT_ID` (its managed identity, which reads the index and calls the model), `ALLOWED_CALLERS`, `PUBLIC_URL`, `SEARCH_ENDPOINT`, `SEARCH_INDEX`, `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL`.

## Run and test

```bash
uv sync
uv run pytest -q
ADAPTERS=fake uv run uvicorn --factory policy_agent.main:create_app --port 8000
```

Fake mode answers `fake policy-agent answers as user <oid>` with no model and no index. Pushing to `main` publishes `ghcr.io/margin-copilot/policy-agent:sha-<commit>`. Deployment: the private infra repo. The corpus and its indexer: the `data` repo. How access works: [security model](https://github.com/margin-copilot/docs/blob/main/security-model.md).

## License

MIT. See [LICENSE](LICENSE).
