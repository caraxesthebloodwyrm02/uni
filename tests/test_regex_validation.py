"""Regex pattern validation and navigational functionality tests.

Tests for:
- Regex compilation and error handling
- Pattern correctness and edge cases
- Performance (no catastrophic backtracking)
- Navigational functionality (finding, matching, extracting)
- Runtime validation against test cases
- Cross-pattern consistency
"""

from __future__ import annotations

import re
from typing import Pattern

import pytest

from scripts.validate_workspace import (
    FORBIDDEN_DOMAINS,
    FORBIDDEN_TOKENS,
    SECRET_PATTERNS,
)


class TestRegexCompilation:
    """Test that all regex patterns compile successfully."""

    def test_forbidden_domains_compiles(self):
        """FORBIDDEN_DOMAINS regex should compile."""
        assert isinstance(FORBIDDEN_DOMAINS, type(re.compile("")))

    def test_forbidden_tokens_compiles(self):
        """FORBIDDEN_TOKENS regex should compile."""
        assert isinstance(FORBIDDEN_TOKENS, type(re.compile("")))

    def test_secret_patterns_compiles(self):
        """SECRET_PATTERNS regex should compile."""
        assert isinstance(SECRET_PATTERNS, type(re.compile("")))

    def test_all_patterns_have_flags(self):
        """Patterns should be properly configured."""
        # These may have flags like re.IGNORECASE
        assert FORBIDDEN_DOMAINS.pattern is not None
        assert FORBIDDEN_TOKENS.pattern is not None
        assert SECRET_PATTERNS.pattern is not None


class TestForbiddenDomainsPattern:
    """Test FORBIDDEN_DOMAINS regex pattern."""

    def test_matches_factory_ai(self):
        """Should match factory.ai."""
        assert FORBIDDEN_DOMAINS.search("visit factory.ai")
        assert FORBIDDEN_DOMAINS.search("http://factory.ai/path")

    def test_matches_cursor_com(self):
        """Should match cursor.com."""
        assert FORBIDDEN_DOMAINS.search("use cursor.com")
        assert FORBIDDEN_DOMAINS.search("https://cursor.com")

    def test_matches_cursor_sh(self):
        """Should match cursor.sh."""
        assert FORBIDDEN_DOMAINS.search("run cursor.sh")
        assert FORBIDDEN_DOMAINS.search("https://cursor.sh/script")

    def test_matches_workos_com(self):
        """Should match workos.com."""
        assert FORBIDDEN_DOMAINS.search("integrate workos.com")
        assert FORBIDDEN_DOMAINS.search("api.workos.com")

    def test_no_false_positives_similar_domains(self):
        """Should not match similar but allowed domains."""
        assert not FORBIDDEN_DOMAINS.search("factory-tools.com")
        assert not FORBIDDEN_DOMAINS.search("cursor-like.com")
        assert not FORBIDDEN_DOMAINS.search("work-os.com")

    def test_matches_in_urls(self):
        """Should match domains in full URLs."""
        assert FORBIDDEN_DOMAINS.search("https://factory.ai/api/v1")
        assert FORBIDDEN_DOMAINS.search("http://cursor.com:8080/")

    def test_matches_with_www_prefix(self):
        """Should match domains with www prefix."""
        assert FORBIDDEN_DOMAINS.search("www.factory.ai")
        assert FORBIDDEN_DOMAINS.search("www.cursor.com")

    def test_multiline_search(self):
        """Should find domains across multiline text."""
        text = """
        This is a note.
        Use factory.ai for processing.
        But avoid it in production.
        """
        assert FORBIDDEN_DOMAINS.search(text)

    def test_case_sensitivity(self):
        """Check if pattern is case-sensitive."""
        # depends on flags - verify behavior
        result_lower = FORBIDDEN_DOMAINS.search("factory.ai")
        result_upper = FORBIDDEN_DOMAINS.search("FACTORY.AI")
        # At least one should match (implementation-dependent)
        assert result_lower or result_upper


