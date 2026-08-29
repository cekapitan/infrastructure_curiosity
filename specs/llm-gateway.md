# LLM gateway

Repo: https://github.com/cekapitan/infrastructure_curiosity
Product: a portable proxy in front of the PR-docs agent.
This file is the spec. Do not treat it as an implementation ticket.
Depends on: `specs/pr-docs-agent.md`

## Goal

Every `grok -p`, `cursor-agent -p`, and later worker call Navy makes for a PR-docs run goes through one local gateway. The gateway logs the prompt and a redacted response, denies anti-jobs, and rate-limits per SHA and per hour. The worker still runs on this computer. The model backend is a config map, not the product.

## Non-goals

- Multi-account CPU or telemetry
- A new AWS account. Bedrock, AgentCore, Guardrails, and CloudWatch are not the control plane.
- Replacing Navy, grok, or cursor-agent
- Parallel grok and cursor-agent
- A third coding binary
- Prompt-only safety
- Hosting a model
- Weekly radar / `last30days`
- GitHub Actions LLM jobs, OIDC, merge queues

## Where it sits

Navy starts workers. The gateway does not. Preferred shape: LiteLLM-class or thin OpenAI-compatible reverse proxy on localhost. Bedrock is not the product. A system prompt is not a portability layer.

## Deny-list (fail-closed on argv)

no-merge, no-push-main, no-force, no-creds, no-provision, no-bare-agent, no-weekly, no-tree-dump.
Fork PRs: comment only.

## Rate limits

per SHA: 1 Navy run, 1 retry per path, at most 4 worker sessions. per clock hour: 12 worker sessions for this repo. Unproxied failover is forbidden.

## Success test

Throwaway PR. grok then cursor-agent both log through the gateway. Inject merge and push to main: denied. Credential read and terraform apply denied. Replay SHA refused. Dummy Azure-shaped endpoint is config only. No Bedrock SDK.
