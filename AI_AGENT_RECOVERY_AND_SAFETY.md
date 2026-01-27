# 🛡️ AI Agent Recovery & Safety Systems

> **Part 2: Robustness and Control Layers**

---

## 6. 🔁 Error Recovery Strategy

### Self-Correction Loop

The agent must not crash on errors but treat them as observations.

```python
class ErrorHandler:
    """Manages failure states and recovery strategies"""
    
    def __init__(self, llm):
        self.llm = llm
        self.retry_counts = {}
        self.MAX_RETRIES = 3
    
    def handle_error(self, 
                    error: Exception, 
                    task: Task, 
                    history: List[Thought]) -> RecoveryAction:
        """Decide how to recover from an error"""
        
        # 1. Classify Error
        error_type = self._classify_error(error)
        
        # 2. Check retry limits
        task_id = task.id
        self.retry_counts[task_id] = self.retry_counts.get(task_id, 0) + 1
        
        if self.retry_counts[task_id] > self.MAX_RETRIES:
            return RecoveryAction(type="ESCALATE", reason="Max retries exceeded")
            
        # 3. Generate correction plan
        prompt = f"""
        Action failed with error: {error}
        Error Type: {error_type}
        
        Previous attempt:
        {history[-1]}
        
        Suggest a fix. Options:
        - RETRY: Try same action again (transient error)
        - MODIFY: Try same tool with different inputs
        - ALT_TOOL: Use a different tool
        - SKIP: Mark task as impossible
        
        Response format:
        Action: <type>
        Reason: <explanation>
        NewInput: <json_if_needed>
        """
        
        suggestion = self.llm.generate(prompt)
        return self._parse_recovery(suggestion)

    def _classify_error(self, error):
        # Implement logic to distinguish between:
        # - ToolError (credentials, params)
        # - NetworkError (timeout)
        # - LogicError (preconditions not met)
        pass
```

### Recovery Actions Enum

```python
class RecoveryType(Enum):
    RETRY_IMMEDIATE = "retry_immediate"   # Transient network issues
    RETRY_DELAYED = "retry_delayed"       # Rate limits
    MODIFY_INPUT = "modify_input"         # Bad parameters
    ALTERNATIVE_TOOL = "alternative_tool" # Tool broken/insufficient
    REPLAN_TASK = "replan_task"           # Approach unworkable
    ESCALATE_USER = "escalate_user"       # Critical failure
```

---

## 7. 🔐 Safety & Guardrails

### Safety Layer Architecture

The safety layer intercepts **every** tool execution before it runs.

```python
class SafetyLayer:
    """Enforces constraints and requires approval"""
    
    def __init__(self, config: SafetyConfig):
        self.config = config
        self.logger = AuditLogger()
    
    def check_action(self, action: Action, context: dict) -> SafetyResult:
        """Validate action before execution"""
        
        # 1. Static Checks (Fast)
        if action.tool.name in self.config.blocked_tools:
            return SafetyResult(allowed=False, reason="Tool is blocked")
            
        if not self._validate_params(action):
            return SafetyResult(allowed=False, reason="Invalid parameters")
            
        # 2. Heuristic Checks (Medium)
        if self._detect_harmful_pattern(action):
             return SafetyResult(allowed=False, reason="Harmful pattern detected")
             
        # 3. Human-in-the-Loop (Slow)
        if self._requires_approval(action):
            return self._request_user_approval(action)
            
        # 4. Log intent
        self.logger.log_intent(action)
        
        return SafetyResult(allowed=True)

    def _requires_approval(self, action: Action) -> bool:
        """Determine if human approval is needed"""
        # Always approve read-only operations
        if action.tool.is_readonly:
            return False
            
        # Check sensitivity
        if action.tool.name in ["delete_file", "send_email", "execute_code"]:
            return True
            
        return False
```

### Guardrail Definitions

Create a `safety_policy.yaml` to configure the system:

```yaml
# safety_policy.yaml
security_level: "high"

blocked_tools:
  - "system_shell"     # Never allow direct shell access
  - "delete_root"

sensitive_tools:
  requires_approval:
    - "write_file"
    - "api_call_post"  # Write operations
  
  auto_approve:
    - "read_file"
    - "web_search"
    - "calculator"

constraints:
  interaction_limit: 100
  budget_limit_usd: 5.0
  file_access:
    allowed_dirs: ["./workspace", "./tmp"]
    blocked_patterns: ["*.env", "*.pem"]
```

### Audit Logging

The system must log everything for post-mortem analysis.

```python
class AuditLogger:
    def log_intent(self, action):
        """Log what the agent WANTS to do"""
        entry = {
            "timestamp": time.now(),
            "type": "INTENT",
            "tool": action.tool.name,
            "input": action.input,
            "reasoning": action.reasoning
        }
        self.persist(entry)
        
    def log_execution(self, result):
        """Log what ACTUALLY happened"""
        entry = {
            "timestamp": time.now(),
            "type": "EXECUTION",
            "success": result.success,
            "output": str(result.result)[:1000] # Truncate large outputs
        }
        self.persist(entry)
```

---

## 10. 🚀 Extending to Multi-Agent Systems

This architecture can be scaled to a **Swarm** or **Hierarchical** multi-agent system.

### Supervisor-Worker Pattern

Transform the `AgentController` into a `Supervisor` that delegates to specialized `WorkerAgents`.

```python
class SupervisorAgent(BaseAgent):
    """Delegates tasks to specialized workers"""
    
    def _select_action(self, thought):
        # Instead of calling a tool, it calls a worker
        if thought.action_name == "call_coder":
            return self._delegate_to_agent("coder_agent", thought.action_input)
            
        elif thought.action_name == "call_researcher":
            return self._delegate_to_agent("researcher_agent", thought.action_input)
            
        return super()._select_action(thought)

class WorkerAgent(BaseAgent):
    """Specialized agent with limited toolset"""
    # ... standard agent implementation ...
```

### Shared Memory Space

For multi-agent systems, the **Semantic Memory** becomes the shared knowledge base.

- **Private Memory**: Each agent's working memory (context)
- **Public Memory**: Shared Vector DB for facts and outcomes
- **Message Bus**: For agent-to-agent communication

```python
class AgentMessageBus:
    def post_message(self, from_agent, to_agent, content):
        queue = self.queues[to_agent]
        queue.put({
            "sender": from_agent,
            "content": content,
            "timestamp": time.now()
        })
```

### Handoff Protocol

1. **Supervisor** decomposes goal into `SubTask A` and `SubTask B`.
2. **Supervisor** calls `ResearcherAgent` with `SubTask A`.
3. `ResearcherAgent` enters execution loop.
4. `ResearcherAgent` finishes and returns `Result A`.
5. **Supervisor** updates context and calls `CoderAgent` with `SubTask B` + `Result A`.
