from autogen_core.components import RoutedAgent, message_handler, type_subscription
from autogen_ext.models import AzureOpenAIChatCompletionClient
from .model import ResourceModel
from autogen_core.base import MessageContext
from .factory import Resource, getResourceType
from autogen_core.components.models import SystemMessage

@type_subscription(topic_type="azureresourceagent")
class AzureResourceAgent(RoutedAgent):
    def __init__(self, 
                 model_client: AzureOpenAIChatCompletionClient,
                ) -> None:
        super().__init__("AzureResourceAgent")
        self._model_client = model_client

    @message_handler
    async def handle_message(
        self, message: ResourceModel, ctx: MessageContext
    ) -> str:
        #print(message.param)
        prompt = ''
        if(len(message.azureResource)==1):
#            print(f"Resource Name : {message.azureResource[0].azureResourceName} Resource Type : {message.azureResource[0].azureResourceType}")
            resource:Resource = getResourceType(message.azureResource[0].azureResourceType)
            prompt = resource.prompt(message.azureResource[0], message.param)
        else:
            resource:Resource = getResourceType(azureResourceType="Default")
            prompt = resource.promptForResources(message.azureResource, message.param)
        print(f" Prompt : {prompt}")
        #if(len(message.azureResource)!=1):
        response = await self._model_client.create(
                [SystemMessage(prompt)],
            )
        #print('response ===> ', response)
        print(response.content)
        return response.content
        #Get the prompts specific to the resource type
        