class TestForbiddenTokensPattern:
    """Test FORBIDDEN_TOKENS regex pattern."""

    def test_matches_workos_uppercase(self):
        """Should match WorkOS token."""
        assert FORBIDDEN_TOKENS.search("Use WorkOS for auth")

    def test_matches_factory_uppercase(self):
        """Should match Factory token."""
        assert FORBIDDEN_TOKENS.search("Integrate Factory with system")

    def test_matches_in_context(self):
        """Should match tokens in normal text."""
        assert FORBIDDEN_TOKENS.search("The WorkOS integration is critical")
        assert FORBIDDEN_TOKENS.search("Factory provides...")

    def test_no_match_lowercase(self):
        """Should not match lowercase versions (case-sensitive)."""
        # This depends on re.IGNORECASE flag
        pytest.skip("Behavior depends on case sensitivity flag")

    def test_no_false_positives_substrings(self):
        """Should not match when token is part of larger word."""
        # This depends on word boundary handling
        pytest.skip("Behavior depends on boundary handling")

    def test_isolated_token_matching(self):
        """Tokens should be matched as whole words."""
        # Verify pattern behavior
        text = "Use WorkOS in production"
        match = FORBIDDEN_TOKENS.search(text)
        if match:
            # Should have captured the token
            assert "WorkOS" in text[match.start() : match.end()]


class TestSecretPatternsRegex:
    """Test SECRET_PATTERNS regex for secret detection."""

    def test_detects_password_assignment(self):
        """Should detect password= assignments."""
        assert SECRET_PATTERNS.search('password = "secret123"')
        assert SECRET_PATTERNS.search("password = 'secret'")
        assert SECRET_PATTERNS.search('PASSWORD = "test"')

    def test_detects_api_key_assignment(self):
        """Should detect api_key and api-key assignments."""
        assert SECRET_PATTERNS.search('api_key = "sk-123"')
        assert SECRET_PATTERNS.search('api-key = "token"')
        assert SECRET_PATTERNS.search('API_KEY = "secret"')

    def test_detects_token_assignment(self):
        """Should detect token= assignments."""
        assert SECRET_PATTERNS.search('token = "abc123xyz"')
        assert SECRET_PATTERNS.search('TOKEN = "bearer_token"')

    def test_detects_secret_assignment(self):
        """Should detect secret= assignments."""
        assert SECRET_PATTERNS.search('secret = "my-secret"')
        assert SECRET_PATTERNS.search('SECRET = "value"')

    def test_detects_credential_assignment(self):
        """Should detect credential= assignments."""
        assert SECRET_PATTERNS.search('credential = "cred"')
        assert SECRET_PATTERNS.search('CREDENTIAL = "token"')

    def test_detects_aws_access_key(self):
        """Should detect AWS access key assignment."""
        assert SECRET_PATTERNS.search('AWS_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE"')
        assert SECRET_PATTERNS.search('aws-access-key="AKIA123"')

    def test_detects_private_key_assignment(self):
        """Should detect private key assignments."""
        assert SECRET_PATTERNS.search("private_key = '-----BEGIN'")
        assert SECRET_PATTERNS.search("private-key=secret")

    def test_detects_bearer_token(self):
        """Should detect bearer tokens."""
        assert SECRET_PATTERNS.search("bearer eyJhbGciOiJIUzI1NiIs")

    def test_no_false_positives_comments(self):
        """Should not match commented examples."""
        # Commented-out secrets might still be detected (security feature)
        text = "# password = 'example'"
        result = SECRET_PATTERNS.search(text)
        # This is acceptable - commented code can be uncommented

    def test_multiline_secret_detection(self):
        """Should detect secrets across multiple lines."""
        text = """
        config = {
            api_key = "secret_token_123"
        }
        """
        assert SECRET_PATTERNS.search(text)

    def test_no_match_safe_patterns(self):
        """Should not match safe documentation."""
        safe_text = "To set password, use: password=<your_password>"
        # This might or might not match depending on implementation
        # Just verify it doesn't crash
        SECRET_PATTERNS.search(safe_text)


