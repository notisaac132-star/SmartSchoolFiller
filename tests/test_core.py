import json
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from schoolfiller import chrome_profile, settings
from schoolfiller.schoology import SchoologyClient, filter_upcoming, parse_assignment


class ChromeProfileTests(unittest.TestCase):
    def test_find_profile_by_display_name(self):
        with TemporaryDirectory() as tmp:
            state = {"profile": {"info_cache": {
                "Default": {"name": "Personal"},
                "Profile 3": {"name": "School"},
            }}}
            Path(tmp, "Local State").write_text(json.dumps(state))
            self.assertEqual(chrome_profile.find_profile("school", tmp), "Profile 3")
            self.assertIsNone(chrome_profile.find_profile("work", tmp))

    def test_missing_local_state(self):
        with TemporaryDirectory() as tmp:
            self.assertEqual(chrome_profile.list_profiles(tmp), {})


class SchoologyTests(unittest.TestCase):
    def test_filter_upcoming_sorts_and_drops_past(self):
        now = datetime(2026, 10, 15, 12)
        work = [
            parse_assignment({"id": 1, "title": "Late", "due": "2026-10-20 23:59:00"}, "Math"),
            parse_assignment({"id": 2, "title": "Past", "due": "2026-10-01 23:59:00"}, "Math"),
            parse_assignment({"id": 3, "title": "Undated", "due": ""}, "Art"),
            parse_assignment({"id": 4, "title": "Soon", "due": "2026-10-16 08:00:00"}, "Bio"),
        ]
        titles = [a.title for a in filter_upcoming(work, now)]
        self.assertEqual(titles, ["Soon", "Late", "Undated"])

    def test_auth_header_is_plaintext_oauth(self):
        header = SchoologyClient("key", "s&cret")._auth_header()
        self.assertTrue(header.startswith("OAuth "))
        self.assertIn('oauth_consumer_key="key"', header)
        self.assertIn('oauth_signature="s%26cret%26"', header)


class SettingsTests(unittest.TestCase):
    def test_round_trip(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp, "s.json")
            data = settings.load(path)
            self.assertEqual(data["profile_name"], "school")
            data["done"].append("42")
            settings.save(data, path)
            self.assertEqual(settings.load(path)["done"], ["42"])


if __name__ == "__main__":
    unittest.main()
