#!/usr/bin/env python3
"""
Shared Telegram transport — the *route* every Ocean courier runs on.

Pure stdlib (no requests/curl) so every courier species — file delivery,
formatted text packs (e.g. Slingshot TOS), future ones — shares ONE
implementation of send / retry / 429-handling / topic-threading against a
single destination concept. Couriers differ only in what they ship; the route
is common.

Token resolution order (first hit wins):
  1. $OCEAN_TELEGRAM_BOT_TOKEN
  2. $TELEGRAM_BOT_TOKEN
  3. file at $OCEAN_TELEGRAM_TOKEN_FILE (default ~/.tg_token)
"""
import json
import mimetypes
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

API = "https://api.telegram.org/bot{token}/{method}"

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def resolve_token() -> str:
    for var in ("OCEAN_TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN"):
        v = os.environ.get(var)
        if v:
            return v.strip()
    path = Path(os.environ.get("OCEAN_TELEGRAM_TOKEN_FILE", str(Path.home() / ".tg_token")))
    if path.is_file():
        return path.read_text().strip()
    raise RuntimeError(
        "No bot token. Set $OCEAN_TELEGRAM_BOT_TOKEN / $TELEGRAM_BOT_TOKEN or create ~/.tg_token"
    )


def kind_for(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in VIDEO_EXT:
        return "video"
    if ext in PHOTO_EXT:
        return "photo"
    return "document"


def parse_link(link: str) -> dict:
    """Resolve a t.me link / @username / raw chat id into routing parts.

    Returns {chat_ref, thread_id, msg_id, kind}. `chat_ref` is what getChat
    accepts (numeric id or @username); None when unresolvable (e.g. invite link).
    """
    link = link.strip()
    if re.fullmatch(r"-?\d+", link):
        return {"chat_ref": link, "thread_id": None, "msg_id": None, "kind": "raw_id"}
    m = re.search(r"t\.me/(.+)$", link)
    tail = (m.group(1) if m else link.lstrip("/")).split("?")[0].rstrip("/")
    parts = [p for p in tail.split("/") if p]
    if parts and parts[0] == "c" and len(parts) >= 2:  # private supergroup/channel
        chat = "-100" + parts[1]
        a = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else None
        b = int(parts[3]) if len(parts) >= 4 and parts[3].isdigit() else None
        return {"chat_ref": chat, "thread_id": a, "msg_id": b, "kind": "private"}
    if parts and parts[0].startswith("+"):  # invite link — not bot-resolvable
        return {"chat_ref": None, "thread_id": None, "msg_id": None, "kind": "invite"}
    if parts:  # public @username[/thread-or-msg]
        a = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else None
        return {"chat_ref": "@" + parts[0], "thread_id": a, "msg_id": None, "kind": "public"}
    return {"chat_ref": None, "thread_id": None, "msg_id": None, "kind": "unknown"}


class Telegram:
    """Thin Telegram Bot API client with built-in 429 + transient retry."""

    def __init__(self, token: str | None = None):
        self.token = token or resolve_token()

    # ---- single attempts ------------------------------------------------
    def _form(self, method: str, params: dict) -> dict:
        data = urllib.parse.urlencode(params).encode()
        url = API.format(token=self.token, method=method)
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            return json.loads(e.read())

    def _upload(self, method: str, fields: dict, file_field: str, file_path: Path) -> dict:
        boundary = "----OceanCourier" + uuid.uuid4().hex
        nl = b"\r\n"
        body = bytearray()
        for k, v in fields.items():
            body += b"--" + boundary.encode() + nl
            body += f'Content-Disposition: form-data; name="{k}"'.encode() + nl + nl
            body += str(v).encode() + nl
        ctype = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        body += b"--" + boundary.encode() + nl
        body += (
            f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"'
        ).encode() + nl
        body += f"Content-Type: {ctype}".encode() + nl + nl
        body += file_path.read_bytes() + nl
        body += b"--" + boundary.encode() + b"--" + nl
        url = API.format(token=self.token, method=method)
        req = urllib.request.Request(url, data=bytes(body), method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            return json.loads(e.read())

    # ---- retrying request ----------------------------------------------
    def request(self, method, params=None, file_field=None, file_path=None, max_tries=3) -> dict:
        params = params or {}
        attempt = 0
        while True:
            attempt += 1
            if file_field and file_path:
                resp = self._upload(method, params, file_field, Path(file_path))
            else:
                resp = self._form(method, params)
            if resp.get("ok"):
                return resp
            if resp.get("error_code") == 429:
                wait = (resp.get("parameters") or {}).get("retry_after", 5)
                time.sleep(wait)
                continue
            if attempt < max_tries:
                time.sleep(5)
                continue
            return resp

    # ---- high-level helpers --------------------------------------------
    def get_me(self) -> dict:
        return self.request("getMe")

    def get_chat(self, chat_id) -> dict:
        return self.request("getChat", {"chat_id": chat_id})

    def send_message(self, chat_id, text, thread_id=None, parse_mode=None, disable_preview=True) -> dict:
        p = {"chat_id": chat_id, "text": text}
        if thread_id:
            p["message_thread_id"] = thread_id
        if parse_mode:
            p["parse_mode"] = parse_mode
        if disable_preview:
            p["disable_web_page_preview"] = "true"
        return self.request("sendMessage", p)

    def send_file(self, chat_id, path, thread_id=None, kind=None) -> dict:
        path = Path(path)
        kind = kind or kind_for(path)
        method = {"video": "sendVideo", "photo": "sendPhoto", "document": "sendDocument"}[kind]
        p = {"chat_id": chat_id}
        if thread_id:
            p["message_thread_id"] = thread_id
        if kind == "video":
            p["supports_streaming"] = "true"
        return self.request(method, p, file_field=kind, file_path=path)
