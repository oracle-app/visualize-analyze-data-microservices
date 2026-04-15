from flask import Flask, request, jsonify
import pandas as pd
import io
from prepareData import prepareData, prepareInsightsData
import ollama
import json

app = Flask(__name__)
client = ollama.Client(host="http://host.docker.internal:11434")
#Constraints for file uploading. 
EXTENSIONS = {"csv", "xlsx"}

def allowed_file(filename:str) -> bool: 
    return "." in filename and filename.rsplit(".", 1)[1].lower() in EXTENSIONS

def parse_file(file) -> pd.DataFrame: 
    filename = file.filename
    content = file.read()

    if filename.endswith(".csv"): 
        return pd.read_csv(io.BytesIO(content))
    
    elif filename.endswith(".xlsx"): 
        return pd.read_excel(io.BytesIO(content))
    raise ValueError(f"Non supported filetype: {file.filename}, please provide either .csv or .xlsx")
    
@app.route("/analyzeData", methods=["POST"])
def analyzeData(): 
    if "file" not in request.files: 
        return jsonify({"error": "Please provide a file"}), 400
    file = request.files["file"]
    if not allowed_file(file.filename):
        return jsonify({"error": "Please provide a file in .csv or .xlsx format"}), 415   
    
    try: 
        df = parse_file(file)
    except Exception as e: 
        return jsonify({"error": f"Failed to parse file: {str(e)}"}), 422
    try: 
        prompt = prepareData(df, file.filename)
    except Exception as e: 
        return jsonify({"error": f"Failed to prepare data: {str(e)}"}), 422
    try: 
        insights = client.chat(model="gemma4:e2b", messages=[
            {
                "role" : "user", 
                "content" : prompt,
            },
        ])
        print(insights)
    except Exception as e: 
        return jsonify({"error": f"Ollama Failed to answer: {str(e)}"}), 424
    try: 
        prompt2 = prepareInsightsData(df, insights.message.content)
        response = client.chat(model="gemma4:e2b", messages=[
            {
                "role" : "user", 
                "content" : prompt2
            }
        ])
    except Exception as e: 
        return jsonify({"error": f"Ollama Failed to answer: {str(e)}"}), 424

    raw = response.message.content
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try: 
        parsed = json.loads(clean)
    except json.JSONDecodeError: 
        return jsonify({"error" : "Model returned invalid JSON" ,"raw": raw}), 500
    return jsonify(parsed), 200 
if __name__ == "__main__": 
    app.run(host="0.0.0.0", port=8080)  