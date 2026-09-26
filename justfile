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

skills: provision
    for skill in skills/*; do "{{ venv }}/bin/skills-ref" validate "$skill"; done

metadata: provision
    "{{ venv }}/bin/python" scripts/validate_repository.py

markdown:
    BUN_INSTALL_CACHE_DIR="{{ bun_cache }}" bunx --bun markdownlint-cli2 "*.md" "skills/**/*.md" "docs/**/*.md"

tests: provision
    "{{ venv }}/bin/python" scripts/run_python_tests.py

assets: provision
    "{{ venv }}/bin/python" scripts/validate_assets.py

justfiles: provision
    "{{ venv }}/bin/python" skills/write-justfiles/scripts/check_justfiles.py .

python-lint: provision
    "{{ venv }}/bin/ruff" check scripts skills typings
    "{{ venv }}/bin/ruff" format --check --exclude '*.md' scripts skills typings

python-types: provision
    BUN_INSTALL_CACHE_DIR="{{ bun_cache }}" bunx --bun pyright --pythonpath "{{ venv }}/bin/python"

shell:
    if command -v shellcheck >/dev/null; then find skills scripts -type f -name '*.sh' -print0 | xargs -0 shellcheck; else echo 'SKIP shellcheck: unavailable'; fi

validate: skills metadata markdown tests assets justfiles python-lint python-types shell benchmarks
    git diff --check

benchmarks:
    sh skills/optimize-javascript-code/assets/examples/verify.sh benchmark
    sh skills/optimize-rust-code/assets/examples/verify.sh benchmark
    sh skills/optimize-csharp-code/assets/examples/verify.sh benchmark
