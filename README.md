# Chart Generator Microservice 1.1.0

A Flask microservice that analyzes your `.csv` or `.xlsx` files using a local LLM and returns chart suggestions as JSON that runs locally. 

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

```json
{
    "Charts": [
        {
            "chartName": "Survival Rate by Class",
            "chartType": "Vertical Bar Chart",
            "metrics": {
                "field1": "Pclass",
                "field2": "Survived"
            },
            "metricsFilter": {
                "Survived": "Avg"
            }
        }
    ]
}
```

**Available chart types**

| Type | Notes |
|---|---|
| Tile | Single KPI, one field only |
| Vertical Bar Chart | Default |
| Horizontal Bar Chart | Default |
| Stacked Bar Chart | Default |
| Line | Two fields to compare |
| Pie | Default |
| Donut | Default |
| Scatter | Two fields to compare |
| Area | Default |

**Available filters:** `Max`, `Min`, `Avg`, `Sum`, `Count`
If there is no filter, asume it is Count. 

---

## Project structure

```
.
├── app.py              # Flask entry point
├── prepareData.py      # Statistical analysis + prompt builder
├── startOllama.sh      # Pulls and serves the LLM on startup
├── Dockerfile          # Flask app container
├── docker-compose.yml  # Orchestrates Flask + Ollama
└── requirements.txt    # Python dependencies
```

---

## Requirements

- Docker + Docker Compose
- ~15GB disk space for containers and model
- ~8GB RAM available while running
