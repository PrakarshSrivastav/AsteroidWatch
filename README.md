# AsteroidWatch ☄️

An interactive Near-Earth Object (NEO) monitoring dashboard and collision risk assessment engine. This application tracks asteroids using data inspired by NASA's NeoWs (Near Earth Object Web Service), caches telemetry, evaluates potential impact hazards using custom physics-based models, and displays them on a premium, dark-themed responsive dashboard.

## Architecture

The project consists of:
- **Backend (Python / FastAPI)**:
  - `main.py`: Application entry point, configures CORS, and mounts routers.
  - `routers/asteroids.py`: API endpoints for fetching daily/weekly tracked asteroids and risk assessments.
  - `services/nasa_client.py`: Client wrapper to query NASA NeoWs API (with fallback mock data for offline/limit-free use).
  - `services/risk_engine.py`: Computes custom hazard ratings, Torino scale approximations, and impact probabilities.
  - `models/asteroid.py`: Pydantic models for structured, typed asteroid and risk data.
  - `cache/redis_cache.py`: Cache client that integrates with Redis for fast retrieval of historical telemetry.
- **Frontend (Vanilla HTML5 / CSS3 / JavaScript)**:
  - `index.html`: Modern, premium web interface with a dark futuristic design, glassmorphic cards, and detailed charts.
  - `dashboard.js`: Interactive logic, asynchronous API requests, and live data rendering.
  - `styles.css`: Custom CSS containing design tokens, rich gradients, micro-animations, and responsive layouts.
- **Containerization & Config**:
  - `Dockerfile` & `docker-compose.yml`: Easily spin up the backend, frontend, and a Redis cache instance.
  - `requirements.txt`: Python package dependencies.
  - `.env.example`: Template for environment variables including NASA API key and Redis settings.

## Getting Started

### Method 1: Using Docker Compose (Recommended)

1. Make sure you have Docker and Docker Compose installed.
2. Copy `.env.example` to `.env` and adjust variables if needed.
3. Run the following command:
   ```bash
   docker-compose up --build
   ```
4. Access the dashboard at [http://localhost:8080](http://localhost:8080) (or whichever port is mapped to the frontend). The API will be available at [http://localhost:8000](http://localhost:8000).

### Method 2: Manual Run

#### Backend:
1. Make sure you are in the project root directory (`asteroidwatch`).
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the development server:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

#### Frontend:
1. Serve the `frontend` folder using any static server (e.g. `python -m http.server 8080` from the `frontend` folder).
2. Open `http://localhost:8080` in your browser.
