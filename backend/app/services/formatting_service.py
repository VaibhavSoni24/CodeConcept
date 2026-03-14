import os
import subprocess
import tempfile

def format_cmd(cmd, code, suffix):
    with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8") as tmp:
        tmp.write(code)
        tmp_path = tmp.name
        
    try:
        # Some formatters write in place, so we copy the command logic here
        cmd_args = cmd(tmp_path)
        result = subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            timeout=3,
            check=False
        )
        if result.returncode != 0:
            return code, result.stderr

        with open(tmp_path, "r", encoding="utf-8") as f:
            formatted_code = f.read()
        return formatted_code, None
    except subprocess.TimeoutExpired:
        return code, "Formatting timed out"
    except Exception as e:
        return code, f"Formatter error: {str(e)}"
    finally:
        try: os.remove(tmp_path)
        except OSError: pass

def format_python(code: str):
    return format_cmd(lambda p: ["black", "-q", p], code, ".py")

def format_javascript(code: str):
    return format_cmd(lambda p: ["npx", "prettier", "--write", p], code, ".js")

def format_cpp(code: str):
    return format_cmd(lambda p: ["clang-format", "-i", p], code, ".cpp")

def format_java(code: str):
    # Depending on system, google-java-format might be invoked differently
    return format_cmd(lambda p: ["google-java-format", "--replace", p], code, ".java")

def format_go(code: str):
    return format_cmd(lambda p: ["gofmt", "-w", p], code, ".go")

def format_rust(code: str):
    return format_cmd(lambda p: ["rustfmt", p], code, ".rs")

def parse_and_format_code(language: str, code: str):
    lang = language.lower()
    if lang == "python": return format_python(code)
    if lang in ["javascript", "js", "node"]: return format_javascript(code)
    if lang in ["cpp", "c++", "c"]: return format_cpp(code)
    if lang == "java": return format_java(code)
    if lang == "go": return format_go(code)
    if lang in ["rust", "rs"]: return format_rust(code)
    
    return code, "Formatting not supported for this language."
