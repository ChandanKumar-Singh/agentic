from agent_web_app.core.planner import Planner
from agent_web_app.core.tool import ToolRegistry
from agent_web_app.tools.search import WebSearchTool
from agent_web_app.tools.calculator import CalculatorTool
from agent_web_app.tools.wikipedia_tool import WikipediaTool
from agent_web_app.tools.image_tool import ImageSearchTool
import json
import re

class Agent:
    def __init__(self, llm_provider):
        self.llm = llm_provider
        self.planner = Planner(llm_provider)
        
        # Initialize Registry
        self.registry = ToolRegistry()
        self.registry.register(WebSearchTool(llm_provider))
        self.registry.register(ImageSearchTool())
        self.registry.register(CalculatorTool())
        self.registry.register(WikipediaTool())
        
        self.history = []

    def run(self, goal: str):
        # 1. Plan
        steps = self.planner.create_plan(goal)
        context = ""
        
        # 2. Execute Loop
        for i, step in enumerate(steps):
            print(f"\n--- Step {i+1}: {step} ---")
            
            # Check if step is structured (from smart Planner)
            if isinstance(step, dict) and "tool_name" in step:
                print(f"[Agent] optimized execution: using planner's suggested tool {step.get('tool_name')}")
                action = {
                    "tool": step.get("tool_name"),
                    "args": step.get("input_value") or step.get("args")
                }
            else:
                # Legacy text-step logic: Ask LLM to decide
                tools_list = self.registry.get_prompt_text()
                prompt = f"""
                Goal: {goal}
                Current Step: {step}
                Context: {context}
                
                {tools_list}
                - finish(answer): Return the final answer.
                
                What should I do?
                Return JSON format: {{"tool": "tool_name", "args": "arguments"}}
                """
                
                response = self.llm.generate(prompt, model="phi3:latest")
                
                # Parse action
                action = self._parse_json(response)
                if not action:
                    # Fallback strategies
                    lower_resp = response.lower()
                    action = {"tool": "finish", "args": response}
                    
                    if "image" in lower_resp and "search" in lower_resp:
                        action = {"tool": "web_search", "args": step}

            # Execute
            tool_name = action.get("tool")
            args = action.get("args")
            
            # Sanitize args: if list, take first element
            if isinstance(args, list) and args:
                args = args[0]
            if isinstance(args, list) and not args:
                args = ""
            
            result = None
            
            if tool_name == "finish":
                return args
            
            tool = self.registry.get(tool_name)
            if tool:
                result = tool.execute(args)
            else:
                result = f"Error: Tool {tool_name} not found."
            
            if result:
                 context += f"\n[{tool_name} Result]: {result}\n"
                 self.history.append(f"Action: {tool_name}({args})\nResult: {result}")
        
        return context # Return accumulated context if no explicit finish
            
    def _parse_json(self, text):
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except:
            pass
        return None
