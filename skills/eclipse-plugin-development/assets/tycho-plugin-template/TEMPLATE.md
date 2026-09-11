# Eclipse Tycho starter

1. Replace `__PLACEHOLDER__` values and align Java packages with their
   directories.
2. Select compatible Java, Maven, Tycho, and a pinned Eclipse target.
3. Set each target environment's Equinox OS, window-system, and architecture
   values; add more `<environment>` entries for a multi-platform repository.
4. Declare required bundles, imports, and extensions.
5. Remove feature/repository modules for a bundle-only package.
6. Run `mvn clean verify`. Check API baselines for exported API changes and p2
   resolution for distribution changes.

The example command encodes the current nonempty text selection as a UTF-8
`application/x-www-form-urlencoded` value, using Java's `URLEncoder`. It is not
a whole-URL or URI-path encoder. It edits the unsaved document, leaves the file
untouched until the user saves, and selects the replacement.

The tests launch an actual Eclipse workbench and exercise the registered command
and undo. Run them in a desktop session, or a supported virtual display on
Linux. Keep the test timeout and inspect the test count: a successful compile or
an empty test run does not prove the command works. Inspect the bundle JAR for
both `plugin.xml` and handler classes before claiming successful packaging.
