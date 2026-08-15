# Security Policy

## Supported versions

Until the first tagged release, security fixes are applied to the latest `main` branch. After releases begin, the latest release will be the supported version unless stated otherwise.

## Reporting a vulnerability

Please do **not** publish API tokens, OAuth credentials, `credentials.json`, `token.json`, Chatwork message contents, or other sensitive information in a public Issue.

If the repository offers GitHub private vulnerability reporting under the **Security** tab, use that channel for vulnerabilities that could expose credentials or private data.

If private reporting is not available, open a public Issue containing only a short request for a private contact channel. Do not include exploit details or secrets in that Issue.

## Credential model

This project is designed so that user credentials remain on the machine running task_scheduler:

- Chatwork API tokens are stored in the local `accounts.yml` file.
- Google OAuth client credentials are stored in local `credentials.json`.
- Google OAuth tokens are stored in local `token.json`.
- These files are excluded by `.gitignore` and must never be committed.

If a credential is accidentally committed, revoke/rotate it immediately; deleting the file in a later commit is not sufficient because Git history may still contain it.
