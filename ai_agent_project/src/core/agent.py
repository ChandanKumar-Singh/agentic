import json
import re
from typing import Optional, List, Dict, Any
from ai_agent_project.src.core.types import AgentResult, Thought, Action, ToolOutput, Step
from ai_agent_project.src.core.llm_provider import LLMProvider
from ai_agent_project.src.tools.registry import ToolRegistry
from ai_agent_project.src.memory.working import WorkingMemory
from ai_agent_project.src.memory.semantic import SemanticMemory
from ai_agent_project.src.planning.planner import Planner, TaskStatus
from ai_agent_project.src.safety.guardrails import SafetyGuardrails, SecurityError
from ai_agent_project.src.config.settings import settings

class Agent:
    def __init__(self, llm: LLMProvider, tools: ToolRegistry, memory: WorkingMemory, semantic_memory: SemanticMemory = None):
        self.llm = llm
        self.tools = tools
        self.working_memory = memory
        self.semantic_memory = semantic_memory or SemanticMemory()
        self.planner = Planner(llm)
        self.safety = SafetyGuardrails()
        self.max_loops = settings.MAX_LOOPS

    def run(self, goal: str, callbacks: Dict[str, Any] = None) -> AgentResult:
        # 1. Initialization
        self.working_memory.initialize(goal)
        callbacks = callbacks or {}
        fire_event = lambda name, data: callbacks.get(name)(data) if callbacks.get(name) else None
        
        print(f"\n🎯 Goal: {goal}")
        fire_event("on_start", {"goal": goal})
        
        # 2. Search Long-term Memory
        relevant_docs = self.semantic_memory.retrieve(goal)
        context_str = "\n".join([f"- {d.content}" for d in relevant_docs]) if relevant_docs else "No relevant past knowledge."
        self.working_memory.context["semantic_context"] = context_str
        
        # 3. Create Plan
        current_plan = self.planner.create_initial_plan(goal)
        
        for i in range(self.max_loops):
            step_id = i + 1
            
             # Check if plan is complete
            if self.planner.plan.is_complete():
                print("\n✅ Plan Complete!")
                return AgentResult(success=True, answer="All planned tasks completed.", steps=self.working_memory.steps)

            # Get next active subtask
            current_task = self.planner.get_next_step()
            if not current_task:
                print("⚠️ No active tasks (blocked?).")
                break
                
            print(f"\n--- Step {step_id} (Subtask {current_task.id}: {current_task.description}) ---")
            self.planner.update_task_status(current_task.id, TaskStatus.IN_PROGRESS)
            fire_event("on_step", {"step_id": step_id, "subtask_id": current_task.id, "subtask": current_task.description})

            # 4. Think
            thought = self._think(goal, current_task.description)
            current_step = Step(step_id=step_id, thought=thought)
            print(f"Thought: {thought.text}")
            fire_event("on_thought", {"thought": thought.text})
            
            if thought.is_final_answer:
                # Agent decided this subtask is done
                print(f"Subtask Result: {thought.answer}")
                self.planner.update_task_status(current_task.id, TaskStatus.COMPLETED, result=thought.answer)
                self.working_memory.add_step(current_step)
                fire_event("on_subtask_complete", {"subtask_id": current_task.id, "result": thought.answer})
                continue # Loop back to check next task

            # 5. Act
            if thought.action_name:
                action = Action(
                    tool_name=thought.action_name,
                    tool_args=thought.action_input or {},
                    thought=thought.text
                )
                current_step.action = action
                print(f"Action: {action.tool_name}({action.tool_args})")
                fire_event("on_action", {"tool": action.tool_name, "args": action.tool_args})
                
                try:
                    # SAFETY CHECK
                    self.safety.validate_action(action)
                    
                    # EXECUTE
                    tool_output = self._act(action.tool_name, action.tool_args)
                    
                    # Store success/failure
                    if tool_output.success:
                         # Automatically add to semantic memory for successful findings
                         if action.tool_name == "web_search" or action.tool_name == "read_file":
                             self.semantic_memory.add(str(tool_output.result), metadata={"source": action.tool_name})

                except SecurityError as se:
                    tool_output = ToolOutput(success=False, result=None, error=f"SECURITY VIOLATION: {str(se)}")
                
                current_step.observation = tool_output
                status = "Success" if tool_output.success else "Failed"
                obs_preview = str(tool_output.result) if tool_output.success else tool_output.error
                print(f"Observation ({status}): {obs_preview[:200]}..." if len(str(obs_preview)) > 200 else f"Observation ({status}): {obs_preview}")
                fire_event("on_observation", {"success": tool_output.success, "result": str(tool_output.result) if tool_output.success else None, "error": tool_output.error})
                
            else:
                 current_step.observation = ToolOutput(success=False, error="No tool selected.")
                 print("Agent did not select a tool.")
                 fire_event("on_observation", {"success": False, "error": "No tool selected"})

            # 6. Save Step
            self.working_memory.add_step(current_step)

        return AgentResult(success=False, error="Max loops exceeded", steps=self.working_memory.steps)

    def _think(self, main_goal: str, subtask: str) -> Thought:
        history = self.working_memory.get_history()
        # Simplify tool desc for tinyllama
        tools_simple = []
        for name, tool in self.tools._tools.items():
            db = tool.to_dict()
            # Create a signature-like string
            # e.g. "web_search(query: str, max_results: int) - Search the internet"
            params = db['parameters']['properties']
            args = ", ".join([f"{k}" for k in params.keys()])
            tools_simple.append(f"{name}({args}): {db.get('descripion', db.get('description', ''))}")
        
        tools_desc = "\n".join(tools_simple)
        
        semantic_context = self.working_memory.context.get("semantic_context", "")
        
        system_prompt = """You are a helpful AI assistant.
You must complete the current subtask.

FORMAT INSTRUCTIONS:
1. To use a tool:
Thought: <reasoning>
Action: <tool_name>
Action Input: {<json_args>}

2. To answer directly (or for chitchat):
Thought: <reasoning>
Final Answer: <your response>

Examples:
Thought: User said hi. I should greet them.
Final Answer: Hello! How can I help you today?

Thought: I need to search for python documentation.
Action: web_search
Action Input: {"query": "python documentation"}
"""

        user_prompt = f"""GOAL: {main_goal}
SUBTASK: {subtask}
CONTEXT: {semantic_context}

TOOLS:
{tools_desc}

HISTORY:
{history}

What is the next step?
"""
        response = self.llm.generate(user_prompt, system_prompt=system_prompt)
        print(f"\n[DEBUG] Raw LLM Response:\n{response}\n[END DEBUG]\n") # Debug for user
        return self._parse_thought(response)

    def _parse_thought(self, llm_response: str) -> Thought:
        # Relaxed parsing
        try:
             # Clean up
             llm_response = llm_response.strip()
             
             # Case-insensitive checks
             llm_lower = llm_response.lower()
             
             # Check Final Answer
             if "final answer:" in llm_lower:
                 # Find the index in the original string to preserve case of the answer
                 idx = llm_lower.index("final answer:")
                 # split using the known case-insensitive match length
                 thought_part = llm_response[:idx].replace("Thought:", "").strip()
                 answer_part = llm_response[idx+len("final answer:"):].strip()
                 return Thought(text=thought_part, is_final_answer=True, answer=answer_part)
             
             # Check Action
             if "action:" in llm_lower:
                 idx = llm_lower.index("action:")
                 thought_part = llm_response[:idx].replace("Thought:", "").strip()
                 rest = llm_response[idx+len("action:"):].strip()
                 
                 # Parse Tool Name
                 tool_lines = rest.split("\n")
                 tool_name_raw = tool_lines[0].strip()
                 # Clean tool name (remove extra text like " - search")
                 tool_name = tool_name_raw.split(" ")[0].split("(")[0].strip()
                 
                 # Parse Input - try multiple patterns
                 action_input = {}
                 
                 # Pattern 1: Look for "action input:" or just "input:"
                 if "action input:" in rest.lower() or "input:" in rest.lower():
                     # use regex to find JSON block anywhere after tool name
                     json_match = re.search(r"(\{.*?\})", rest, re.DOTALL)
                     if json_match:
                         try:
                            action_input = json.loads(json_match.group(1))
                         except Exception as e:
                            print(f"⚠️ JSON parse failed in Action Input: {e}")
                            # Try to extract from the line itself
                            for line in tool_lines[1:]:
                                if "{" in line:
                                    try:
                                        # Extract everything from { to }
                                        start = line.index("{")
                                        end = line.rindex("}") + 1
                                        action_input = json.loads(line[start:end])
                                        break
                                    except:
                                        pass
                 
                 return Thought(text=thought_part, action_name=tool_name, action_input=action_input)
             
             # Fallback: Just thought
             return Thought(text=llm_response.replace("Thought:", "").strip())
             
        except Exception as e:
            print(f"[Parse Error] {e}")
            return Thought(text=llm_response, is_final_answer=False)

    def _act(self, tool_name: str, tool_input: Dict) -> ToolOutput:
        tool = self.tools.get(tool_name)
        if not tool:
            return ToolOutput(success=False, result=None, error=f"Tool {tool_name} not found")
        try:
            if hasattr(tool, 'input_schema') and tool.input_schema:
                 validated_input = tool.input_schema(**tool_input)
                 return tool.execute(validated_input)
            else:
                 return tool.execute(tool_input)
        except Exception as e:
            return ToolOutput(success=False, result=None, error=f"Execution failed: {str(e)}")
