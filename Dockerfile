# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install system dependencies
# This ensures 'stockfish' is available in the container's environment
RUN apt-get update && apt-get install -y \
    stockfish \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variables
ENV STOCKFISH_PATH=/usr/games/stockfish
ENV PORT=5000

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run gunicorn to serve the Flask app
# The $PORT environment variable will be set by the platform (like Render)
CMD gunicorn --bind 0.0.0.0:5000 app:app
