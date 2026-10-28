## What happened

The remote refused your push: `{{branch}}` is a protected branch. You committed straight
onto it, but this repository requires changes to arrive through a feature branch and a
pull request. Your commit is not lost — it is just not in the right place yet.

This is not the same as scenario 7: there, git itself said "fetch theirs first". Here the
push reached the remote and was turned away by a rule.

## Where you are

- Repository: `{{repo}}`
- Branch: `{{branch}}` → `{{upstream}}`
- Waiting to be sent: {{ahead}} commit(s)
- Last commit: {{last_subject}}

## What to do

Move your commits onto a new branch. The order matters: create the new branch first, then
reset `{{branch}}` back to the remote's version.

Create the branch exactly as things stand and push it:

    git switch -c feature/{{branch}}-changes
    git push -u {{first_remote}} feature/{{branch}}-changes

Then open a pull request on GitHub. If you want to clean up `{{branch}}` afterwards,
first confirm the new branch really arrived with
`git log --oneline {{first_remote}}/feature/{{branch}}-changes`, and only then:

    git switch {{branch}}
    git reset --hard {{upstream}}

> WARNING: `git reset --hard {{upstream}}` drops the {{ahead}} commit(s) from
> `{{branch}}` and PERMANENTLY deletes any uncommitted changes. Run it only after you
> have confirmed the new branch was pushed. gitwhy never runs this for you.
