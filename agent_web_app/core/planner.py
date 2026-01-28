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
        
        Break this down into simple, sequential steps.
        Return ONLY a JSON list of strings.
        Example: ["Search for X", "Summarize findings", "Write to file"]
        """
        
        response = self.llm.generate(prompt, model="phi3:medium")
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
