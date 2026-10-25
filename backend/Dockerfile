FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy all files from the current directory to the container's working directory
COPY . .

# Install dependencies from the requirements file without using cache to reduce image size
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Start the Flask app with Gunicorn on port 7860
# -w 4: 4 worker processes
# -b 0.0.0.0:7860: bind to all interfaces on port 7860
# app:superkart_api: module `app.py`, Flask instance named `superkart_api`
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:7860", "app:superkart_api"]
