from .errors import AzaleaError
from enum import Enum

# Character Errors

class CharCreateErrReasons(Enum):
    NameAlreadyExists = '이미 해당 이름이 존재합니다'
    InvalidName = '사용할 수 없는 이름입니다'
    InvalidLength = '이름의 길이가 올바르지 않습니다'
    CannotIncludePrefix = '봇 접두사를 포함할 수 없습니다'

class CharCreateError(AzaleaError):
    def __init__(self, reason: CharCreateErrReasons):
        self.reason = reason
        super().__init__(f'캐릭터를 생성할 수 없습니다! (이유: {reason.value})')
        
class CharacterNotFound(AzaleaError):
    def __init__(self, uid: str):
        self.uid = uid
        super().__init__(f'캐릭터를 찾을 수 없습니다 (UUID: "{uid}")')
        
class SettingNotFound(AzaleaError):
    def __init__(self, name: str):
        self.name = NameError
        super().__init__(f'설정을 찾을 수 없습니다! (NAME: "{name}")')
        
class CannotLoginBeingDeleted(AzaleaError):
    def __init__(self, *, uid: str):
        self.uid = uid
        super().__init__(f'삭제 중인 캐릭터에 로그인할 수 없습니다 (UUID: "{uid}")')
        
# Item Errors

class ItemNotFound(AzaleaError):
    def __init__(self, *, uid: str):
        self.uid = uid
        super().__init__(f'아이템을 찾을 수 없습니다 (UUID: "{uid}")')