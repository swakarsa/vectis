import os
import json
import urllib.parse
import urllib.request
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Header
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/api", tags=["GitHub Auth"])

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")

from pydantic import BaseModel

class TokenAuthRequest(BaseModel):
    token: str

@router.get("/auth/github/login")
def github_login(redirect_uri: Optional[str] = None):
    """Initiates GitHub OAuth flow."""
    if not GITHUB_CLIENT_ID:
        return {
            "configured": False,
            "url": None,
            "message": "GITHUB_CLIENT_ID is not configured in backend environment."
        }
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "scope": "repo,read:user,user:email",
        "redirect_uri": redirect_uri or f"{FRONTEND_BASE_URL}/api/auth/github/callback",
    }
    url = f"https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}"
    return {"configured": True, "url": url}

@router.post("/auth/github/token")
def authenticate_pat(req: TokenAuthRequest):
    """Validates a GitHub Personal Access Token and returns verified user profile."""
    headers = {
        "Authorization": f"Bearer {req.token.strip()}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "Vectis-Sentinel"
    }
    try:
        user_req = urllib.request.Request("https://api.github.com/user", headers=headers)
        with urllib.request.urlopen(user_req, timeout=10) as resp:
            user_data = json.loads(resp.read().decode("utf-8"))
        return {
            "status": "success",
            "user": {
                "id": user_data.get("id"),
                "login": user_data.get("login"),
                "name": user_data.get("name"),
                "avatar_url": user_data.get("avatar_url"),
                "html_url": user_data.get("html_url")
            },
            "token": req.token.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid GitHub Token: {str(e)}")

@router.get("/auth/github/callback")
def github_callback(code: str = Query(...)):
    """Exchanges authorization code for GitHub access token."""
    token_url = "https://github.com/login/oauth/access_token"
    payload = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        req = urllib.request.Request(
            token_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
        access_token = data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail=data.get("error_description", "Failed to retrieve access token"))
            
        # Redirect back to frontend with token in fragment or query
        return RedirectResponse(url=f"{FRONTEND_BASE_URL}/cockpit?access_token={access_token}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/auth/user")
def get_user_profile(authorization: Optional[str] = Header(None)):
    """Returns profile of authenticated GitHub user."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    headers = {
        "Authorization": authorization,
        "Accept": "application/vnd.github+json",
        "User-Agent": "Vectis-Sentinel"
    }
    try:
        req = urllib.request.Request("https://api.github.com/user", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            user_data = json.loads(resp.read().decode("utf-8"))
            return {
                "id": user_data.get("id"),
                "login": user_data.get("login"),
                "name": user_data.get("name"),
                "avatar_url": user_data.get("avatar_url"),
                "html_url": user_data.get("html_url")
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/repos")
def list_user_repositories(authorization: Optional[str] = Header(None)):
    """Lists repositories accessible to the authenticated user."""
    if not authorization:
        # Fallback for unauthenticated demo
        return [
            {"full_name": "swakarsa/vectis", "name": "vectis", "owner": "swakarsa", "default_branch": "main", "is_fixture": False},
            {"full_name": "swakarsa/sample-fintech-monorepo", "name": "sample-fintech-monorepo", "owner": "swakarsa", "default_branch": "main", "is_fixture": True}
        ]

    headers = {
        "Authorization": authorization,
        "Accept": "application/vnd.github+json",
        "User-Agent": "Vectis-Sentinel"
    }
    try:
        req = urllib.request.Request("https://api.github.com/user/repos?sort=updated&per_page=30", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            repos_data = json.loads(resp.read().decode("utf-8"))
            return [
                {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "full_name": r.get("full_name"),
                    "owner": r.get("owner", {}).get("login"),
                    "private": r.get("private"),
                    "default_branch": r.get("default_branch", "main"),
                    "html_url": r.get("html_url")
                }
                for r in repos_data
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
