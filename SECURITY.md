# Security Policy

## Supported Versions

Security fixes target `main` and the latest tagged release.

## Reporting a Vulnerability

Do not open a public issue with exploit details, private vault content, tokens, or personal paths.

Use GitHub private vulnerability reporting if it is available for this repository. If not, open a minimal public issue that says you need a private security channel, without including sensitive details.

## Scope

Cobsidian is a local workflow skill and helper-script project. Security-sensitive areas include:

- accidental leakage of private vault content
- unsafe handling of personal paths, tokens, or raw logs
- helper scripts that read or validate local Markdown files
- local write plans, backups, and manifests under a vault's `.cobsidian/transactions/` directory
- CI and GitHub Actions configuration

Transaction records can contain complete before/after note content. Keep `.cobsidian/` private, exclude it from version control and support bundles, and delete old transactions according to your own retention policy.
