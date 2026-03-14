import ast as py_ast
import tree_sitter
from typing import Dict, Any, List

# To avoid crashing if not all tree-sitter modules are available, we safely import them.
try:
    import tree_sitter_javascript
    import tree_sitter_cpp
    import tree_sitter_java
    import tree_sitter_go
    import tree_sitter_rust
    TS_AVAILABLE = True
except ImportError:
    TS_AVAILABLE = False


def normalize_python_ast(node: py_ast.AST) -> Dict[str, Any]:
    """Recursively converts a standard Python AST node into normalized JSON format."""
    result = {
        "type": node.__class__.__name__,
        "label": getattr(node, "name", getattr(node, "id", getattr(node, "arg", ""))),
        "line": getattr(node, "lineno", None),
        "children": []
    }
    
    for child in py_ast.iter_child_nodes(node):
        result["children"].append(normalize_python_ast(child))
        
    return result

def normalize_ts_ast(node) -> Dict[str, Any]:
    """Recursively converts a Tree-sitter Node into normalized JSON format."""
    line_num = node.start_point[0] + 1 if hasattr(node, "start_point") else None
    
    label_text = ""
    try:
        if node.is_named and not node.children:
            label_text = node.text.decode("utf8")
    except:
        pass

    result = {
        "type": node.type,
        "label": label_text,
        "line": line_num,
        "children": []
    }
    
    for i in range(node.child_count):
        child = node.child(i)
        if child.is_named:
            result["children"].append(normalize_ts_ast(child))
            
    return result

def get_ts_language(lang: str):
    if not TS_AVAILABLE:
        return None
        
    lang_map = {
        "javascript": tree_sitter_javascript.language(),
        "js": tree_sitter_javascript.language(),
        "node": tree_sitter_javascript.language(),
        "cpp": tree_sitter_cpp.language(),
        "c++": tree_sitter_cpp.language(),
        "c": tree_sitter_cpp.language(),
        "java": tree_sitter_java.language(),
        "go": tree_sitter_go.language(),
        "rust": tree_sitter_rust.language(),
        "rs": tree_sitter_rust.language(),
    }
    
    lang_mod = lang_map.get(lang.lower())
    if lang_mod:
        return tree_sitter.Language(lang_mod)
    return None

def parse_ast(language: str, code: str) -> Dict[str, Any]:
    """
    Parses code using the appropriate language parser and returns a normalized JSON AST.
    """
    lang = language.lower()
    
    if lang == "python":
        try:
            tree = py_ast.parse(code)
            return normalize_python_ast(tree)
        except SyntaxError as e:
            return {"type": "SyntaxError", "line": e.lineno, "message": str(e), "children": []}
            
    if TS_AVAILABLE:
        ts_lang = get_ts_language(lang)
        if ts_lang:
            parser = tree_sitter.Parser(ts_lang)
            
            # tree-sitter expects bytes
            tree = parser.parse(bytes(code, "utf8"))
            return normalize_ts_ast(tree.root_node)
            
    return {"type": "UnsupportedLanguageOrParserMissing", "line": None, "children": []}
