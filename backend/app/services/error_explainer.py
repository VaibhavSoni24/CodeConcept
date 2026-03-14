"""Error Explanation Engine - Analyzes tracebacks and explains them."""

import re

def explain_runtime_error(language: str, stderr: str) -> str:
    """Takes stderr output and attempts to provide a beginner-friendly explanation."""
    if not stderr or not stderr.strip():
        return ""
        
    stderr_lower = stderr.lower()
    
    if language == "python":
        if "syntaxerror" in stderr_lower:
            return "Syntax Error: Python doesn't understand your code. Check for missing colons (:), unclosed parentheses, or incorrect indentation."
        elif "nameerror" in stderr_lower:
            return "Name Error: You tried to use a variable or function name that hasn't been defined yet. Did you misspell it?"
        elif "typeerror" in stderr_lower:
            return "Type Error: You're trying to perform an operation on wrong types of data (like adding a string and an integer). Check your variable types."
        elif "indexerror" in stderr_lower:
            return "Index Error: You tried to access an item in a list that doesn't exist. Remember that lists start at index 0!"
        elif "indentationerror" in stderr_lower:
            return "Indentation Error: Your spaces or tabs don't match. Python uses indentation to group code blocks."
            
    elif language == "javascript":
        if "referenceerror" in stderr_lower:
            return "Reference Error: You are trying to use a variable that doesn't exist. Did you forget to declare it with let or const?"
        elif "typeerror" in stderr_lower:
            match = re.search(r"typeerror: (.*)", stderr_lower)
            detail = match.group(1) if match else "You are using a value in the wrong way."
            return f"Type Error: {detail.capitalize()} Ensure the variable contains what you think it does."
            
    elif language == "cpp" or language == "c":
        if "expected" in stderr_lower and "before" in stderr_lower:
            return "Syntax Error: You likely forgot a semicolon (;) at the end of a line or a closing brace/bracket."
        elif "was not declared in this scope" in stderr_lower:
            return "Scope Error: You used a variable that C++ cannot find. Check your spelling or ensure it is declared before usage."
            
    elif language == "java":
        if "cannot find symbol" in stderr_lower:
            return "Symbol Error: Java doesn't recognize a variable or method. Check for exact spelling and case-sensitivity, or forgotten imports."
        elif "expected" in stderr_lower and ";" in stderr_lower:
            return "Syntax Error: You missed a semicolon (;) on a specific line."
            
    elif language == "go":
        if "undefined:" in stderr_lower:
            return "Undefined Error: A variable or function was an unknown identifier. Verify spelling and scope."
        elif "expected" in stderr_lower:
            return "Syntax Error: Go compiler expected a different token. Check formatting around the reported line."
            
    elif language == "rust":
        if "expected one of" in stderr_lower:
            return "Syntax Error: Rust expected a semicolon (;), comma, or closing brace."
        elif "not found in this scope" in stderr_lower:
            return "Scope Error: You used a variable or function Rust cannot find. Did you import it or define it?"
        elif "cannot borrow" in stderr_lower:
            return "Borrow Checker Error: You violated Rust's ownership rules. Make sure you aren't mutating something that is immutably borrowed."

    # Generic fallback
    return "Runtime Error: Your code crashed during execution. Read the error trace closely to identify the buggy line."
