# XsyeTopz Skills

My reusable skills for AI coding agents.

## Install

Use the [Vercel Skills CLI](https://skills.sh/docs/cli) with Bun to choose skills interactively:

```shell
bunx skills add xsyetopz/skills
```

List the skills and their descriptions without installing:

```shell
bunx skills add xsyetopz/skills --list
```

Install every skill for every detected agent:

```shell
bunx skills add xsyetopz/skills --all
```

To install globally, add `--global`. To install one skill, use `--skill <name>`.

Agents list installed skills within a budget of about 8,000 characters, so install one bundle
from [`bundles.toml`](bundles.toml) at a time rather than the whole catalog.

Update installed skills later with:

```shell
bunx skills update
```

## Skill Index

`just index` prints a list of skills with when to use each, to paste into CLAUDE.md or AGENTS.md.
Pass `--bundle NAME` once per bundle to list only the bundles you installed.
