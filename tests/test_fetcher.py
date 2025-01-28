import pytest
from app.data.fetcher import DexScreenerFetcher

def test_fetcher_initialization():
    fetcher = DexScreenerFetcher()
    assert fetcher is not None
    assert fetcher.dex_base_url == "https://api.dexscreener.com/latest/dex"