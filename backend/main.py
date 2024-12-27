from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from .util import initialize_agent_runtime
from .model import Message, APIModel
from .agent import ClientServerAgent
from autogen_core.base import MessageContext, TopicId
import asyncio
import uuid
from typing import Dict

@asynccontextmanager
async def init(app: FastAPI):
    print('initialize the context manager.')
    global agent_runtime
    # Initialize the agent runtime
    agent_runtime = await initialize_agent_runtime()
    print('initialize the agent runtime.')
    #
    await ClientServerAgent.register(agent_runtime, "clientserveragent", lambda: ClientServerAgent(manager))

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

@app.get("/")
async def root():
    return "Use the websockets /imagetobiceps"


class ConnectionManager:
    """Class defining socket events"""
    def __init__(self):
        """init method, keeping track of connections"""
        print("Init the connection. ")
        self.connections: Dict[str, WebSocket] = {}
    
    async def connect(self, 
                      session_id: str, 
                      websocket: WebSocket):
        """connect event"""
        print("connect the websocket ")
        self.connections[session_id] = websocket
        await websocket.accept()

    async def handle_message(self,
                             session_id: str, 
                             websocket: WebSocket):
        print("Receive message from the socket")
        #user_message_text = await websocket.receive_text()
        #print(f"Received the message from the user {user_message_text} ")
        try:
            while True:
                data = await websocket.receive_text()
                print(f'data {data}')
                #validate the input JSON 
                try:
                    message = Message.from_json(data)
                except Exception as e:
                    await websocket.send_text(f"Input is not in the expected format.. please try again.")
                    print(str(e))
                # publish the message
                await agent_runtime.publish_message(
                    message, 
                    topic_id=TopicId(type="iac-router", source=session_id)
                )
        except WebSocketDisconnect:
            manager.disconnect(session_id, websocket)
    
    def disconnect(self, 
                    session_id: str, 
                    websocket: WebSocket):
        """disconnect event"""
        print(f"remove the websocket {self.connections}")
        del self.connections[session_id]

manager = ConnectionManager()

# WebSocket endpoint to handle user messages
@app.websocket("/imagetobiceps")
async def websocket_endpoint(websocket: WebSocket):
    print("Make connection to the websocket")
    session_id = str(uuid.uuid4())
    await manager.connect(session_id, websocket)
    await manager.handle_message(session_id, websocket)

# Run the FastAPI app
if __name__ == "__main__":
    print('main')
    import uvicorn
    #
    uvicorn.run("backend.main:app", host="127.0.0.1", port=9999, reload=True)