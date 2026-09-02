import unittest, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from detect_bands import detect

BASE = [10, 11, 9, 10, 10, 11, 9, 10, 10, 10]  # mean 10, sd ≈ 0.63

class DetectBands(unittest.TestCase):
    def test_no_breach(self):
        self.assertIsNone(detect(BASE + [10, 10.5, 9.5], 10)["tier"])
    def test_three_sigma_single_point(self):
        self.assertEqual(detect(BASE + [10, 13], 10)["tier"], "3sigma")
    def test_two_sigma_two_of_three(self):
        self.assertEqual(detect(BASE + [11.5, 10, 11.5], 10)["tier"], "2sigma")
    def test_one_sigma_four_of_five(self):
        self.assertEqual(detect(BASE + [10.8, 10.8, 10, 10.8, 10.8], 10)["tier"], "1sigma")
    def test_needs_points_beyond_window(self):
        self.assertIsNone(detect(BASE, 10)["tier"])

if __name__ == "__main__": unittest.main()
