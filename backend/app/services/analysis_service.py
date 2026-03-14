from .analyzers.python_analyzer import run_python_analysis
from .analyzers.js_analyzer import run_js_analysis
from .analyzers.cpp_analyzer import run_cpp_analysis
from .analyzers.java_analyzer import run_java_analysis
from .analyzers.go_analyzer import run_go_analysis
from .analyzers.rust_analyzer import run_rust_analysis
from .analyzers.base import get_empty_analysis

def dispatch_analysis(language: str, code: str):
    lang = language.lower()
    if lang == "python":
        return run_python_analysis(code)
    elif lang in ["javascript", "js", "node"]:
        return run_js_analysis(code)
    elif lang in ["cpp", "c++", "c"]:
        return run_cpp_analysis(code)
    elif lang == "java":
        return run_java_analysis(code)
    elif lang == "go":
        return run_go_analysis(code)
    elif lang in ["rust", "rs"]:
        return run_rust_analysis(code)
    else:
        return get_empty_analysis()
