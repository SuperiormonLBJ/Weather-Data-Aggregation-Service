"""
Basic test to verify test setup works
"""
import pytest
import sys
import os

# Add app to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_basic_import():
    """Test that we can import basic modules"""
    try:
        from app.config import OPENWEATHER_API_KEY
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import app.config: {e}")

def test_pytest_working():
    """Test that pytest is working"""
    assert 1 + 1 == 2

@pytest.mark.asyncio
async def test_async_working():
    """Test that async tests work"""
    import asyncio
    await asyncio.sleep(0.01)  # Small delay
    assert True
