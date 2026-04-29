from flask import Flask, request, jsonify
import pandas as pd
import io
from prepareData import prepareData, prepareInsightsData
from queryData import dataQuery
import ollama
import json
from json_repair import repair_json
import gc
from pydantic import BaseModel
import uuid
import redis
import pika

app = Flask(__name__)
r = redis.Redis(host='redis', port=6379, db=0)
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


@app.route("/analyzeData", methods=["POST"])
def analyzeData(): 
    print("Request recieved")
    if "file" not in request.files: 
        return jsonify({"error": "Please provide a file"}), 400
    file = request.files["file"]
    if not allowed_file(file.filename):
        return jsonify({"error": "Please provide a file in .csv or .xlsx format"}), 415   
    
    taskID = str(uuid.uuid4())
    try: 
        r.setex(f"file:{taskID}", 1800, file.read())
        r.setex(f"status:{taskID}", 1800, "QUEUED")
        r.setex(f"filename:{taskID}", 1800, file.filename)
        conn = pika.BlockingConnection(pika.ConnectionParameters(
            host='rabbitmq',
            heartbeat=0, 
            blocked_connection_timeout=300))
        channel = conn.channel()
        channel.basic_publish(exchange='', routing_key='task_queue', body=taskID)
        conn.close()
        
        gc.collect()

        return jsonify({
            "task_id": taskID,
            "status": "QUEUED",
            "message": "File received, validated and queued for processing"}), 202

    except Exception as e: 
        return jsonify({"error" : f"failed to queue task; str{e}"}), 500

@app.route("/results/<taskID>", methods = ["GET"])
def results(taskID): 
    status = r.get(f"status:{taskID}")
    if not status: 
        return jsonify({"error":"Task not found"}), 404
    status = status.decode()
    
    if status != "COMPLETED": 
        return jsonify({"status": status}), 202
    
    countR = r.get(f"result:{taskID}:count")
    if not countR: 
         return jsonify({"status": status, "error": "Results not yet indexed"}), 202
    chartCount = int(countR.decode())

    chartIndex = request.args.get("chart", type=int)
    page = request.args.get("page", 1, type=int)
    preview = request.args.get("preview", "false").lower() == "true"
    pageSize = 100 if preview else 5000

    if chartIndex is None: 
        overview = []
        for i in range(chartCount):
            metaRaw = r.get(f"result:{taskID}:{i}:meta")
            if not metaRaw:
                continue  # skip charts that weren't stored
            meta = json.loads(metaRaw.decode())       
            totalPoints = r.llen(f"result:{taskID}:{i}:field1")
            meta["totalPoints"] = totalPoints
            meta["totalPages"] = -(-totalPoints // pageSize)
            meta["chartIndex"] = i
            overview.append(meta)
        return jsonify({
            "status" : "COMPLETED", 
            "totalCharts": chartCount,
            "charts" : overview
        })
    if chartIndex >= chartCount: 
        return jsonify({"error" : "Chart index out of range"}), 404
    meta = json.loads(r.get(f"result:{taskID}:{chartIndex}:meta").decode())
    start = (page - 1) * pageSize 
    end = start + pageSize - 1
    totalPoints = r.llen(f"result:{taskID}:{chartIndex}:field1")
    totalPages = -(-totalPoints // pageSize)

    field1 = [v.decode() for v in r.lrange(f"result:{taskID}:{chartIndex}:field1", start, end)]

    field2type = r.type(f"result:{taskID}:{chartIndex}:field2").decode()
    if field2type == "string": 
        field2 = json.loads(r.get(f"result:{taskID}:{chartIndex}:field2").decode())
        field2p = {k: v[start:end+1] for k, v in field2.items()}

    elif field2type == "list":
        field2r = r.lrange(f"result:{taskID}:{chartIndex}:field2", start, end)
        field2p = [v.decode() for v in field2r]
    else: 
        field2p = []
    response = {
        "status": "COMPLETED", 
        "chartIndex" : chartIndex, 
        "page" : page, 
        "pageSize" : pageSize,
        "totalPages" : totalPages,
        "totalPoints" : totalPoints,
        "preview" : preview,
        **meta,
        "data": {
            "field1": field1,
            "field2": field2p
        }
    }
    field3Raw = r.lrange(f"result:{taskID}:{chartIndex}:field3", start, end)
    if field3Raw:
        response["data"]["field3"] = [v.decode() for v in field3Raw]

    return jsonify(response), 200

if __name__ == "__main__": 
    app.run(host="0.0.0.0", port=8080)  