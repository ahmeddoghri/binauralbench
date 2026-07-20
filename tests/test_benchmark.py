import unittest
import binauralbench

class BenchmarkTest(unittest.TestCase):
    def test_research_method_clears_baseline(self):
        result = binauralbench.run()
        self.assertGreaterEqual(result["ild_error_reduction_pct"], 70)

if __name__ == "__main__":
    unittest.main()
