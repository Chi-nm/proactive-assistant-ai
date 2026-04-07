# 🚀 Proactive Multi-Agent Personal Assistant

**Live Demo:** [Click here to talk to the Assistant](https://proactive-assistant-941120253400.us-central1.run.app/dev-ui)

A sophisticated, multi-agent AI system built using the **Google Agent Development Kit (ADK)** and deployed on **Google Cloud Run**. This assistant manages tasks, schedules, and information by coordinating specialized agents and interacting with a persistent SQL database.

## 🌟 Key Features

* **Multi-Agent Orchestration**: Utilizes a `SequentialAgent` workflow to coordinate between a **Coordinator**, an **Execution Specialist**, and a **Response Formatter**.
* **Proactive Conflict Detection**: Unlike standard LLMs, this system performs a "Read-before-Write" check against a SQL database to prevent overlapping schedule entries.
* **Persistent Memory**: Stores and retrieves structured tasks and general "Information Notes" using a SQLite database (optimized for Cloud Run's `/tmp` directory).
* **Advanced Tooling**: Integrates simulated **Model Context Protocol (MCP)** tools for calendar management and database logging.
* **Traceability**: Full execution transparency via the ADK Inspector, showing agent hand-offs and tool outputs.

---

## 🏗️ Architecture

The system follows a hierarchical delegation pattern:

1.  **Greeter Coordinator**: The entry point that identifies user intent and routes it to the workflow.
2.  **Assistant Workflow (Sequential)**:
    * **Step 1: Execution Specialist**: Interacts with the `check_conflicts`, `save_note`, and `search_memory` tools.
    * **Step 2: Response Formatter**: Synthesizes raw technical data from the Specialist into a natural, human-friendly response.



---

## 🛠️ Tech Stack

* **Framework**: Google Agent Development Kit (ADK)
* **Model**: Gemini 2.5 Flash (via Vertex AI)
* **Database**: SQLite3 (Structured Persistence)
* **Deployment**: Google Cloud Run (Serverless API)
* **Protocol**: Model Context Protocol (MCP) Design Patterns

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Google Cloud Project with Vertex AI API enabled.
* `google-adk` library installed.

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Chi-nm/proactive-assistant-ai.git
   cd proactive-assistant-ai
   ```
2. Set up your environment variables in a `.env` file:
   ```text
   MODEL=gemini-2.5-flash
   PROJECT_ID=your-google-cloud-project-id
   ```
3. Deploy to Cloud Run:
   ```bash
   adk deploy cloud_run --project=$PROJECT_ID --region=us-central1 --with_ui .
   ```

---

## 📊 Real-World Workflow Example

**User Prompt**: *"Schedule a meeting for 10 AM tomorrow and remember that my manager likes Flat Whites."*

**System Execution**:
1.  **Coordinator** transfers control to the `assistant_workflow`.
2.  **Execution Specialist** calls `check_conflicts_and_schedule(time="10 AM tomorrow")`.
3.  **Execution Specialist** calls `save_note(content="Manager likes Flat Whites")`.
4.  **Response Formatter** confirms the schedule and the saved preference in a single polite message.

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.

---

### **Submission Note for Judges**
This project demonstrates the ability to handle **ephemeral storage constraints** in serverless environments by utilizing the `/tmp/` directory for SQLite persistence, ensuring the assistant remains "stateful" across sessions.
