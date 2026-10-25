# Use a minimal base image with Python 3.11 installed
FROM python:3.11-slim

# Set the working directory inside the container to /app
WORKDIR /app

# Install Python dependencies first so this layer is cached when only the code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Streamlit app
COPY . .

EXPOSE 8501

# Run the Streamlit app on port 8501 and make it accessible externally
# XSRF protection is disabled so batch CSV uploads work reliably through the Codespaces port tunnel
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableXsrfProtection=false"]
