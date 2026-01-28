class CalculatorTool:
    name = "calculator"
    description = "Perform mathematical calculations. Input should be a valid python expression string (e.g. '153 * 19')."

    def execute(self, expression: str) -> str:
        try:
            # Safe evaluation ensuring only math is done
            allowed_chars = "0123456789+-*/(). "
            if not all(c in allowed_chars for c in expression):
                 return "Error: Invalid characters in expression."
            
            result = eval(expression, {"__builtins__": None}, {})
            return str(result)
        except Exception as e:
            return f"Error calculating: {str(e)}"
