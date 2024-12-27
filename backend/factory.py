from abc import ABC, abstractmethod
import orjson
from autogen_core.components import RoutedAgent, message_handler, type_subscription
from .model import AzureResource, InitalPrompt
from typing import List, Dict
from autogen_core.base import AgentId, MessageContext

# Create base class
class Resource(ABC):
    @abstractmethod
    def prompt(self, azureResource: AzureResource, param: Dict[str, Dict]) -> str:
        """Get the prompt."""
        pass
    
    """Default Resource Type:."""
    def promptForResources(self, azureResources: List[AzureResource], param: Dict[str, Dict]) -> str:
        print(f"defaulr resource should be list {type(azureResources)}")
        #json_data = json.dumps(azureResources)
        print(f"Length {len(azureResources)}")
        json_data = orjson.dumps(azureResources).decode("utf-8")
        print(f"JSON {json_data}")
        prompt = f""" 
            Following are the details of the list of Azure resources in JSON array. You need to create the biceps scripts with the given details and also take into consideration the dependencies information.         
            {json_data}
            
            You just need to create the biceps with parameters for configurable properties and no other instructions or explanation or text is needed. The output has to be just the biceps file.
        """
        return prompt
    
class DefaultResource(Resource):

    """Default Resource Type:."""
    def prompt(self, azureResource: AzureResource, param: Dict[str, Dict]) -> str:
        print(f"defaulr resource {type(azureResource)}")
        prompt = f""" 
            Following are the details for the Azure {azureResource.azureResourceType} resource. You need to create the biceps scripts with the given details and also take into consideration the dependencies information.         
                Azure Resource - {azureResource.azureResourceType} 
                Resource Name - {azureResource.azureResourceName}
                Dependencies - {azureResource.azureResourceDependencies}

            You just need to create the biceps with parameters for configurable properties and no other instructions or explanation or text is needed. The output has to be just the biceps file.
            """
        return prompt    

def getResourceType(azureResourceType="Default"):

    resources = {

    }
    return resources[azureResourceType]() if azureResourceType in resources else DefaultResource()

@type_subscription(topic_type="biceps-reviewer")
class Review(RoutedAgent):
    def __init__(self
                ) -> None:
        super().__init__("Review Biceps")

    @message_handler
    async def handle_message(
        self, message: InitalPrompt, ctx: MessageContext
    ) -> str:
        print(f"Sender {ctx.sender.key} {ctx.sender.type} TopicId {ctx.topic_id}  key {self.id.key} ")
        print(f'Critic {message}')
        await self.send_message(InitalPrompt(prompt="Response from review agent"),
                    AgentId(type=ctx.sender.type, key=self.id.key),
                )
        return message.prompt    
