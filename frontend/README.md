# Gumball Crypto News Frontend

A static web application for cryptocurrency and stock price information, integrated with Telegram Web Apps.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. For production deployment:
   ```bash
   npm start
   ```

## Features

- **Static File Serving**: Uses the `serve` module for efficient static file serving
- **Telegram Web App Integration**: Sends data back to the Telegram bot
- **Responsive Design**: Mobile-friendly interface
- **Crypto & Stock Pages**: Individual pages for each cryptocurrency and stock
- **Interactive Buttons**: Send commands directly to the Telegram bot

## File Structure

- `index.html` - Main landing page
- `crypto.html` - Cryptocurrency list page
- `stocks.html` - Stock list page
- `style.css` - Main stylesheet
- `script.js` - JavaScript for Telegram Web App integration
- `coins/` - Individual cryptocurrency detail pages
- `stocks/` - Individual stock detail pages
- `img/` - Image assets

## Deployment

The frontend is configured for deployment on Railway with the `serve` module. The `npm start` command automatically uses the `PORT` environment variable set by Railway. 