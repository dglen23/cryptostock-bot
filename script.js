/**
 * GBCN Bot Frontend - Telegram Integration Script
 * 
 * This script provides functionality to interact with the GBCN Telegram bot
 * from the web frontend by opening Telegram with specific commands.
 */

// Bot username - update this if your bot username changes
const BOT_USERNAME = 'gbcn_bot';

/**
 * Sends a command to the GBCN Telegram bot
 * 
 * @param {string} command - The command to send to the bot
 * @param {boolean} newTab - Whether to open in a new tab (default: true)
 * 
 * @example
 * sendTelegramCommand('/crypto')           // Get all crypto prices
 * sendTelegramCommand('/chart bitcoin 7d') // Get Bitcoin 7-day chart
 * sendTelegramCommand('/news AAPL')        // Get news for AAPL
 */
function sendTelegramCommand(command, newTab = true) {
    // Validate input
    if (!command || typeof command !== 'string') {
        console.error('Invalid command provided to sendTelegramCommand:', command);
        return;
    }
    
    // Remove leading slash if present to avoid double slashes
    const cleanCommand = command.startsWith('/') ? command : `/${command}`;
    
    // Encode the command for URL safety
    const encodedCommand = encodeURIComponent(cleanCommand);
    
    // Construct the Telegram URL with the /start parameter
    const telegramUrl = `https://t.me/${BOT_USERNAME}?start=${encodedCommand}`;
    
    try {
        if (newTab) {
            // Open in a new tab
            window.open(telegramUrl, '_blank', 'noopener,noreferrer');
        } else {
            // Open in the same tab
            window.location.href = telegramUrl;
        }
        
        console.log(`Telegram command sent: ${cleanCommand}`);
    } catch (error) {
        console.error('Error opening Telegram:', error);
        // Fallback: try to open in the same tab
        try {
            window.location.href = telegramUrl;
        } catch (fallbackError) {
            console.error('Fallback also failed:', fallbackError);
        }
    }
}

/**
 * Convenience function to get crypto prices
 */
function getCryptoPrices() {
    sendTelegramCommand('/crypto');
}

/**
 * Convenience function to get stock prices
 */
function getStockPrices() {
    sendTelegramCommand('/stocks');
}

/**
 * Convenience function to get a crypto chart
 * 
 * @param {string} crypto - The cryptocurrency symbol (e.g., 'bitcoin', 'ethereum')
 * @param {string} period - The time period (e.g., '7d', '30d')
 */
function getCryptoChart(crypto, period = '7d') {
    sendTelegramCommand(`/chart ${crypto} ${period}`);
}

/**
 * Convenience function to get news for a symbol
 * 
 * @param {string} symbol - The symbol to get news for (e.g., 'bitcoin', 'AAPL')
 */
function getNews(symbol) {
    sendTelegramCommand(`/news ${symbol}`);
}

// Export functions for use in modules (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        sendTelegramCommand,
        getCryptoPrices,
        getStockPrices,
        getCryptoChart,
        getNews
    };
} 