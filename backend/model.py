from pydantic import BaseModel
from typing import List, Optional, Dict
from dataclasses_json import dataclass_json
from dataclasses import dataclass

@dataclass_json
@dataclass
class Message:
    imagePath: str
    avm: bool = False

@dataclass
class Result:
    biceps: str        
    error: str

@dataclass
class AzureResource(BaseModel):
    azureResourceType: str
    azureResourceName: str
    bicepsSymbolicName: str
    azureResourceDependencies: Optional[List[str]] = None

    def __init__(self, azureResourceType: str, azureResourceName: str, bicepsSymbolicName: str, azureResourceDependencies: List[str]) -> None:
        super().__init__(azureResourceType=azureResourceType, azureResourceName=azureResourceName, bicepsSymbolicName=bicepsSymbolicName, azureResourceDependencies=azureResourceDependencies)

@dataclass
class AzureResourceList(BaseModel):
    azureresources: List[AzureResource]

    def __init__(self, azureresources: List[AzureResource]) -> None:
        super().__init__(azureresources=azureresources)        

@dataclass    
class ResourceModel(BaseModel):
    azureResource: List[AzureResource]
    param: Dict[str, Dict]

    def __init__(self, azureResource: List[AzureResource], param: Dict[str, str]) -> None:
        super().__init__(azureResource=azureResource, param=param)