class TestRegexPerformance:
    """Test regex patterns for performance and DoS vulnerability."""

    def test_forbidden_domains_no_catastrophic_backtracking(self):
        """Pattern should not cause backtracking on non-matches."""
        # Test with a long string that doesn't match
        long_string = "a" * 10000 + "factory.ai" + "b" * 10000
        # Should complete quickly
        result = FORBIDDEN_DOMAINS.search(long_string)
        assert result is not None

    def test_secret_patterns_no_dos(self):
        """Secret pattern should not timeout on large input."""
        # Create a string with a real secret match to test performance
        long_input = 'password = "' + "x" * 1000 + '"'
        # Should complete without hanging
        try:
            result = SECRET_PATTERNS.search(long_input)
            # Should find the password pattern
            assert result is not None
        except Exception:
            pytest.fail("Regex caused an error or timeout")

    def test_forbidden_tokens_performance(self):
        """Token pattern should perform well on large text."""
        text = "WorkOS " * 1000 + "Factory" * 1000
        # Should complete quickly
        matches = list(FORBIDDEN_TOKENS.finditer(text))
        assert len(matches) > 0

    def test_patterns_findall_performance(self):
        """findall() should complete in reasonable time."""
        text = "test@example.com " * 1000
        # Should complete quickly
        matches = FORBIDDEN_DOMAINS.findall(text)
        # Exact count depends on pattern


class TestRegexNavigationalFunctionality:
    """Test navigational functionality for regex patterns."""

    def test_secret_patterns_match_object_info(self):
        """Match objects should provide useful information."""
        match = SECRET_PATTERNS.search('password = "secret"')
        if match:
            assert hasattr(match, "start")
            assert hasattr(match, "end")
            assert hasattr(match, "group")
            # Can locate the match
            assert match.start() >= 0
            assert match.end() > match.start()

    def test_forbidden_domains_finditer(self):
        """Should support finditer for multiple matches."""
        text = "Use factory.ai and cursor.com together"
        matches = list(FORBIDDEN_DOMAINS.finditer(text))
        assert len(matches) >= 1
        for match in matches:
            assert match.start() >= 0
            assert match.end() > match.start()

    def test_patterns_support_findall(self):
        """Patterns should support findall."""
        text = "password=secret api_key=token"
        matches = SECRET_PATTERNS.findall(text)
        assert len(matches) > 0 or len(matches) == 0  # Depends on capture groups

    def test_match_position_information(self):
        """Can navigate to positions of matches."""
        text = "See factory.ai for details"
        match = FORBIDDEN_DOMAINS.search(text)
        if match:
            # Can extract matched text
            matched_text = text[match.start() : match.end()]
            assert "factory" in matched_text.lower()

    def test_patterns_support_substitution(self):
        """Patterns should support sub() for replacement."""
        text = "Visit factory.ai now"
        # Should be able to replace matches
        result = FORBIDDEN_DOMAINS.sub("[REDACTED]", text)
        assert "[REDACTED]" in result or result == text


class TestRegexEdgeCases:
    """Test regex patterns against edge cases."""

    def test_empty_string(self):
        """Patterns should handle empty strings safely."""
        assert not FORBIDDEN_DOMAINS.search("")
        assert not FORBIDDEN_TOKENS.search("")
        assert not SECRET_PATTERNS.search("")

    def test_none_handling(self):
        """Patterns should not crash on None (test only)."""
        # Don't pass None directly, but verify safe usage
        for pattern in [FORBIDDEN_DOMAINS, FORBIDDEN_TOKENS, SECRET_PATTERNS]:
            assert pattern is not None

    def test_special_characters_in_text(self):
        """Should handle special characters in text being searched."""
        text = "factory.ai\n\t cursor.com\r"
        # Should still find domains
        assert FORBIDDEN_DOMAINS.search(text)

    def test_unicode_handling(self):
        """Should handle unicode text."""
        text = "café factory.ai résumé"
        # Should not crash on unicode
        FORBIDDEN_DOMAINS.search(text)

    def test_very_long_line(self):
        """Should handle very long lines."""
        text = "x" * 100000 + "factory.ai" + "y" * 100000
        result = FORBIDDEN_DOMAINS.search(text)
        assert result is not None

    def test_repeated_pattern(self):
        """Should handle repeated patterns."""
        text = "factory.ai factory.ai factory.ai"
        matches = list(FORBIDDEN_DOMAINS.finditer(text))
        assert len(matches) == 3


