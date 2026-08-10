# Weekly infrastructure-curiosity run

Work only in this repository. Your job is to prepare a small, evidence-backed, review-only update about AWS, cloud infrastructure, and infrastructure tooling.

## Required research

1. Read `README.md`, `CONTRIBUTING.md`, `AGENTS.md`, all existing discovery records, the newest weekly briefs, examples, and tests. Avoid duplicates.
2. Invoke the installed `$last30days` skill for the rolling 30-day window. Use its discovery workflow and source reporting; do not replace it with an ordinary web search.
3. Search dated first-party release sources to catch important changes the community scan missed. Cover AWS What's New and relevant upstream release notes or changelogs for Terraform/OpenTofu, the AWS provider, CloudFormation/CDK, Pulumi, Crossplane, Kubernetes, Helm, Ansible, Packer, policy-as-code, observability, FinOps, secrets, identity, and agent infrastructure.
4. Use community evidence only to nominate leads. Verify each accepted technical claim against a dated first-party source. If a claim cannot be corroborated, reject or defer it in the weekly brief.

## Selection bar

- Prefer one to three items that create a concrete adoption question for an infrastructure team. A no-op is better than noise.
- Label items exactly: `new`, `operational-lesson`, `established`, or `tool-watch`.
- Never describe an older feature as new. Established capabilities are welcome when newly relevant, but label their original release date plainly.
- Record rejected and deferred leads with a short reason so later runs do not recycle hype.
- For each accepted item, update the README, add a dated brief under `docs/weekly/`, and add or update a canonical JSON record under `discoveries/`.
- Add an example only when it clarifies the adoption decision. Examples must be static and test-only.
- Every completed research run adds one dated weekly brief and advances the README's latest-brief link. If no item clears the bar, use a `No additions` section and document what was checked; do not fabricate a discovery record or example.

## Hard safety boundaries

- Do not obtain, inspect, or use cloud, cluster, Vault, Terraform Cloud, Pulumi, or deployment credentials.
- Do not provision, deploy, preview, apply, destroy, refresh, import, mutate state, contact a cloud control plane, or configure a remote backend.
- Do not add deployment workflows, GitHub OIDC, `id-token: write`, auto-merge, or a path that pushes to `main`.
- Terraform tests must use mocked providers and `command = plan` only.
- You may modify only `README.md`, `docs/weekly/**`, `discoveries/**`, and `examples/**`. Add Terraform tests beside examples as `.tftest.hcl`; do not edit the fixed contract tests under `tests/**`.
- Do not modify `automation/**`, `.codex/**`, `.github/**`, `scripts/**`, `Makefile`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, or `LICENSE`.

## Validate and publish

1. Run `make gate` and fix only in-scope failures.
2. If research could not complete reliably, leave the repository unchanged and report the exact failure. An evidence-backed run with no accepted item is still a valid brief-only update.
3. Invoke exactly this no-argument publisher for the completed weekly brief:

   `/Users/codyes18/workspace/github.com/cekapitan/infrastructure_curiosity/.codex/bin/publish-weekly-pr`

   Do not invoke `git`, `gh`, or any other publication command yourself. The publisher revalidates the diff, creates an automation branch, pushes that branch, and opens a pull request for human review. It cannot merge or push to `main`.
4. End with accepted items, rejected/deferred leads, validation results, and the PR URL or a clear no-op reason.
