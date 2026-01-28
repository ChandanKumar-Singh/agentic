from agent_web_app.core.planner import Planner
from agent_web_app.tools.search import WebSearchTool
from agent_web_app.tools.calculator import CalculatorTool
from agent_web_app.tools.wikipedia_tool import WikipediaTool
import json
import re

class Agent:
    def __init__(self, llm_provider):
        self.llm = llm_provider
        self.planner = Planner(llm_provider)
        self.search_tool = WebSearchTool(llm_provider)
        self.calculator_tool = CalculatorTool()
        self.wikipedia_tool = WikipediaTool()
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
            - web_search(query): Search the internet for text information.
            - image_search(query): Search for images.
            - wikipedia(query): Search Wikipedia for summary.
            - calculator(expression): Calculate math expression (e.g. '12 * 5').
            - finish(answer): Return the final answer.
            
            What should I do?
            Return JSON format: {{"tool": "tool_name", "args": "arguments"}}
            """
            
            response = self.llm.generate(prompt, model="phi3:latest")
            
            # Parse action
            action = self._parse_json(response)
            if not action:
                # Fallback: try to guess from text
                lower_resp = response.lower()
                if "image" in lower_resp and "search" in lower_resp:
                     action = {"tool": "image_search", "args": step}
                elif "wikipedia" in lower_resp:
                     action = {"tool": "wikipedia", "args": step}
                elif "calc" in lower_resp:
                     action = {"tool": "calculator", "args": step}
                elif "search" in lower_resp:
                    action = {"tool": "web_search", "args": step}
                else:
                    action = {"tool": "finish", "args": response}

            # Execute
            tool_name = action.get("tool")
            args = action.get("args")
            
            # Sanitize args: if list, take first element
            if isinstance(args, list) and args:
                args = args[0]
            if isinstance(args, list) and not args:
                args = ""
            
            result = None
            if tool_name == "web_search":
                result = self.search_tool.execute(args)
            elif tool_name == "image_search":
                result = self.search_tool.search_images(args)
            elif tool_name == "wikipedia":
                result = self.wikipedia_tool.execute(args)
            elif tool_name == "calculator":
                result = self.calculator_tool.execute(args)
            elif tool_name == "finish":
                return args
            
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
