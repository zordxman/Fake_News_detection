# Fake News Detection — Cleaned Project

This is the cleaned version of the uploaded fake-news notebook and its LLM,
retrieval, and verification modules.

## Structure

```text
fake_news_fixed_full/
├── data/
│   ├── fake.csv
│   └── true.csv
├── models/
├── notebooks/
│   └── 01_data_loading_and_eda_fixed.ipynb
├── src/
│   ├── llm.py
│   ├── retrieval.py
│   └── verification.py
└── requirements.txt
```

Copy `fake.csv` and `true.csv` into `data/`.

## Install

```cmd
python -m pip install -r requirements.txt
```

## Run

```cmd
jupyter notebook
```

Open `notebooks/01_data_loading_and_eda_fixed.ipynb` and run cells from top to bottom.

## Ollama

The ML/EDA section does not require Ollama.

For claim extraction and verification, run:

```cmd
ollama serve
ollama pull llama3.2:3b
```

The configured Ollama endpoint is `http://localhost:11434/api/generate`.

## Fixed

- 106 cells reduced to 27 ordered cells.
- Removed duplicate dataset loading.
- Removed repeated EDA cells.
- Removed repeated TF-IDF/SVM training.
- Removed duplicate prediction functions.
- Removed duplicate analysis execution.
- Removed test-only evidence from the main workflow.
- Removed the middle-of-notebook `pip install`.
- Added robust project path detection.
- Added dataset validation and empty-text handling.
- Added safe optional LLM/retrieval/verification stages.
- Added claim parsing without assuming exactly 3 claims.
- Added Ollama timeout/error handling.
- Made Google News URL decoding optional at runtime.
