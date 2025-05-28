# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install git, which is required to install packages from git repositories
# Update apt package list and install git
RUN apt-get update && apt-get install -y git

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run fastmcp_server.py when the container launches
# The script is already set up to read HOST, PORT, MCP_PATH from env vars
CMD ["python", "fastmcp_server.py"] 
