# Use Python base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the application files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir uvicorn fastapi -r requirements.txt

# Expose the port (change this for each app)
EXPOSE 11001

# Command to run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "11001"]