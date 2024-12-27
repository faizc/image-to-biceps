from pydantic import BaseModel
from typing import List, Optional, Dict
from dataclasses_json import dataclass_json
from dataclasses import dataclass

@dataclass_json
@dataclass
class APIModel:
    version: str

@dataclass_json
@dataclass
class Message:
    imagePath: str
    avd: bool = False

@dataclass
class Result:
    biceps: str        
    error: str

@dataclass
class AzureResource(BaseModel):
    azureResourceType: str
    azureResourceName: str
    azureResourceDependencies: Optional[List[str]] = None

    def __init__(self, azureResourceType: str, azureResourceName: str, azureResourceDependencies: List[str]) -> None:
        super().__init__(azureResourceType=azureResourceType, azureResourceName=azureResourceName, azureResourceDependencies=azureResourceDependencies)

@dataclass
class AzureResourceList(BaseModel):
    azureresources: List[AzureResource]

@dataclass    
class ResourceModel(BaseModel):
    azureResource: List[AzureResource]
    param: Dict[str, Dict]

    def __init__(self, azureResource: List[AzureResource], param: Dict[str, str]) -> None:
        super().__init__(azureResource=azureResource, param=param)