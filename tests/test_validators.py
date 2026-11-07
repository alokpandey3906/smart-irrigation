import unittest

from irrigation.validators import validate

GOOD = dict(crop="Wheat", stage="mid", soil="Loam", method="Drip", moisture="20", tmax="32",
            tmin="18", humidity="45", rain="0", lat="25.4", area="1000", flow="2000")


class Validation(unittest.TestCase):
    def test_valid_input_passes_and_is_converted(self):
        clean, errors = validate(GOOD)
        self.assertEqual(errors, [])
        self.assertEqual(clean["moisture"], 20.0)

    def test_missing_field(self):
        bad = {k: v for k, v in GOOD.items() if k != "area"}
        self.assertTrue(validate(bad)[1])

    def test_text_instead_of_number(self):
        self.assertTrue(validate({**GOOD, "tmax": "hot"})[1])

    def test_out_of_range(self):
        self.assertTrue(validate({**GOOD, "humidity": "150"})[1])

    def test_unknown_crop(self):
        self.assertTrue(validate({**GOOD, "crop": "Banana"})[1])

    def test_tmax_below_tmin(self):
        self.assertTrue(validate({**GOOD, "tmax": "10", "tmin": "20"})[1])

    def test_nan_and_infinity_rejected(self):
        self.assertTrue(validate({**GOOD, "rain": "nan"})[1])
        self.assertTrue(validate({**GOOD, "rain": "inf"})[1])


if __name__ == "__main__":
    unittest.main()
