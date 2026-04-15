Chart Generator Microservices

Hello there, this is the microservices for visualize 
How does it work?
1. You upload a file
2. The service computes stats, correlations and samples
3. Gemma reads the summary and finds interesting patterns
4. Gemma suggests 5 charts to visualize those patterns
5. You get a clean JSON back, ready to render


How do I run it?
Make sure you have Docker and Docker Compose installed!!!
then run:
docker-compose up --build 
as simple as that. 

Be aware that on the first run, it will download both the Ollama Image and the Gemma4:e2b model, which has a 7Gb size, please be patient. 
You can check the logs, or wait arround 10 min, and use: 
GET http://localhost:11434/api/tags
If you get this it means that it has already downloaded the model. (You could have more models but we only care about this one, check for the :e2b. 
{
    "models": [
        {
            "name": "gemma4:e2b",
            "model": "gemma4:e2b",
            "modified_at": "2026-04-15T23:07:19.115361312Z",
            "size": 7162405886,
            "digest": "7fbdbf8f5e45a75bb122155ed546e765b4d9c53a1285f62fd9f506baa1c5a47e",
            "details": {
                "parent_model": "",
                "format": "gguf",
                "family": "gemma4",
                "families": [
                    "gemma4"
                ],
                "parameter_size": "5.1B",
                "quantization_level": "Q4_K_M"
            }
        }]
}    
Services:
ServicePortFlask: APIhttp://localhost:8080
Ollamahttp://localhost:11434

API
POST /analyzeData
Upload a .csv or .xlsx file and get chart suggestions back.
Request
Content-Type: multipart/form-data
Key: file
Value: your_file.csv
Response
json{
    "Charts": [
        {
            "chartName": "Survival Rate by Class",
            "chartType": "Vertical Bar Chart",
            "metrics": { "field1": "Pclass", "field2": "Survived" },
            "metricsFilter": { "Survived": "Avg" }
        }
    ]
}
Chart types available: Tile, Vertical Bar Chart, Horizontal Bar Chart, Stacked Bar Chart, Line, Pie, Donut, Scatter, Area
Filters available: Max, Min, Avg, Sum


File structure
├── app.py              # Flask entry point
├── prepareData.py      # Statistical analysis + prompt builder
├── startOllama.sh      # Pulls and serves the LLM on startup
├── Dockerfile          # Flask app container
├── docker-compose.yml  # Orchestrates Flask + Ollama
└── requirements.txt    # Python dependencies

Recommended Requirements: 

~15GB disk space for the docker container
~8 GB of ram available while running 

 

