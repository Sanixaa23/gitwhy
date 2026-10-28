"""Measured scenario accuracy: every scenario is built in a real repository.

Also runs standalone (no pytest needed):
    python tests/test_rules.py
In that form it prints the confusion matrix; the README table comes from here.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fixtures  # noqa: E402
from gitwhy import context, explain, rules  # noqa: E402


def _predict(fx) -> str:
    ctx = context.collect(fx.repo)
    return rules.match(ctx, fx.error_text) or "(no match)"


def test_every_scenario_matches():
    """Every state built by a fixture must match its own scenario."""
    try:
        for fx in fixtures.all_fixtures():
            assert _predict(fx) == fx.scenario_id, (
                "got %s instead of %s" % (_predict(fx), fx.scenario_id)
            )
    finally:
        fixtures.cleanup()


def test_rebase_checked_before_detached():
    """The verified ordering rule: a mid-rebase repo also looks detached.

    This test catches anyone accidentally reversing that order.
    """
    try:
        fx = fixtures.build("03_rebase_in_progress")
        ctx = context.collect(fx.repo)
        assert ctx.detached, "mid-rebase repo does not look detached; fixture broken"
        assert "rebase-merge" in ctx.in_progress or "rebase-apply" in ctx.in_progress
        assert rules.match(ctx, fx.error_text) == "03_rebase_in_progress"
    finally:
        fixtures.cleanup()


def test_all_error_lines_are_scanned():
    """In a merge conflict the first line is "Auto-merging"; CONFLICT is below."""
    try:
        fx = fixtures.build("02_merge_conflict")
        assert "CONFLICT" in fx.error_text
        lines = rules.error_lines(fx.error_text)
        assert lines, "no decision line found"
        assert any("CONFLICT" in line for line in lines)
    finally:
        fixtures.cleanup()


def test_env_example_is_not_a_false_positive():
    """`.env.example` exists in order to be committed; it is not a secret."""
    try:
        fx = fixtures.build("10_secret_staged")
        ctx = context.collect(fx.repo)
        assert ".env" in ctx.staged and ".env.example" in ctx.staged
        assert rules.secret_paths(ctx) == [".env"]
    finally:
        fixtures.cleanup()


def test_dependency_reported_as_directory_not_files():
    """Two files inside node_modules must yield a single directory name."""
    try:
        fx = fixtures.build("09_dependency_staged")
        ctx = context.collect(fx.repo)
        assert len(ctx.staged) == 2
        assert rules.dependency_paths(ctx) == ["node_modules"]
    finally:
        fixtures.cleanup()


def test_behind_count_reads_zero_after_rejected_push():
    """Verified finding: a rejected push does not update the remote-tracking ref.

    That is why scenario 7 decides from the error text and not `branch.ab`.
    The test stops anyone later writing a rule that leans on ctx.behind.
    """
    try:
        fx = fixtures.build("07_push_rejected")
        ctx = context.collect(fx.repo)
        assert "! [rejected]" in fx.error_text
        assert ctx.behind == 0, "git's behaviour changed; revisit the rule"
        assert rules.match(ctx, fx.error_text) == "07_push_rejected"
        # Without the error text this state is UNDETECTABLE; that is deliberate.
        assert rules.match(ctx, "") != "07_push_rejected"
    finally:
        fixtures.cleanup()


def test_staged_ignore_check_uses_no_index():
    """Without --no-index a staged path always reads as "not ignored"."""
    try:
        fx = fixtures.build("10_secret_staged")
        with open(os.path.join(fx.repo, ".gitignore"), "w", encoding="utf-8") as f:
            f.write(".env\n")
        ctx = context.collect(fx.repo)
        assert ".env" in ctx.ignored_staged, (
            "no rule match seen for a staged .env; --no-index may have been dropped"
        )
    finally:
        fixtures.cleanup()


def test_negative_controls_match_nothing():
    """A clean repo, a repo after amend, and main with an unpushed commit:
    none of the three is a scenario. A match here is a false positive."""
    try:
        for variant in ("neg_clean", "neg_amend", "neg_main_ahead"):
            fx = fixtures.build(variant)
            ctx = context.collect(fx.repo)
            assert rules.match(ctx, fx.error_text) is None, (
                "%s gave a false positive: %s" % (variant, rules.match(ctx, fx.error_text))
            )
    finally:
        fixtures.cleanup()


def test_amend_is_not_a_lost_commit():
    """`commit --amend` leaves the old commit unreachable; that is not a loss."""
    try:
        fx = fixtures.build("neg_amend")
        assert context.lost_commits(fx.repo) == []
        fx2 = fixtures.build("12_reset_hard")
        assert len(context.lost_commits(fx2.repo)) == 1
    finally:
        fixtures.cleanup()


def test_cherry_pick_and_revert_share_a_scenario_but_not_a_command():
    """Both variants land on one scenario, but the suggested command differs."""
    try:
        for variant, command in (("04_cherry_pick", "cherry-pick"),
                                 ("04_revert", "revert")):
            fx = fixtures.build(variant)
            ctx = context.collect(fx.repo)
            assert rules.match(ctx, fx.error_text) == "04_cherry_pick_in_progress"
            text = explain.explain("04_cherry_pick_in_progress", ctx)
            assert "git %s --continue" % command in text, (
                "wrong command suggested for %s" % variant
            )
    finally:
        fixtures.cleanup()


def test_protected_branch_differs_from_push_rejection():
    """Scenarios 8 and 7 both carry "failed to push some refs"; keep them apart."""
    try:
        protected = fixtures.build("08_protected_branch")
        rejected = fixtures.build("07_push_rejected")
        assert "[remote rejected]" in protected.error_text
        assert "[remote rejected]" not in rejected.error_text
        assert rules.match(context.collect(protected.repo),
                           protected.error_text) == "08_wrong_branch"
        assert rules.match(context.collect(rejected.repo),
                           rejected.error_text) == "07_push_rejected"
    finally:
        fixtures.cleanup()


def test_scenario_11_checkout_and_merge_variants():
    try:
        for variant in ("11_checkout_blocked", "11_merge_blocked"):
            fx = fixtures.build(variant)
            ctx = context.collect(fx.repo)
            assert ctx.unstaged == ["a.txt"], "%s: %s" % (variant, ctx.unstaged)
            assert rules.match(ctx, fx.error_text) == "11_local_changes_block"
    finally:
        fixtures.cleanup()


def test_text_driven_fixtures_pass_the_marker_gate():
    """ERROR_MARKERS is a gate: a line that misses it never reaches match().

    Every text-driven scenario's fixture must leave at least one decision
    line. Without this test, scenario 8 silently matched nothing.
    """
    try:
        for variant in ("05_no_remote", "06_no_upstream", "07_push_rejected",
                        "08_protected_branch", "11_checkout_blocked",
                        "11_merge_blocked"):
            fx = fixtures.build(variant)
            assert rules.error_lines(fx.error_text), (
                "%s: error text does not pass the marker gate" % variant
            )
    finally:
        fixtures.cleanup()


def test_git_subcommand_parsing():
    assert rules.git_subcommand("git push") == "push"
    assert rules.git_subcommand("git -c user.email=x push -u origin main") == "push"
    assert rules.git_subcommand("git -C /tmp/repo status --short") == "status"
    assert rules.git_subcommand("git --no-pager log") == "log"
    assert rules.git_subcommand("npm install") is None
    assert rules.git_subcommand("git") is None
    assert rules.git_subcommand("") is None
    assert rules.git_subcommand(None) is None


def test_wrapper_finds_scenarios_without_error_text():
    """The wrapper leaves the error on screen, so there is no text, only a command.

    Without this block scenarios 5, 6 and 11 never matched through the
    wrapper; measured in a real repository (see tools/wrapper_test.sh).
    """
    try:
        expectations = (
            ("05_no_remote", "git push", "05_no_remote"),
            ("06_no_upstream", "git push", "06_no_upstream"),
            ("11_checkout_blocked", "git checkout feature",
             "11_local_changes_block"),
        )
        for variant, command, expected in expectations:
            fx = fixtures.build(variant)
            ctx = context.collect(fx.repo)
            assert rules.match(ctx, "", command) == expected, (
                "%s: textless match failed" % variant
            )
    finally:
        fixtures.cleanup()


def test_command_alone_gives_no_false_positive():
    """A failed push with a remote and an upstream must not hit a command rule."""
    try:
        fx = fixtures.build("neg_main_ahead")
        ctx = context.collect(fx.repo)
        assert ctx.has_remote and ctx.upstream
        assert rules.match(ctx, "", "git push") is None
        # A failed checkout in a clean repo must not be invented either.
        fx2 = fixtures.build("neg_clean")
        ctx2 = context.collect(fx2.repo)
        assert rules.match(ctx2, "", "git checkout main") is None
    finally:
        fixtures.cleanup()


def test_record_validity():
    """A stale record, or one from another repository, must not fire a rule."""
    import time
    from gitwhy import capture
    try:
        fx = fixtures.build("05_no_remote")
        fresh = {"repo": fx.repo, "time": time.time(), "command": "git push"}
        stale = {"repo": fx.repo, "time": time.time() - 3600, "command": "git push"}
        elsewhere = {"repo": os.path.join(fx.repo, "other"), "time": time.time(),
                     "command": "git push"}
        assert capture.is_valid(fresh, fx.repo)
        assert not capture.is_valid(stale, fx.repo)
        assert not capture.is_valid(elsewhere, fx.repo)
        assert not capture.is_valid(None, fx.repo)
    finally:
        fixtures.cleanup()


def test_implemented_scenarios_have_templates():
    missing = [s for s in rules.IMPLEMENTED if s not in explain.templates()]
    assert not missing, "scenario without a template: %s" % missing


def test_no_unfilled_placeholders():
    """Rendered against its own fixture, no template may leave {{...}} behind."""
    import re
    leftovers = {}
    try:
        for fx in fixtures.all_fixtures():
            scenario = _predict(fx)
            if scenario == "(no match)":
                continue
            text = explain.explain(scenario, context.collect(fx.repo))
            found = re.findall(r"\{\{\w+\}\}", text)
            if found:
                leftovers[scenario] = found
    finally:
        fixtures.cleanup()
    assert not leftovers, "unfilled placeholders: %s" % leftovers


def test_empty_error_text_does_not_crash():
    try:
        fx = fixtures.build("01_detached_head")
        ctx = context.collect(fx.repo)
        assert rules.match(ctx, "") == "01_detached_head"
        assert rules.match(ctx, None) == "01_detached_head"
    finally:
        fixtures.cleanup()


def test_directory_that_is_not_a_repository():
    import tempfile
    d = tempfile.mkdtemp(prefix="gitwhy_empty_")
    try:
        ctx = context.collect(d)
        assert not ctx.is_repo
        assert rules.match(ctx, "fatal: not a git repository") is None
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


def _short(scenario_id: str) -> str:
    """Short matrix header. The "none" row holds the negative controls."""
    return "none" if scenario_id == "(no match)" else scenario_id.split("_")[0]


def confusion_matrix():
    """Confusion matrix: truth down the rows, prediction across the columns.

    The last row/column are the negative controls: a clean repository, a
    repository after amend, and main with an unpushed commit. A correct
    diagonal there means "produced no false positive".
    """
    scenarios = list(fixtures.SCENARIOS)
    matrix = {t: {p: 0 for p in scenarios} for t in scenarios}
    try:
        for fx in fixtures.all_fixtures():
            matrix[fx.scenario_id][_predict(fx)] += 1
    finally:
        fixtures.cleanup()

    headers = [_short(s) for s in scenarios]
    print("truth \\ prediction " + " ".join("%4s" % h for h in headers))
    correct = total = 0
    for t in scenarios:
        row = " ".join("%4d" % matrix[t][p] for p in scenarios)
        print("%-18s %s" % (_short(t), row))
        correct += matrix[t][t]
        total += sum(matrix[t].values())
    print("\n%d scenarios, %d fixtures, %d/%d correct (%d%%)" % (
        len(rules.IMPLEMENTED), len(fixtures.VARIANTS),
        correct, total, round(100 * correct / total)))
    return matrix


if __name__ == "__main__":
    confusion_matrix()
