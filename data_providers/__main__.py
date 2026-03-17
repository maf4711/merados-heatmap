"""
meradOS Heatmap - CLI Test for Data Providers

Usage: python -m data_providers [TICKER]
"""

import sys

from . import get_stock_data, get_news, get_sentiment, get_api_status


def main():
    ticker = sys.argv[1] if len(sys.argv) > 1 else 'AAPL'

    print(f"\n{'='*60}")
    print(f"  meradOS Multi-Source Data Test: {ticker}")
    print(f"{'='*60}")

    # API Status
    print("\n📡 API Status:")
    status = get_api_status()
    for api, info in status.items():
        avail = "✅" if info['available'] else "❌"
        print(f"   {api}: {avail}")

    # Daten holen
    print(f"\n📊 Lade Daten fuer {ticker}...")
    data, quality = get_stock_data(ticker)

    print(f"\n💰 Quote:")
    print(f"   Price: ${data.get('price', 'N/A')}")
    print(f"   Change: {data.get('change_percent', 'N/A')}%")

    print(f"\n📈 Fundamentals:")
    print(f"   P/E: {data.get('pe_ratio', 'N/A')}")
    print(f"   ROE: {data.get('roe', 'N/A')}")
    print(f"   Profit Margin: {data.get('profit_margin', 'N/A')}")

    print(f"\n⭐ Data Quality:")
    print(f"   Overall Score: {quality.get('overall_score', 'N/A')}/100")
    print(f"   Quote Source: {quality.get('quote', {}).get('source', 'N/A')}")
    print(f"   Fundamentals Source: {quality.get('fundamentals', {}).get('source', 'N/A')}")

    # News
    news = get_news(ticker)
    if news:
        print(f"\n📰 News ({len(news)} Artikel):")
        for n in news[:3]:
            print(f"   - {n.get('title', 'N/A')[:60]}...")

    # Sentiment
    sentiment = get_sentiment(ticker)
    if sentiment:
        print(f"\n🎭 Sentiment:")
        print(f"   Bullish: {sentiment.get('bullish_percent', 'N/A')}%")
        print(f"   Bearish: {sentiment.get('bearish_percent', 'N/A')}%")

    print(f"\n{'='*60}\n")


if __name__ == '__main__':
    main()
