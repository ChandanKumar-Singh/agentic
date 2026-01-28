from agent_web_app.core.planner import Planner
from agent_web_app.tools.search import WebSearchTool
import json
import re

class Agent:
    def __init__(self, llm_provider):
        self.llm = llm_provider
        self.planner = Planner(llm_provider)
        self.search_tool = WebSearchTool(llm_provider)
        self.history = []

    def run(self, goal: str):
        # 1. Plan
        steps = self.planner.create_plan(goal)
        context = ""
        
        # 2. Execute Loop
        for i, step in enumerate(steps):
            print(f"\n--- Step {i+1}: {step} ---")
            
            # Decide action using Phi-3
            prompt = f"""
            Goal: {goal}
            Current Step: {step}
            Context: {context}
            
            Available Tools:
            - web_search(query): Search the internet.
            - finish(answer): Return the final answer.
            
            What should I do?
            Return JSON format: {{"tool": "tool_name", "args": "arguments"}}
            """
            
            response = self.llm.generate(prompt, model="phi3:medium")
            
            # Parse action
            action = self._parse_json(response)
            if not action:
                # Fallback: try to guess from text
                if "search" in response.lower():
                    action = {"tool": "web_search", "args": step}
                else:
                    action = {"tool": "finish", "args": response}

            # Execute
            tool_name = action.get("tool")
            args = action.get("args")
            
            if tool_name == "web_search":
                result = self.search_tool.execute(args)
                context += f"\n[Search Result for '{args}']: {result}\n"
                self.history.append(f"Action: Search {args}\nResult: {result}")
            
            elif tool_name == "finish":
                return args
        
        return context # Return accumulated context if no explicit finish
            
    def _parse_json(self, text):
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except:
            pass
        return None
