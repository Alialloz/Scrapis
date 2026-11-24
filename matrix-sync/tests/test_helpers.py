import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import helpers  # noqa: E402


class HelpersTest(unittest.TestCase):
    def test_matrix_date(self):
        self.assertEqual(helpers.matrix_date("2026-11-20"), "20261120+")
        with self.assertRaises(ValueError):
            helpers.matrix_date("20/11/2026")

    def test_header_en_vigueur(self):
        parsed = helpers.parse_header("19643026 (En vigueur)")
        self.assertEqual(parsed["number"], "19643026")
        self.assertEqual(parsed["status"], "En vigueur")
        self.assertIsNone(parsed["date"])

    def test_header_expire(self):
        parsed = helpers.parse_header("19356747 (Expiré 2026-11-20)")
        self.assertEqual(parsed["number"], "19356747")
        self.assertEqual(parsed["status"], "Expiré")
        self.assertEqual(parsed["date"], "2026-11-20")

    def test_header_vendu_avec_pa(self):
        parsed = helpers.parse_header(
            "19276389 (Vendu 2026-11-19, 200 jours) (PA acceptée 2026-08-22, 111 jours)"
        )
        self.assertEqual(parsed["number"], "19276389")
        self.assertEqual(parsed["status"], "Vendu")
        self.assertEqual(parsed["date"], "2026-11-19")

    def test_status_matches_phase(self):
        self.assertTrue(helpers.header_status_matches("EXPIRED", "Expiré"))
        self.assertTrue(helpers.header_status_matches("SOLD", "Vendu"))
        self.assertFalse(helpers.header_status_matches("SOLD", "En vigueur"))
        self.assertFalse(helpers.header_status_matches("EXPIRED", None))
        self.assertTrue(helpers.header_status_matches("NEW", "En vigueur"))

    def test_counter(self):
        self.assertEqual(helpers.parse_counter("· 1 de 7"), (1, 7))
        self.assertIsNone(helpers.parse_counter("rien"))

    def test_itq_url(self):
        href = "javascript:Dpy.ITQPopup('74',160,'','11 Mzc4NzAwNjk0','8fdf7af9b8ceea92cb0e05386c6211e9',400,400)"
        self.assertEqual(
            helpers.itq_popup_url("https://matrix.centris.ca", href),
            "https://matrix.centris.ca/Matrix/Public/DisplayITQPopup.aspx"
            "?iid=74&did=160&strtabid=&params=11%20Mzc4NzAwNjk0&exk=8fdf7af9b8ceea92cb0e05386c6211e9",
        )
        self.assertIsNone(helpers.itq_popup_url("https://matrix.centris.ca", "javascript:void(0)"))

    def test_doors_from_type(self):
        self.assertEqual(helpers.doors_from_property_type("Quadruplex"), 4)
        self.assertEqual(helpers.doors_from_property_type("Triplex"), 3)
        self.assertEqual(helpers.doors_from_property_type("Duplex"), 2)
        self.assertIsNone(helpers.doors_from_property_type("Unifamiliale"))


if __name__ == "__main__":
    unittest.main()
