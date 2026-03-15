from .analyzers.python_analyzer import run_python_analysis
from .analyzers.js_analyzer import run_js_analysis
from .analyzers.cpp_analyzer import run_cpp_analysis
from .analyzers.java_analyzer import run_java_analysis
from .analyzers.go_analyzer import run_go_analysis
from .analyzers.rust_analyzer import run_rust_analysis
from .analyzers.base import get_empty_analysis
from .complexity_analyzer import analyze_complexity_for_language
from .vulnerability_analyzer import analyze_vulnerabilities
from .flow_graph import build_flow_graph


def dispatch_analysis(language: str, code: str):
    lang = language.lower()
    if lang == "python":
        res = run_python_analysis(code)
    elif lang in ["javascript", "js", "node"]:
        res = run_js_analysis(code)
    elif lang in ["cpp", "c++", "c"]:
        res = run_cpp_analysis(code)
    elif lang == "java":
        res = run_java_analysis(code)
    elif lang == "go":
        res = run_go_analysis(code)
    elif lang in ["rust", "rs"]:
        res = run_rust_analysis(code)
    else:
        res = get_empty_analysis()

    # Always inject full complexity metrics (Lizard + Big-O) for all languages.
    # python_analyzer already calls analyze_complexity() internally, but we
    # override it here so the full metric set (loc, time_complexity, etc.) is
    # always present regardless of which individual analyzer was executed.
    res["complexity"] = analyze_complexity_for_language(language, code)
    res["flow_graph"] = build_flow_graph(language, code)

    vuln = analyze_vulnerabilities(language, code)
    res["vulnerabilities"] = vuln.get("findings", [])
    res["vulnerability_meta"] = vuln.get("meta", {"engine": "semgrep", "status": "error", "message": "unknown"})

    return res
