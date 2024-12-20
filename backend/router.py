import asyncio
from autogen_core.components import RoutedAgent, message_handler, type_subscription
from autogen_ext.models import AzureOpenAIChatCompletionClient
from .model import InitalPrompt, AzureResourceList, ResourceModel
from autogen_core.base import AgentId, MessageContext
from autogen_core.components import Image as AGImage
from autogen_core.components.models import UserMessage
import json
from typing import List
import base64

@type_subscription(topic_type="iac-router")
class IACRouterAgent(RoutedAgent):
    def __init__(
        self,
        name: str,
        model_client: AzureOpenAIChatCompletionClient,
#        agent_registry: AgentRegistry,
    ) -> None:
        print(f"\n IACRouterAgent Constructor \n")
        super().__init__("IAC Router")
        self._name = name
        self._model_client = model_client
#        self._registry = agent_registry

    @message_handler
    async def route_message(self, message: InitalPrompt, ctx: MessageContext) -> None:
        print(f"Prompt: {message.prompt}\n\n")
        await self.__scan_image_to_list_azure_resources(message.prompt)

    async def __scan_image_to_list_azure_resources(self, message) -> None:
        with open("C:\\tmp\\rg-agentic-to-iac.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        imageUri = f"data:image/jpeg;base64,{encoded_string.decode("utf-8")}"

        init_prompt = f"""

        Analyze the azure network diagram at {AGImage.from_uri(imageUri)} and identify all the azure resource and the relationship between them. Remove the trailing text and have them consitent across the complete response. 

        Output needs to be scrictly JSON format as below
        
            azureResourceType:"The Azure resource type",
            azureResourceName:"The Azure resource name, this can be blank if the name is not available",
            azureResourceDependencies:"This can be list of the dependent azure resource"
               

        """

        init_prompt_lines = ['Analyze the azure network diagram at {} and identify all the azure resource and the relationship between them. Remove the trailing text and have them consitent across the complete response.', 
         '', 
         'Output needs to be scrictly JSON format as below', 
         '', 
         'azureResourceType:"The Azure resource type, this should be in lower case and without any space and use standard azure vocabulary"', 
         'azureResourceName:"The Azure resource name, this can be blank if the name is not available",', 
         'azureResourceDependencies:"This can be list of the dependent azure resource"'
        ]
        init_prompt = '\n'.join(init_prompt_lines)

        user_message = UserMessage(content=[init_prompt,AGImage.from_uri(imageUri)], source="tool")
        messages = [user_message]
        
        try:
            #response = await analyze_network_diagram_assistant.client.create(
            response = await self._model_client.create(
                messages, json_output=True,
                #[SystemMessage(message)], json_output=True,
                #[UserMessage(content=system_message, source="user")], json_output=True
                extra_create_args={"response_format": AzureResourceList},
            )
            print(response)
            print(response.content)

            azureResource: Model.AzureResourceList = AzureResourceList.model_validate(
                json.loads(response.content)
            )
            print(len(azureResource.azureresources))
            for idx, x in enumerate(azureResource.azureresources):
                print(idx, x)

            diction = {}
            for idx, x in enumerate(azureResource.azureresources):
                diction[x.azureResourceType]={}
                diction[x.azureResourceType]['name']=x.azureResourceName
                diction[x.azureResourceType]['dependency']=x.azureResourceDependencies
                print(idx, x)

            #
            resources = list()
            dependentResources = list()
            #
            for task in azureResource.azureresources:
                if(len(task.azureResourceDependencies)==0):
                    resources.insert(0, [task])
                else:
                    dependentResources.insert(0, task)
            #
            if(len(dependentResources) != 0):
                resources.append(dependentResources)

            tasks = [
                self.send_message(ResourceModel(azureResource=task, param=diction),
                    AgentId(type='azureresourceagent', 
                    key=self.id.key),
                )
                for task in resources
            ]
            finalBiceps:str = None
            try:
                group_results: List[str] = await asyncio.gather(*tasks)
                print("-" * 50)
                print(
                    f"GroupChatManager received responses from agents: {group_results}"
                )
                print("-" * 50)
                finalBiceps = ''.join(str(x.replace('```bicep','').replace('```','')) for x in group_results)
                print(finalBiceps)
            except Exception as e:
                print(f"Error sending messages to agents: {e}")
                return
            

        except Exception as e:
            print(f"Failed to parse activities response: {str(e)}")
        