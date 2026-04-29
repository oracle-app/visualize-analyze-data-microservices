# Chart Generator Microservice 3.0.0

A Flask microservice that analyzes your `.csv` or `.xlsx` files using a local LLM and returns chart suggestions as a structured JSON. 

---

## What does it do?

- Upload any structured data file
- Get 5 meaningful chart suggestions back
- Runs fully local via Docker and Ollama
- No external API keys required

---

## How it works

1. You upload a file
2. The service computes stats, correlations and samples
3. Gemma reads the summary and finds interesting patterns
4. Gemma suggests 5 charts to visualize those patterns
5. You get a clean JSON back, ready to render

---

## Running it

Make sure you have Docker and Docker Compose installed, then:

```bash
docker-compose up --build
```

On first run, Ollama will pull the `gemma4:e2b` model (~7GB). This takes around 10 minutes depending on your connection. To verify the model is ready, call:

```
GET http://localhost:11434/api/tags
```

You should see `gemma4:e2b` in the response:

```json
{
    "models": [
        {
            "name": "gemma4:e2b",
            "model": "gemma4:e2b",
            "parameter_size": "5.1B",
            "quantization_level": "Q4_K_M"
        }
    ]
}
```

### Services

| Service    | URL                          |
|------------|------------------------------|
| Flask API  | http://localhost:8080        |
| Ollama     | http://localhost:11434       |

---

## API

### POST `/analyzeData`

Upload a `.csv` or `.xlsx` file and receive chart suggestions.

**Request**

```
Content-Type: multipart/form-data
Key:   file
Value: your_file.csv
```

**Response**
Structure: 
```json
{
    "message": "File received, validated and queued for processing",
    "status": "QUEUED",
    "task_id": "08c9f84a-e569-4af8-bbd5-cd7a16d3ce62" //<--- Use this to later get your results once is completed. 
}
```

### GET `/results<id>?chart=<chartNumber>&page=<pageNumber?&preview=true`
The endpoint has 3 different use cases to handle the data. 
- GET results/mySuperID
    Serves as a index to know what is the info inside: 
**Response**
Structure: 
```json
{
    "charts": [
        {
            "chartIndex": 0, //a number from 0 to 4, it refers to the chart number
            "chartName": "Occupancy vs Revenue", 
            "chartType": "Scatter",
            "metrics": {
                "field1": "occupancy",
                "field2": "revenue"
            }, //Names of the fields ordered. 
            "totalPages": 224, // Amount of pages of data avaiable, each one has a maximum of 5k data points on each field. 
            "totalPoints": 1115174 //Amount of total data points
        },
        {
            ...
        }
    ],
    "status": "COMPLETED",
    "totalCharts": 5
}
```
- GET results/mySuperID/?chart=0?preview=true
    Serves as a way to retrieve data on a managable size to render quickly. 
**Response**
Structure: 
```json
{
    "chartIndex": 0,
    "chartName": "Occupancy vs Revenue",
    "chartType": "Scatter",
    "data": {
        "field1": [
            "0.75",
            "0.871",
            "0.733",
            "...",
        ],
        "field2": [
            "860.0",
            "1100.0",
            "886.0",
            "...",
        ]
    },
    "metrics": {
        "field1": "occupancy",
        "field2": "revenue"
    },
    "page": 1,
    "pageSize": 100,
    "preview": true,
    "status": "COMPLETED",
    "totalPages": 11152,
    "totalPoints": 1115174
}
```

- GET results/mySuperID/?chart=0&page=1
    Serves as a way to retrieve medium size of data 5k data points at a time, making sure the client can handle them propertly
**Response**
Structure: 
```json
{
    "chartIndex": 0,
    "chartName": "Occupancy vs Revenue",
    "chartType": "Scatter",
    "data": {
        "field1": [
            "0.75",
            "0.871",
            "0.733",
            "...",
        ],
        "field2": [
            "860.0",
            "1100.0",
            "886.0",
            "...",
        ]
    },
    "metrics": {
        "field1": "occupancy",
        "field2": "revenue"
    },
    "page": 1,
    "pageSize": 100,
    "preview": true,
    "status": "COMPLETED",
    "totalPages": 11152,
    "totalPoints": 1115174
}
```

Note: Area and Stacked Bar Charts have three fields, be aware of this case when implementing. 
Please check the example of the end to see an actual example of how it will work on the practice, it covers all the cases.

**Available chart types**

| Type | Notes |
|---|---|
| Tile | Single KPI, one field only |
| Vertical Bar Chart | List[Str: Float] |
| Horizontal Bar Chart | List[Str: Float] |
| Stacked Bar Chart | List[Str: List[Float]] |
| Line | List[Float : Float] |
| Pie | List[Float] |
| Donut | List[Float] |
| Scatter | List[Float : Float] |
| Area | List[Float : List[Float]] |


**Available filters:** `Max`, `Min`, `Avg`, `Sum`, `Count`
If there is no filter, asume it is Count. 
You will never see them in the response, the queryData.py manages them when quering the data.

---

## Project structure

```
.
├── produce.py          # Flask entry point, queues the tasks for the worker.
├── worker.py           # Executes and coordinates the requests between the tools to process the tasks. 
├── prepareData.py      # Statistical analysis + prompt builder
├── startOllama.sh      # Pulls and serves the LLM on startup
├── Dockerfile          # Flask app container
├── docker-compose.yml  # Orchestrates Worker, Producer, Ollama, RabbitMQ and redis containers. 
└── requirements.txt    # Python dependencies
```

---

## Requirements

- Docker + Docker Compose
- ~15GB disk space for containers and model
- ~16GB RAM 
- ~8GB  


