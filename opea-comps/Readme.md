## Running Ollama Third-party Service

### Choosing a Model

Get the model_id  that ollama will launch from the [Ollama Library](https://ollama.com/library)

eg. https://ollama.com/library/llama3.2

#### Mac

Grab you IP
```
ipconfig getifaddr en0
```


NO_PROXY=localhost LLM_ENDPOINT_PORT=9000:11434 LLM_MODEL_ID="llama3.2:1b" 
host_ip=192.168.1.90 docker-compose up

### Ollama API 

Once the Ollama server is running we can make API calls to the ollama API 

https://github.com/ollama/ollama/blob/main/docs/api.md

## Download (pull) a model

curl http://localhost:9000/api/pull -d '{
  "model": "llama3.2:1b"
}'


## Generate a request

curl http://localhost:9000/api/generate -d '{
  "model": "llama3.2:1b",
  "prompt": "Why is the sky blue?"
}'

# Technical Uncertainty 

Q: Does bridge mode mean we can only access the model from another model in the docker compose? 

A: No, bridge mode means we can access the model from another model in the docker compose. In other words, the host machine is able to access it 

Q: Which port is being mapped 8008 -> 11434

A: 8008 is the port that the Ollama server is running on, and 11434 is the port that the Ollama API is running on.

Q: If we pass the LLM_MODEL_ID as a parameter to the curl command,will it download the model when on start?

A: No, the LLM_MODEL_ID parameter is used to specify the model that the Ollama server should launch, but it does not affect the download of the model. The model is downloaded when the Ollama server is started, regardless of the LLM_MODEL_ID parameter.

Q: Will the model be downloaded in the container? does that mean the model will be deleted when the container is stopped?

A: The model will download into the container, and it will not be deleted when the container is stopped. The model will be available for use in the container until it is deleted or the container is stopped. 

Q: For LLM service which can txt-generation, it suggests it will only work with TGI/vLLM and all you have to do is have it running. Does TGI and vLLM have a standarized API or is there code to detect which one is running? Do we have to really use Xeon or Guadi processor? 

vLLM, TGI (Text Gen Inference) are both open-source models, and they have standardized APIs. You can use any processor that supports the model, as long as it has the necessary hardware and software requirements.In theory, they should be interchamgable. 