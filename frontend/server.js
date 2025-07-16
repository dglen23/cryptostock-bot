const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 8080;

// Serve static files from the current directory (adjust if needed)
app.use(express.static(path.join(__dirname)));

// Fallback to index.html for all routes (optional for SPAs)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Frontend is running on port ${PORT}`);
});
