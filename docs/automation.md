# Weekly automation

The weekly loop runs locally because the installed `last30days` skill and its research configuration live on this Mac. GitHub Actions only validates committed artifacts and reports staleness; it does not perform research or receive research/cloud credentials.

## Installed schedule

The repository includes a macOS launchd job for **Monday at 07:17 in the Mac's local time zone**:

- label: `com.cekapitan.infrastructure-curiosity-weekly`
- definition: `automation/com.cekapitan.infrastructure-curiosity-weekly.plist`
- runner: `automation/run-weekly.sh`
- prompt: `automation/WEEKLY_PROMPT.md`
- standard log: `~/Library/Logs/infrastructure-curiosity-weekly.log`
- error log: `~/Library/Logs/infrastructure-curiosity-weekly.error.log`

Check the installed job:

```bash
launchctl print "gui/$(id -u)/com.cekapitan.infrastructure-curiosity-weekly"
```

The job is intentionally not started at installation time. To request a manual run later:

```bash
launchctl kickstart "gui/$(id -u)/com.cekapitan.infrastructure-curiosity-weekly"
```

To disable it without deleting repository files:

```bash
launchctl bootout "gui/$(id -u)/com.cekapitan.infrastructure-curiosity-weekly"
```

The committed plist targets this repository's absolute path on the owner's Mac. Update both the plist and the trusted absolute publisher command if the checkout moves.

## Execution model

1. The runner takes a lock and refuses to touch a dirty or non-`main` primary checkout.
2. It fetches `origin/main`, fast-forwards only, and creates a detached worktree at the fixed path `~/workspace/worktrees/infrastructure_curiosity-weekly`.
3. It starts an ephemeral Codex run with the workspace-write sandbox, network access for public research, no interactive approvals, and a scrubbed environment. A run-scoped trust override lets Codex load the repository's narrow execution rule at that stable path; cloud credential variables are not inherited.
4. The agent invokes the installed `last30days` skill, cross-checks official sources, edits only allowlisted research paths, and runs `make gate`.
5. Each completed research run writes a dated brief, even when it records no radar additions. A trusted publisher outside the temporary worktree rechecks the path and no-provision contracts, creates a weekly branch, pushes that branch, and opens a pull request. It never pushes or merges `main`.
6. A successful temporary worktree is removed. A failed worktree is preserved and its path is written to the error log for diagnosis.

The publisher executable is deliberately addressed by its absolute path. The scheduled agent can edit only its temporary worktree, so it cannot rewrite the executable it is allowed to run in the primary checkout.

## Codex Scheduled Tasks alternative

Codex Scheduled Tasks can also run the same versioned prompt. Configure a weekly task in the Codex app with this repository as the working directory, Monday at 07:17 America/New_York, and the contents of `automation/WEEKLY_PROMPT.md` as its instruction. Keep the Mac awake and the Codex app running when the task is due.

Use only one scheduler to avoid duplicate weekly branches. The launchd job is the active scheduler for this checkout.

## Security boundaries

- The runner constructs a minimal environment containing local identity, paths, locale, and Codex state. It does not pass AWS, Azure, GCP, Vault, Kubernetes, Terraform Cloud, Pulumi, or GitHub token variables.
- GitHub authentication comes from the existing `gh` credential store only when the trusted publisher opens a PR.
- `.codex/rules/weekly-publisher.rules` allows exactly the no-argument absolute publisher command. It does not allow arbitrary `git`, `gh`, or shell commands outside the sandbox.
- The publisher accepts only README, weekly-note, discovery, and example changes, including colocated `.tftest.hcl` example tests. It rejects fixed `tests/**` contract changes, deletions, links, unusual paths, executable additions, deployment primitives, and non-plan Terraform tests; then runs the full gate.
- GitHub workflows have `contents: read`, no OIDC, no cloud login, no deployment job, and no auto-merge.

## Failure handling

The automation fails closed. Dirty primary checkouts, divergent history, duplicate weekly branches, failed research, validation errors, publisher-policy violations, push failures, and PR-creation failures all stop the run. No failure path merges code or mutates cloud infrastructure.

Inspect the error log and the preserved temporary worktree. Resolve the cause manually, retain any useful research, and remove the worktree only after reviewing it:

```bash
git -C /Users/codyes18/workspace/github.com/cekapitan/infrastructure_curiosity worktree list
```
