from abc import ABC, abstractmethod
import orjson
from autogen_core.components import RoutedAgent, message_handler, type_subscription
from .model import AzureResource, Message
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
        lst=[]
        for item in azureResources:
            item2 = AzureResource(azureResourceName=item.azureResourceName, 
                                  azureResourceDependencies=[], 
                                  azureResourceType=item.azureResourceType,
                                  bicepsSymbolicName=item.bicepsSymbolicName          
                                )
            lst.append(item2)
        json_data = orjson.dumps(lst).decode("utf-8")
        print(f"JSON {json_data}")
        prompt = f""" 
            Following are the details of the list of Azure resources in JSON array. You need to create the biceps scripts with the given details and also take into consideration the dependencies information.         
            {json_data}
            
            You just need to create the biceps with parameters for configurable properties and no other instructions or explanation or text is needed. The output has to be just the biceps file.
        """
        return prompt
    
class DefaultResource(Resource):

#                Dependencies - {azureResource.azureResourceDependencies}


    """Default Resource Type:."""
    def prompt(self, azureResource: AzureResource, param: Dict[str, Dict]) -> str:
        print(f"defaulr resource {type(azureResource)}")
        prompt = f""" 
            Following are the details for the Azure {azureResource.azureResourceType} resource. You need to create the biceps scripts with the given details and also take into consideration the dependencies information.         
                Azure Resource - {azureResource.azureResourceType} 
                Resource Name - {azureResource.azureResourceName}
                Dependencies - []
                bicepsSymbolicName - {azureResource.bicepsSymbolicName}

            You just need to create the biceps with parameters for configurable properties and no other instructions or explanation or text is needed. The output has to be just the biceps file.
            """
        return prompt    

def getResourceType(azureResourceType="Default"):

    resources = {

    }
    return resources[azureResourceType]() if azureResourceType in resources else DefaultResource()   
