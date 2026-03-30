# Code Coach 🧑‍🏫

Code Coach is a beginner-focused programming support tool designed to help new developers identify and fix common coding mistakes in real-time. It currently provides intelligent, pattern-based hints for Java code.

## 🌟 Features

- **Beginner-Friendly Diagnostics:** Code Coach identifies common logical and syntax errors that beginners often make, such as:
  - **Off-By-One Loop Boundaries:** Detects loops using `<= array.length` instead of `< array.length`.
  - **Incorrect Conditional Operators:** Warns when assignments (`=`) are used instead of equality checks (`==`) within `if` or `while` conditions.
  - **Array Length Index Misuse:** Highlights out-of-bounds risks when using `array[array.length]` instead of `array.length - 1`.
- **VS Code Integration:** Seamlessly integrated into VS Code, allowing you to trigger analysis with a simple command.
- **AST-Based Analysis:** Powered by a robust Python backend that parses code into an Abstract Syntax Tree (AST) for accurate error detection.

## 📁 Project Structure

This project follows a client-server architecture:

- `extension/` - The VS Code extension (TypeScript), which provides the user interface and sends code to the backend.
- `backend/` - The Python backend (FastAPI), which parses Java code and generates diagnostics.
- `shared/` - Shared schemas and examples across the project.
- `data/` - Datasets used for testing or knowledge building.
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

## 🛠️ Technologies Used

- **Frontend:** TypeScript, VS Code Extension API
- **Backend:** Python, FastAPI, Pydantic, Tree-sitter (for AST parsing)