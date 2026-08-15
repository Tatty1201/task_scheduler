# Changelog

All notable changes to this project will be documented in this file.

The project follows semantic versioning for public releases.

## Unreleased

### Added

- Automated CI tests across supported Python versions.
- Unit tests for Chatwork API empty responses, task mapping, and sync-state behavior.
- MIT license and contribution/security documentation.
- GitHub Issue and Pull Request templates.

### Fixed

- Handle Chatwork `204 No Content` correctly when there are no matching tasks instead of attempting to parse an empty JSON body.

## 0.1.0 - planned

First public OSS release focused on reliable Chatwork-to-Google-Calendar insert-only synchronization.
