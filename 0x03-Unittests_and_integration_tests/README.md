# GitHub Organization Client

A Python client library for interacting with GitHub's organization API, featuring utility functions and comprehensive unit testing.

## Files Overview

### `utils.py`
Generic utility functions used throughout the application:

- **`access_nested_map(nested_map, path)`**: Safely navigate nested dictionaries using a sequence of keys
- **`get_json(url)`**: Fetch and parse JSON data from remote URLs
- **`memoize`**: Decorator for caching method results to improve performance

### `client.py`
Main GitHub organization client implementation:

- **`GithubOrgClient`**: Primary class for interacting with GitHub's organization API
  - Fetches organization information
  - Retrieves repository lists
  - Filters repositories by license
  - Implements caching for efficient API usage

### `test_utils.py`
Comprehensive unit tests for all utility functions:

- **`TestAccessNestedMap`**: Tests for nested dictionary navigation
- **`TestGetJson`**: Mocked tests for HTTP JSON fetching
- **`TestMemoize`**: Tests for method result caching

## Key Features

- **Caching**: Uses memoization to avoid redundant API calls
- **Error Handling**: Graceful handling of missing keys and network errors
- **Type Safety**: Full type hints for better code maintainability
- **Comprehensive Testing**: Parameterized tests with mocking for external dependencies

## Usage Example

```python
from client import GithubOrgClient

# Initialize client for a GitHub organization
client = GithubOrgClient("google")

# Get all public repositories
repos = client.public_repos()

# Get repositories with specific license
mit_repos = client.public_repos(license="mit")

# Access organization information
org_info = client.org
```

## Testing

Run the test suite:

```bash
python -m unittest test_utils.py
```

## Dependencies

- `requests`: For HTTP requests
- `parameterized`: For parameterized testing
- `unittest.mock`: For mocking external dependencies

## Design Patterns

- **Memoization**: Caches expensive API calls
- **Property Pattern**: Clean access to computed values
- **Static Methods**: Pure functions that don't require instance state
- **Parameterized Testing**: Efficient testing of multiple input scenarios