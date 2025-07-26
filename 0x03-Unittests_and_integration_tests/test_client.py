#!/usr/bin/env python3
"""Unit and integration tests for GithubOrgClient class.
Covers testing of org fetching, public repo listing,
license filtering, and memoization behavior.
"""

import unittest
from unittest.mock import patch, PropertyMock, Mock
from parameterized import parameterized, parameterized_class
from client import GithubOrgClient
from fixtures import org_payload, repos_payload, expected_repos, apache2_repos
from typing import Dict


class TestGithubOrgClient(unittest.TestCase):
    """Unit tests for GithubOrgClient class."""

    @parameterized.expand([
        ("google",),
        ("abc",)
    ])
    @patch("client.get_json")
    def test_org(self, org_name, mock_get_json):
        """Test that .org() returns correct organization data."""
        # Set up the mock return value
        expected = {"payload": True}
        mock_get_json.return_value = expected

        # Create client and call .org()
        client = GithubOrgClient(org_name)
        result = client.org

        # Assert get_json called with correct URL
        expected_url = f"https://api.github.com/orgs/{org_name}"
        mock_get_json.assert_called_once_with(expected_url)
        self.assertEqual(result, expected)

    @patch.object(GithubOrgClient, "org", new_callable=PropertyMock)
    def test_public_repos_url(self, mock_org):
        """Test that _public_repos_url returns correct url."""
        test_url = "https://api.github.com/orgs/test_org/repos"
        mock_org.return_value = {"repos_url": test_url}

        client = GithubOrgClient("test_org")
        result = client._public_repos_url

        self.assertEqual(result, test_url)

    @patch("client.get_json")
    def test_public_repos(self, mock_get_json):
        """Test that public_repos returns a list of repo names."""
        # Define a fake payload that get_json will return
        payload = [
            {"name": "repo1"},
            {"name": "repo2"},
            {"name": "repo3"},
        ]
        mock_get_json.return_value = payload

        # Mock the _public_repos_url property using patch as context manager
        with patch("client.GithubOrgClient._public_repos_url",
                   new_callable=PropertyMock) as mock_url:
            test_url = "https://api.github.com/orgs/test_org/repos"
            mock_url.return_value = test_url
            
            client = GithubOrgClient("test_org")
            result = client.public_repos()

            # Assert the result is a list of repo names
            self.assertEqual(result, ["repo1", "repo2", "repo3"])

            # Check each mock was called exactly once
            mock_url.assert_called_once()
            mock_get_json.assert_called_once_with(test_url)

    @parameterized.expand([
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False),
    ])
    def test_has_license(self, repo: Dict[str, Dict[str, str]], 
                        license_key: str, expected: bool) -> None:
        """Test that has_license returns correct boolean for license match."""
        result = GithubOrgClient.has_license(repo, license_key)
        self.assertEqual(result, expected)


@parameterized_class([
    {
        "org_payload": org_payload,
        "repos_payload": repos_payload,
        "expected_repos": expected_repos,
        "apache2_repos": apache2_repos,
    }
])
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """Integration tests for GithubOrgClient using actual data fixtures."""

    @classmethod
    def setUpClass(cls):
        """Patch requests.get and set side_effects for org and repos URLs."""
        cls.get_patcher = patch("requests.get")
        mock_get = cls.get_patcher.start()

        # Create mock response objects with .json() method
        org_response = Mock()
        org_response.json.return_value = cls.org_payload
        
        repos_response = Mock()
        repos_response.json.return_value = cls.repos_payload

        # Set side_effect to return appropriate responses
        mock_get.side_effect = [org_response, repos_response]

    @classmethod
    def tearDownClass(cls):
        """Stop the patched requests.get."""
        cls.get_patcher.stop()

    def test_public_repos(self):
        """Test public_repos returns expected repositories."""
        client = GithubOrgClient("google")
        self.assertEqual(client.public_repos(), self.expected_repos)

    def test_public_repos_with_license(self):
        """Test public_repos filters repos by license."""
        client = GithubOrgClient("google")
        self.assertEqual(client.public_repos(license="apache-2.0"), 
                        self.apache2_repos)


if __name__ == '__main__':
    unittest.main()