# 🧠 NeuroOps: Autonomous AI Task Execution System

**NeuroOps** is a production-grade, multi-agent orchestration framework designed to transform high-level natural language goals into executed actions. Unlike simple chatbots, NeuroOps employs a cyclic reasoning architecture involving **Planning**, **Tool Execution**, **Reflection**, and **Long-Term Memory**.

Built with **FastAPI**, **Ollama (Qwen)**, and **ChromaDB**, it provides a scalable backend for autonomous agents capable of web research, file manipulation, code execution, and self-correction.

---

## 🌟 Key Features

- ** Multi-Agent Architecture**: Distinct roles for Planning, Execution, and Critiquing ensure high-quality outputs.
- **🛠 Dynamic Tool Selection**: An intelligent router decides whether to use LLM reasoning or specific tools (Web Search, Python Interpreter, File I/O) per task.
- **♻️ Self-Reflection Loop**: A dedicated "Critic" agent reviews outputs against original goals to improve accuracy and completeness before final delivery.
- **💾 Persistent Memory**: Integrated ChromaDB vector store allows the system to retain context and learn from past executions across sessions.
- ** Production Ready**: Built on FastAPI with type safety, error handling, retry mechanisms, and modular design patterns.
- **🔒 Safe Execution**: Sandboxed Python execution and controlled file access prevent unintended system modifications.

---

## 🏗 System Architecture

```mermaid
graph TD
    User[User Goal] --> API[FastAPI Endpoint]
    API --> Orchestrator[Orchestrator]
    
    subgraph "Agent Core"
        Orchestrator --> Planner[Planner Agent]
        Planner -->|Task List| Executor[Executor Agent]
        Executor -->|Raw Output| Critic[Critic Agent]
        Critic -->|Refined Output| Final[Final Response]
    end
    
    subgraph "Tool Registry"
        Executor -->|Selects| Tools[Dynamic Tools]
        Tools --> Web[Web Search]
        Tools --> Code[Python Exec]
        Tools --> File[File I/O]
    end
    
    subgraph "Memory Layer"
        Orchestrator -->|Store/Retrieve| Chroma[(ChromaDB)]
    end
    
    Final --> User
    