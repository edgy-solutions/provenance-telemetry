# ADR-0028 A version tag publishes to PyPI by Trusted Publishing

## Status

`built`. Enforced in this repository.

## Governs

| Kind | Ids |
|---|---|
| component | none |
| flow | none |

No component or flow of these records: it governs the release process.

## Decision

A `v*` tag builds the package. The job checks that the tag equals the packaged version, installs the wheel in a clean environment and imports it, attaches it to a GitHub Release, and publishes to PyPI through OIDC from the `pypi` environment. A failure fails the job; nothing is skipped.

## Why

A PyPI release cannot be replaced, so a mismatched version would be permanent. A release that quietly did not publish is the worst outcome the workflow names.

## Consequences

The trusted publisher on PyPI and the `pypi` environment are configured outside the repository. A newcomer cannot read them here.

## Evidence

Leaf paths are at `e84fd29a66c6207ae94131c78bb777e6ddfba3f6`; library paths are under `provenance_telemetry/`. Paths marked edgy-solutions/invincible-agent are at `6b3e8ef`.

| Claim | Source | Test | Status |
|---|---|---|---|
| The release job | `.github/workflows/build-package.yml:24-27`, `:49-71`, `:82-87`, `:92-106` | a CI job | `built` |
