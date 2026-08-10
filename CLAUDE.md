# Infrastructure Curiosity Context

This file mirrors `AGENTS.md` so the repository behaves consistently across coding agents.

## Purpose

Maintain a weekly AWS and infrastructure-tool radar sourced through `last30days`, verified with first-party documentation, and expressed as team-ready notes plus offline tests.

## Commands

- `make gate` - repository contracts, Terraform format/init-without-backend/validate/mocked tests, TFLint, ShellCheck, and Gitleaks.
- `make freshness` - verify that the newest dated weekly brief is no more than eight days old.

## Hard boundaries

No provisioning, cloud authentication, remote state, live provider calls, deployment pipelines, direct pushes to `main`, or automatic merges. Terraform examples are educational modules; every `.tftest.hcl` file uses provider mocks and plan-only runs.

## Research quality

Community discussion surfaces candidates. A dated upstream announcement, documentation page, changelog, or release establishes the claim. Recency labels must be honest: an established feature can be useful without being new.
