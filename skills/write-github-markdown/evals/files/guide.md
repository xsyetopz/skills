# Example App Guide

Example App syncs notes between devices.

## Contents

- Install
- Configuration & secrets
- Usage

## Install

Run the installer:

```
curl -fsSL https://example.com/install.sh | sh
```

## Configuration & secrets

**Environment variables**

| Name | Default | Purpose |
| --- | --- |
| `APP_PORT` | 8080 | Port to listen on |
| `APP_TOKEN` | | API token |

For the token format, click [here](#configuration-secrets).

## Usage

```
example-app sync --all
```
