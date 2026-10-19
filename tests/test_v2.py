import unittest

from binauralbench_v2 import run


class NonOracleSeparator(unittest.TestCase):
    def test_published_scene_without_the_clean_target(self):
        r = run()
        # The crossover is found from the mixture's own spectrum.
        self.assertTrue(330 < r["crossover_hz"] < 770)
        self.assertEqual(r["mono"]["ild_db"], 0.0)
        self.assertEqual(r["per_ear"]["ild_db"], 0.0)
        self.assertLess(r["linked"]["ild_error_db"], 0.1)
        self.assertGreater(r["linked"]["sdr_db"], 25)

    def test_linked_beats_collapsing_on_a_hard_scene(self):
        r = run(seed=3, f_target=430.0, f_interf=600.0, g=(0.8, 0.2), h=(1.1, 0.7), noise=0.2)
        self.assertLess(r["linked"]["ild_error_db"], r["mono"]["ild_error_db"])
        self.assertLess(r["linked"]["ild_error_db"], r["per_ear"]["ild_error_db"])


if __name__ == "__main__":
    unittest.main()
