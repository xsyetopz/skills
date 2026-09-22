# Operate PCSX2 in controlled environments

Record supported OS/architecture/GPU backends, distribution channel,
BIOS/content handling policy, user memory-card/save/config isolation, dump/log
privacy, reproducible build inputs, and rollback package. Use
organization-approved storage for licensed test images, firmware, dumps, saves,
and traces. Never add those artifacts to the skill package or upload them to an
unapproved service.

Use a per-run isolated state root and copy only the minimum required
configuration. Mark generated patches, textures, dumps, screenshots, and logs
with the source revision and input identity. Redact usernames, paths, tokens,
and private content before sharing diagnostics. Reproduce release candidates on
the declared host/GPU matrix and install the exact built artifact. Publication,
signing, or replacement of a distributed build requires separate authority.
