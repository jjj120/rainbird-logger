# Use the official Python image as the base image
FROM python:3.12-slim

# Copy the Python script and the requirements file into the container
COPY . /app

# Set the working directory in the container
WORKDIR /app

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# # Run the Python script
CMD ["python", "main.py"]