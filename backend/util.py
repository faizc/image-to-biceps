from .config import Config
from .agent import AzureResourceAgent
from .router import IACRouterAgent
from autogen_core.application import SingleThreadedAgentRuntime

model_capabilities = {
    "vision": True,
    "function_calling": True,
    "json_output": True,
}
__aoai_chatCompletionClient = Config.GetAzureOpenAIChatCompletionClient(model_capabilities)

async def initialize_agent_runtime() -> SingleThreadedAgentRuntime:
    runtime = SingleThreadedAgentRuntime()

    # Start the runtime
    runtime.start()

    print(f"Agent runtime initialized successfully.")

    await IACRouterAgent.register(runtime, "IACRouterAgent", lambda: IACRouterAgent("IACRouterAgent", __aoai_chatCompletionClient))
    await AzureResourceAgent.register(runtime, "azureresourceagent", lambda: AzureResourceAgent(__aoai_chatCompletionClient))

    return runtime