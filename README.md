# 🤖 AI Chatbot with Streamlit + Ollama + LangChain + LangGraph

A modern, production-ready AI chatbot UI built using:

- Streamlit (UI)
- Ollama (local LLMs)
- LangChain (LLM abstraction)
- LangGraph (stateful workflows)

---

# 🚀 Features

- 💬 ChatGPT-like UI with Streamlit
- 🧠 Local LLMs via Ollama (no API cost)
- 🔄 Stateful conversations with LangGraph
- ⚡ Streaming responses
- 🧱 Clean, scalable architecture

---

# 📦 Installation (uv - Recommended)

## 1. Create project

```bash
uv init ai-chatbot
cd ai-chatbot
```

## 2. Add dependencies

```bash
uv add streamlit langchain langgraph langchain-ollama ollama python-dotenv
```

## 🔒 Optional (exact versions)

```bash
uv add \
  streamlit==1.55.0 \
  langchain==1.2.14 \
  langgraph==1.1.4 \
  langchain-ollama==1.0.1 \
  ollama==0.6.1 \
  python-dotenv==1.2.2
```

---

# 🧠 Setup Ollama

## Install Ollama

👉 [https://ollama.com](https://ollama.com)

## Pull a model

```bash
ollama pull llama3
```

## Run Ollama server

```bash
ollama serve
```

---

# 📁 Project Structure

```
.
├── app.py
├── services/
│   └── llm.py
├── graph/
│   └── workflow.py
├── components/
│   └── chat_ui.py
├── .env
└── pyproject.toml
```

---

# 💻 Basic Streamlit Chat UI (app.py)

```python
import streamlit as st

st.set_page_config(page_title="AI Chatbot", page_icon="🤖")

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🤖 AI Chatbot")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    response = f"Echo: {prompt}"

    st.session_state.messages.append({"role": "assistant", "content": response})

    with st.chat_message("assistant"):
        st.markdown(response)
```

---

# 🔌 Connect to Ollama (LangChain)

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3")

response = llm.invoke("Hello")
print(response.content)
```

---

# 🔄 LangGraph Basic Workflow

```python
from langgraph.graph import StateGraph

class State(dict):
    pass


def chatbot(state: State):
    state["response"] = "Hello from LangGraph"
    return state


graph = StateGraph(State)
graph.add_node("chatbot", chatbot)
graph.set_entry_point("chatbot")

graph = graph.compile()
```

---

# ⚡ Streaming Responses (Better UX)

```python
import time


def stream_response(text):
    for word in text.split():
        yield word + " "
        time.sleep(0.05)
```

---

# ▶️ Run the App

```bash
uv run streamlit run app.py
```

---

# 🧠 Best Practices

- ✅ Keep UI and logic separate
- ✅ Limit chat history size
- ✅ Use streaming for UX
- ✅ Store config in `.env`
- ✅ Use LangGraph for complex flows

---

# 🔥 Next Steps

- Add RAG (PDF / database)
- Connect FastAPI backend
- Add authentication
- Deploy with Docker

---

# 📄 License

MIT
