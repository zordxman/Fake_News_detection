import re
import string
from pathlib import Path

import joblib


BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "models" / "fake_news_svm.pkl"
VECTORIZER_PATH = BASE_DIR / "models" / "tfidf_vectorizer.pkl"


# Load model
model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)


def clean_text(text: str) -> str:
    text = str(text).lower()

    text = re.sub(
        r"https?://\S+|www\.\S+",
        " ",
        text
    )

    text = re.sub(
        r"<.*?>",
        " ",
        text
    )

    text = text.translate(
        str.maketrans(
            "",
            "",
            string.punctuation
        )
    )

    text = re.sub(
        r"\d+",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    return text


def predict_news(text: str):

    if not text or not text.strip():
        raise ValueError(
            "News text cannot be empty."
        )

    cleaned_text = clean_text(text)

    features = vectorizer.transform(
        [cleaned_text]
    )

    prediction = model.predict(features)[0]

    decision_score = float(
        model.decision_function(features)[0]
    )

    # Existing dataset mapping
    label = (
        "REAL"
        if int(prediction) == 1
        else "FAKE"
    )

    # Distance from SVM decision boundary.
    # This is NOT factual confidence.
    strength = abs(decision_score)

    if strength < 0.25:
        classification_strength = "LOW"
    elif strength < 0.75:
        classification_strength = "MEDIUM"
    else:
        classification_strength = "HIGH"

    return {
        "prediction": label,
        "decision_score": decision_score,
        "classification_strength": classification_strength,
        "note": (
            "This is a text-pattern classification based on "
            "the model's training data. It does not independently "
            "verify whether the claims are factually true."
        )
    }