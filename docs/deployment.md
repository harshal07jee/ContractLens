# Deploying ContractLens on Render

You can deploy ContractLens on [Render](https://render.com) using either **Render Blueprints (automatic)** or by manually setting up **two Web Services** (one for the backend and one for the frontend).

---

## Method 1: Using Render Blueprints (Recommended)

1. Push your latest code to your GitHub repository:
   ```bash
   git push origin main
   ```
2. Go to your [Render Dashboard](https://dashboard.render.com).
3. Click **"New +"** in the top-right corner and select **"Blueprint"**.
4. Connect your GitHub repository (`harshal07jee/ContractLens`).
5. Render will automatically read `render.yaml` and create two services:
   - `contractlens-backend` (FastAPI Python service)
   - `contractlens-frontend` (Next.js Node service)
6. Once the backend deploys, copy its URL (e.g. `https://contractlens-backend.onrender.com`).
7. In the Render Dashboard, open `contractlens-frontend` -> **Environment**, and set:
   - `NEXT_PUBLIC_API_BASE_URL`: `https://<your-backend-service-name>.onrender.com`
8. Trigger a redeploy of `contractlens-frontend` so Next.js embeds the URL during the build.

---

## Method 2: Manual Web Service Setup (Step-by-Step)

If you prefer to configure each service manually in the Render UI:

### Step 1: Deploy the Backend API

1. In Render Dashboard, click **New +** -> **Web Service**.
2. Connect your repo: `https://github.com/harshal07jee/ContractLens`.
3. Fill in the configuration:
   - **Name**: `contractlens-backend`
   - **Region**: Choose closest to you (e.g., Oregon, Frankfurt, Singapore)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
4. Expand **Advanced** -> **Add Environment Variable**:
   - `PYTHON_VERSION`: `3.11.9`
   - `CORS_ORIGINS`: `*`
   - `MAX_UPLOAD_SIZE_MB`: `25`
5. Click **Create Web Service**.
6. Wait for the deploy to complete. Copy your live backend URL (e.g. `https://contractlens-backend.onrender.com`). Test it by visiting `https://contractlens-backend.onrender.com/health` in your browser (should return `{"status": "ok"}`).

---

### Step 2: Deploy the Frontend Dashboard

1. In Render Dashboard, click **New +** -> **Web Service**.
2. Connect the same repo: `https://github.com/harshal07jee/ContractLens`.
3. Fill in the configuration:
   - **Name**: `contractlens-frontend`
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Runtime**: `Node`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`
   - **Instance Type**: `Free`
4. Expand **Advanced** -> **Add Environment Variable**:
   - `NEXT_PUBLIC_API_BASE_URL`: Paste your backend URL from Step 1 (e.g. `https://contractlens-backend.onrender.com` without trailing slash).
5. Click **Create Web Service**.
6. Once deployed, open your live frontend URL (e.g. `https://contractlens-frontend.onrender.com`).

---

## Verification on Render

1. Open your live frontend URL.
2. Click **"+ Upload contract"** and upload `sample_contracts/Enterprise_Service_Agreement.pdf`.
3. Verify that the Overview metrics, Obligations, Timeline events, and AI Assistant respond with citations and that the Source Evidence Drawer opens when clicking citations.
