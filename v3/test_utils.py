"""Tests for utility helper functions."""

import pytest

from src.utils.helpers import (
    calculate_similarity_score,
    clean_text,
    estimate_tokens,
    extract_keywords,
    format_timestamp,
    generate_id,
    merge_metadata,
    safe_dict_get,
    split_into_sentences,
    truncate_text,
    validate_language_code,
)


class TestGenerateId:
    """Tests for generate_id function."""

    def test_generate_id_basic(self):
        """Test basic ID generation."""
        id1 = generate_id("test_text")
        assert isinstance(id1, str)
        assert len(id1) == 16

    def test_generate_id_with_prefix(self):
        """Test ID generation with prefix."""
        id_with_prefix = generate_id("test", prefix="doc_")
        assert id_with_prefix.startswith("doc_")
        assert len(id_with_prefix) == 20  # 4 (prefix) + 16 (hash)

    def test_generate_id_consistency(self):
        """Test that same input generates same ID."""
        id1 = generate_id("same_text")
        id2 = generate_id("same_text")
        assert id1 == id2


class TestCleanText:
    """Tests for clean_text function."""

    def test_clean_text_whitespace(self):
        """Test cleaning extra whitespace."""
        text = "This  has   extra    spaces"
        cleaned = clean_text(text)
        assert "  " not in cleaned
        assert cleaned == "This has extra spaces"

    def test_clean_text_special_chars(self):
        """Test cleaning special characters."""
        text = "Hello @#$% World!"
        cleaned = clean_text(text)
        assert "@" not in cleaned
        assert "#" not in cleaned

    def test_clean_text_empty(self):
        """Test cleaning empty string."""
        assert clean_text("") == ""


class TestEstimateTokens:
    """Tests for estimate_tokens function."""

    def test_estimate_tokens_basic(self):
        """Test basic token estimation."""
        text = "This is a test"
        tokens = estimate_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)

    def test_estimate_tokens_empty(self):
        """Test token estimation for empty string."""
        assert estimate_tokens("") == 0


class TestSplitIntoSentences:
    """Tests for split_into_sentences function."""

    def test_split_sentences_basic(self):
        """Test basic sentence splitting."""
        text = "This is first. This is second! This is third?"
        sentences = split_into_sentences(text)
        assert len(sentences) == 3

    def test_split_sentences_empty(self):
        """Test splitting empty string."""
        sentences = split_into_sentences("")
        assert len(sentences) == 0


class TestValidateLanguageCode:
    """Tests for validate_language_code function."""

    def test_validate_language_code_valid(self):
        """Test validating valid language code."""
        assert validate_language_code("en", ["en", "es", "fr"]) is True

    def test_validate_language_code_invalid(self):
        """Test validating invalid language code."""
        assert validate_language_code("xx", ["en", "es", "fr"]) is False

    def test_validate_language_code_case_insensitive(self):
        """Test case insensitive validation."""
        assert validate_language_code("EN", ["en", "es", "fr"]) is True


class TestCalculateSimilarityScore:
    """Tests for calculate_similarity_score function."""

    def test_calculate_similarity_basic(self):
        """Test basic similarity calculation."""
        score = calculate_similarity_score(0.8, 0.6, 0.5, 0.5)
        assert 0 <= score <= 1

    def test_calculate_similarity_weights(self):
        """Test similarity calculation with different weights."""
        score1 = calculate_similarity_score(1.0, 0.0, 1.0, 0.0)
        assert score1 == 1.0

        score2 = calculate_similarity_score(0.0, 1.0, 0.0, 1.0)
        assert score2 == 1.0


class TestExtractKeywords:
    """Tests for extract_keywords function."""

    def test_extract_keywords_basic(self):
        """Test basic keyword extraction."""
        text = "artificial intelligence machine learning deep learning neural networks"
        keywords = extract_keywords(text, top_k=3)
        assert isinstance(keywords, list)
        assert len(keywords) <= 3

    def test_extract_keywords_stopwords(self):
        """Test that stop words are filtered."""
        text = "the and or but artificial intelligence"
        keywords = extract_keywords(text)
        assert "the" not in keywords
        assert "and" not in keywords


class TestTruncateText:
    """Tests for truncate_text function."""

    def test_truncate_text_basic(self):
        """Test basic text truncation."""
        text = "This is a very long text that needs to be truncated"
        truncated = truncate_text(text, max_length=20)
        assert len(truncated) <= 20
        assert truncated.endswith("...")

    def test_truncate_text_short(self):
        """Test truncating short text."""
        text = "Short"
        truncated = truncate_text(text, max_length=20)
        assert truncated == text


class TestSafeDictGet:
    """Tests for safe_dict_get function."""

    def test_safe_dict_get_exists(self):
        """Test getting existing key."""
        d = {"key": "value"}
        assert safe_dict_get(d, "key") == "value"

    def test_safe_dict_get_not_exists(self):
        """Test getting non-existing key."""
        d = {"key": "value"}
        assert safe_dict_get(d, "missing", "default") == "default"

    def test_safe_dict_get_error(self):
        """Test handling errors."""
        result = safe_dict_get(None, "key", "default")
        assert result == "default"


class TestMergeMetadata:
    """Tests for merge_metadata function."""

    def test_merge_metadata_basic(self):
        """Test basic metadata merging."""
        base = {"key1": "value1"}
        additional = {"key2": "value2"}
        merged = merge_metadata(base, additional)
        assert merged["key1"] == "value1"
        assert merged["key2"] == "value2"

    def test_merge_metadata_overwrite(self):
        """Test that additional overwrites base."""
        base = {"key": "old"}
        additional = {"key": "new"}
        merged = merge_metadata(base, additional)
        assert merged["key"] == "new"
