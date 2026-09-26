# Deployment guide

This guide explains how the release job builds the container image, pushes it to the internal registry, and rolls it out to the staging cluster before production.

## Build

The build runs in CI on every tag that matches `v*`, and it uses the same Dockerfile that developers use locally, so a local build is a faithful reproduction of what CI produces.

```sh
docker build --build-arg VERSION="$(git describe --tags)" --tag registry.internal.example/app:"$(git describe --tags)" .
```

## Rollout

Rollouts are described in the [runbook](https://wiki.example.com/runbooks/app-rollout#staging-first-then-production-with-a-manual-approval-step) and require a manual approval from the on-call engineer before production.

- Staging receives every tagged build automatically, and the smoke tests must pass there before anyone approves production.
- Production rollouts pause after the first availability zone so that error rates can be compared against the previous release.
