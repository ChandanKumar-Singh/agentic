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

    async def run(self, goal: str):
        # 1. Plan (Sync for now unless we optimize Planner too, but let's make it async calling LLM)
        # Actually Planner uses self.llm.generate which is sync. We should make planner async too ideally.
        # For now, let's wrap planner call or just keep it sync (it's fast enough with phi3).
        # Wait, if we are in async run, we should try to be non-blocking.
        # Let's fix Planner.create_plan to use generate_async if possible or just wrap it here.
        
        # But wait, Planner.create_plan calls llm.generate. 
        # Modifying Planner is good.
        # Let's assume Planner is Sync for this step but we'll optimize it later or now.
        # Let's just run it in thread to be safe.
        import asyncio
        from functools import partial
        loop = asyncio.get_event_loop()
        steps = await loop.run_in_executor(None, self.planner.create_plan, goal)
        
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
                # Legacy text-step logic: Ask LLM to decide (Async)
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
                
                response = await self.llm.generate_async(prompt, model="phi3:latest")
                
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
            
            # Sanitize args
            if isinstance(args, list) and args: args = args[0]
            if isinstance(args, list) and not args: args = ""
            
            result = None
            
            if tool_name == "finish":
                return args
            
            tool = self.registry.get(tool_name)
            if tool:
                result = await tool.execute(query=str(args) if "expression" not in str(args) else args) 
                # Note: execute signature might vary but python kwargs handle it if tool implementation matches
                # Calculator expects 'expression' but we pass generic args.
                # All my tools defined execute with specific args.
                # I should just call tool.execute(args) but define my tools to accept a single arg or parse?
                # Python doesn't support single arg overload easily.
                # Let's fix tool signatures to match "args" or use **kwargs properly.
                # Actually, WebSearchTool(query), Calculator(expression).
                # Simplest is to pass positional arg if just one.
                # BUT `execute` usually takes explicit named params in my definition.
                # Let's inspect the tools again.
                # WebSearchTool: execute(query, ...)
                # CalculatorTool: execute(expression)
                # WikipediaTool: execute(query)
                # ImageSearchTool: execute(query)
                # So I can just pass positional args if I call it directly? 
                # Example: await tool.execute(args) -- this passes 'args' as first argument 'query' or 'expression'.
                # Yes, that works in Python.
                result = await tool.execute(args)
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
