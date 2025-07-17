#!/usr/bin/env python3
import os

def remove_charts_from_page(file_path):
    """Remove chart container and related elements from a page"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove the chart.js script reference
    content = content.replace('<script src="../chart.js"></script>', '')
    
    # Remove the entire chart container section (from Chart Container comment to end of timeframe buttons)
    import re
    
    # Pattern to match from Chart Container comment to the end of timeframe buttons
    pattern = r'<!-- Chart Container -->.*?<!-- Timeframe Buttons -->.*?</div>\s*</div>\s*</div>'
    
    # Remove the chart container
    new_content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Updated {file_path}")

def main():
    # Crypto pages to update
    crypto_pages = [
        'bitcoin.html', 'ethereum.html', 'ripple.html', 'hedera-hashgraph.html', 
        'stellar.html', 'quant-network.html', 'ondo.html', 'xdc-network.html', 
        'pepe.html', 'shiba-inu.html', 'solana.html', 'dogecoin.html'
    ]
    
    # Stock pages to update
    stock_pages = [
        'aapl.html', 'msft.html', 'nvda.html', 'amzn.html', 'googl.html'
    ]
    
    # Update crypto pages
    for filename in crypto_pages:
        file_path = f"frontend/coins/{filename}"
        if os.path.exists(file_path):
            remove_charts_from_page(file_path)
        else:
            print(f"Warning: {file_path} not found")
    
    # Update stock pages
    for filename in stock_pages:
        file_path = f"frontend/stocks/{filename}"
        if os.path.exists(file_path):
            remove_charts_from_page(file_path)
        else:
            print(f"Warning: {file_path} not found")
    
    print("\nAll charts removed from pages!")

if __name__ == "__main__":
    main() 