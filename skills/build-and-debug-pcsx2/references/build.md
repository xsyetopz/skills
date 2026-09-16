# PCSX2 PS2 emulator: select the source-build task

Resolve the requested source revision and read its build documentation, CMake
options, dependency provisioning, and supported host/target architectures. Do
not infer native support for an architecture from an available translated/x86
build or a third-party patch.

Use a separate source/build location, preserve existing work, and record
compiler, SDK, generator, build type, dependency identities, and enabled
optional targets. Let the project's native build system express these settings
rather than creating a replacement build schema.

Configure, compile, and package through that revision's documented path. Keep
generated resources, patch archives, Qt plugins, and runtime libraries matched
to the build when they are required. An executable copied alone may not be a
functional package.

For a GS dump runner request, enable/build the supported runner target for that
revision and verify its own CLI. Do not assume the Qt executable's options or
that a successful GS replay constitutes a full guest execution test.

Inspect the resulting artifact and its architecture. Run only the requested
feasible smoke check, using isolated data when startup writes configuration. Do
not overwrite a normal installation or execute guest content as an automatic
consequence of a build request.

Return the artifact path, revision/configuration and exact commands, plus which
of configure, compile, package, launch, and guest/GS behavior were verified. Do
not report an unrun stage as passed.

Sources: [PCSX2 building][ref-pcsx2-building], [GS dump
runner][ref-gs-dump-runner], [source
repository](https://github.com/PCSX2/pcsx2).

[ref-pcsx2-building]: https://pcsx2.net/docs/advanced/building/
[ref-gs-dump-runner]: https://pcsx2.net/docs/advanced/gsdumprunner/
