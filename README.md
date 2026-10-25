# SuperKart Sales Prediction API

Flask API backend and Streamlit frontend for predicting product-store sales. Both apps run as Docker containers and can be used from a GitHub Codespace.

## Run the apps in GitHub Codespaces

Open the repository in a Codespace and use its terminal. Docker must be available. The backend listens on port `7860`; the frontend listens on port `8501`. The frontend calls the backend at `http://backend:7860` over their shared Docker network.

### First-time setup

Docker applies network and host mappings when a container is created. If the `superkart-backend` and `superkart-frontend` containers already exist (as they do in this Codespace), simply starting them again will not apply these settings. Remove the existing containers first, then run the commands below to recreate both:

```bash
docker rm -f superkart-frontend superkart-backend
```

From the repository root, build the images and create a Docker network:

```bash
docker build -t superkart-backend ./backend
docker build -t superkart-frontend ./frontend
docker network inspect superkart-network >/dev/null 2>&1 || docker network create superkart-network
```

Start the backend and frontend containers:

```bash
docker run -d \
  --name superkart-backend \
  --network superkart-network \
  --network-alias backend \
  -p 7860:7860 \
  superkart-backend

docker run -d \
  --name superkart-frontend \
  --network superkart-network \
  --add-host backend:host-gateway \
  -p 8501:8501 \
  superkart-frontend
```

The frontend calls the API at `http://backend:7860`. The `--add-host backend:host-gateway` option maps that hostname to the Docker host gateway from inside the frontend container. This is needed in Codespaces environments where direct container-to-container connections time out. Keep the backend's `-p 7860:7860` mapping so the host gateway can forward the request to the API.

### Open the apps

In VS Code, open the **Ports** panel. Codespaces should detect ports `7860` and `8501`; if they are not listed, forward them from the Ports panel.

- **Frontend:** open the forwarded port `8501` URL.
- **Backend health check:** open the forwarded port `7860` URL; it should return `Welcome to the SuperKart Sales Prediction API!`.

To make the API accessible outside the Codespace, set port `7860` to public. Anyone with the forwarded URL can then reach it. The frontend can remain private, or you can make port `8501` public if you want others to use the web app. Set the port visibility from the Codespace terminal:

```bash
# Public API (anyone with the URL can access it)
gh codespace ports visibility 7860:public -c "$CODESPACE_NAME"

# Optional: make the frontend publicly accessible too
gh codespace ports visibility 8501:public -c "$CODESPACE_NAME"

# Keep the frontend private
gh codespace ports visibility 8501:private -c "$CODESPACE_NAME"
```

You can find the forwarded URLs and current visibility in the **Ports** panel, or list them with:

```bash
gh codespace ports -c "$CODESPACE_NAME"
```

The API does not require authentication. Make it public only if you intend anyone with its forwarded URL to be able to send prediction requests. A Codespace must remain running for its forwarded URLs to work.

### Check, stop, and restart

```bash
# Check container status
docker ps

# View application logs
docker logs -f superkart-backend
docker logs -f superkart-frontend

# Stop the applications
docker stop superkart-frontend superkart-backend

# Start them again
docker start superkart-backend superkart-frontend
```

Stopping the Codespace also stops access to its apps. When the Codespace is available again, start the containers with the `docker start` commands above.

### Rebuild after changing application code

Rebuild both images, then remove and recreate the containers so they use the updated images:

```bash
docker build -t superkart-backend ./backend
docker build -t superkart-frontend ./frontend
docker network inspect superkart-network >/dev/null 2>&1 || docker network create superkart-network

docker stop superkart-frontend superkart-backend
docker rm superkart-frontend superkart-backend

docker run -d \
  --name superkart-backend \
  --network superkart-network \
  --network-alias backend \
  -p 7860:7860 \
  superkart-backend

docker run -d \
  --name superkart-frontend \
  --network superkart-network \
  --add-host backend:host-gateway \
  -p 8501:8501 \
  superkart-frontend
```

## API endpoints

The API accepts the following requests:

- `GET /` — health/welcome response.
- `POST /v1/predict` — JSON input for a single prediction. Required fields: `Product_Weight`, `Product_Sugar_Content`, `Product_Allocated_Area`, `Product_MRP`, `Store_Size`, `Store_Location_City_Type`, `Store_Type`, `Product_Id_char`, `Store_Age_Years`, and `Product_Type_Category`.
- `POST /v1/predictbatch` — CSV upload using a multipart form field named `file`. The CSV must contain the same feature columns as the single-prediction endpoint.

Example health check from the Codespace terminal:

```bash
curl http://localhost:7860/
```

## Run locally without Docker

The frontend is configured to call the backend at `http://backend:7860`. Use the host-gateway mapping shown above in Codespaces so requests can reach the published backend port.
