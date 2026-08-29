# PR documentation agent

Repo: https://github.com/cekapitan/infrastructure_curiosity
Product: cost-efficient docs on a pull request, from the diff only.
This file is the spec. Do not treat it as an implementation ticket.

## Goal

When a PR is opened or updated, Navy (Grok Bot) runs one coding path against the PR diff. That path documents what changed. Humans still review. The agent never merges.

Coding bar: pstack / poteto-mode. One job. Unslopped. Verified against the diff. Superpowers is not the bar.

## Non-goals

- Weekly radar research (`last30days`, discovery JSON, first-party corroboration). That is the existing local weekly loop.
- Writing, reviewing, or rewriting IaC or application code.
- Dumping or summarizing the whole repo.
- GitHub Actions that run the model, OIDC, merge queues, auto-merge.
- Parallel grok and cursor-agent runs.
- A third coding binary.

## Trigger

GitHub `pull_request` `opened` or `synchronize` on `cekapitan/infrastructure_curiosity`.

Navy is the listener. It uses existing `gh` auth on this computer (notifications or `gh pr view`). Do not add a workflow that checks out the tree, mints `id-token`, or sends cloud credentials. Current CI stays `contents: read`.

One run per PR head SHA. Ignore comment-only updates. Skip if labeled `skip-docs-agent`, if the SHA already has a docs comment from this agent, or if the diff is docs-complete (README / `docs/**` already match the change).

## Inputs

Pass the diff, not a repo dump.

Required:

```
gh pr diff <n>
gh pr view <n> --json number,title,body,files,baseRefName,headRefName,isCrossRepository,url,headRefOid
```

Allowed extra reads: files named in the diff, plus at most one existing docs target that would be edited (`README.md` section, sibling under `docs/`, or `docs/automation.md`).

Do not pass the full tree, `git archive`, full history, `last30days` output, or unrelated examples.

## Outputs

Always: a PR comment that states

- what the diff changed
- docs to add, or why none
- path used (`grok` or `cursor-agent`)
- Notion task URL
- `No infrastructure was provisioned.`

Optional patch on the **PR branch** (never `main`):

- edit `README.md` or existing `docs/**` when that is the natural home
- otherwise add `docs/drafts/pr-<n>-<shortsha>.md`

Fork PRs (`isCrossRepository: true`): comment only. No push.

If a patch is pushed, run `make gate` first. If gate fails for reasons outside the docs files, comment only and do not push.

## Anti-jobs

Never:

- merge, auto-merge, approve, or bypass reviews
- push to `main`
- force-push (`--force`, `--force-with-lease`)
- rewrite history
- invoke bare `agent` (Grok Build owns that name)
- start grok and cursor-agent on the same SHA in parallel
- obtain, print, or use AWS, Azure, GCP, Vault, Kubernetes, Terraform Cloud, or Pulumi credentials
- provision, apply, deploy, preview, destroy, refresh, import, or add OIDC / `id-token: write`
- call the weekly publisher (`.codex/bin/publish-weekly-pr`)
- edit `tests/**` contract tests
- invent radar items or backdate evidence
- dump the repo into the prompt

## Two-path failover

Navy starts path 1, checks the result, starts path 2 only if path 1 failed. Failover is serial. Not a bake-off.

| Order | Command | Meter | Role |
| --- | --- | --- | --- |
| 1 | `grok -p` | SuperGrok Heavy | default, this computer |
| 2 | `cursor-agent -p` | Cursor Ultra | failover only |

Success: zero exit, PR comment posted, proposal matches the diff, no anti-job fired. Optional patch, if any, is on the PR branch and `make gate` passed.

Failure: non-zero exit, empty or off-diff comment, worker attempted an anti-job, or a needed docs proposal is missing.

Retry a given path at most once per SHA. Do not start path 2 after a successful path 1. Do not install or call any other agent.

Worker prompt (both paths): pstack / poteto-mode. Read the supplied diff. Name the docs gap. Post the comment. Patch docs only when durable. Stop.

## Notion Tasks

Database: Tasks. Per PR SHA, three rows in this order:

1. `grok`
2. `cursor-agent`
3. `agent run`

Status values: `Todo` | `Doing` | `Blocked` | `Done`.

| Event | grok | cursor-agent | agent run |
| --- | --- | --- | --- |
| PR arrives | Todo | Todo | Todo |
| Navy starts grok | Doing | Todo | Doing |
| grok succeeds | Done | Todo (unused) | Done |
| grok fails | Blocked | Doing | Doing |
| cursor-agent succeeds | Blocked | Done | Done |
| both fail | Blocked | Blocked | Blocked |

Put the error on the Blocked row. Link the `agent run` page in the PR comment.

## Success test

Open a throwaway PR that adds an example or script with no docs.

Pass:

1. Navy starts `grok -p` only.
2. The worker prompt contains `gh pr diff` output, not a full tree.
3. A PR comment names the missing docs.
4. If a patch is made, it lands on the PR branch only.
5. `main` is unchanged. No merge. No force-push. No cloud env in the process.
6. Notion: grok `Done`, cursor-agent `Todo`, agent run `Done`.
7. Failover drill: kill grok mid-run. Navy starts `cursor-agent -p` only after that failure. grok is `Blocked`. Comment still posts. `main` still untouched.

Fail: both paths run after a healthy grok; bare `agent` is invoked; `main` moves; credentials appear; the prompt was a repo dump.

## Cost notes

- Diff-sized context is the cost control. Do not buy a full checkout for the model.
- Pay SuperGrok Heavy first. Pay Cursor Ultra only on failure. Never both for one SHA.
- Skip lockfile, typo, badge, and already-documented weekly-radar PRs.
- One run per head SHA.
- Comment is cheaper than a patch. Patch only when the docs will still be true after merge.
- No extra models, no Superpowers pack, no GitHub-hosted LLM job.
