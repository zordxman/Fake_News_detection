import re
import string
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


# ============================================================
# 1. TEXT CLEANING
# ============================================================

def clean_text(text):
    text = str(text).lower()

    text = re.sub(
        r"https?://\S+|www\.\S+",
        " ",
        text
    )

    text = re.sub(
        r"<[^>]*>",
        " ",
        text
    )

    text = text.translate(
        str.maketrans("", "", string.punctuation)
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


# ============================================================
# 2. LOAD DATASET
# ============================================================

print("=" * 70)
print("LOADING DATASET")
print("=" * 70)

fake_path = "fake_news_fixed_full/data/fake.csv"
true_path = "fake_news_fixed_full/data/true.csv"

fake = pd.read_csv(fake_path)
true = pd.read_csv(true_path)

print("Fake records :", len(fake))
print("True records :", len(true))


# Labels
fake["label"] = 0
true["label"] = 1

df = pd.concat(
    [fake, true],
    ignore_index=True
)


# ============================================================
# 3. DATA CLEANING
# ============================================================

print("\nCleaning dataset...")

df["text"] = (
    df["text"]
    .fillna("")
    .astype(str)
)

# Remove empty articles
df = df[
    df["text"].str.strip().ne("")
]

# Remove duplicate rows
before_duplicates = len(df)

df = df.drop_duplicates(
    keep="first"
).reset_index(drop=True)

after_duplicates = len(df)

print(
    "Duplicates removed:",
    before_duplicates - after_duplicates
)


# Shuffle exactly as training pipeline
df = df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)


# Clean text
df["clean_text"] = df["text"].apply(
    clean_text
)

# Remove empty cleaned text
df = df[
    df["clean_text"].str.strip().ne("")
].reset_index(drop=True)


print("Final dataset size:", len(df))


# ============================================================
# 4. FEATURES AND LABELS
# ============================================================

X = df["clean_text"]
y = df["label"]


print("\nLabel distribution:")
print(
    y.value_counts().rename(
        index={
            0: "FAKE",
            1: "REAL"
        }
    )
)


# ============================================================
# 5. TRAIN / TEST SPLIT
# ============================================================

print("\nCreating train/test split...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Training samples:", len(X_train))
print("Testing samples :", len(X_test))


# ============================================================
# 6. TF-IDF
# ============================================================

print("\nCreating TF-IDF features...")

tfidf = TfidfVectorizer(
    max_features=50000,
    ngram_range=(1, 2)
)

X_train_tfidf = tfidf.fit_transform(
    X_train
)

X_test_tfidf = tfidf.transform(
    X_test
)

print(
    "TF-IDF training shape:",
    X_train_tfidf.shape
)

print(
    "TF-IDF testing shape:",
    X_test_tfidf.shape
)


# ============================================================
# 7. TRAIN NEW MODEL
# ============================================================

print("\nTraining NEW LinearSVC model...")

model = LinearSVC()

model.fit(
    X_train_tfidf,
    y_train
)

print("Training completed.")


# ============================================================
# 8. TEST MODEL
# ============================================================

print("\nRunning predictions...")

y_pred = model.predict(
    X_test_tfidf
)


# ============================================================
# 9. RESULTS
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

print("\n")
print("=" * 70)
print("PROPER MODEL EVALUATION")
print("=" * 70)

print(
    f"\nAccuracy: {accuracy:.4f}"
)

print(
    f"Accuracy: {accuracy * 100:.2f}%"
)


print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        target_names=[
            "FAKE",
            "REAL"
        ],
        digits=4
    )
)


print("Confusion Matrix:")

cm = confusion_matrix(
    y_test,
    y_pred
)

print(cm)


# ============================================================
# 10. ERROR COUNT
# ============================================================

errors = (y_test != y_pred).sum()

print("\nTotal test articles:", len(y_test))
print("Incorrect predictions:", errors)
print(
    "Correct predictions:",
    len(y_test) - errors
)


print("\n")
print("=" * 70)
print("EVALUATION FINISHED")
print("=" * 70)