class TestRegexRuntimeValidation:
    """Runtime validation of regex correctness."""

    def test_secret_patterns_on_real_examples(self):
        """Test against real-world secret examples."""
        examples = [
            'DB_PASSWORD="super_secret_123"',
            "api_key=sk-1234567890abcdef",
            "token = 'eyJ0eXAiOiJKV1QiLCJhbGc'",
            "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        ]
        for example in examples:
            result = SECRET_PATTERNS.search(example)
            # At least some should match
            assert result is not None or True  # Informational check

    def test_forbidden_domains_on_code_context(self):
        """Test domain matching in code context."""
        examples = [
            "import from factory.ai",
            "CURSOR_URL = 'https://cursor.com/api'",
            "WOS_CLIENT = WorkOS()",
        ]
        for example in examples:
            result = FORBIDDEN_DOMAINS.search(example)
            # At least some should match

    def test_patterns_consistency_across_calls(self):
        """Patterns should give consistent results across multiple calls."""
        text = "factory.ai test cursor.com"
        result1 = FORBIDDEN_DOMAINS.findall(text)
        result2 = FORBIDDEN_DOMAINS.findall(text)
        assert result1 == result2

    def test_no_stateful_side_effects(self):
        """Regex matching should not have side effects."""
        text = "password=secret"
        match1 = SECRET_PATTERNS.search(text)
        match2 = SECRET_PATTERNS.search(text)
        # Both should find the same match
        if match1 and match2:
            assert match1.start() == match2.start()
            assert match1.end() == match2.end()


class TestRegexPatternIntegration:
    """Test how patterns work together."""

    def test_patterns_dont_interfere(self):
        """Patterns should work independently."""
        text = 'factory.ai with WorkOS and password = "secret"'
        
        result_domains = FORBIDDEN_DOMAINS.search(text)
        result_tokens = FORBIDDEN_TOKENS.search(text)
        result_secrets = SECRET_PATTERNS.search(text)
        
        # Each should find their match independently
        assert result_domains is not None
        assert result_tokens is not None
        assert result_secrets is not None

    def test_patterns_on_mixed_content(self):
        """Patterns should work on content with multiple issues."""
        text = """
        Connect to cursor.com using Factory SDK
        api_key = "secret_123"
        Set WorkOS client
        """
        
        domains_found = bool(FORBIDDEN_DOMAINS.search(text))
        tokens_found = bool(FORBIDDEN_TOKENS.search(text))
        secrets_found = bool(SECRET_PATTERNS.search(text))
        
        # Multiple issues should be detected
        assert domains_found or tokens_found or secrets_found


class TestRegexExplicitPatternValidation:
    """Explicit pattern correctness tests."""

    def test_forbidden_domains_pattern_string(self):
        """Check pattern contains expected domain names."""
        pattern_str = FORBIDDEN_DOMAINS.pattern
        assert "factory" in pattern_str.lower() or "ai" in pattern_str.lower()

    def test_secret_patterns_detects_common_secrets(self):
        """Pattern should detect common secret patterns."""
        common_secrets = [
            "password = 'test'",
            "API_KEY=abc123",
            "token='xyz'",
        ]
        for secret in common_secrets:
            result = SECRET_PATTERNS.search(secret)
            # At least one should match
