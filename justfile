set dotenv-load := false

cache := env("SKILLS_CACHE_DIR", env("HOME") + "/.cache/xsyetopz-skills")
venv := cache + "/validation-venv"
bun_cache := cache + "/bun"

default: validate

hooks:
    bun install --frozen-lockfile
    bunx --bun --no-install lefthook validate
    bunx --bun --no-install lefthook install

provision:
    mkdir -p "{{ cache }}" "{{ bun_cache }}"
    test -x "{{ venv }}/bin/python" || python3 -m venv "{{ venv }}"
    # Git hooks export GIT_INDEX_FILE; pip's git clone of skills-ref would
    # otherwise write its tree into the index being committed.
    env -u GIT_DIR -u GIT_INDEX_FILE -u GIT_WORK_TREE -u GIT_PREFIX \
        "{{ venv }}/bin/python" -m pip install --disable-pip-version-check -r requirements-validation.txt

# skills-ref rules, minus the documented Claude Code frontmatter fields.
skills: provision
    "{{ venv }}/bin/python" scripts/validate_spec.py skills/*

metadata: provision
    "{{ venv }}/bin/python" scripts/validate_repository.py

# `agents/` holds each skill's Codex metadata (agents/openai.yaml).
skill-lint: provision
    "{{ venv }}/bin/python" scripts/skill_lint.py --strict --allow agents

# pre-commit-hooks checks: large files, private keys, case conflicts,
# symlinks, and shebangs against the executable bit.
hygiene: provision
    "{{ venv }}/bin/python" scripts/check_hygiene.py

# Secrets in staged changes, unstaged changes, and history.
secrets:
    if command -v gitleaks >/dev/null; then gitleaks git --no-banner --redact --pre-commit --staged . && gitleaks git --no-banner --redact --pre-commit . && gitleaks git --no-banner --redact .; else echo 'SKIP gitleaks: unavailable'; fi

markdown:
    BUN_INSTALL_CACHE_DIR="{{ bun_cache }}" bunx --bun markdownlint-cli2 "*.md" "skills/**/*.md" "docs/**/*.md"

tests: provision
    "{{ venv }}/bin/python" scripts/run_python_tests.py
    BUN_INSTALL_CACHE_DIR="{{ bun_cache }}" bun test skills

assets: provision
    "{{ venv }}/bin/python" scripts/validate_assets.py

justfiles: provision
    "{{ venv }}/bin/python" skills/write-justfile/scripts/check_justfiles.py justfile skills

python-lint: provision
    "{{ venv }}/bin/ruff" check --no-cache scripts skills
    "{{ venv }}/bin/ruff" format --no-cache --check --exclude '*.md' scripts skills

python-types: provision
    BUN_INSTALL_CACHE_DIR="{{ bun_cache }}" bunx --bun pyright --pythonpath "{{ venv }}/bin/python"

shell:
    if command -v shellcheck >/dev/null; then find skills scripts -type f -name '*.sh' -print0 | xargs -0 shellcheck; else echo 'SKIP shellcheck: unavailable'; fi

validate: skills metadata skill-lint hygiene secrets markdown tests assets justfiles python-lint python-types shell
    git diff --check

[positional-arguments]
eval-triggers *args:
    python3 scripts/evals/trigger_eval.py "$@"

[positional-arguments]
eval-outputs *args:
    python3 scripts/evals/output_eval.py "$@"
