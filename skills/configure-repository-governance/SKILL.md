---
name: configure-repository-governance
description: >-
  Use only when explicitly invoked by name. Create or audit CODEOWNERS, issue
  and pull-request templates, contribution policy, and repository governance
  files from provider rules. Excludes hosted settings mutations, CI pipelines,
  AGENTS.md, and general README work.
---

# Configure Repository Governance

Run this workflow only when the user explicitly invokes this skill by name. A
related keyword or an ordinary implementation request is not an invocation.

Resolve the hosting provider, supported file locations, current enforcement, and
requested policy. Read [governance formats](references/governance-formats.md).

Use provider-native syntax. Distinguish repository files from hosted branch
protection, approval, or settings enforcement. Do not invent signing, DCO/CLA,
conduct, disclosure, or ownership requirements without authority. Validate
paths, owners, template fields, and provider parsing.
