from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.services.prediction_service import predict_news
from backend.services.factcheck_service import fact_check_news


# ============================================================
# CREATE FASTAPI APP
# ============================================================

app = FastAPI(
    title="Fake News Detection API",
    description="AI-powered fake news detection backend",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class NewsRequest(BaseModel):
    text: str


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Fake News Detection API is running"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model": "loaded"
    }


# ============================================================
# ML PREDICTION
# ============================================================

@app.post("/api/predict")
def predict(request: NewsRequest):

    try:
        result = predict_news(request.text)

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(e)}"
        )


# ============================================================
# COMPLETE ANALYSIS
# ============================================================

@app.post("/api/analyze")
def analyze_news(request: NewsRequest):

    try:

        # ---------------------------------------------
        # 1. ML classification
        # ---------------------------------------------

        prediction = predict_news(
            request.text
        )

        # ---------------------------------------------
        # 2. Evidence-based fact checking
        # ---------------------------------------------

        fact_check = fact_check_news(
            request.text
        )

        # ---------------------------------------------
        # 3. Return combined result
        # ---------------------------------------------

        return {
            "success": True,

            # ML information
            "ml_prediction": prediction["prediction"],
            "decision_score": prediction["decision_score"],
            "classification_strength": prediction[
                "classification_strength"
            ],

            # Fact-check information
            "final_verdict": fact_check.get(
                "final_verdict",
                "INCONCLUSIVE"
            ),

            "claims": fact_check.get(
                "claims",
                []
            ),

            "message": fact_check.get(
                "message",
                ""
            )
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Analysis error: {str(e)}"
        )