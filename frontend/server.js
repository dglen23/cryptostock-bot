const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 8080;

// Serve all static files in the root folder
app.use(express.static(__dirname));

// Fallback to index.html for any unknown route
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Frontend is running on port ${PORT}`);
}); 