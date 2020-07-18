from utils.datamgr import Setting, SettingType

class Where_to_Levelup_Message:
    selections = {
        'dm': ('1️⃣', '개인 메시지로'),
        'current': ('2️⃣', '레벨업한 채널로'),
        False: ('⛔', '끄기')
    }

CHAR_SETTINGS = (
    Setting('private-item', '아이템 비공개', '다른 사람이 이 캐릭터의 아이템을 볼 수 없게 합니다.', bool, True),
    Setting('where-to-levelup-msg', '레벨 업 알림', '레벨 업 메시지를 어디로 보낼지 선택합니다.', Where_to_Levelup_Message, 'dm'),
)