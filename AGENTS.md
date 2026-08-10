# Agent Guide

## Mission

Keep this repository a current, evidence-backed infrastructure radar. Discover with the installed `last30days` skill, corroborate with dated first-party sources, and propose reviewable documentation and test-only infrastructure examples.

## Required workflow

1. Read `README.md`, `CONTRIBUTING.md`, existing weekly notes, discoveries, examples, and tests.
2. Invoke the installed `last30days` skill for the current 30-day infrastructure/cloud-tool window. Do not replace it with generic search.
3. Treat community evidence as candidate discovery. Verify every accepted technical claim against dated first-party material.
4. Classify each accepted item as `new`, `operational-lesson`, `established`, or `tool-watch`.
5. Prefer one to three strong additions. A no-op is better than noise.
6. Add a static example only when it materially clarifies adoption.
7. Run `make gate`.

## Never do

- Never provision, deploy, preview, apply, destroy, refresh, import, or mutate infrastructure or state.
- Never access AWS, Azure, GCP, Kubernetes, Vault, Terraform Cloud, or Pulumi credentials.
- Never add Terraform backend blocks, provisioners, data sources that require live APIs, or deployment workflows.
- Never add GitHub OIDC or `id-token: write`.
- Never push directly to `main`, merge, auto-merge, or bypass CI.
- Never call an older capability a new release.

## Validation

Run `make gate`. Terraform tests must use mocked providers and `command = plan`. CI must remain read-only.

## Weekly publication

The scheduled agent may change only `README.md`, `docs/weekly/**`, `discoveries/**`, and `examples/**` (including `.tftest.hcl` tests). Contract tests under `tests/**` are part of the fixed safety boundary and require a human-authored change. After validation the agent may invoke only the fixed absolute publisher command in `automation/WEEKLY_PROMPT.md`; it must not call `git` or `gh` publication commands directly.
