# 🛠️ AI Agent Implementation Guide

> **Part 3: Implementation Details & Examples**

---

## 8. 📁 Suggested Project Folder Structure

Follow this modular structure to keep the agent scalable.

```bash
ai_agent_project/
├── config/
│   ├── safety_policy.yaml     # Guardrails configuration
│   └── settings.py            # Env vars (API keys, DB paths)
│
├── core/
│   ├── __init__.py
│   ├── agent.py               # Main AgentController class
│   ├── llm_provider.py        # Wrapper for OpenAI/Anthropic
│   └── types.py               # Common data classes (Action, Thought)
│
├── memory/
│   ├── __init__.py
│   ├── manager.py             # MemorySystem facade
│   ├── working.py             # WorkingMemory implementation
│   ├── semantic.py            # Vector DB wrapper
│   └── episodic.py            # SQLite/experience wrapper
│
├── planning/
│   ├── __init__.py
│   ├── planner.py             # Task decomposition logic
│   └── tracker.py             # Task state tracking
│
├── tools/
│   ├── __init__.py
│   ├── base.py                # Abstract Tool class
│   ├── registry.py            # ToolRegistry
│   └── library/               # Actual tool implementations
│       ├── search.py
│       ├── filesystem.py
│       └── api_client.py
│
├── safety/
│   ├── __init__.py
│   ├── guardrail.py           # SafetyLayer logic
│   └── validator.py           # Input validation rules
│
├── main.py                    # Entry point
├── requirements.txt
└── .env                       # Secrets
```

---

## 9. 🧪 Example Agent Run (Step-by-Step Trace)

Here is a trace of the agent handling the request: **"Research the latest features of Python 3.12 and write a summary to 'python_updates.txt'."**

### Initialization
- **Goal**: "Research python 3.12 features and write summary to file"
- **Plan**:
  1. Search for "Python 3.12 new features"
  2. Extract key points from results
  3. Write points to 'python_updates.txt'

### Step 1: Execution
**Context**: Goal initialized. No previous steps.

**Reasoning (LLM)**:
> Thought: I need to find out what's new in Python 3.12. I should use the web search tool tool.
> Action: web_search
> Action Input: {"query": "Python 3.12 new features official release notes"}

**Safety**: Check `web_search` -> Allowed.

**Execution**:
`WebSearchTool` runs. Returns snippets: "Improved error messages", "F-string parsing", "Per-interpreter GIL...".

**Observation**:
> Success: True
> Result: [List of 5 search results...]

---

### Step 2: Execution
**Context**: Step 1 complete. Search results in memory.

**Reasoning (LLM)**:
> Thought: The search results mention 'f-strings', 'error messages', and 'GIL'. This is good. I have enough information to write the summary. I will now write this to the file as requested.
> Action: file_operations
> Action Input: {
>   "filepath": "python_updates.txt",
>   "mode": "w",
>   "content": "Python 3.12 Updates:\n1. Improved Error Messages\n2. F-string parsing flexibility\n3. Per-Interpreter GIL\n4. Performance improvements"
> }

**Safety**: Check `file_operations` (write) -> **REQUIRES APPROVAL** (Policy: write_file is sensitive).

**User Interaction**:
> System: "Agent wants to write to 'python_updates.txt'. Approve? (y/n)"
> User: "y"

**Execution**:
`FileOperationsTool` runs. Writes file.

**Observation**:
> Success: True
> Result: "Written to python_updates.txt"

---

### Step 3: Execution
**Context**: Step 1 & 2 complete. File written.

**Reasoning (LLM)**:
> Thought: I have searched for the features and written the summary file. The task is complete.
> Final Answer: I have successfully researched Python 3.12 features and saved a summary to 'python_updates.txt'.

**Result**: Agent loop terminates with success.

---

## ✅ Implementation Checklist

Use this checklist to build the system from scratch:

1.  **Setup Environment**
    - [ ] Install `langchain` (optional, or build raw), `pydantic`, `faiss-cpu` (or `chromadb`), `openai`.
    - [ ] Set up `.env` with API keys.

2.  **Core Primitives (Day 1)**
    - [ ] Define `Tool` abstract base class.
    - [ ] Implement `AgentReasoningLoop` (the `while` loop).
    - [ ] Connect `llm_provider` to OpenAI API.
    - [ ] Verify: Agent can receive a prompt and output a Thought.

3.  **Tooling (Day 2)**
    - [ ] Implement `WebSearchTool` (mock it first if needed).
    - [ ] Implement `FileOperationsTool`.
    - [ ] Create `ToolRegistry` and pass it to the prompt.
    - [ ] Verify: Agent can "call" a tool (output the JSON).

4.  **Memory (Day 3)**
    - [ ] Implement `WorkingMemory` (simple dict list).
    - [ ] Add previous steps to the LLM prompt context.
    - [ ] Verify: Agent remembers what it did in Step 1 during Step 2.

5.  **Safety & Robustness (Day 4)**
    - [ ] Add `SafetyLayer` interceptor.
    - [ ] Add `try/catch` blocks around tool execution.
    - [ ] Verify: Agent handles a tool error gracefully (tries again).
