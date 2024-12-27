import os
from autogen_ext.models import AzureOpenAIChatCompletionClient
from azure.identity.aio import ClientSecretCredential, DefaultAzureCredential, get_bearer_token_provider
import configparser
from openai import AzureOpenAI
#from .util import getAssistant, getVectorStore

config = configparser.ConfigParser()
config.read('backend\config.txt')

#def GetRequiredConfig(name):
#    return os.environ[name]

#def GetOptionalConfig(name, default=""):
    
    #if name in os.environ:
    #    return os.environ[name]
#    return default

def GetConfig(name):
    return config.get('azure-services-info', name)

class Config:
    AZURE_TENANT_ID = GetConfig("AZURE_TENANT_ID")
    AZURE_CLIENT_ID = GetConfig("AZURE_CLIENT_ID")
    AZURE_CLIENT_SECRET = GetConfig("AZURE_CLIENT_SECRET")

    AZURE_OPENAI_DEPLOYMENT_NAME = GetConfig("AZURE_OPENAI_DEPLOYMENT_NAME")
    AZURE_OPENAI_API_VERSION = GetConfig("AZURE_OPENAI_API_VERSION")
    AZURE_OPENAI_ENDPOINT = GetConfig("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY = GetConfig("AZURE_OPENAI_API_KEY")

    ASSISTANT_VECTOR_NAME = GetConfig("ASSISTANT_VECTOR_NAME")
    ASSISTANT_NAME = GetConfig("ASSISTANT_NAME")
    ASSISTANT_AZURE_OPENAI_API_VERSION = GetConfig("ASSISTANT_AZURE_OPENAI_API_VERSION")
    ASSISTANT_AZURE_OPENAI_DEPLOYMENT_NAME = GetConfig("ASSISTANT_AZURE_OPENAI_DEPLOYMENT_NAME")

    __azure_credentials = DefaultAzureCredential()
    __aoai_chatCompletionClient = None
    __aoai_Client = None
    __aoai_Assistant = None

    def GetAzureCredentials():
        # If we have specified the credentials in the environment, use them (backwards compatibility)
        if all(
            [Config.AZURE_TENANT_ID, Config.AZURE_CLIENT_ID, Config.AZURE_CLIENT_SECRET]
        ):
            return ClientSecretCredential(
                tenant_id=Config.AZURE_TENANT_ID,
                client_id=Config.AZURE_CLIENT_ID,
                client_secret=Config.AZURE_CLIENT_SECRET,
            )

        # Otherwise, use the default Azure credential which includes managed identity
        return Config.__azure_credentials
    
    
    def GetTokenProvider(scopes):
        return get_bearer_token_provider(Config.GetAzureCredentials(), scopes)
    
    def getAssistant(client:AzureOpenAI, assistantName: str): 
        if len(client.beta.assistants.list().data)==0:
            return None 
        
        for assistantInfo in client.beta.assistants.list().data:
            if(assistantInfo.name == assistantName):
                return assistantInfo

    def getVectorStore(client:AzureOpenAI, vectorStoreName: str): 
        if len(client.beta.vector_stores.list().data)==0:
            return None 
        
        for vectorStoreInfo in client.beta.vector_stores.list().data:
            if(vectorStoreInfo.name == vectorStoreName):
                return vectorStoreInfo
    
    def createAssistant(instruction:str):
        if Config.__aoai_Assistant is not None:
            return Config.__aoai_Assistant
        client = Config.GetAzureOpenAIClient(api_version=Config.ASSISTANT_AZURE_OPENAI_API_VERSION)
        print(type(client))

        # Check if the vector store already exists with the configured vector name
        vector_store = Config.getVectorStore(client=client, vectorStoreName=Config.ASSISTANT_VECTOR_NAME)
        if vector_store == None:
            # Create a vector store"
            vector_store = client.beta.vector_stores.create(name=Config.ASSISTANT_VECTOR_NAME)      
            # Ready the files for upload to OpenAI
            file_paths = [
                'avm/bastion-waf.txt', 
                'avm/networkinterface-waf.txt',
                'avm/networksecuritygroup-waf.txt',
                'avm/privatednszone-waf.txt', 
                'avm/privateendpoint-waf.txt',
                'avm/publicipaddress-waf.txt',
                'avm/virtualnetwork-waf.txt', 
                'avm/storageaccount-waf.txt',
                'avm/resource-version-info.txt',
            ]
            file_streams = [open(path, "rb") for path in file_paths]
            # Use the upload and poll SDK helper to upload the files, add them to the vector store,
            # and poll the status of the file batch for completion.
            file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=file_streams
            )
        #print(vector_store)
        # Check if the assistant already exists with the configured assistant name
        assistant = Config.getAssistant(client=client, assistantName=Config.ASSISTANT_NAME)
        if assistant == None:
            # Create an assistant
            assistant = client.beta.assistants.create(
                name=Config.ASSISTANT_NAME,
                instructions=instruction,
                tools=[{"type": "file_search"}],
                tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
                model=Config.ASSISTANT_AZURE_OPENAI_DEPLOYMENT_NAME
            )
        #print(type(assistant))
        #print(assistant)
        return assistant

    def GetAzureOpenAIClient(api_version):
        if Config.__aoai_Client is not None:
            return Config.__aoai_Client
        if Config.AZURE_OPENAI_API_KEY == "":
            Config.__aoai_Client = AzureOpenAI(
                azure_ad_token_provider=Config.GetTokenProvider(
                    "https://cognitiveservices.azure.com/.default"
                ),
                api_version=api_version,
                azure_endpoint = Config.AZURE_OPENAI_ENDPOINT
            )
        else:
            Config.__aoai_Client = AzureOpenAI(
                api_key=Config.AZURE_OPENAI_API_KEY,  
                api_version=api_version,
                azure_endpoint = Config.AZURE_OPENAI_ENDPOINT
            )            
        return Config.__aoai_Client        

    def GetAzureOpenAIChatCompletionClient(model_capabilities):
        if Config.__aoai_chatCompletionClient is not None:
            return Config.__aoai_chatCompletionClient

        if Config.AZURE_OPENAI_API_KEY == "":
            # Use DefaultAzureCredential for auth
            Config.__aoai_chatCompletionClient = AzureOpenAIChatCompletionClient(
                model=Config.AZURE_OPENAI_DEPLOYMENT_NAME,
                api_version=Config.AZURE_OPENAI_API_VERSION,
                azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
                azure_ad_token_provider=Config.GetTokenProvider(
                    "https://cognitiveservices.azure.com/.default"
                ),
                model_capabilities=model_capabilities,
            )
        else:
            # Fallback behavior to use API key
            Config.__aoai_chatCompletionClient = AzureOpenAIChatCompletionClient(
                model=Config.AZURE_OPENAI_DEPLOYMENT_NAME,
                api_version=Config.AZURE_OPENAI_API_VERSION,
                azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
                api_key=Config.AZURE_OPENAI_API_KEY,
                model_capabilities=model_capabilities,
            )

        return Config.__aoai_chatCompletionClient