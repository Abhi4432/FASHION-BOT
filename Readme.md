🛍️ Fashion Dealer AI Assistant

An AI-powered assistant for managing fashion orders, product queries, and recommendations.
The system combines FastAPI backend, LangGraph orchestration, Ollama LLM integration, and a Streamlit frontend for an interactive experience.

📌 Features

🔐 User Authentication (username/email + password)

📦 Order Viewer Agent – fetch order details from SQLite DB

🧭 Router Node – decides which agent handles user queries

🤖 Conversational Bot – interactive UI via Streamlit

🛠️ LangGraph Workflow – modular agents with orchestration

🗂️ SQLite Database – orders and products stored locally

🖼️ Product Information – includes description and image URL

📡 Streaming Support – LLM responses stream back in real time

🏗️ Project Structure
fashion_agent/
│
├── backend/
│   ├── src/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── agents/
│   │   │   ├── router.py        # Router node (intent detection)
│   │   │   ├── order_viewer.py  # Order viewer node
│   │   │   ├── workflow.py      # LangGraph workflow (orchestrator)
│   │   └── data/
│   │       └── fashion_ai.db    # SQLite database
│
├── frontend/
│   └── src/
│       ├── app.py               # Streamlit entry
│       ├── home.py              # Login page
│       ├── bot.py               # Chatbot page
│
└── README.md

⚙️ Installation
1️⃣ Clone the Repository
git clone https://github.com/yourusername/fashion-dealer.git
cd fashion-dealer

2️⃣ Setup Conda Environment
conda create -n fashion_ai python=3.10 -y
conda activate fashion_ai

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Install & Run Ollama (for LLM)

Download Ollama: https://ollama.ai

Start the Ollama server:

ollama serve


Pull a model (example: Gemma-2B):

ollama pull gemma:2b

▶️ Running the Project
Start Backend (FastAPI + LangGraph) and navigate to backend directory
cd backend
uvicorn src.main:app --reload

Start Frontend (Streamlit)
streamlit run frontend/src/app.py

💡 Usage

Open the frontend in your browser (default: http://localhost:8501)

Login with your username/email & password

Chat with the AI assistant:

Ask for order details (e.g., "Check my order with ID 35")

Get product info from DB

Receive contextual LLM responses using past conversation history

Logout or reset conversation when needed

📊 Database Schema
ORDERS

ORDER_ID

PRODUCT_ID

USER_ID

ORDER_DATE, SHIPPING_DATE, DELIVERY_DATE

AMOUNT, STATUS, DELIVERY_PARTNER_NO

PRODUCTS

P_ID

NAME, PRICE, COLOUR, BRAND

DESCRIPTION

IMAGE_URL

🚀 Roadmap

 Add Recommendation Agent

 Expand to multi-agent workflows (products, returns, billing)

 Add vector store + RAG for product search

 Improve UI with image previews in Streamlit