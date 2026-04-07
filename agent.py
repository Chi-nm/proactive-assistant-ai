# import os
# import sqlite3
# from datetime import datetime
# from dotenv import load_dotenv

# from google.adk import Agent
# from google.adk.agents import SequentialAgent

# # Load environment variables
# load_dotenv()
# model_name = os.getenv("MODEL")

# # --- DATABASE CONFIGURATION (Cloud Run Compatible) ---
# # We use /tmp/ because Cloud Run's root filesystem is read-only.
# DB_PATH = '/tmp/assistant_memory.db'

# def init_db():
#     """Initializes the structured SQL database in the writable /tmp directory."""
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     # Create a table for structured task storage
#     c.execute('''CREATE TABLE IF NOT EXISTS tasks 
#                  (id INTEGER PRIMARY KEY, description TEXT, status TEXT, timestamp TEXT)''')
#     conn.commit()
#     conn.close()

# # Run initialization on module load
# init_db()

# # --- TOOLS (Database & MCP Integration) ---

# def record_task_to_db(task_description: str) -> dict:
#     """Stores a new task into the structured SQL database and returns a status dict."""
#     conn = sqlite3.connect(DB_PATH)
#     c = conn.cursor()
#     ts = datetime.now().strftime("%Y-%m-%d %H:%M")
#     c.execute("INSERT INTO tasks (description, status, timestamp) VALUES (?, ?, ?)",
#               (task_description, "pending", ts))
#     conn.commit()
#     conn.close()
#     return {
#         "status": "success", 
#         "logged_task": task_description, 
#         "database_timestamp": ts
#     }

# def call_calendar_mcp(event_name: str, time: str) -> str:
#     """Simulated MCP Tool for Google Calendar coordination."""
#     # In a real MCP setup, this would be a JSON-RPC call to a calendar server
#     return f"Calendar Update: Scheduled '{event_name}' for {time}."

# # --- STEP 1: The Execution Agent ---
# execution_specialist = Agent(
#     name="execution_specialist",
#     model=model_name,
#     description="Logs tasks to the DB and schedules calendar events.",
#     instruction="""
#     Analyze the user's request. 
#     1. Use 'record_task_to_db' to save any to-do items into the SQL database.
#     2. Use 'call_calendar_mcp' for any time-specific meetings or events.
    
#     Format your output as a raw summary of the tool results.
#     """,
#     tools=[record_task_to_db, call_calendar_mcp],
#     output_key="raw_execution_data" # The key used for the sequential hand-off
# )

# # --- STEP 2: The Response Formatter Agent ---
# response_formatter = Agent(
#     name="response_formatter",
#     model=model_name,
#     description="Synthesizes raw data into a friendly, professional response.",
#     instruction="""
#     You are a polite and professional Personal Assistant. 
#     Take the provided RAW_EXECUTION_DATA and turn it into a friendly summary for the user.
    
#     If multiple actions were taken (DB log and Calendar), mention both clearly.
    
#     RAW_EXECUTION_DATA:
#     { raw_execution_data }
#     """
# )

# # --- THE SEQUENTIAL WORKFLOW ---
# # This creates the visual 'hand-off' in the ADK Inspector Trace UI
# assistant_workflow = SequentialAgent(
#     name="assistant_workflow",
#     description="A multi-step pipeline that executes tasks then formats the result.",
#     sub_agents=[
#         execution_specialist, # Step 1: Tool Execution
#         response_formatter    # Step 2: Human-readable Formatting
#     ]
# )

# # --- ROOT AGENT (Entry Point) ---
# root_agent = Agent(
#     name="greeter_coordinator",
#     model=model_name,
#     description="The main entry point for the Proactive Assistant.",
#     instruction="""
#     Gently greet the user and ask how you can manage their tasks or schedule today.
    
#     Once the user provides a task-related request:
#     - Transfer control to the 'assistant_workflow'.
#     - Do not try to use the tools yourself; let the workflow handle it.
#     """,
#     sub_agents=[assistant_workflow]
# )

import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents import SequentialAgent

load_dotenv()
model_name = os.getenv("MODEL")
DB_PATH = '/tmp/assistant_memory.db'

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Table for Tasks/Schedules
    c.execute('''CREATE TABLE IF NOT EXISTS events 
                 (id INTEGER PRIMARY KEY, description TEXT, time TEXT, type TEXT)''')
    # Table for General Notes/Information
    c.execute('''CREATE TABLE IF NOT EXISTS notes 
                 (id INTEGER PRIMARY KEY, content TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- TOOLS ---

def check_conflicts_and_schedule(event_name: str, time: str) -> str:
    """Checks the DB for existing events at the same time before scheduling."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT description FROM events WHERE time=?", (time,))
    conflict = c.fetchone()
    if conflict:
        conn.close()
        return f"CONFLICT ERROR: You already have '{conflict[0]}' scheduled at {time}."
    
    c.execute("INSERT INTO events (description, time, type) VALUES (?, ?, ?)",
              (event_name, time, "meeting"))
    conn.commit()
    conn.close()
    return f"SUCCESS: Scheduled '{event_name}' at {time}."

def search_memory(query: str) -> str:
    """Searches both tasks and notes to answer user questions about their info."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT description, time FROM events WHERE description LIKE ?", (f'%{query}%',))
    events = c.fetchall()
    c.execute("SELECT content FROM notes WHERE content LIKE ?", (f'%{query}%',))
    notes = c.fetchall()
    conn.close()
    
    res = f"Events found: {events}. Notes found: {notes}."
    return res if (events or notes) else "I couldn't find any information regarding that in my database."

def save_note(content: str) -> str:
    """Saves general information or snippets to the notes table."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    ts = datetime.now().strftime("%Y-%m-%d")
    c.execute("INSERT INTO notes (content, timestamp) VALUES (?, ?)", (content, ts))
    conn.commit()
    conn.close()
    return f"Note saved: '{content}'"

# --- AGENTS ---

execution_specialist = Agent(
    name="execution_specialist",
    model=model_name,
    tools=[check_conflicts_and_schedule, search_memory, save_note],
    instruction="""
    1. If the user wants to schedule, use 'check_conflicts_and_schedule'.
    2. If the user asks 'what', 'when', or 'remind me', use 'search_memory'.
    3. If the user provides a fact or a note, use 'save_note'.
    """
)

response_formatter = Agent(
    name="response_formatter",
    model=model_name,
    instruction="Take the tool output and give a friendly, human response. If a conflict was found, apologize and ask for a new time."
)

assistant_workflow = SequentialAgent(
    name="assistant_workflow",
    sub_agents=[execution_specialist, response_formatter]
)

root_agent = Agent(
    name="proactive_coordinator",
    model=model_name,
    sub_agents=[assistant_workflow],
    instruction="Greet the user. Once they ask to schedule, remember, or save info, hand off to assistant_workflow."
)