

# 📊 Virtual Accounting Chatbot with FastMCP

**An AI-powered Virtual Accounting Assistant built with FastMCP, local LLMs, and Streamlit.**

This project demonstrates how the **Model Context Protocol (MCP)** can be used to build an intelligent accounting chatbot that understands natural language queries, retrieves financial data, and generates official accounting documents using local language models.

---

## 🔍 Table of Contents

* About the Project
* Features
* System Architecture
* Installation
* Running the Application
* UI Preview
* Project Structure
* Example Use Cases
* Technologies Used
* License

---

## 📌 About the Project

The **Virtual Accounting Chatbot with FastMCP** is an AI-based chatbot designed to assist with accounting and financial operations through natural language interaction.

It enables users to:

* Ask accounting-related questions
* Retrieve financial or taxpayer information
* Generate official documents such as petitions or reports
* Interact with structured tools via MCP instead of plain text responses

The project uses **FastMCP** to connect LLM reasoning with custom accounting tools, and **Streamlit** to provide a simple and interactive user interface.

---

## 🚀 Features

* 🤖 AI-powered accounting chatbot
* 🔗 Model Context Protocol (MCP) integration
* 🧠 Local LLM support (e.g., Ollama)
* 🖥️ Streamlit-based user interface
* 📄 Automatic document and petition generation
* 📊 Financial data querying via natural language
* 🛠️ Modular and extensible tool-based architecture

---

## 🧠 System Architecture

The system consists of four main components:

1. **FastMCP Server**

   * Acts as a bridge between the LLM and accounting tools
   * Exposes structured tools instead of raw text prompts

2. **Local LLM (e.g., Ollama)**

   * Understands user queries
   * Decides which MCP tools to call

3. **Streamlit UI**

   * Provides a chat-based interface
   * Displays responses and generated documents

4. **Database (Optional)**

   * Stores accounting data, query history, or mock financial records

---

## 🛠️ Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/iremclk812/Virtual-Accounting-Chatbot-with-FastMCP.git
cd Virtual-Accounting-Chatbot-with-FastMCP
```

### 2️⃣ Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Application

### Start the FastMCP Server

```bash
python mcp_server.py
```

### Launch the Streamlit Interface

```bash
streamlit run chatbot_gui.py
```

Then open your browser at:

👉 **[http://localhost:8501](http://localhost:8501)**

---

## 🖼️ UI Preview (Conceptual)

Below is a conceptual representation of the chatbot interface:

```
┌───────────────────────────────────────────┐
│ Virtual Accounting Chatbot                │
├───────────────────────────────────────────┤
│ User: Show my annual financial report     │
│ AI:   Please specify the year.            │
│                                           │
│ User: 2025                                │
│ AI:   Here is your 2025 financial summary │
│                                           │
├───────────────────────────────────────────┤
│ Tip: You can say "generate a petition"    │
└───────────────────────────────────────────┘
```

> You can add real screenshots by placing images in the repository and linking them here.

---

## 📁 Project Structure

```
.
├── client/
│   └── assets/                # UI images or static files
├── db/
│   └── data.db                # Database (optional)
├── tools/
│   └── accounting_tools.py    # MCP accounting tools
├── mcp_server.py              # FastMCP server
├── chatbot_gui.py             # Streamlit UI
├── requirements.txt
├── README.md
```

---

## 💡 Example Use Cases

* “Show my tax obligations for this year.”
* “Get my current bank account balance.”
* “Summarize expenses by category.”
* “Generate an official accounting petition.”
* “Prepare a financial report for Q1.”

---

## 🧰 Technologies Used

* **Python**
* **FastMCP** (Model Context Protocol)
* **Streamlit**
* **Local LLMs (e.g., Ollama)**
* **SQLite / JSON (optional storage)**

---

## 📄 License

This project is licensed under the **MIT License**.
See the `LICENSE` file for more details.

---
