# Image to Biceps 

Leverage the multi-modal capabilities of the Azure OpenAI GPT models to analyze image files containing the Azure network diagram or resource viewer diagram to extract the Azure Resources, orchestrated through Autogen agentic framework to generate the Biceps file for the diagram.  

## Features
1. Extract the Azure resource information and the dependency relationsip between the resource from the images. Follow the guidance for the image (size, resolution etc.) [here](https://learn.microsoft.com/en-us/azure/ai-services/openai/overview#image-tokens)
2. Biceps are created based on the Azure resource specific information extract from the images. You have option to generate the biceps as per the standard [Azure Verified Module](https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/storage/storage-account#example-11-waf-aligned) or generate bare minimum biceps file. 

## Message Flow
1. **App Init** - The "main.py" is the main class where the websockets, factory classes, routers, agents are subscribed and initialized.   
2. **User Input** - On receipt of the message, data is validated and the iac-router subscriber is invoked 
3. **Image Processing** - Image is processed by the router and based on the AVM flag (true/false), the respective agents are invoked.
    * **AVM=TRUE** - Router invokes the assistant-agent which generates the AVM standard files, collates the data for all the resources and reverts back to the router. 
    * **AVM=FALSE** - Router invokes the N number of agents based on the dependencies between the azure resources. Collates the response from all the agents and send back to the router.  

![alt text](./images/flow-diagram.png "Flow Diagram")

## Usage

### Clone the repository
```bash
git clone https://github.com/faizc/image-to-biceps
cd image-to-biceps
```

#### Install Dependencies:

Ensure you have Python 3.12 or higher installed. Install required packages using pip:

```bash
pip install -r requirements.txt
```

## Configuration

The application requires several environment variables to be set, which can be placed in a `.env` file in the `backend` directory:

```ini
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview (Use api versions **2024-08-01-preview or later** as we are using the feature to return the response in JSON format)
AZURE_OPENAI_ENDPOINT=your-openai-endpoint
ASSISTANT_VECTOR_NAME=biceps-assistant-vector-store
ASSISTANT_NAME=biceps-assistant
ASSISTANT_AZURE_OPENAI_API_VERSION=2024-05-01-preview (Use API version which is compatible with Assistant's API)
ASSISTANT_AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

__For OpenAI Key based authentication__
```ini
AZURE_OPENAI_API_KEY=azure-openai-api-key
```

__For OpenAI service principal based authentication__
```ini
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

### Running the application
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 9999
```

#### Access the Chatbot:

Connect to the WebSocket endpoint at `ws://127.0.0.1:8000/imagetobiceps` to start interacting with the chatbot.

__NOTE__ - You will need to use Postman or Apidog like API testing tool for connecting to websocket

#### Sample Test:

##### Sample network/resource viewer image

Resource Visualizer image for resource group which has Virtual Machine and Storage behind private endpoint and the connectivity of the VM is through bastion.   
![alt text](./images/rg-agentic-to-iac.png "Resource Viewer")

##### Test the websocket

The input should be in below JSON format
```json
{
    "imagePath": "C:\\tmp\\rg-agentic-to-iac.png",
    "avd": false
}
```
__NOTE__ - If the input is not send in this format then the request would fail with some guided error message from the server and ensure that the image is the local path on your machine. 

![alt text](./images/websocket-1.png "Connected to the websocket")

Click on the **Send** button

![alt text](./images/websocket-2.png "Biceps file")

#### TODO/Limitations:
1. Implement the logging framework by replacing print statements
2. Currently we have the logic to split the azure resource based on dependencies which has been done so that LLM doesn't generate unwated biceps configuration. This can be optimized further based on the token usage/content lenght etc. 
3. The LLM response for the images exported through the resource visualizer on Azure Portal are far better than architecture diagrams. Problem is that architecture diagram may not depict the dependencies properly and may also contain some unwated information like users, operational services, custom icons etc.   
