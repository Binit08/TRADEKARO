import json
import os
import sys

# Add backend to sys.path if not there
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.strategy_parser.parser.strategy_parser import StrategyParser
from backend.strategy_parser.ast.ast_builder import ASTBuilder

def print_ast(node, indent=0):
    if not node:
        return
    pad = "  " * indent
    lookback = getattr(node, 'lookback_periods', None)
    lookback_str = f" [lookback={lookback}]" if lookback is not None else ""
    
    # We might have data_type for market references
    data_type = getattr(node, 'data_type', '')
    data_type_str = f"({data_type})" if data_type else ""
    
    print(f"{pad}- {node.__class__.__name__}{data_type_str}{lookback_str}")
    
    for child in getattr(node, 'children', []):
        print_ast(child, indent + 1)

def main():
    prompt = """
    Entry Condition: buy when the previous candle is green
    Exit Condition: sell the stock at profit of 1 percent of buy price
    stop loss at 1 percent of buy price
    """
    
    print("Testing Strategy Parser & AST Builder...")
    
    # The parser needs the llm_config, we might need to rely on the environment variables
    from backend.strategy_parser.parser.llm_client import LLMConfig
    import dotenv
    dotenv.load_dotenv("backend/.env")
    
    # Check if we have gemini api key
    api_key = os.getenv("GOOGLE_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: API key not set in backend/.env")
        return
        
    try:
        parser = StrategyParser()
        print("\n1. Calling LLM Strategy Parser...")
        parsed_json = parser.parse_strategy(prompt)
        print("\nParsed JSON:")
        print(json.dumps(parsed_json, indent=2))
        
        print("\n2. Building AST...")
        builder = ASTBuilder()
        ast = builder.build(parsed_json)
        
        print("\nAST Tree:")
        if getattr(ast, 'operation_nodes', None):
            for op in ast.operation_nodes:
                if getattr(op, 'entry_nodes', None):
                    for entry_node in op.entry_nodes:
                        print("\nEntry AST:")
                        print_ast(entry_node)
        elif getattr(ast, 'entry_node', None):
            print("\nEntry AST:")
            print_ast(ast.entry_node)
        
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
