import unittest
import numpy as np
from services.segmentation.service import SegmentationEngine

class TestSegmentation(unittest.TestCase):
    def setUp(self):
        self.engine = SegmentationEngine()
    
    def test_volume_classification(self):
        data = np.array([100, 200, 50, 30, 10, 5, 2, 1, 0, 0, 0, 0])
        result = self.engine.segment(data)
        self.assertIn(result.volume_class, ['A', 'B', 'C'])
    
    def test_intermittency_detection(self):
        # More than 50% zeros
        data = np.array([100, 0, 0, 0, 0, 0, 0, 50, 0, 0, 0, 0])
        result = self.engine.segment(data)
        self.assertTrue(result.intermittent)
    
    def test_trend_detection(self):
        # Upward trend
        data = np.arange(1, 37)
        result = self.engine.segment(data)
        self.assertEqual(result.trend, 'upward')

if __name__ == '__main__':
    unittest.main()