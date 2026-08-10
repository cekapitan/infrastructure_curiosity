# Security policy

This repository contains public research and non-deployable, test-only infrastructure examples. Do not report ordinary research disagreements as security vulnerabilities.

For a vulnerability in the automation boundary, publisher, workflow permissions, or repository tooling, use GitHub's private vulnerability-reporting feature for `cekapitan/infrastructure_curiosity`. Do not include real cloud credentials, secrets, production state, customer data, or exploit details in a public issue.

The project does not provision infrastructure and does not require cloud credentials. If a contribution introduces a credential, state file, remote backend, deployment path, or other live-control-plane dependency, treat that as a defect and remove the sensitive material from Git history before publication.
