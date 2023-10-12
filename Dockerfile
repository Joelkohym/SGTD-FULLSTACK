# Use the official Python image as the base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Update the package lists
RUN apt-get update && apt-get install -y build-essential

# Install the required system packages
RUN apt-get install -y pkg-config libmariadb-dev

# Install the required Python packages
RUN pip install -r requirements.txt

#RUN chmod +x ./start.sh

# Copy the rest of the application code into the container
COPY . .

# Expose the port that your Flask app listens on
EXPOSE 5000

# Start the Flask app
CMD ["python", "app.py"]