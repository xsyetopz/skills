# Eclipse Tycho starter

1. Replace `__PLACEHOLDER__` values and align Java packages with their
   directories.
2. Select compatible Java, Maven, Tycho, and a pinned Eclipse target.
3. Declare required bundles, imports, and extensions.
4. Remove feature/repository modules for a bundle-only package.
5. Run `mvn clean verify`. Check API baselines for exported API changes and p2
   resolution for distribution changes.
