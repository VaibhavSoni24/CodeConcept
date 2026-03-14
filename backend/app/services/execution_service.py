import os
import sys
import subprocess
import tempfile
import pathlib

# Helper for executing commands
def run_cmd(cmd, timeout=3, cwd=None):
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            cwd=cwd
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": f"Execution timed out after {timeout} seconds.", "exit_code": -1}
    except Exception as e:
        return {"stdout": "", "stderr": f"Error running process: {str(e)}", "exit_code": -1}

def run_python(code: str) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(code)
        tmp_path = tmp.name
    try:
        return run_cmd([sys.executable, "-I", tmp_path], timeout=3)
    finally:
        try: os.remove(tmp_path)
        except OSError: pass

def run_javascript(code: str) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tmp:
        tmp.write(code)
        tmp_path = tmp.name
    try:
        return run_cmd(["node", tmp_path], timeout=3)
    finally:
        try: os.remove(tmp_path)
        except OSError: pass

def run_cpp(code: str) -> dict:
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "main.cpp")
        exe = os.path.join(td, "main.exe" if os.name == "nt" else "main")
        with open(src, "w", encoding="utf-8") as f:
            f.write(code)
        comp = run_cmd(["g++", "-O2", src, "-o", exe], timeout=5, cwd=td)
        if comp["exit_code"] != 0:
            return comp # compilation failed
        return run_cmd([exe], timeout=3, cwd=td)

def run_java(code: str) -> dict:
    # Quick regex or search to find public class name, or assume 'Main'
    # Simplified: put it in a file called Main.java. If users use a different public class, it fails.
    class_name = "Main"
    if "public class " in code:
        class_name = code.split("public class ")[1].split(" ")[0].split("{")[0].strip()
    
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, f"{class_name}.java")
        with open(src, "w", encoding="utf-8") as f:
            f.write(code)
        comp = run_cmd(["javac", src], timeout=5, cwd=td)
        if comp["exit_code"] != 0:
            return comp
        return run_cmd(["java", class_name], timeout=3, cwd=td)

def run_go(code: str) -> dict:
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "main.go")
        with open(src, "w", encoding="utf-8") as f:
            f.write(code)
        return run_cmd(["go", "run", "main.go"], timeout=5, cwd=td)

def run_rust(code: str) -> dict:
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "main.rs")
        exe = os.path.join(td, "main.exe" if os.name == "nt" else "main")
        with open(src, "w", encoding="utf-8") as f:
            f.write(code)
        comp = run_cmd(["rustc", src, "-o", exe], timeout=5, cwd=td)
        if comp["exit_code"] != 0:
            return comp
        return run_cmd([exe], timeout=3, cwd=td)

def execute_code(language: str, code: str) -> dict:
    lang = language.lower()
    result = None
    if lang == "python": result = run_python(code)
    elif lang in ["javascript", "js", "node"]: result = run_javascript(code)
    elif lang in ["cpp", "c++", "c"]: result = run_cpp(code)
    elif lang == "java": result = run_java(code)
    elif lang == "go": result = run_go(code)
    elif lang in ["rust", "rs"]: result = run_rust(code)
    else: result = {"stdout": "", "stderr": f"Unsupported language: {language}", "exit_code": 1}
    
    if result.get("exit_code", 0) != 0 and result.get("stderr"):
        from .error_explainer import explain_runtime_error
        explanation = explain_runtime_error(language, result["stderr"])
        if explanation:
            result["stderr"] += f"\n\n---💡 Error Explanation 💡---\n{explanation}\n"
            
    return result
