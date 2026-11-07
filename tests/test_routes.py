import os
import tempfile
import unittest

from irrigation import create_app

GOOD = dict(crop="Wheat", stage="mid", soil="Loam", method="Drip", moisture=20, tmax=32,
            tmin=18, humidity=45, rain=0, lat=25.4, area=1000, flow=2000)


class Routes(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.client = create_app({"DATABASE": self.path, "TESTING": True}).test_client()

    def tearDown(self):
        os.remove(self.path)

    def test_pages_load(self):
        for url in ("/", "/history", "/health"):
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_recommend_returns_result_and_is_saved(self):
        r = self.client.post("/api/recommend", json=GOOD)
        self.assertEqual(r.status_code, 200)
        self.assertIn("litres", r.get_json())
        self.assertIn(b"Wheat", self.client.get("/history").data)

    def test_bad_input_returns_errors(self):
        r = self.client.post("/api/recommend", json={**GOOD, "humidity": 500})
        self.assertEqual(r.status_code, 400)
        self.assertTrue(r.get_json()["errors"])

    def test_non_json_body_rejected(self):
        self.assertEqual(self.client.post("/api/recommend", data="x").status_code, 400)

    def test_csv_export_and_clear(self):
        self.client.post("/api/recommend", json=GOOD)
        csv_text = self.client.get("/history.csv").data.decode()
        self.assertIn("crop", csv_text.splitlines()[0])
        self.assertEqual(len(csv_text.strip().splitlines()), 2)
        self.client.post("/history/clear")
        self.assertEqual(len(self.client.get("/history.csv").data.decode().strip().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
