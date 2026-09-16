# Create and verify hosted software release resources

## GitHub

Create `POST .../releases` with `tag_name`, `name`, `body`, `draft` and
`prerelease`. `target_commitish` matters when creating a missing tag, so resolve
the intended commit first. Publication can make both release content and
artifacts visible. A draft release is still a hosted mutation. Upload assets to
the returned `upload_url` after removing its URI template, supplying asset name,
binary bytes and content type. Inspect returned asset ID/size and the release
afterward. Release creation requires Contents write; some targets that change
workflow files additionally require Workflows write. Check the endpoint's
permission block and actual target rather than expanding token privileges by
default. [Releases][ref-releases], [assets][ref-assets].

Prepare notes and artifact hashes. For a staged publication, create with
`draft:true` explicitly, upload assets, and verify them before setting
`draft:false` to publish. Omission of `draft` must not accidentally publish an
incomplete release. Define “latest” explicitly: release publication order,
semantic version precedence and prerelease eligibility differ. Deleting a
release is not the same as deleting its Git tag; verify each requested effect
separately.

## GitLab

`POST /projects/123/releases` accepts `tag_name`, `name`, `description`, and
`ref` when a missing tag must be created. Assets can include links with `name`
and `url`; these are references, not proof that binary bytes were uploaded.
Upload release binaries through the package/upload endpoint before linking them.
`released_at` controls release timing metadata; it is not a generic GitHub-style
draft toggle. [Releases](https://docs.gitlab.com/api/releases/).

Read back by URL-encoded tag at `/projects/123/releases/TAG`. Compare notes,
tag, asset links and timing. Treat tag deletion and release deletion as separate
operations. Finalize local notes and artifact identity before release creation;
verify each external asset URL after release creation.

[ref-releases]: https://docs.github.com/en/rest/releases/releases
[ref-assets]: https://docs.github.com/en/rest/releases/assets
