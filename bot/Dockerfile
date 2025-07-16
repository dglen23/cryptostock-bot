# Use the official Python 3.12 slim image
FROM python:3.12-slim

# Install build dependencies
RUN apt-get update && apt-get install -y gcc g++ libffi-dev libssl-dev python3-dev build-essential && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Run the bot
CMD ["python", "bot.py"]
