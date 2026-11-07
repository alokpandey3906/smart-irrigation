import unittest

from irrigation.engine import (effective_rain, extraterrestrial_radiation,
                               hargreaves_et0, humidity_adjustment, recommend)

BASE = dict(crop="Wheat", stage="mid", soil="Loam", method="Drip", moisture=20.0,
            tmax=32.0, tmin=18.0, humidity=45.0, rain=0.0, lat=25.4, area=1000.0, flow=2000.0)
DOY = 60  # 1 March


class EngineMath(unittest.TestCase):
    def test_ra_in_expected_range(self):
        self.assertTrue(11 < extraterrestrial_radiation(25.4, DOY) < 15)

    def test_et0_zero_when_no_temperature_range(self):
        self.assertEqual(hargreaves_et0(25, 25, 25.4, DOY), 0.0)

    def test_et0_rises_with_temperature_range(self):
        self.assertGreater(hargreaves_et0(35, 15, 25.4, DOY), hargreaves_et0(30, 20, 25.4, DOY))

    def test_humidity_adjustment(self):
        self.assertEqual(humidity_adjustment(50), 1.0)
        self.assertAlmostEqual(humidity_adjustment(100), 0.8)

    def test_effective_rain(self):
        self.assertEqual(effective_rain(4.9), 0.0)
        self.assertAlmostEqual(effective_rain(10), 8.0)


class Decisions(unittest.TestCase):
    def rec(self, **over):
        return recommend({**BASE, **over}, doy=DOY)

    def test_wet_soil_needs_nothing(self):
        r = self.rec(moisture=28)
        self.assertEqual(r["level"], "ok")
        self.assertEqual(r["litres"], 0)

    def test_dry_soil_is_urgent(self):
        r = self.rec(moisture=14)
        self.assertEqual(r["level"], "urgent")
        self.assertGreater(r["litres"], 0)

    def test_moderately_dry_soil_irrigates(self):
        self.assertEqual(self.rec(moisture=19)["level"], "irrigate")

    def test_rain_skips_irrigation(self):
        dry = self.rec(moisture=20)
        self.assertEqual(dry["level"], "irrigate")
        wet = self.rec(moisture=20, rain=40)
        self.assertEqual(wet["level"], "skip")
        self.assertEqual(wet["litres"], 0)

    def test_litres_equal_depth_times_area(self):
        r = self.rec(moisture=15)
        self.assertAlmostEqual(r["litres"], r["gross_mm"] * 1000, delta=60)

    def test_less_efficient_method_uses_more_water(self):
        drip = self.rec(moisture=15, method="Drip")["litres"]
        flood = self.rec(moisture=15, method="Flood")["litres"]
        self.assertGreater(flood, drip)

    def test_pump_hours_scale_with_flow(self):
        slow = self.rec(moisture=15, flow=1000)["hours"]
        fast = self.rec(moisture=15, flow=4000)["hours"]
        self.assertGreater(slow, fast)

    def test_moisture_clamped_between_wilting_and_field_capacity(self):
        self.assertEqual(self.rec(moisture=0)["moisture_pct"], 0)
        self.assertEqual(self.rec(moisture=60)["moisture_pct"], 100)


if __name__ == "__main__":
    unittest.main()
