# Code Coach 🧑‍🏫

Code Coach is a beginner-focused programming support tool designed to help new developers identify and fix common coding mistakes in real-time. It currently provides intelligent, pattern-based hints for Java code.

## 🌟 Features

- **Beginner-Friendly Diagnostics:** Code Coach identifies common logical and syntax errors that beginners often make, such as:
  - **Off-By-One Loop Boundaries:** Detects loops using `<= array.length` instead of `< array.length`.
  - **Incorrect Conditional Operators:** Warns when assignments (`=`) are used instead of equality checks (`==`) within `if` or `while` conditions.
  - **Array Length Index Misuse:** Highlights out-of-bounds risks when using `array[array.length]` instead of `array.length - 1`.
- **VS Code Integration:** Seamlessly integrated into VS Code, allowing you to trigger analysis with a simple command.
- **AST-Based Analysis:** Powered by a robust Python backend that parses code into an Abstract Syntax Tree (AST) for accurate error detection.
- **Machine Learning Pipeline:** An end-to-end ML pipeline extracts AST-based features from Java snippets and trains baseline classifiers (Logistic Regression, Random Forest, SVM) to detect common bug patterns.

## 📁 Project Structure

This project follows a client-server architecture:

- `extension/` - The VS Code extension (TypeScript), which provides the user interface and sends code to the backend.
- `backend/` - The Python backend (FastAPI), which parses Java code and generates diagnostics.
  - `app/feature_extractor.py` - Extracts AST-based numeric features from Java source code.
  - `app/detectors/` - Rule-based detectors for off-by-one errors, incorrect conditionals, and array index misuse.
  - `app/dev_tools/` - Developer scripts for the ML pipeline (see below).
  - `models/` - Trained `.joblib` model files and a metrics summary CSV.
- `data/ml/` - ML datasets and splits.
  - `raw_snippets/` - Raw Java code snippets used for training.
  - `metadata/snippet_index.csv` - Index of all snippets with labels.
  - `extracted/` - Feature CSVs extracted from snippets.
  - `splits/` - Train / val / test split CSVs.
- `shared/` - Shared schemas and examples across the project.
- `knowledge_base/` - Hint rules and concept mappings.
- `logs/` - System logs.
- `docs/` - Project notes and screenshots.

## 🚀 Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) (for the VS Code extension)
- [Python 3.8+](https://www.python.org/) (for the backend)
- [Visual Studio Code](https://code.visualstudio.com/)

### 1. Backend Setup

The backend handles the code parsing and diagnostic generation using FastAPI.

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   ```
   **On Windows:**
   ```bash
   .venv\Scripts\activate
   ```
   **On macOS/Linux:**
   ```bash
   source .venv/bin/activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```
   The backend will start on `http://localhost:8000`.

### 2. Extension Setup

The VS Code extension communicates with the locally running backend.

1. Open a new terminal and navigate to the extension directory:
   ```bash
   cd extension/code-coach-vscode
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Open the `extension/code-coach-vscode` folder in VS Code.
4. Press `F5` to start debugging. This will open a new Extension Development Host window.

## 💻 Usage

1. In the Extension Development Host window, open any Java file (`.java`).
2. Open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`).
3. Run **"Code Coach: Analyze Current File"**.
4. Review the beginner-friendly hints provided for common coding errors.

## 🧪 ML Pipeline (Dev Tools)

The ML pipeline trains baseline classifiers to detect bug patterns using AST-derived numeric features. All scripts are run from the `backend/` directory.

### Pipeline Overview

```
raw_snippets/ + snippet_index.csv
        ↓
  build_dataset   →  data/ml/extracted/features_v1.csv
                      (+ per-bug binary CSVs)
        ↓
  split_dataset   →  data/ml/splits/  (train / val / test)
        ↓
  train_baselines →  backend/models/*.joblib
                     backend/models/baseline_metrics_v1.csv
```

### Step 1 — Build the Feature Dataset

Extracts AST-based features for every snippet listed in `snippet_index.csv` and writes the master feature CSV and three per-bug binary datasets.

```bash
py -m app.dev_tools.build_dataset
```

**Outputs:**
- `data/ml/extracted/features_v1.csv` — master feature table (all labels)
- `data/ml/extracted/off_by_one_binary_v1.csv`
- `data/ml/extracted/incorrect_conditional_binary_v1.csv`
- `data/ml/extracted/array_length_index_binary_v1.csv`

### Step 2 — Split the Dataset

Splits the master feature table into train / val / test sets (70 / 15 / 15 split). Paired snippets (buggy + clean pairs) are kept together to prevent data leakage.

```bash
py -m app.dev_tools.split_dataset
```

**Outputs:**
- `data/ml/splits/train_v1.csv`
- `data/ml/splits/val_v1.csv`
- `data/ml/splits/test_v1.csv`

### Step 3 — Train Baseline Models

Trains three classifiers (Logistic Regression, Random Forest, SVM) for each of the three bug targets and saves them as `.joblib` files alongside a metrics summary.

```bash
py -m app.dev_tools.train_baselines
```

**Trained targets:**

| Target | Description |
|---|---|
| `has_off_by_one` | Off-by-one loop boundary errors |
| `has_incorrect_conditional` | Assignment used instead of equality check |
| `has_array_length_index_misuse` | Array accessed at `array.length` index |

**Outputs:**
- `backend/models/<target>__<model>.joblib` — 9 model files (3 targets × 3 models)
- `backend/models/baseline_metrics_v1.csv` — val & test precision / recall / F1 / accuracy per model

## 🛠️ Technologies Used

- **Frontend:** TypeScript, VS Code Extension API
- **Backend:** Python, FastAPI, Pydantic, Tree-sitter (for AST parsing)
- **ML:** scikit-learn (Logistic Regression, Random Forest, SVM), pandas, joblib