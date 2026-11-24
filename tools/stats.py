"""Read the profile's numbers from the GitHub API and write stats.json.

Trophy ranks follow ryo-ma/github-profile-trophy (src/trophy.ts for the
thresholds, src/user_info.ts for the scores). Unlike its site, which only sees
public data, this runs with the owner's token (scopes repo, read:user), so
private repositories and pull requests count too.
Usage: GITHUB_TOKEN=... python stats.py [stats.json]
"""

import json
import math
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LOGIN = "LouisStani"
RELEASE_REPOS = ["kindric"]
STATS = Path(__file__).parent / "stats.json"
API = "https://api.github.com/graphql"

# (rank, title, minimum score), best rank first.
COMMITS = [("SSS", "god committer", 4000), ("SS", "deep committer", 2000), ("S", "super committer", 1000),
           ("AAA", "ultra committer", 500), ("AA", "hyper committer", 200), ("A", "high committer", 100),
           ("B", "middle committer", 10), ("C", "first commit", 1)]
EXPERIENCE = [("SSS", "seasoned veteran", 70), ("SS", "grandmaster", 55), ("S", "master dev", 40),
              ("AAA", "expert dev", 28), ("AA", "experienced dev", 18), ("A", "intermediate dev", 11),
              ("B", "junior dev", 6), ("C", "newbie", 2)]
PULL_REQUESTS = [("SSS", "god puller", 1000), ("SS", "deep puller", 500), ("S", "super puller", 200),
                 ("AAA", "ultra puller", 100), ("AA", "hyper puller", 50), ("A", "high puller", 20),
                 ("B", "middle puller", 10), ("C", "first pull", 1)]
REPOSITORIES = [("SSS", "god repo creator", 50), ("SS", "deep repo creator", 45), ("S", "super repo creator", 40),
                ("AAA", "ultra repo creator", 35), ("AA", "hyper repo creator", 30), ("A", "high repo creator", 20),
                ("B", "middle repo creator", 10), ("C", "first repository", 1)]

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    contributionsCollection { totalCommitContributions restrictedContributionsCount }
    pullRequests(first: 1) { totalCount }
    repositories(first: 50, ownerAffiliations: OWNER, orderBy: {direction: DESC, field: STARGAZERS}) {
      totalCount
      nodes { createdAt }
    }
  }
  %s
}
"""


def release_fields() -> str:
    return "\n".join(f'r{i}: repository(owner: $login, name: "{repo}") {{ latestRelease {{ tagName }} }}'
                     for i, repo in enumerate(RELEASE_REPOS))


def graphql(token: str) -> dict:
    body = json.dumps({"query": QUERY % release_fields(), "variables": {"login": LOGIN}}).encode()
    request = urllib.request.Request(API, data=body, headers={"Authorization": f"bearer {token}",
                                                              "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        raise SystemExit(f"GitHub API: HTTP {error.code} {error.read().decode(errors='replace')}")
    if payload.get("errors"):
        raise SystemExit(f"GitHub API: {payload['errors']}")
    return payload["data"]


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def experience_score(user: dict, now: datetime) -> int:
    """Days since the earliest of account and repository creation, divided by 100."""
    earliest = min([parse_time(user["createdAt"])] + [parse_time(n["createdAt"]) for n in user["repositories"]["nodes"]])
    return math.floor((now - earliest).total_seconds() / 86400 / 100)


def ranked(name: str, score: int, table: list[tuple[str, str, int]]) -> dict:
    for rank, title, minimum in table:
        if score >= minimum:
            return {"rank": rank, "name": name, "title": title}
    return {"rank": "?", "name": name, "title": "not yet"}


def build_stats(data: dict, now: datetime) -> tuple[dict, dict]:
    """Return what the profile shows, and the raw scores behind it."""
    user = data["user"]
    contributions = user["contributionsCollection"]
    scores = {
        "commits": contributions["totalCommitContributions"] + contributions["restrictedContributionsCount"],
        "experience": experience_score(user, now),
        "pull requests": user["pullRequests"]["totalCount"],
        "repositories": user["repositories"]["totalCount"],
    }
    tables = {"commits": COMMITS, "experience": EXPERIENCE, "pull requests": PULL_REQUESTS, "repositories": REPOSITORIES}
    releases = {repo: data[f"r{i}"]["latestRelease"]["tagName"]
                for i, repo in enumerate(RELEASE_REPOS) if data[f"r{i}"] and data[f"r{i}"]["latestRelease"]}
    return {"releases": releases, "trophies": [ranked(name, scores[name], tables[name]) for name in tables]}, scores


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is not set (locally: GITHUB_TOKEN=$(gh auth token) python stats.py)")
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else STATS
    stats, scores = build_stats(graphql(token), datetime.now(timezone.utc))
    print("scores:", json.dumps(scores))
    output.write_text(json.dumps(stats, indent=2) + "\n")


if __name__ == "__main__":
    main()
