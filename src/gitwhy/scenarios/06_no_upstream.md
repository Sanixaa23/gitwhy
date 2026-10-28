## What happened

A remote is configured (`{{remotes}}`), but nothing records which remote branch
`{{branch}}` tracks. Git knows where to send, not what to send it as. This happens once
on every new branch you create.

Do not confuse this with scenario 5: there, no remote existed at all. Here one does, but
the branch has no match.

## Where you are

- Repository: `{{repo}}`
- Branch: `{{branch}}`
- Upstream: {{upstream}}
- Remotes configured: {{remotes}}

## What to do

Push the branch and set up tracking in the same command:

    git push -u {{first_remote}} {{branch}}

The `-u` is needed only once. After that, plain `git push` is enough.

If you would rather not type this on every new branch:

    git config --global push.autoSetupRemote true
