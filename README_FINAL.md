# SAIL Maritime Procurement Desk — Final Full Project

This package preserves the original Streamlit application, ML datasets/models and Python scripts, and adds the final React/Vite dashboard plus a FastAPI bridge to the same `optimizer.py` pipeline.

## Project structure

- `app.py` — original Streamlit application
- `optimizer.py` — unified freight, fuel, timing and vessel pipeline
- `feight model/` — freight XGBoost model, encoders and dataset
- `fuel model/` — fuel dataset/model script
- `timing model/` — charter timing model files
- `vessel model/` — vessel ranking dataset/model files
- `backend/` — FastAPI bridge for React
- `frontend/` — final React maritime procurement dashboard

## React frontend

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`.

## Backend

From the repository root:

```bash
source venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

If the virtual environment does not exist, create one and install `requirements.txt`.

## Original Streamlit app

```bash
streamlit run app.py
```

The React dashboard and Streamlit application can coexist because they use the same Python optimization layer.

## Important

Do not include the local `venv/` directory when moving this project between machines. It is platform/Python-version specific. Install dependencies from `requirements.txt` instead.
