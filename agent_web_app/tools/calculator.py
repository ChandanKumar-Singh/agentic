from agent_web_app.core.tool import Tool

class CalculatorTool(Tool):
    name = "calculator"
    description = "Perform mathematical calculations. Input: valid python expression (e.g. '153 * 19')."

    def _eval_expr(self, node):
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.BitXor: operator.xor,
            ast.USub: operator.neg
        }

        if isinstance(node, ast.Num):  # <number>
            return node.n
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            return operators[type(node.op)](self._eval_expr(node.left), self._eval_expr(node.right))
        elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
            return operators[type(node.op)](self._eval_expr(node.operand))
        else:
            raise TypeError(f"Unsupported type {node}")

    def execute(self, expression: str) -> str:
        try:
            # Parse only (no eval)
            # Limit characters for extra safety
            allowed_chars = "0123456789+-*/().^ "
            if not all(c in allowed_chars for c in expression):
                 return "Error: Invalid characters. Only basic math allowed."

            # AST safe evaluation
            node = ast.parse(expression, mode='eval').body
            result = self._eval_expr(node)
            return str(result)
        except Exception as e:
            return f"Error calculating: {str(e)}"
