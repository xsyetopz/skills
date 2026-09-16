# DuckStation PS1 emulator: select the source-build task

Read the README/build files at the selected revision and identify the supported
host architecture, compiler, CMake generator, dependency provisioning, and
packaging layout. Use that revision's instructions, not an old universal package
list. A current branch's README is not automatically correct for a historical
commit.

Build in a separate directory and preserve the source checkout's existing work.
Record the full source revision, submodule/dependency revisions, compiler
identity, build type, and relevant CMake options. Configure explicitly for the
intended host/target; do not silently substitute emulation or a different
architecture when native support is absent.

Acquire dependencies only from the project's documented sources under the
authorized environment. Verify expected artifact identity where provided. Keep
downloaded packs, build trees, package-manager caches, and generated binaries
outside the skill repository.

Run configuration, compilation, and packaging as separate checked operations
using the selected revision's supported commands. Generic `cmake -S SOURCE -B
BUILD` and `cmake --build BUILD` describe phases, not a complete
version-independent build recipe. Do not claim they are sufficient without the
required toolchain and options.

Inspect the produced executable and companion resources/libraries. Do not
overwrite an installed emulator to test a build. A successful link does not
prove that the packaged Qt/plugins/resources can be found at runtime. Perform a
version/help or GUI startup check only when it is requested and feasible;
launching a guest is a separate test with separate prerequisites.

Deliver the artifact location, exact revision/configuration/commands, and the
highest verified stage. If configuration or a dependency fails, retain the
actual failure and do not describe the build as complete.

Source: [selected-revision build
documentation][ref-selected-revision-build-documentation]; resolve the requested
ref before using it.

[ref-selected-revision-build-documentation]: https://github.com/stenzek/duckstation/blob/master/README.md
