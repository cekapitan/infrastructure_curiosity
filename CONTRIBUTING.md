# Contributing

Infrastructure Curiosity accepts practices that are timely, useful to an infrastructure team, corroborated, and safe to demonstrate without deploying anything.

## Evidence bar

Every discovery record must include:

- a stable ID and category;
- discovery date and evidence window;
- at least one dated first-party source;
- a concise description of what changed or why an established capability is newly relevant;
- operational value, caveats, and a concrete adoption question;
- confidence and disposition;
- a link to a test-only example, or a reason documentation is enough.

Community posts and `last30days` output are leads, not proof. Use first-party release notes, service documentation, provider changelogs, or upstream repositories to accept technical claims. Do not call an older feature "new."

## Safe changes

Permitted examples are static and offline:

- Terraform formatting, validation, and mocked `command = plan` tests;
- policy tests and parsers;
- CloudFormation linting;
- Helm lint/template or manifest schema validation;
- Ansible lint and syntax checks without inventory access.

Do not add cloud credentials, remote backends, provider authentication, state operations, cluster access, deploy/apply/destroy commands, OIDC permissions, or auto-merge.

## Pull request checklist

- [ ] Sources are dated and first party.
- [ ] The README and weekly brief use the correct recency label.
- [ ] The discovery ID and canonical source URLs are unique.
- [ ] Examples are minimal and test-only.
- [ ] `make gate` passes.
- [ ] The PR states: `No infrastructure was provisioned.`
