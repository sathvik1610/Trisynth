from src.frontend.lexer import Lexer
import sys

def main():
    print("Trisynth Lexer Demo")
    print("-------------------")
    print("Type your code below (press Ctrl+Z then Enter on Windows to finish):")
    
    # Read all input from stdin
    try:
        source_code = sys.stdin.read()
    except KeyboardInterrupt:
        return

    print("\n--- Tokenizing ---")
    try:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        
        for token in tokens:
            print(token)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
