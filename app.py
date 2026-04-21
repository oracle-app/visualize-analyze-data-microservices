from flask import Flask, request, jsonify
import pandas as pd
import io
from prepareData import prepareData, prepareInsightsData
from queryData import dataQuerienator3000
import ollama
import json
from json_repair import repair_json
import gc

app = Flask(__name__)
client = ollama.Client(host="http://host.docker.internal:11434")
#Constraints for file uploading. 
EXTENSIONS = {"csv", "xlsx"}

def allowed_file(filename:str) -> bool: 
    return "." in filename and filename.rsplit(".", 1)[1].lower() in EXTENSIONS
#? It is not critical, but logic to manage different encodings may be need to be implmented (currently only UTF-8 and Latin-1) as they are the two more common. 
def parse_file(file) -> pd.DataFrame: 
    filename = file.filename
    content = file.read()

    
    if filename.endswith(".csv"): 
        try: 
            return pd.read_csv(io.BytesIO(content), on_bad_lines='skip')
        
        except Exception: 
            return pd.read_csv(io.BytesIO(content), encoding='latin-1', on_bad_lines='skip')

    elif filename.endswith(".xlsx"): 
        return pd.read_excel(io.BytesIO(content), na_filter=False)
    raise ValueError(f"Non supported filetype: {file.filename}, please provide either .csv or .xlsx")

def jsonSanitizer(raw: str) -> dict:
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").removesuffix("```").strip()
    repaired = repair_json(clean)
    parsed = json.loads(repaired)

    valid_filters = {"Max", "Min", "Avg", "Sum"}
    valid_chart_types = {
        "Tile", "Vertical Bar Chart", "Horizontal Bar Chart",
        "Stacked Bar Chart", "Line", "Pie", "Donut", "Scatter", "Area"
    }
    #Forces name of metrics to be field1, 2 and 3. 
    for chart in parsed["Charts"]:
        metrics = chart.get("metrics", {})
        keys = list(metrics.keys())
        if keys and "field1" not in metrics:
            normalized = {}
            if len(keys) >= 1: normalized["field1"] = metrics[keys[0]]
            if len(keys) >= 2: normalized["field2"] = metrics[keys[1]]
            if len(keys) >= 3: normalized["field3"] = metrics[keys[2]]
            chart["metrics"] = normalized
    #Attepmts to save work by forcing default values for chart types and empty filters
    for i, chart in enumerate(parsed["Charts"]):
        if chart.get("chartType") not in valid_chart_types:
            chart["chartType"] = "Vertical Bar Chart"

        for field, value in (chart.get("metricsFilter") or {}).items():
            if value not in valid_filters:
                chart["metricsFilter"][field] = "Count"

    return parsed

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

    #! This is not enough clean, there is a need to test and implement the logic for enforcing the correct name of fields and 
    #! overwriting them if needed. 
    rawJson = response.message.content
    try: 
        parsed = jsonSanitizer(rawJson)
        print(parsed)
    

    except json.JSONDecodeError: 
        return jsonify({"error" : "Model returned invalid JSON" ,"raw": rawJson}), 500
    try: 
        res = []
        print(parsed) 
        for chart in parsed["Charts"]: 
            res.append(dataQuerienator3000(chart, df))
    except Exception as e: 
        return jsonify({"error" : f"Fail to query the data propertly: {str(e)}"}), 500
    #Finally, we free the memory
    del df
    gc.collect()
    return jsonify({"Charts" : res}), 200 
if __name__ == "__main__": 
    app.run(host="0.0.0.0", port=8080)  