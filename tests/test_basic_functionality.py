"""
Basic functionality tests for DataLineagePy.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datalineagepy import LineageDataFrame, LineageTracker
import pandas as pd


def test_basic_creation():
    """Test basic LineageDataFrame creation."""
    data = {'A': [1, 2, 3], 'B': [4, 5, 6]}
    ldf = LineageDataFrame(data, name="test_data")

    assert ldf.shape == (3, 2)
    assert list(ldf.columns) == ['A', 'B']
    print("✅ Basic creation test passed")


if __name__ == "__main__":
    print("🧪 Running basic test...")
    test_basic_creation()
    print("🎉 Test completed!")
