# Use the official Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Tell Docker how to run your bot
CMD ["python", "bot.py"]
