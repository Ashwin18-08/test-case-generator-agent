This README provides a comprehensive overview of your **AI QA Test Case Generator**, explaining the LangGraph architecture, the Playwright MCP integration, and the setup process.

---

# AI QA Test Case Generator

An autonomous AI agent built with **LangGraph**, **Playwright MCP**, and **Groq (Llama 3.1)**. This tool browses live websites, extracts their rendered HTML, and generates structured test cases (JSON/Gherkin) based on the actual UI components found.

## How the Nodes Work

The project uses a Directed Acyclic Graph (DAG) to manage the state and logic flow. Each node is responsible for a specific part of the QA lifecycle.

### 1. Extractor Node (`extractor_node`)

* **Purpose**: Parses the initial user input.
* **Logic**: Uses Regex to find URLs and keywords (like "json" or "gherkin").
* **State Update**: Populates `url`, `raw_html` (if provided directly), and `output_format`.

### 2. Analyst Node (`analyst_node`)

* **Purpose**: The "Brain" of the operation.
* **Logic**: Decides whether the agent has enough information to proceed or if it needs to trigger a browser fetch or ask the user for missing details.
* **Decisions**: `FETCH_URL`, `ASK_CLARIFICATION`, or `PROCEED`.

### 3. Fetch Node (`fetch_url_node`)

* **Purpose**: Controlled browsing via Playwright MCP.
* **Logic**:
1. Starts a secure **stdio** transport session with the Playwright MCP server.
2. Uses the LLM to decide on browser actions (Navigate).
3. Executes `browser_run_code` to extract the full `document.documentElement.outerHTML`.


* **Output**: Cleaned raw HTML string.

### 4. Clarification Node (`clarification_node`)

* **Purpose**: Handles missing data.
* **Logic**: Uses `interrupt` to pause the graph and ask the user for a URL or preferred output format.

### 5. Generator Node (`generator_node`)

* **Purpose**: Final output creation.
* **Logic**: Analyzes the `raw_html` and generates high-quality test cases mapped to the requested format (JSON/Gherkin).

---

## 🛠️ Installation & Setup

### 1. Prerequisites

* **Python 3.10+**
* **Node.js & npx** (Required for the Playwright MCP server)
* **Groq API Key** (For the Llama 3.1 model)

### 2. Clone and Install Dependencies

```bash
git clone repo link
cd test_case_generation
pip install -r requirements.txt

```

### 3. Install Playwright Browsers

The MCP server uses Playwright under the hood. You must install the browser binaries:

```bash
playwright install chromium

```

### 4. Environment Configuration

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key_here

```

### 5. Running the Application

You can run the agent in two ways:

**CLI Mode:**

```bash
python main.py

```

**Streamlit Web UI:**

```bash
streamlit run app.py

```

---

## 🧪 Usage Example

1. **Input**: "I want to generate test cases for [https://example.com](https://example.com)"
2. **Agent**: "I'd be happy to help! Would you like the output in JSON or Gherkin?"
3. **User**: "json"
4. **Agent**: *Browsing... Extracting HTML... Generating...*
5. **Output**: A structured `.json` file containing functional test cases for the "Example Domain" website.

---

## 📁 Project Structure

```text
├── src/
│   ├── main.py          # CLI Entry point (Async)
│   ├── app.py           # Streamlit Web UI
│   ├── graph.py         # LangGraph Workflow definition
│   ├── nodes.py         # Individual Node functions
│   ├── state.py         # QAState TypedDict definition
├── .env                 # API Keys (Ignored by git)
├── .gitignore           # File exclusion rules
└── requirements.txt     # Python dependencies

```

Would you like me to add a **"Troubleshooting"** section regarding the specific Playwright tool names we discovered?
