## What happened

You ran `git push`, but this repository has no remote address at all. Git does not know
where to send anything. If you created the repository locally with `git init`, this is
normal: you have not connected it to the one on GitHub yet.

## Where you are

- Repository: `{{repo}}`
- Branch: `{{branch}}`
- Remotes configured: none
- Commits waiting to be sent: {{ahead}} (git cannot count this while no upstream is set)

## What to do

Create an empty repository on GitHub, then connect its address here and push for the
first time:

    git remote add origin https://github.com/<user>/<repo>.git
    git push -u origin {{branch}}

The `-u` is needed only once: it records which remote branch this branch tracks. After
that, plain `git push` is enough.

To confirm the connection was made:

    git remote -v
