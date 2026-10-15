"""Minimal read-only client for the Schoology REST API (two-legged OAuth 1.0, PLAINTEXT)."""

import json
import secrets
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime

API_BASE = "https://api.schoology.com/v1"


@dataclass
class Assignment:
    course: str
    title: str
    due: datetime | None
    url: str
    id: str


class SchoologyClient:
    def __init__(self, consumer_key, consumer_secret):
        self.key = consumer_key
        self.secret = consumer_secret

    def _auth_header(self):
        params = {
            "realm": "Schoology API",
            "oauth_consumer_key": self.key,
            "oauth_token": "",
            "oauth_nonce": secrets.token_hex(8),
            "oauth_timestamp": str(int(time.time())),
            "oauth_signature_method": "PLAINTEXT",
            "oauth_version": "1.0",
            "oauth_signature": urllib.parse.quote(self.secret, safe="") + "%26",
        }
        return "OAuth " + ", ".join(f'{k}="{v}"' for k, v in params.items())

    def get(self, path, **query):
        url = API_BASE + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        request = urllib.request.Request(url, headers={
            "Authorization": self._auth_header(),
            "Accept": "application/json",
        })
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def me(self):
        return self.get("/users/me")

    def sections(self, user_id):
        return self.get(f"/users/{user_id}/sections").get("section", [])

    def assignments(self, section_id):
        return self.get(f"/sections/{section_id}/assignments", start=0, limit=200).get("assignment", [])

    def upcoming_work(self, now=None):
        user = self.me()
        user_id = user.get("uid") or user.get("id")
        work = []
        for section in self.sections(user_id):
            course = section.get("course_title") or section.get("section_title") or "Course"
            for raw in self.assignments(section["id"]):
                work.append(parse_assignment(raw, course))
        return filter_upcoming(work, now)


def parse_due(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def parse_assignment(raw, course):
    return Assignment(
        course=course,
        title=raw.get("title", "Untitled"),
        due=parse_due(raw.get("due")),
        url=raw.get("web_url", ""),
        id=str(raw.get("id", "")),
    )


def filter_upcoming(work, now=None):
    """Keep assignments due from now on (plus undated ones last), soonest first."""
    now = now or datetime.now()
    upcoming = [a for a in work if a.due is None or a.due >= now]
    return sorted(upcoming, key=lambda a: (a.due is None, a.due or datetime.max))
