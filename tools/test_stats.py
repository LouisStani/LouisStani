"""Thresholds checked against ryo-ma/github-profile-trophy src/trophy.ts and src/user_info.ts."""

from datetime import datetime, timezone

from stats import COMMITS, EXPERIENCE, PULL_REQUESTS, REPOSITORIES, build_stats, experience_score, ranked, rounded


def test_rank_uses_the_best_threshold_reached() -> None:
    assert ranked("commits", 1000, COMMITS, "")["rank"] == "S"
    assert ranked("commits", 999, COMMITS, "")["rank"] == "AAA"
    assert ranked("pull requests", 9, PULL_REQUESTS, "9 opened") == {
        "rank": "C", "name": "pull requests", "title": "first pull", "value": "9 opened"}


def test_rank_is_unknown_below_the_lowest_threshold() -> None:
    assert ranked("repositories", 0, REPOSITORIES, "0 owned")["rank"] == "?"


def test_experience_is_days_over_100_from_the_earliest_date() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    user = {"createdAt": "2023-01-01T00:00:00Z", "repositories": {"nodes": [{"createdAt": "2022-01-01T00:00:00Z"}]}}
    # 2022-01-01 to 2026-01-01 is 1461 days.
    assert experience_score(user, now) == 14
    assert ranked("experience", 14, EXPERIENCE, "")["title"] == "intermediate dev"


def test_build_stats_adds_private_commits_and_skips_missing_releases() -> None:
    data = {
        "user": {
            "createdAt": "2025-01-01T00:00:00Z",
            "contributionsCollection": {"totalCommitContributions": 600, "restrictedContributionsCount": 500},
            "pullRequests": {"totalCount": 9},
            "repositories": {"totalCount": 3, "nodes": []},
        },
        "r0": {"latestRelease": None},
    }
    stats, scores = build_stats(data, datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert scores["commits"] == 1100
    assert stats["releases"] == {}
    assert [t["rank"] for t in stats["trophies"]] == ["S", "C", "C", "C"]
    assert [t["value"] for t in stats["trophies"]] == ["1,100 in 12 months", "since 2025", "9 opened", "3 owned"]


def test_shown_numbers_keep_two_figures_rounded_down() -> None:
    assert [rounded(n) for n in (0, 17, 99, 100, 126, 999, 1192, 1200, 12345)] == [
        "0", "17", "99", "100", "120+", "990+", "1,100+", "1,200", "12,000+"]  # experience: 365 days -> 3, C from 2
