---
name: configure-repository-governance
description: >-
  Create or audit CODEOWNERS, issue and pull-request templates, contribution
  policy, and repository governance files. Use when repository governance
  files are the requested outcome; not for hosted settings, CI pipelines,
  AGENTS.md, or general README work.
---

# Configure Repository Governance

Apply this workflow when repository governance files are the requested work.
Implicit activation selects guidance only; it does not authorize hosted or
local mutations beyond the user's request.

Resolve the hosting provider, supported file locations, current enforcement, and
requested policy. Read [governance formats](references/governance-formats.md).

Use provider-native syntax. Distinguish repository files from hosted branch
protection, approval, or settings enforcement. Do not invent signing, DCO/CLA,
conduct, disclosure, or ownership requirements without authority. Validate
paths, owners, template fields, and provider parsing.
