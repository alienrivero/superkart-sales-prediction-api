# Python 3.11 matches the environment the model was trained and serialized in
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies first so this layer is cached when only the code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API code and the serialized model
COPY . .

EXPOSE 7860

# Start the Flask app with Gunicorn on port 7860
# -w 4: 4 worker processes
# -b 0.0.0.0:7860: bind to all interfaces on port 7860
# app:superkart_api: module `app.py`, Flask instance named `superkart_api`
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:7860", "app:superkart_api"]
