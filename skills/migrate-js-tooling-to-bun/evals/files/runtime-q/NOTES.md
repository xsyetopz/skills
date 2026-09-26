Last week we replaced `npm ci` with `bun install --frozen-lockfile` in CI and
the Dockerfile. Production runs `bun run start`.
