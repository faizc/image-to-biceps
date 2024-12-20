import os
from autogen_ext.models import AzureOpenAIChatCompletionClient
from azure.identity.aio import ClientSecretCredential, DefaultAzureCredential, get_bearer_token_provider
import configparser

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

    __azure_credentials = DefaultAzureCredential()
    __aoai_chatCompletionClient = None

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