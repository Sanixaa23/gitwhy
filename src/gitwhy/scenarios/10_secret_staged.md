## What happened

A secret-bearing file got staged: **{{secrets}}**. If this file is committed, the key
inside it enters the repository's history. If you have pushed even once, treat the key as
leaked: deleting the file is not enough, and cleaning history is not enough either — the
key itself has to be replaced.

Template files such as `.env.example` and `.env.sample` do not warn; those exist in order
to be committed.

{{ignore_status}}

## Where you are

- Repository: `{{repo}}`
- Branch: `{{branch}}`
- Staged secret files: {{secret_count}} — {{secrets}}
- Upstream: {{upstream}} (if an upstream exists, this repo may already have been pushed)

## What to do

If you have not committed yet, this is the easy case:

    git rm --cached {{first_secret}}
    echo "{{first_secret}}" >> .gitignore
    git add .gitignore

If you committed but have **not** pushed, amend the last commit:

    git rm --cached {{first_secret}}
    git commit --amend

If you have pushed, the order matters. First revoke the key in your provider's dashboard
and issue a new one; do this before cleaning history, because a pushed key is no longer
under your control. Then remove the file from history with `git filter-repo`, and finally
tell everyone who has a copy of the repository to re-clone it.

To see which commits contain the file:

    git log --oneline -- {{first_secret}}

> WARNING: `git filter-repo` rewrites the entire history; every commit gets a new id and
> the old history is PERMANENTLY gone. Open pull requests and other people's local copies
> break. gitwhy never runs this for you.
