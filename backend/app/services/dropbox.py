import urllib.parse
import json
import httpx
from app.config import settings

AUTHORIZE = "https://www.dropbox.com/oauth2/authorize"
TOKEN = "https://api.dropboxapi.com/oauth2/token"
CREATE_FOLDER = "https://api.dropboxapi.com/2/files/create_folder_v2"
UPLOAD = "https://content.dropboxapi.com/2/files/upload"

def auth_url(state: str) -> str:
    params = {
        "client_id": settings.DROPBOX_APP_KEY,
        "response_type": "code",
        "redirect_uri": settings.DROPBOX_REDIRECT_URL,
        "state": state,
    }
    return AUTHORIZE + "?" + urllib.parse.urlencode(params)

async def exchange_code(code: str) -> dict:
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": settings.DROPBOX_APP_KEY,
        "client_secret": settings.DROPBOX_APP_SECRET,
        "redirect_uri": settings.DROPBOX_REDIRECT_URL,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(TOKEN, data=data)
        r.raise_for_status()
        return r.json()

async def ensure_folder(access_token: str, path: str):
    path = path if path.startswith("/") else "/" + path
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            CREATE_FOLDER,
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json={"path": path, "autorename": False}
        )
        if r.status_code == 409:
            return
        r.raise_for_status()

async def upload_bytes(access_token: str, path: str, content: bytes):
    path = path if path.startswith("/") else "/" + path
    folder = "/".join(path.split("/")[:-1])
    if folder:
        await ensure_folder(access_token, folder)
    args = {"path": path, "mode": "add", "autorename": True, "mute": True, "strict_conflict": False}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            UPLOAD,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/octet-stream",
                "Dropbox-API-Arg": json.dumps(args)
            },
            content=content
        )
        r.raise_for_status()
        return r.json()
