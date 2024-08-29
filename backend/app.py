from flask import Flask, request, jsonify
import sys
import traceback

app = Flask(__name__)

def trace_code_execution(code):
    trace_data = []

    def trace_function(frame, event, arg):
        if event == "call":
            func_name = frame.f_code.co_name
            line_no = frame.f_lineno
            if func_name == "<module>":
                func_name = f"code"
            trace_data.append({
                "event": "call",
                "line_no": line_no,
                "message": f"Calling '{func_name}' (line {line_no})",
                "locals": safe_locals(frame.f_locals)
            })

        elif event == "line":
            line_no = frame.f_lineno
            trace_data.append({
                "event": "line",
                "line_no": line_no,
                "locals": safe_locals(frame.f_locals),
                "message": f"Executing line {line_no}."
            })

        elif event == "return":
            line_no = frame.f_lineno
            return_value = arg
            func_name = frame.f_code.co_name
            if func_name == "<module>":
                func_name = f"code"
            trace_data.append({
                "event": "return",
                "line_no": line_no,
                "locals": safe_locals(frame.f_locals),
                "message": f"Returning from '{func_name}' (line {line_no}) with value {return_value}"
            })

        return trace_function

    sys.settrace(trace_function)
    try:
        exec(code, {})
    except Exception:
        trace_data.append({
            "event": "exception",
            "message": "An exception occurred",
            "traceback": traceback.format_exc()
        })
    finally:
        sys.settrace(None)

    return trace_data

def safe_locals(local_vars):
    safe_vars = {}
    for k, v in local_vars.items():
        if k == "__builtins__":
            continue
        try:
            if callable(v):
                safe_vars[k] = f"function '{v.__name__}' at {hex(id(v))}"
            else:
                safe_vars[k] = str(v)
        except Exception:
            safe_vars[k] = f"<non-serializable: {type(v).__name__}>"
    return safe_vars

@app.route('/visualize', methods=['POST'])
def visualize_code():
    code = request.form.get('code')
    if not code:
        return jsonify({"error": "No code provided"}), 400

    execution_trace = trace_code_execution(code)
    return jsonify({"execution_trace": execution_trace})

if __name__ == "__main__":
    app.run(debug=True)