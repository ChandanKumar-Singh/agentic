import json
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from ai_agent_project.src.core.llm_provider import LLMProvider

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class SubTask(BaseModel):
    id: int
    description: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    dependencies: List[int] = []

class Plan(BaseModel):
    root_goal: str
    subtasks: List[SubTask] = []
    
    def get_active_task(self) -> Optional[SubTask]:
        """Returns the first pending task whose dependencies are met."""
        completed_ids = {t.id for t in self.subtasks if t.status == TaskStatus.COMPLETED}
        
        # 1. Try to find a task with satisfied dependencies
        for task in self.subtasks:
            if task.status == TaskStatus.PENDING:
                # Check dependencies
                if all(dep_id in completed_ids for dep_id in task.dependencies):
                    return task
        
        # 2. Fallback: If we have pending tasks but all are blocked, return the first pending one.
        # This handles cases where the LLM hallucinated circular or invalid dependencies.
        pending_tasks = [t for t in self.subtasks if t.status == TaskStatus.PENDING]
        if pending_tasks:
            print(f"Plan: ⚠️ Logic Error - All {len(pending_tasks)} pending tasks are blocked. Forcing execution of Task {pending_tasks[0].id}.")
            return pending_tasks[0]
        
        return None
        
    def is_complete(self) -> bool:
        return all(t.status == TaskStatus.COMPLETED for t in self.subtasks)

class Planner:
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.plan: Optional[Plan] = None

    def create_initial_plan(self, goal: str) -> Plan:
        """Generates a plan from the goal using the LLM."""
        print(f"Plan: Generating initial plan for '{goal}'...")
        
        prompt = f"""
You are a project manager.
Your task is to break down the user's goal into a list of steps.

GOAL: {goal}

RESPONSE FORMAT:
You MUST return valid JSON only. Do not add markdown or explanations.
{{
  "subtasks": [
    {{ "id": 1, "description": "precise action step", "dependencies": [] }},
    {{ "id": 2, "description": "precise action step", "dependencies": [1] }}
  ]
}}

RESPONSE:
"""
        response = self.llm.generate(prompt)
        try:
            # Basic parsing helper
            import re
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                subtasks_data = data.get("subtasks", [])
                
                # Robust cleaning for local models
                cleaned_subtasks = []
                for t in subtasks_data:
                    # Fix typo keys
                    if "descripion" in t and "description" not in t:
                        t["description"] = t["descripion"]
                    
                    # Fix dependencies format
                    deps = t.get("dependencies", [])
                    cleaned_deps = []
                    if isinstance(deps, list):
                        for d in deps:
                            if isinstance(d, int):
                                cleaned_deps.append(d)
                            elif isinstance(d, dict) and "id" in d:
                                cleaned_deps.append(d["id"])
                    t["dependencies"] = cleaned_deps
                    
                    # Ensure required fields
                    if "id" in t and "description" in t:
                         cleaned_subtasks.append(t)

                subtasks = [SubTask(**t) for t in cleaned_subtasks]
                
                if not subtasks: 
                     raise ValueError("No valid subtasks found in JSON")

                self.plan = Plan(root_goal=goal, subtasks=subtasks)
                print(f"Plan: Created {len(subtasks)} steps.")
                return self.plan
            else:
                 raise ValueError("No JSON found")
                
        except Exception as e:
            print(f"Plan: Error generating plan: {e}. Defaulting to single step.")
            self.plan = Plan(root_goal=goal, subtasks=[SubTask(id=1, description=goal)])
            return self.plan

    def update_task_status(self, task_id: int, status: TaskStatus, result: str = None):
        if not self.plan:
            return
            
        for task in self.plan.subtasks:
            if task.id == task_id:
                task.status = status
                if result:
                    task.result = result
                print(f"Plan: Task {task_id} marked as {status}.")
                break
                
    def get_next_step(self) -> Optional[SubTask]:
        if not self.plan:
            return None
        return self.plan.get_active_task()
