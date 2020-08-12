from .errors import AzaleaError
from enum import Enum

class CharCreateErrReasons(Enum):
    NameAlreadyExists = '이미 해당 이름이 존재합니다'
    InvalidName = '사용할 수 없는 이름입니다'
    InvalidLength = '이름의 길이가 올바르지 않습니다'
    CannotIncludePrefix = '봇 접두사를 포함할 수 없습니다'

class CharCreateError(AzaleaError):
    def __init__(self, reason: CharCreateErrReasons):
        self.reason = reason
        super().__init__(f'캐릭터를 생성할 수 없습니다! (이유: {reason.value})')