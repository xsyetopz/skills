# Issues

## GitHub

`POST /repos/OWNER/REPO/issues` accepts `title`, `body`, and optional
labels/assignees. A successful creation returns 201 with `number`, `html_url`
and state. Update selected fields with `PATCH .../issues/NUMBER`; close using
`{"state":"closed"}`. `POST .../issues/NUMBER/comments` takes `{"body":"..."}`;
editing uses `/issues/comments/COMMENT_ID`, not the issue number. PR
conversation comments share these endpoints; inline review comments have
different position/diff contracts. Use Issues write permission for issue
mutations. [Issues](https://docs.github.com/en/rest/issues/issues),
[comments](https://docs.github.com/en/rest/issues/comments).

For literal multiline content, prepare a UTF-8 body file and run the command
below:

```sh
gh issue create --repo OWNER/REPO --title 'Concrete defect' \
  --body-file /tmp/issue-body.md
```

Shell interpolation is not a serialization method.

## GitLab

`POST /projects/123/issues` accepts `title` and `description`; success returns
201 with global `id`, project-local `iid` and `web_url`. Update with
`PUT /projects/123/issues/7`, using `state_event:"close"` or `"reopen"` for
transitions. GitHub's `body` and `state:"closed"` are not equivalent GitLab
input fields. Add a note with `POST /projects/123/issues/7/notes` and `body`;
note editing requires the note ID.
[Issues](https://docs.gitlab.com/api/issues/),
[notes](https://docs.gitlab.com/api/notes/).

For pagination or confidential issues, distinguish “not returned” from “does not
exist.” Visibility depends on account access. Editing assignees, labels or
milestones is an explicit field change; preserve omitted values.
