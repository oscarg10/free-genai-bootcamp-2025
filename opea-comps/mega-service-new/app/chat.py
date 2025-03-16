from comps import ServiceOrchestrator, ServiceRoleType, MicroService
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest, 
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo
)
from fastapi import Request, HTTPException
import requests
import os

# Following Flask best practices for configuration
LLM_ENDPOINT = os.getenv('LLM_ENDPOINT', 'http://localhost:11434')

class Chat:
    def __init__(self):
        print('init')
        self.megaservice = ServiceOrchestrator()
        self.endpoint = '/james-is-great'
        self.host = '0.0.0.0'
        self.port = 8888

    def add_remote_services(self):
        print('add_remote_services')

    def start(self):
        print('start')
        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=ChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )

        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])
        self.service.start()

    async def handle_request(self, request: Request):
        try:
            # Following Flask best practices for error handling
            body = await request.json()
            if not body or 'messages' not in body:
                raise HTTPException(status_code=400, detail="Invalid request format")

            # Forward request to Ollama
            ollama_request = {
                "model": body.get('model', 'llama2:7b'),
                "prompt": body['messages'][0]['content']
            }

            # Following Flask best practices for external service calls
            try:
                ollama_response = requests.post(
                    f"{LLM_ENDPOINT}/api/generate",
                    json=ollama_request
                )
                if ollama_response.status_code != 200:
                    raise HTTPException(
                        status_code=502,
                        detail=f"LLM service error: {ollama_response.text}"
                    )
                
                result = ollama_response.json()
                content = result.get('response', '')

            except requests.RequestException as e:
                raise HTTPException(
                    status_code=502,
                    detail=f"Error communicating with LLM service: {str(e)}"
                )

            # Create standardized response
            response = ChatCompletionResponse(
                model=ollama_request['model'],
                choices=[
                    ChatCompletionResponseChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=content
                        ),
                        finish_reason="stop"
                    )
                ],
                usage=UsageInfo(
                    prompt_tokens=len(ollama_request['prompt']),
                    completion_tokens=len(content),
                    total_tokens=len(ollama_request['prompt']) + len(content)
                )
            )
            
            return response.dict()
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    print('main')
    chat = Chat()
    chat.add_remote_services()
    chat.start()