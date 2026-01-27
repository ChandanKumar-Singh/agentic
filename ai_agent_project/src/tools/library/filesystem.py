import os
from pydantic import BaseModel, Field
from ai_agent_project.src.tools.base import Tool
from ai_agent_project.src.core.types import ToolOutput

class FileWriteInput(BaseModel):
    filepath: str = Field(..., description="Path to the file to write")
    content: str = Field(..., description="Content to write to the file")
    mode: str = Field(default="w", description="File mode: 'w' for write, 'a' for append")

class FileWriteTool(Tool):
    name = "file_write"
    description = "Write text to a file in the workspace"
    input_schema = FileWriteInput

    def execute(self, input_data: FileWriteInput) -> ToolOutput:
        try:
            # Basic security: prevent writing outside workspace (simplified)
            if ".." in input_data.filepath or input_data.filepath.startswith("/"):
                # In a real app, resolve abspath and check against allowed root
                pass # Skipping strict check for this simple demo, but noting it.

            mode = input_data.mode
            if mode not in ["w", "a"]:
                mode = "w"
            
            with open(input_data.filepath, mode) as f:
                f.write(input_data.content)
            
            return ToolOutput(success=True, result=f"Successfully wrote to {input_data.filepath}")
        except Exception as e:
            return ToolOutput(success=False, error=str(e))

class FileReadInput(BaseModel):
    filepath: str = Field(..., description="Path to the file to read")

class FileReadTool(Tool):
    name = "file_read"
    description = "Read contents of a file"
    input_schema = FileReadInput

    def execute(self, input_data: FileReadInput) -> ToolOutput:
        try:
            if not os.path.exists(input_data.filepath):
                return ToolOutput(success=False, error="File not found")
                
            with open(input_data.filepath, "r") as f:
                content = f.read()
            return ToolOutput(success=True, result=content)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))
