from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from .util import initialize_agent_runtime
from .model import InitalPrompt
from autogen_core.base import MessageContext, TopicId
import asyncio


@asynccontextmanager
async def init(app: FastAPI):
    print('initialize the context manager.')
    global agent_runtime
    # Initialize the agent runtime
    agent_runtime = await initialize_agent_runtime()
    #
    await agent_runtime.publish_message(
        InitalPrompt(prompt="system_message", imagePath=""), 
        topic_id=TopicId(type="iac-router", source="iac-router")
    )
    # 
    await agent_runtime.stop_when_idle()

    yield  # This separates the startup and shutdown logic

    print("Agent runtime set to None now...")
    # Cleanup logic goes here
    agent_runtime = None

app = FastAPI(lifespan=init)

# temporary async method to test the invocation from /process
async def async_add(a, b):
    print("Starting async_add")
    await asyncio.sleep(5)  # Simulate an async operation
    print("Result From async_add", a + b)
    return a + b

@app.get("/process")
async def root():
    
    print(type(agent_runtime))
    if agent_runtime is not None:
        print("agent_runtime is not None")

    #results = await agent_runtime.publish_message(
    #    InitalPrompt(prompt="system_message", imagePath=""), 
    #    topic_id=TopicId(type="iac-router", source="iac-router")
    #)

    # not invoking the async method.. need to check 
    results=async_add(12,43)
    print(f"Get output is {results}")
    return "results"


class ConnectionManager:
    """Class defining socket events"""
    def __init__(self):
        """init method, keeping track of connections"""
        print("Init the connection. ")
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        """connect event"""
        await websocket.accept()
        self.active_connections.append(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Direct Message"""
        await websocket.send_text(message)
    
    def disconnect(self, websocket: WebSocket):
        """disconnect event"""
        self.active_connections.remove(websocket)

manager = ConnectionManager()

@app.websocket("/communicate")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Received:{data}",websocket)
            #await runtime.publish_message(
            #    InitalPrompt(prompt="system_message", imagePath=""), topic_id=TopicId(type="iac-router", source="iac-router")
            #)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.send_personal_message("Bye!!!",websocket)

# Run the FastAPI app
if __name__ == "__main__":
    print('main')
    import uvicorn
    #
    uvicorn.run("backend.main:app", host="127.0.0.1", port=9999, reload=True)