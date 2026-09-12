set dotenv-load := false

cache := env("SKILLS_CACHE_DIR", env("HOME") + "/.cache/xsyetopz-skills")
venv := cache + "/validation-venv"
bun_cache := cache + "/bun"

default: validate

provision:
    mkdir -p "{{ cache }}" "{{ bun_cache }}"
    test -x "{{ venv }}/bin/python" || python3 -m venv "{{ venv }}"
    "{{ venv }}/bin/python" -m pip install --disable-pip-version-check -r requirements-validation.txt

skills: provision
    for skill in skills/*; do "{{ venv }}/bin/skills-ref" validate "$skill"; done

metadata: provision
    "{{ venv }}/bin/python" scripts/validate_repository.py

markdown:
    BUN_INSTALL_CACHE_DIR="{{ bun_cache }}" bunx --bun markdownlint-cli2@0.23.2 "AGENTS.md" "skills/**/*.md"

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
    BUN_INSTALL_CACHE_DIR="{{ bun_cache }}" bunx --bun pyright@1.1.414 --pythonpath "{{ venv }}/bin/python"

shell:
    if command -v shellcheck >/dev/null; then find skills scripts -type f -name '*.sh' -print0 | xargs -0 shellcheck; else echo 'SKIP shellcheck: unavailable'; fi

validate: skills metadata markdown tests assets justfiles python-lint python-types shell benchmarks
    git diff --check

benchmarks:
    bash skills/optimize-bun-code/assets/benchmark-repro/verify.sh
    bash skills/optimize-rust-code/assets/benchmark-repro/verify.sh
    bash skills/optimize-dotnet-code/assets/benchmark-repro/verify.sh
