set dotenv-load := false

cache := env("XDG_CACHE_HOME", env("HOME") + "/.cache")

default:
    @printf '%s\n' "{{ cache }}"
