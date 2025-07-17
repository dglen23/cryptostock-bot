#!/usr/bin/env python3
import os
import re

def remove_charts_from_page(file_path):
    """Remove all chart-related elements from a page, leaving only the price display."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove chart.js script reference
    content = content.replace('<script src="../chart.js"></script>', '')

    # Remove chart container and everything inside it
    content = re.sub(r'<!-- Chart Container -->.*?</div>\s*</main>', '</main>', content, flags=re.DOTALL)

    # Remove any remaining timeframe buttons
    content = re.sub(r'<div class="timeframe-buttons">.*?</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<button class="timeframe-btn.*?</button>', '', content, flags=re.DOTALL)

    # Remove any remaining chart titles
    content = re.sub(r'<div class="chart-title">.*?</div>', '', content, flags=re.DOTALL)

    # Remove any empty lines or extra whitespace left by removals
    content = re.sub(r'\n\s*\n', '\n', content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Cleaned {file_path}")

def main():
    crypto_pages = [
        'bitcoin.html', 'ethereum.html', 'ripple.html', 'hedera-hashgraph.html',
        'stellar.html', 'quant-network.html', 'ondo.html', 'xdc-network.html',
        'pepe.html', 'shiba-inu.html', 'solana.html', 'dogecoin.html'
    ]
    stock_pages = [
        'aapl.html', 'msft.html', 'nvda.html', 'amzn.html', 'googl.html'
    ]
    for filename in crypto_pages:
        file_path = f"frontend/coins/{filename}"
        if os.path.exists(file_path):
            remove_charts_from_page(file_path)
    for filename in stock_pages:
        file_path = f"frontend/stocks/{filename}"
        if os.path.exists(file_path):
            remove_charts_from_page(file_path)
    print("\nAll chart evidence removed from pages!")

if __name__ == "__main__":
    main() 