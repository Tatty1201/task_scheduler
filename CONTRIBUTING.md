# Contributing to task_scheduler

Thanks for your interest in improving task_scheduler.

This project is intentionally small and practical: the goal is to make Chatwork tasks reliably appear in Google Calendar without taking control away from the user after an event is created.

## Before you start

- Search existing Issues before opening a new one.
- Never post Chatwork API tokens, Google OAuth credentials, `token.json`, or other secrets in an Issue or Pull Request.
- For behavior changes, open an Issue first so the expected behavior can be discussed.

## Local setup

```bash
git clone https://github.com/Tatty1201/task_scheduler.git
cd task_scheduler
python -m venv .venv
```

Activate the virtual environment, then install dependencies:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

Run the tests:

```bash
python -m pytest -q
```

## Pull Requests

1. Create a branch from `main`.
2. Keep changes focused on one problem.
3. Add or update tests when behavior changes.
4. Update documentation if setup or user-visible behavior changes.
5. Confirm `python -m pytest -q` passes before opening the PR.

A good PR description explains:

- what problem it solves,
- what changed,
- how it was tested,
- whether there are any migration or configuration changes.

## Useful contribution areas

Good first contributions include:

- improving Windows/macOS/Linux setup instructions,
- adding test coverage,
- clearer error messages,
- safer configuration validation,
- support for account-specific calendar IDs,
- documentation and examples from real-world usage.

## Project principles

- **Insert-only by default:** once an event has been created, user edits in Google Calendar are respected.
- **No secrets in Git:** credentials and tokens must stay local.
- **Small, understandable changes:** reliability is more important than feature count.
- **Real usage first:** features should solve a concrete workflow problem.
