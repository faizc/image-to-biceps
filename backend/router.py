import asyncio
from autogen_core.components import RoutedAgent, message_handler, type_subscription
from autogen_ext.models import AzureOpenAIChatCompletionClient
from .model import Message, AzureResourceList, ResourceModel, Result
from .config import Config
from autogen_core.base import AgentId, MessageContext, TopicId
from autogen_core.components import Image as AGImage
from autogen_core.components.models import UserMessage
import json
import time 
from typing import List
import base64
from autogen_core.application import SingleThreadedAgentRuntime

@type_subscription(topic_type="iac-router")
class IACRouterAgent(RoutedAgent):
    def __init__(
        self,
        name: str,
        model_client: AzureOpenAIChatCompletionClient,
        agent_registry: SingleThreadedAgentRuntime,
    ) -> None:
        print(f"\n IACRouterAgent Constructor \n")
        super().__init__("IAC Router")
        self._name = name
        self._model_client = model_client
        self._registry = agent_registry

    @message_handler
    async def route_message(self, message: Message, ctx: MessageContext) -> None:
        print(f"Prompt in route message: {message}\n\n")
        result = await self.__scan_image_to_list_azure_resources(message)
        # publish the message
        await self._registry.publish_message(
            result, 
            topic_id=TopicId(type="server-agent", source=ctx.topic_id.source)
        )

    async def __process_avd(self, azureResource: AzureResourceList) -> Result:
        print('__process_avd')

        instruction=f"""
            You are a helpful AI assistant who will be generating biceps file based on the following instruction. 
                1. Use the Azure resource specific biceps module as base bicep and update the 'params' section with the information provided by the users (i.e. name, location, dependencies etc.). 
                   If the relevant base Bicep file for the Azure resource type is not found in the provided files then create biceps file based on your knowledge and follow the same instructions.
                   Note - None of the attributes from the base bicep module should be omitted or missing in the final biceps file. 
                2. Parameterize the values in the biceps on top of the biceps file. 
                    for e.g. 
                    @description('VM Disk Name')
                    param diskName string = 'vm-cindia-fc-disk1-bf2a815'
                3. Base biceps file has values within <> braces which needs to be parameterized on top of the biceps configuration. Only the values need to be parameterized and not the complete parent section.
                    for e.g. configuration in the base biceps file
                        location: '<location>' 
                        
                    will be replaced with
                    
                        param location_azure_resource_type string = '<location>'
                        location: location_azure_resource_type

                4. New information that is being updated to the base biceps needs to be parameterized as well. 
                5. Ensure that all the JSON elements in the biceps file under the params section are included in the final biceps file. 
                6. Add the dependsOn section to the biceps file based on the information provided in the azureResourceDependencies.
                7. Remove the zones section from the biceps file. 
                8. Replace with the version with the version information as per the azure resource type.

            Please note that the final output needs to be Biceps file only with no additional comments or text. Validate all the attributes and sections from the biceps module are included in the final biceps file. 
        """
        assistant = Config.createAssistant(instruction)
        #print('\n\n\n================================================================')
        #print(assistant.model_dump_json(indent=2))
        #print('================================================================\n\n')

        diction = {}
        count = 0

        for idx, x in enumerate(azureResource.azureresources):
            count = count + 1
            user_prompt = f""" 
                Add the following information to the existing biceps file, pick the base biceps file based on the azure resource type. If the relevant base Bicep file for the Azure resource type is not found in the provided files then create biceps file based on your knowledge and follow the same instructions.
                {{
                    {x}
                }}
                Please note that the final output needs to be Biceps file only with no additional comments or text.
            """
            print(f'Count {count}\nUserPrompt - {user_prompt}')

            client = Config.GetAzureOpenAIClient(api_version=Config.ASSISTANT_AZURE_OPENAI_API_VERSION)
            # Create a thread
            thread = client.beta.threads.create()
            #print('\n\n================================================================')
            #print(f'thread - {thread}')
            #print('================================================================\n\n')

            # Add a user question to the thread
            message = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_prompt
            )

            thread_messages = client.beta.threads.messages.list(thread.id)
            #print('\n\n================================================================')
            #print(thread_messages.model_dump_json(indent=2))
            #print('================================================================\n\n')

            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id,
            )

            start_time = time.time()

            status = run.status
            while status not in ["completed", "cancelled", "expired", "failed"]:
                time.sleep(5)
                run = client.beta.threads.runs.retrieve(thread_id=thread.id,run_id=run.id)
                #print("Elapsed time: {} minutes {} seconds".format(int((time.time() - start_time) // 60), int((time.time() - start_time) % 60)))
                status = run.status
                #print(f'Status: {status} reason {run.last_error}')

            messages = client.beta.threads.messages.list(thread_id=thread.id)
            data = json.loads(messages.model_dump_json(indent=2))  # Load JSON data into a Python object
            #print(data['data'][0]['content'][0]['text']['value'])
            diction[x.azureResourceType]=data['data'][0]['content'][0]['text']['value']

            #delete the thread
            client.beta.threads.delete(thread.id)

            user_prompt = ""
            #if count==2:
            #    break

        #print(diction)
        for val in diction.values():
            print('-------------------------------------------------------------\n')
            print(val)
            print('\n--------------------------------\n\n-----------------------------\n\n')

        finalBiceps = ''.join(str(x.replace('```bicep','').replace('```','')) for x in diction.values())
        return Result(biceps=finalBiceps, error="")


    async def __process_non_avd(self, azureResource: AzureResourceList) -> Result:
        print('__process_non_avd')
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
            return Result(biceps=None, error=str(e))
        
        return Result(biceps=finalBiceps, error="")

    async def __scan_image_to_list_azure_resources(self, message) -> Result:
        with open("C:\\tmp\\rg-agentic-to-iac.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        imageUri = f"data:image/jpeg;base64,{encoded_string.decode("utf-8")}"

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
                messages, 
                json_output=True,
                #[SystemMessage(message)], json_output=True,
                #[UserMessage(content=system_message, source="user")], json_output=True
                extra_create_args={"response_format": AzureResourceList},
            )
            print(response)
            print(response.content)

            azureResource: AzureResourceList = AzureResourceList.model_validate(
                json.loads(response.content)
            )
            print(len(azureResource.azureresources))
            for idx, x in enumerate(azureResource.azureresources):
                print(idx, x)

            result = None
            if message.avd == True:
                result = await self.__process_avd(azureResource)
            else:
                result = await self.__process_non_avd(azureResource)
            
            return result

        except Exception as e:
            print(f"Failed to parse activities response: {str(e)}")
            return Result(biceps=None, error=str(e))
