import urllib.parse
import httpx
from app.config import settings

GRAPH = "https://graph.microsoft.com/v1.0"

def auth_url(state: str) -> str:
    params = {
        "client_id": settings.ONEDRIVE_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.ONEDRIVE_REDIRECT_URL,
        "response_mode": "query",
        "scope": "offline_access Files.ReadWrite",
        "state": state
    }
    return "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?" + urllib.parse.urlencode(params)

async def exchange_code(code: str) -> dict:
    url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        "client_id": settings.ONEDRIVE_CLIENT_ID,
        "client_secret": settings.ONEDRIVE_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.ONEDRIVE_REDIRECT_URL,
        "scope": "offline_access Files.ReadWrite"
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, data=data)
        r.raise_for_status()
        return r.json()

async def refresh(refresh_token: str) -> dict:
    url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        "client_id": settings.ONEDRIVE_CLIENT_ID,
        "client_secret": settings.ONEDRIVE_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "redirect_uri": settings.ONEDRIVE_REDIRECT_URL,
        "scope": "offline_access Files.ReadWrite"
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, data=data)
        r.raise_for_status()
        return r.json()

async def ensure_folder(access_token: str, path: str):
    url = f"{GRAPH}/me/drive/root:{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {access_token}"})
        if r.status_code == 200:
            return
        parent = "/".join(path.rstrip("/").split("/")[:-1])
        name = path.rstrip("/").split("/")[-1]
        if parent:
            await ensure_folder(access_token, parent)
        parent_url = f"{GRAPH}/me/drive/root:{parent}:/children" if parent else f"{GRAPH}/me/drive/root/children"
        payload = {"name": name, "folder": {}, "@microsoft.graph.conflictBehavior": "rename"}
        await client.post(parent_url, headers={"Authorization": f"Bearer {access_token}"}, json=payload)

async def upload_bytes(access_token: str, path: str, content: bytes, content_type: str):
    folder = "/".join(path.split("/")[:-1])
    if folder:
        await ensure_folder(access_token, folder)
    url = f"{GRAPH}/me/drive/root:{path}:/content"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.put(url, headers={"Authorization": f"Bearer {access_token}", "Content-Type": content_type}, content=content)
        r.raise_for_status()
        return r.json().get("webUrl", "")
