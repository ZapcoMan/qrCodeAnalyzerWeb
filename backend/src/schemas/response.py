from typing import Generic, TypeVar, Optional
from dataclasses import dataclass, asdict

T = TypeVar('T')

@dataclass
class APIResponse(Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    code: int = 200
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def success_response(cls, data: T, code: int = 200):
        return cls(success=True, data=data, code=code)
    
    @classmethod
    def error_response(cls, error: str, code: int = 400):
        return cls(success=False, error=error, code=code)