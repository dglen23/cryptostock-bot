/**
 * Chart and Price Management for Crypto/Stock Detail Pages
 */

let chartInstance = null;
let currentSymbol = '';
let currentType = '';

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
 * Initialize the detail page with price and chart
 */
async function initializeDetailPage(symbol, type) {
    currentSymbol = symbol;
    currentType = type;
    
    // Load Chart.js if not already loaded
    if (typeof Chart === 'undefined') {
        await loadChartJS();
    }
    
    // Load initial price and chart
    await loadCurrentPrice();
    await loadChart('1d');
    
    // Add event listeners to timeframe buttons
    setupTimeframeButtons();
}

/**
 * Load Chart.js from CDN
 */
function loadChartJS() {
    return new Promise((resolve, reject) => {
        if (typeof Chart !== 'undefined') {
            resolve();
            return;
        }
        
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

/**
 * Load and display current price
 */
async function loadCurrentPrice() {
    const priceElement = document.getElementById('current-price');
    if (!priceElement) return;
    
    try {
        priceElement.innerHTML = '<span class="loading">Loading price...</span>';
        
        let price = '';
        if (currentType === 'crypto') {
            price = await fetchCryptoPrice(currentSymbol);
        } else {
            price = await fetchStockPrice(currentSymbol);
        }
        
        priceElement.innerHTML = `<span class="price-value">${price}</span>`;
    } catch (error) {
        console.error('Error loading price:', error);
        priceElement.innerHTML = '<span class="error">Price unavailable</span>';
    }
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
 * Load chart data and render
 */
async function loadChart(timeframe) {
    const canvas = document.getElementById('price-chart');
    if (!canvas) return;
    
    try {
        // Show loading state
        canvas.style.display = 'none';
        const loadingDiv = document.getElementById('chart-loading');
        if (loadingDiv) loadingDiv.style.display = 'block';
        
        let chartData;
        if (currentType === 'crypto') {
            chartData = await fetchCryptoChartData(currentSymbol, timeframe);
        } else {
            chartData = await fetchStockChartData(currentSymbol, timeframe);
        }
        
        renderChart(chartData, timeframe);
        
        // Hide loading, show chart
        canvas.style.display = 'block';
        if (loadingDiv) loadingDiv.style.display = 'none';
        
        // Update active timeframe button
        updateActiveTimeframeButton(timeframe);
        
    } catch (error) {
        console.error('Error loading chart:', error);
        canvas.style.display = 'none';
        const loadingDiv = document.getElementById('chart-loading');
        if (loadingDiv) {
            loadingDiv.style.display = 'block';
            loadingDiv.innerHTML = '<span class="error">Chart unavailable</span>';
        }
    }
}

/**
 * Fetch crypto chart data from CoinGecko
 */
async function fetchCryptoChartData(symbol, timeframe) {
    const coinId = getCoinGeckoId(symbol);
    const days = getDaysFromTimeframe(timeframe);
    const response = await fetch(`https://api.coingecko.com/api/v3/coins/${coinId}/market_chart?vs_currency=usd&days=${days}`);
    const data = await response.json();
    
    return {
        labels: data.prices.map(point => new Date(point[0]).toLocaleDateString()),
        prices: data.prices.map(point => point[1])
    };
}

/**
 * Fetch stock chart data from Yahoo Finance
 */
async function fetchStockChartData(symbol, timeframe) {
    const interval = getIntervalFromTimeframe(timeframe);
    const range = getRangeFromTimeframe(timeframe);
    
    const response = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${symbol.toUpperCase()}?interval=${interval}&range=${range}`);
    const data = await response.json();
    
    if (data.chart && data.chart.result && data.chart.result[0]) {
        const result = data.chart.result[0];
        const timestamps = result.timestamp;
        const prices = result.indicators.quote[0].close;
        
        return {
            labels: timestamps.map(ts => new Date(ts * 1000).toLocaleDateString()),
            prices: prices.filter(price => price !== null)
        };
    }
    throw new Error('Chart data not available');
}

/**
 * Convert timeframe to days for crypto API
 */
function getDaysFromTimeframe(timeframe) {
    switch (timeframe) {
        case '1h': return 1;
        case '1d': return 1;
        case '7d': return 7;
        case '30d': return 30;
        default: return 1;
    }
}

/**
 * Convert timeframe to interval for stock API
 */
function getIntervalFromTimeframe(timeframe) {
    switch (timeframe) {
        case '1m': return '1m';
        case '5m': return '5m';
        case '1h': return '1h';
        case '1d': return '1d';
        default: return '5m';
    }
}

/**
 * Convert timeframe to range for stock API
 */
function getRangeFromTimeframe(timeframe) {
    switch (timeframe) {
        case '1h': return '1h';
        case '1d': return '1d';
        case '7d': return '7d';
        case '30d': return '1mo';
        default: return '1d';
    }
}

/**
 * Render the chart using Chart.js
 */
function renderChart(data, timeframe) {
    const canvas = document.getElementById('price-chart');
    if (!canvas) return;
    
    // Destroy existing chart
    if (chartInstance) {
        chartInstance.destroy();
    }
    
    const ctx = canvas.getContext('2d');
    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: `${currentSymbol.toUpperCase()} Price`,
                data: data.prices,
                borderColor: '#4CAF50',
                backgroundColor: 'rgba(76, 175, 80, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#4CAF50'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            aspectRatio: 2,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `${currentSymbol.toUpperCase()}: ${formatPrice(context.parsed.y)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 8
                    }
                },
                y: {
                    display: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatPrice(value);
                        }
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

/**
 * Setup timeframe button event listeners
 */
function setupTimeframeButtons() {
    const buttons = document.querySelectorAll('.timeframe-btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const timeframe = this.getAttribute('data-timeframe');
            loadChart(timeframe);
        });
    });
}

/**
 * Update active timeframe button styling
 */
function updateActiveTimeframeButton(activeTimeframe) {
    const buttons = document.querySelectorAll('.timeframe-btn');
    buttons.forEach(button => {
        button.classList.remove('active');
        if (button.getAttribute('data-timeframe') === activeTimeframe) {
            button.classList.add('active');
        }
    });
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
        initializeDetailPage(symbol, type);
        startPriceRefresh();
    }
}); 