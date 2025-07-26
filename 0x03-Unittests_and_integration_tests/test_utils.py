#!/usr/bin/env python3
"""
Unit tests for utility functions in utils.py.
Covers:
- access_nested_map
- get_json
- memoize
"""
import unittest
from parameterized import parameterized
from utils import access_nested_map, get_json, memoize
from unittest.mock import Mock, patch
from typing import Mapping, Sequence, Any, Dict


class TestAccessNestedMap(unittest.TestCase):
    """Unit tests for access_nested_map function."""
    
    # Lets me run the same test method with different inputs,
    # without the need to repeat code for many input variations.
    @parameterized.expand([
        ({"a": 1}, ("a",), 1),
        ({"a": {"b": 2}}, ("a",), {"b": 2}),
        ({"a": {"b": 2}}, ("a", "b"), 2),
    ])
    def test_access_nested_map(self, nested_map: Mapping, path: Sequence, expected: Any) -> None:
        """Test correct values returned from nested maps."""
        self.assertEqual(access_nested_map(nested_map, path), expected)
    
    @parameterized.expand([
        ({}, ("a",)),
        ({"a": 1}, ("a", "b")),
    ])
    def test_access_nested_map_exception(self, nested_map: Mapping, path: Sequence) -> None:
        """Test KeyError is raised for missing keys"""
        with self.assertRaises(KeyError) as cm:
            access_nested_map(nested_map, path)
        self.assertEqual(cm.exception.args[0], path[-1])


class TestGetJson(unittest.TestCase):
    """Unit tests for get_json function."""
    
    @parameterized.expand([
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False}),
    ])
    def test_get_json(self, test_url: str, test_payload: Dict) -> None:
        """Test get_json fetches and returns the correct JSON data."""
        # Patch replaces requests.get in the utils module with a mock
        with patch("utils.requests.get") as mock_get:
            # create a mock response with .json method returning test_payload
            mock_response = Mock()
            mock_response.json.return_value = test_payload
            mock_get.return_value = mock_response
            
            result = get_json(test_url)
            
            # Assert requests.get was called once with test_url
            mock_get.assert_called_once_with(test_url)
            # Assert the result matches the expected payload
            self.assertEqual(result, test_payload)


class TestMemoize(unittest.TestCase):
    """Unit tests for the memoize decorator."""
    
    def test_memoize(self) -> None:
        """Test that a memoized method is only called once."""
        class TestClass:
            """Test class with memoized property."""
            
            def a_method(self):
                """Sample method returning 42"""
                return 42
            
            @memoize
            def a_property(self):
                """Memoized property calling a_method."""
                return self.a_method()
        
        # mocks TestClass.a_method
        with patch.object(TestClass, "a_method", return_value=42) as mock_method:
            obj = TestClass()
            result1 = obj.a_property  # First call, should call a_method
            result2 = obj.a_property  # Second call, should not call a_method again
            
            self.assertEqual(result1, 42)
            self.assertEqual(result2, 42)
            # Ensure a_method was only called once
            mock_method.assert_called_once()


if __name__ == '__main__':
    unittest.main()