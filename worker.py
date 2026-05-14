import pika
import redis
import ollama
from pydantic import BaseModel
import pandas as pd
import json
import io
from json_repair import repair_json
#Actualliry libraries
from prepareData import prepareData, prepareInsightsData
from queryData import dataQuery
#Conns
client = ollama.Client(host="http://host.docker.internal:11434")
r = redis.Redis(host='redis', port=6379, db=0)

#Hot start the LLM
try:
    wakeUpCall = client.chat(
        model="gemma4:e2b", 
        messages=[{"role": "user", "content": "Hello"}],
        options={"num_predict": 1}  
    )
    print("LLM ready")
except Exception as e:
    print(f"LLM warmup failed, continuing anyway: {e}")
#Class definitions for structural responses
class Chart(BaseModel): 
    chartName: str
    chartType: str
    metrics: dict[str, str]
    metricsFilter: dict[str, str]

class Charts(BaseModel): 
    Charts: list[Chart]

#Helper functions for the process
#? It is not critical, but logic to manage different encodings may be need to be implmented (currently only UTF-8 and Latin-1) as they are the two more common. 
def parse_file(filename: str , content: bytes) -> pd.DataFrame: 
    if filename.endswith(".csv"): 
        try: 
            return pd.read_csv(io.BytesIO(content), on_bad_lines='skip')
        
        except Exception: 
            return pd.read_csv(io.BytesIO(content), encoding='latin-1', on_bad_lines='skip')

    elif filename.endswith(".xlsx"): 
        return pd.read_excel(io.BytesIO(content), na_filter=False)
    raise ValueError(f"Non supported filetype: {filename}, please provide either .csv or .xlsx")

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
            if len(keys) >= 1: normalized["field1"] = keys[0]
            if len(keys) >= 2: normalized["field2"] = keys[1]
            if len(keys) >= 3: normalized["field3"] = keys[2]
            chart["metrics"] = normalized
    #Attepmts to save work by forcing default values for chart types and empty filters
    for i, chart in enumerate(parsed["Charts"]):
        if chart.get("chartType") not in valid_chart_types:
            chart["chartType"] = "Vertical Bar Chart"

        for field, value in (chart.get("metricsFilter") or {}).items():
            if value not in valid_filters:
                chart["metricsFilter"][field] = "Count"

    
    return parsed    

def callback(ch, method, properties, body): 
    taskID = body.decode()
    fileContent = r.get(f"file:{taskID}")
    filename = r.get(f"filename:{taskID}").decode()
    print(f"Consuming task {taskID}")
    try: 
        #Log
        print(f"Processing task: {taskID}") 
        df = parse_file(filename, fileContent)
        prompt = prepareData(df, filename)
        insights = client.chat(model="gemma4:e2b", messages=[
            {
                "role" : "user", 
                "content" : prompt,
            }
        ])
        print("==========================================Log==================================================")
        print(insights.message.content)
        prompt2 = prepareInsightsData(df, insights.message.content)
        response = client.chat(model="gemma4:e2b", messages=[
            {
                "role" : "user", 
                "content" : prompt2,
                "format": Charts.model_json_schema
            }
        ])
        print("==========================================Log==================================================")
        print(response.message.content)
        rawJson = response.message.content
        parsed = jsonSanitizer(rawJson)
        res = []
        for chart in parsed["Charts"]: 
            print("==========================================Log==================================================")
            print(chart)
            res.append(dataQuery(chart, df))
        pipe = r.pipeline()

        for i, chartResult in enumerate(res):
            print(f"ChartResult {i}: {chartResult}")
            if not chartResult or "data" not in chartResult or not chartResult["data"]:
                pipe.set(f"result:{taskID}:{i}:meta", json.dumps({
                "chartName": chartResult.get("chartName", "Unknown"),
                "chartType": chartResult.get("chartType", "Unknown"),
                "metrics": {},
                "error": "No data available"
                }))
                continue
            data = chartResult["data"]
    
            if data.get("field1"):
                pipe.rpush(f"result:{taskID}:{i}:field1", *data["field1"])
    
            field2 = data.get("field2")
            if isinstance(field2, dict):
                pipe.set(f"result:{taskID}:{i}:field2", json.dumps(field2))
            elif isinstance(field2, list) and len(field2) > 0:
                pipe.rpush(f"result:{taskID}:{i}:field2", *field2)
            if data.get("field3"):
                pipe.rpush(f"result:{taskID}:{i}:field3", *data["field3"])

            pipe.set(f"result:{taskID}:{i}:meta", json.dumps({
                "chartName": chartResult["chartName"],
                "chartType": chartResult["chartType"],
                "metrics": chartResult.get("fieldNames", {})
                }))
        pipe.set(f"result:{taskID}:count", len(res))
        pipe.set(f"status:{taskID}", "COMPLETED")
        pipe.execute()

    except Exception as e: 
        print(f"Error: {str(e)}")
        r.set(f"status:{taskID}", f"ERROR: {str(e)}")

    ch.basic_ack(delivery_tag= method.delivery_tag)


conn = pika.BlockingConnection(pika.ConnectionParameters(
    host='rabbitmq',
    heartbeat=0,
    blocked_connection_timeout=300))
channel = conn.channel()
channel.queue_declare("task_queue")
channel.basic_consume("task_queue", on_message_callback=callback)
print("Lock and loaded")
channel.start_consuming()