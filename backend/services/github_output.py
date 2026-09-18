from typing import Any, Dict

import requests

import env
from core.exceptions import ExternalServiceException


def publish_bundle(files: Dict[str, Any], message: str) -> Dict[str, str]:
    if not env.GITHUB_OUTPUT_ENABLED:
        raise ExternalServiceException("GitHub output", "Publishing is disabled")
    if not env.GITHUB_OUTPUT_TOKEN or "/" not in env.GITHUB_OUTPUT_REPOSITORY:
        raise ExternalServiceException("GitHub output", "Publishing credentials are not configured")

    owner, repository = env.GITHUB_OUTPUT_REPOSITORY.split("/", 1)
    base = f"https://api.github.com/repos/{owner}/{repository}"
    headers = {
        "Authorization": f"Bearer {env.GITHUB_OUTPUT_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    def request(method, path, **kwargs):
        response = requests.request(method, f"{base}{path}", headers=headers, timeout=30, **kwargs)
        response.raise_for_status()
        return response.json()

    reference = request("GET", f"/git/ref/heads/{env.GITHUB_OUTPUT_BRANCH}")
    parent_sha = reference["object"]["sha"]
    parent = request("GET", f"/git/commits/{parent_sha}")
    tree_items = []
    for path, content in files.items():
        blob_data = content if isinstance(content, dict) else {"content": content, "encoding": "utf-8"}
        blob = request("POST", "/git/blobs", json=blob_data)
        tree_items.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    tree = request(
        "POST",
        "/git/trees",
        json={"base_tree": parent["tree"]["sha"], "tree": tree_items},
    )
    commit = request(
        "POST",
        "/git/commits",
        json={"message": message, "tree": tree["sha"], "parents": [parent_sha]},
    )
    request(
        "PATCH",
        f"/git/refs/heads/{env.GITHUB_OUTPUT_BRANCH}",
        json={"sha": commit["sha"], "force": False},
    )
    return {
        "commit_sha": commit["sha"],
        "repository_url": f"https://github.com/{owner}/{repository}",
    }