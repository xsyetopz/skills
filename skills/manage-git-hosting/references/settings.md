# Read and update hosted repository settings

## GitHub

Read `GET /repos/OWNER/REPO`, then `PATCH` only the requested fields, for
example `{"has_wiki":false}`. Settings commonly require Administration write
permission; verify the operation-specific permission block. Visibility,
archiving, transfer and deletion have broader consequences than editing
metadata; resolve the exact effect before issuing those requests. Branch
protection and rulesets have their own endpoints and schemas. [Repository
endpoints][ref-repository-endpoints].

Patch intended settings only. Verify changed values with an independent GET. For
unsupported Enterprise fields or a new endpoint, refresh that endpoint's schema
and permission block; the procedures here do not imply all GitHub servers have
SaaS parity.

To change branch protection, read `/repos/OWNER/REPO/branches/BRANCH/protection`
first. The full `PUT` endpoint requires a complete intended configuration for
required checks, administrator enforcement, review requirements and
restrictions; null can disable a protection. Do not send a small
repository-metadata patch to this endpoint. Prefer its narrower subresource
endpoint when changing one supported protection. Arrays of allowed users/teams
replace previous arrays, so preserve existing entries unless removal was
requested. Branch names need URL encoding; wildcard policy belongs to the
appropriate ruleset/GraphQL contract rather than assuming this REST path accepts
a pattern. Read back the changed protection and applicable rules; verify that
unrelated protections remain effective. [Branch protection contract][source-1].

[source-1]: https://docs.github.com/en/rest/branches/branch-protection

## GitLab

`GET /projects/123` establishes current visibility, default branch, enabled
features and merge settings. `PUT /projects/123` edits selected supported
fields, for example `{"description":"Documented project purpose"}`. Do not copy
a GET object wholesale into PUT: response fields include read-only and unrelated
policy values. Project role, token scopes and protected resources jointly
constrain authority; an `api` scope does not grant a role the user lacks. CI job
tokens support only specific APIs, not arbitrary administrative operations.
[Projects](https://docs.gitlab.com/api/projects/),
[authentication][ref-authentication].

Use [transport and recovery](provider-semantics.md) for status-specific handling
and ambiguous outcomes. Do not infer the exact missing permission from a status
code alone.

Read `/projects/123/protected_branches` and the named branch before changing
protection. Creating a policy uses `POST /projects/123/protected_branches` with
`name` and intended access settings. A structural policy for a new branch could
use this payload for no direct pushes, Maintainer merges, and no force push:

```json
{
  "name": "release",
  "push_access_level": 0,
  "merge_access_level": 40,
  "allow_force_push": false
}
```

Set access fields from the intended branch policy. Access levels include 0 for
no push/merge access, 30 Developer and 40 Maintainer; 0 is not valid as an
unprotect access level. User/group/deploy-key and custom-role selectors have
tier/server constraints. Updating existing access entries requires their IDs and
supported update fields; do not delete/recreate protection merely to avoid
understanding them. [Protected branches][ref-protected-branches].

Wildcard policies can overlap. Check effective permission and inherited/group
rules after a change, not only the one returned object.

[ref-repository-endpoints]: https://docs.github.com/en/rest/repos/repos
[ref-authentication]: https://docs.gitlab.com/api/rest/authentication/
[ref-protected-branches]: https://docs.gitlab.com/api/protected_branches/
