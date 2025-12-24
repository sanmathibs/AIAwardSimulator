"""
Simple test to verify the app setup
"""

import html
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")

    try:
        import config

        print("✓ config")

        from utils.openai_client import OpenAIClient

        print("✓ OpenAIClient")

        from ingestion.award_fetcher import AwardFetcher

        print("✓ AwardFetcher")

        from ingestion.html_parser import HTMLParser

        print("✓ HTMLParser")

        from ingestion.clause_chunker import ClauseChunker

        print("✓ ClauseChunker")

        from ingestion.vector_store import VectorStore

        print("✓ VectorStore")

        from extraction.rule_extractor import RuleExtractor

        print("✓ RuleExtractor")

        from analysis.gap_analyzer import GapAnalyzer

        print("✓ GapAnalyzer")

        from generation.json_generator import ConfigGenerator

        print("✓ JSONGenerator")

        from generation.patch_generator import PatchGenerator

        print("✓ PatchGenerator")

        from core.orchestrator import Orchestrator

        print("✓ Orchestrator")

        from models import SessionState, Gap, GapReport, AwardSpec

        print("✓ Models")

        print("\n✅ All imports successful!")
        return True

    except Exception as e:
        print(f"\n❌ Import failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_config():
    """Test configuration"""
    print("\nTesting configuration...")

    try:
        import config

        # Check directories exist
        assert config.DATA_DIR.exists(), "DATA_DIR does not exist"
        print("✓ DATA_DIR exists")

        assert config.SESSIONS_DIR.exists(), "SESSIONS_DIR does not exist"
        print("✓ SESSIONS_DIR exists")

        # Check baseline config
        baseline_path = config.DATA_DIR / "baseline_config.json"
        assert baseline_path.exists(), "baseline_config.json does not exist"
        print("✓ baseline_config.json exists")

        # Check API key (don't print it!)
        if (
            config.OPENAI_API_KEY
            and config.OPENAI_API_KEY != "your_openai_api_key_here"
        ):
            print("✓ OpenAI API key configured")
        else:
            print("⚠️  OpenAI API key not configured (create .env file)")

        print("\n✅ Configuration test passed!")
        return True

    except Exception as e:
        print(f"\n❌ Configuration test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_award_fetcher():
    """Test award fetcher (without actually fetching)"""
    print("\nTesting AwardFetcher...")

    try:
        from ingestion.award_fetcher import AwardFetcher

        fetcher = AwardFetcher()
        print("✓ AwardFetcher instantiated")

        # Test URL parsing
        award_id = fetcher._extract_award_id(
            "https://awards.fairwork.gov.au/MA000028.html"
        )
        assert award_id == "MA000028", f"Expected MA000028, got {award_id}"
        print(f"✓ Award ID extraction works: {award_id}")

        print("\n✅ AwardFetcher test passed!")
        return True

    except Exception as e:
        print(f"\n❌ AwardFetcher test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_award_parser():
    import trafilatura

    # downloaded = trafilatura.fetch_url(
    #     url="https://awards.fairwork.gov.au/MA000028.html"
    # )
    # markdown = trafilatura.extract(downloaded, output_format="markdown")

    from markdownify import markdownify as md
    from ingestion.award_fetcher import AwardFetcher
    from bs4 import BeautifulSoup

    fetcher = AwardFetcher()
    print("✓ AwardFetcher instantiated")

    # Test URL parsing
    data = fetcher.fetch_from_url("https://awards.fairwork.gov.au/MA000034.html")
    html = data["raw_html"]
    # soup = BeautifulSoup(html, "lxml")
    # html = soup.select_one("#mainContent > div.WordSection2").text
    markdown = md(html)
    # save to file
    with open("test_award_MA000034x.md", "w", encoding="utf-8") as f:
        f.write(markdown)


def main():
    """Run all tests"""
    print("=" * 60)
    print("AI AWARD INTERPRETER - SETUP VERIFICATION")
    print("=" * 60)

    results = []

    results.append(test_imports())
    results.append(test_config())
    results.append(test_award_fetcher())

    print("\n" + "=" * 60)
    if all(results):
        print("✅ ALL TESTS PASSED!")
        print("\nYou're ready to run the app:")
        print("  streamlit run app.py")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease fix the issues above before running the app.")
    print("=" * 60)


if __name__ == "__main__":
    # main()
    test_award_parser()
