import json
import re

class Planner:
    def __init__(self, llm):
        self.llm = llm
        self.plan = []

    def create_plan(self, goal: str):
        print(f"[Planner] Creating plan for: {goal}")
        prompt = f"""
        Goal: {goal}
        
        Available Tools:
        1. web_search(query): Search internet for text.
        2. image_search(query): Search internet for images.
        3. wikipedia(query): Search Wikipedia.
        4. calculator(expression): Math calculations.
        
        Break this down into simple, sequential steps that use these tools.
        Each step should ideally correspond to one tool call.
        Do NOT include manual steps like 'Open browser', 'Click link', 'Type in search bar'.
        
        Return ONLY a JSON list of objects.
        Example: [{{"tool_name": "wikipedia", "input_value": "Taj Mahal"}}, {{"tool_name": "image_search", "input_value": "Taj Mahal"}}]
        """
        
        response = self.llm.generate(prompt, model="phi3:latest")
        try:
            # Phi-3 might add text, so we hunt for the JSON list
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                self.plan = json.loads(match.group(0))
            else:
                # Fallback: Split by lines if no JSON
                self.plan = [line.strip("- *") for line in response.split("\n") if line.strip()]
                
            print(f"[Planner] Plan: {self.plan}")
            return self.plan
        except Exception as e:
            print(f"[Planner] Error parsing plan: {e}")
            self.plan = [goal] # Fallback to single step
            return self.plan
