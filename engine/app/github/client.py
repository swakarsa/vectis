"""
GitHub Defender Client for Vectis Sentinel
Handles GitHub REST API interactions:
- Fetching PR diffs and changed files
- Setting Commit Status checks (Pending, Failure, Success)
- Posting automated Sentinel Release Gate clearance comments
- Pushing IBM Granite 3.0 auto-heal shims directly to PR branches
"""

import os
import json
import base64
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

GITHUB_API_BASE = "https://api.github.com"

class GitHubDefenderClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "")

    def _headers(self, accept: str = "application/vnd.github+json") -> Dict[str, str]:
        headers = {
            "Accept": accept,
            "User-Agent": "Vectis-Sentinel-Release-Gate/1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        raw_accept: Optional[str] = None
    ) -> Any:
        url = f"{GITHUB_API_BASE}{endpoint}" if endpoint.startswith("/") else endpoint
        accept = raw_accept or "application/vnd.github+json"
        headers = self._headers(accept=accept)
        
        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = resp.read()
                if "application/json" in resp.headers.get("Content-Type", "") or accept == "application/vnd.github+json":
                    try:
                        return json.loads(res_data.decode("utf-8"))
                    except Exception:
                        return res_data.decode("utf-8")
                return res_data.decode("utf-8")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"GitHub API Error [{e.code}]: {err_body}")

    def get_pr_files(self, owner: str, repo: str, pull_number: int) -> List[Dict[str, Any]]:
        """Fetch list of modified files in a Pull Request."""
        return self._request(f"/repos/{owner}/{repo}/pulls/{pull_number}/files")

    def get_pr_diff(self, owner: str, repo: str, pull_number: int) -> str:
        """Fetch unified diff of a Pull Request."""
        return self._request(
            f"/repos/{owner}/{repo}/pulls/{pull_number}",
            raw_accept="application/vnd.github.v3.diff"
        )

    def set_commit_status(
        self,
        owner: str,
        repo: str,
        sha: str,
        state: str,
        description: str,
        target_url: str,
        context: str = "vectis/release-safety-gate"
    ) -> Dict[str, Any]:
        """
        Sets commit status check (pending, success, failure, error).
        Directly enforces merge blocking on GitHub Pull Requests.
        """
        payload = {
            "state": state,
            "target_url": target_url,
            "description": description[:140],  # GitHub 140 char limit
            "context": context
        }
        return self._request(f"/repos/{owner}/{repo}/statuses/{sha}", method="POST", data=payload)

    def post_pr_comment(self, owner: str, repo: str, pull_number: int, body: str) -> Dict[str, Any]:
        """Posts or updates Vectis Sentinel analysis bot comment on the PR."""
        payload = {"body": body}
        return self._request(f"/repos/{owner}/{repo}/issues/{pull_number}/comments", method="POST", data=payload)

    def push_file_to_branch(
        self,
        owner: str,
        repo: str,
        branch: str,
        file_path: str,
        content: str,
        commit_message: str
    ) -> Dict[str, Any]:
        """
        Commits a file directly to the PR branch via GitHub Contents API.
        Used by the 1-click Auto-Heal feature to deploy the IBM Granite shim.
        """
        # 1. Check if file already exists on the branch to get its SHA
        existing_sha = None
        try:
            file_meta = self._request(f"/repos/{owner}/{repo}/contents/{file_path}?ref={branch}")
            if isinstance(file_meta, dict) and "sha" in file_meta:
                existing_sha = file_meta["sha"]
        except Exception:
            pass  # File doesn't exist yet, clean creation

        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        payload: Dict[str, Any] = {
            "message": commit_message,
            "content": encoded_content,
            "branch": branch,
        }
        if existing_sha:
            payload["sha"] = existing_sha

        return self._request(f"/repos/{owner}/{repo}/contents/{file_path}", method="PUT", data=payload)
