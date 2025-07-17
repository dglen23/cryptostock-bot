#!/usr/bin/env python3
import os

def add_price_script(file_path):
    """Add price.js script reference to a page"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add price.js script after script.js
    content = content.replace(
        '<script src="../script.js"></script>',
        '<script src="../script.js"></script>\n    <script src="../price.js"></script>'
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
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
            add_price_script(file_path)
        else:
            print(f"Warning: {file_path} not found")
    
    # Update stock pages
    for filename in stock_pages:
        file_path = f"frontend/stocks/{filename}"
        if os.path.exists(file_path):
            add_price_script(file_path)
        else:
            print(f"Warning: {file_path} not found")
    
    print("\nAll pages updated with price.js script!")

if __name__ == "__main__":
    main() 