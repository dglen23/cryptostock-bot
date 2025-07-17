/**
 * Simple Price Loading Script
 * Loads current prices for crypto and stocks
 */

/**
 * Map common coin names to CoinGecko IDs
 */
function getCoinGeckoId(symbol) {
    const coinMap = {
        'bitcoin': 'bitcoin',
        'ethereum': 'ethereum',
        'ripple': 'ripple',
        'hedera-hashgraph': 'hedera-hashgraph',
        'stellar': 'stellar',
        'quant-network': 'quant-network',
        'ondo': 'ondo',
        'xdc-network': 'xdc-network',
        'pepe': 'pepe',
        'shiba-inu': 'shiba-inu',
        'solana': 'solana',
        'dogecoin': 'dogecoin'
    };
    return coinMap[symbol] || symbol;
}

/**
 * Fetch crypto price from CoinGecko API
 */
async function fetchCryptoPrice(symbol) {
    const coinId = getCoinGeckoId(symbol);
    const response = await fetch(`https://api.coingecko.com/api/v3/simple/price?ids=${coinId}&vs_currencies=usd`);
    const data = await response.json();
    
    if (data[coinId] && data[coinId].usd) {
        const price = data[coinId].usd;
        return formatPrice(price);
    }
    throw new Error('Price not available');
}

/**
 * Fetch stock price from Yahoo Finance API
 */
async function fetchStockPrice(symbol) {
    const response = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${symbol.toUpperCase()}`);
    const data = await response.json();
    
    if (data.chart && data.chart.result && data.chart.result[0]) {
        const result = data.chart.result[0];
        const price = result.meta.regularMarketPrice;
        return formatPrice(price);
    }
    throw new Error('Price not available');
}

/**
 * Format price for display
 */
function formatPrice(price) {
    if (price >= 1) {
        return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    return `$${price.toFixed(8).replace(/\.?0+$/, '')}`;
}

/**
 * Load and display current price
 */
async function loadCurrentPrice() {
    const priceElement = document.getElementById('current-price');
    if (!priceElement) return;
    
    try {
        priceElement.innerHTML = '<span class="loading">Loading price...</span>';
        
        const symbol = document.body.getAttribute('data-symbol');
        const type = document.body.getAttribute('data-type');
        
        if (!symbol || !type) {
            throw new Error('Missing symbol or type data');
        }
        
        let price = '';
        if (type === 'crypto') {
            price = await fetchCryptoPrice(symbol);
        } else {
            price = await fetchStockPrice(symbol);
        }
        
        priceElement.innerHTML = `<span class="price-value">${price}</span>`;
    } catch (error) {
        console.error('Error loading price:', error);
        priceElement.innerHTML = '<span class="error">Price unavailable</span>';
    }
}

/**
 * Auto-refresh price every 30 seconds
 */
function startPriceRefresh() {
    setInterval(loadCurrentPrice, 30000);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Extract symbol and type from page data
    const symbol = document.body.getAttribute('data-symbol');
    const type = document.body.getAttribute('data-type');
    
    if (symbol && type) {
        loadCurrentPrice();
        startPriceRefresh();
    }
}); 