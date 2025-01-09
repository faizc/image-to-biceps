from autogen_core.components import RoutedAgent, message_handler, type_subscription
from autogen_ext.models import AzureOpenAIChatCompletionClient
from .model import ResourceModel, Result
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
        instruction=f"""
            You are a helpful AI assistant who will be generating biceps file based on the following instruction. 
                1. Use the Azure resource specific biceps module as base bicep and update the 'params' section with the information provided by the users (i.e. name, location, dependencies etc.). 
                   If the relevant base Bicep file for the Azure resource type is not found in the provided files then create biceps file based on your knowledge and follow the same instructions.
                   Note - None of the attributes from the base bicep module should be omitted or missing in the final biceps file. 
                2. Parameterize the values in the biceps on top of the biceps file and variable name should be suffixed with the azure resource type 
                    for e.g. 
                    @description('VM Disk Name')
                    param diskName_disk string = 'vm-cindia-fc-disk1-bf2a815'
                    param location_publicIpAddress = 'some-location'
                3. Base biceps file has values within <> braces which needs to be parameterized on top of the biceps configuration. Only the values need to be parameterized and not the complete parent section.
                    for e.g. configuration in the base biceps file
                        location: '<location>' 
                        
                    will be replaced with
                    
                        param location_azure_resource_type string = '<location>'
                        location: location_azure_resource_type

                4. The biceps would start as the below, replace the bicepsSymbolicName from the JSON                          
                         resource <bicepsSymbolicName> 'Microsoft.Storage/storageAccounts@2023-05-01'

                5. New information that is being updated to the base biceps needs to be parameterized as well. 
                6. Ensure that all the JSON elements in the biceps file under the params section are included in the final biceps file. 
                7. Add the dependsOn section to the biceps file based on the information provided in the azureResourceDependencies.
                    The dependsOn would be as below where it's an array of the symbolicname of the azure resources and no spaces or new line after the comma
                    dependsOn: [diskResource,networkInterface_vm]
                8. Remove the zones section from the biceps file. 
                9. Replace with the version with the version information as per the azure resource type.
                10. Following is the sample biceps files

                    resource symbolicname 'Microsoft.Storage/storageAccounts@2023-05-01' = {{
                    kind: 'string'
                    location: 'string'
                    name: 'string'
                    properties: {{
                        property: 'string'
                    }}
                    sku: {{
                        name: 'string'
                    }}
                    dependsOn: []
                    }}

                    Where,
                        sybolicname - Use the bicepsSymbolicName from the provided input information
                        kind is optional and required for certain azure resource type like StorageAccounts where the value can be StorageV2 or Storage or FileStorage
                        name is the name of the resource 
                        location is the location of the resource, the best thing to do is to make it resourceGroup.location()
                    	properties is where you have all the other properties related to the azure resource. If there are no entries then it can be skipped as well.
                        sku is the SKU to be used for the resource, this can differ for database, storage and VMs, this needs to be populated with some default SKU 
                        dependsOn is option which would have the dependent resources which will typically be the symbolic name of the dependent resource, can be skipped if no elements


            Please note that the final output needs to be Biceps file only with no additional comments or text. Validate all the attributes and sections from the biceps module are included in the final biceps file. 

            {prompt}

        """
        #if(len(message.azureResource)!=1):
        response = await self._model_client.create(
                [SystemMessage(instruction)],
            )
        #print('response ===> ', response)
        print(response.content)
        return response.content
        #Get the prompts specific to the resource type
        
@type_subscription(topic_type="server-agent")
class ClientServerAgent(RoutedAgent):
    def __init__(self, 
            connection_manager,
            ) -> None:
        super().__init__("ClientServerAgent")
        self.connection_manager = connection_manager

    @message_handler
    async def handle_agent_response(
        self,
        message: Result,
        ctx: MessageContext,
    ) -> None:
        print('handle_server_response')
        session_id = ctx.topic_id.source
        try:
            websocket = self.connection_manager.connections.get(session_id)
            if websocket:
                await websocket.send_text(message.biceps)
                await websocket.send_text(f"Finished processing the message for session {session_id}.")

        except Exception as e:
            print(f"Failed to send message to session {session_id}: {str(e)}")


@type_subscription(topic_type="validatoragent")
class BicepsValidatorAgent(RoutedAgent):
    def __init__(self, 
                 model_client: AzureOpenAIChatCompletionClient,
                ) -> None:
        super().__init__("ValidatorAgent")
        self._model_client = model_client
    


