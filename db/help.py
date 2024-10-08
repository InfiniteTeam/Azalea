GENERAL = ('기본 명령어', """
**`{p}도움`**: 도움말 메시지를 표시합니다.
**`{p}등록`**: Azalea에 등록해 사용을 시작합니다.
**`{p}정보`**: 봇 정보를 확인합니다.
**`{p}핑`**: 봇의 핑을 확인합니다.
**`{p}샤드`**: 현재 서버의 Azalea 샤드 번호를 확인합니다.
**`{p}공지채널 [#채널멘션]`**: Azalea 공지를 받을 채널을 설정합니다.
**`{p}뉴스`**: Azalea 뉴스를 확인합니다.
**`{p}탈퇴`**: Azalea 에서 탈퇴합니다.
""")

CHARACTER = ('캐릭터 명령어', """
**`{p}캐릭터`**: 내 캐릭터들을 확인합니다.
**`{p}캐릭터 생성`**: 새 캐릭터를 생성합니다.
**`{p}캐릭터 삭제 (캐릭터이름)`**: 캐릭터를 삭제합니다.
**`{p}캐릭터 삭제취소 (캐릭터이름)`**: 캐릭터 삭제를 취소합니다.
**`{p}캐릭터 닉변 [캐릭터이름]`**: 캐릭터의 이름을 변경합니다.
**`{p}캐릭터 정보 [캐릭터이름]`**: 캐릭터의 레벨, 능력치 등을 확인합니다.
**`{p}캐릭터 설정 [캐릭터이름]`**: 캐릭터의 설정을 변경합니다.
**`{p}로그아웃`**: 현재 캐릭터 연결을 끊습니다.
**`{p}가방`**: 현재 캐릭터의 아이템을 확인합니다.
""")

INGAME = ('게임 명령어', """
**`{p}출첵`**: 오늘의 출석체크 보상을 받습니다.
**`{p}낚시`**: 낚시로 물고기를 잡아보세요.
**`{p}상점`**: 상점에서 아이템을 사거나 팔 수 있습니다.
**`{p}순위 [서버/전체]`**: Azalea 순위를 확인합니다.
""")

ETC = ('기타 명령어', """
**`{p}알파찬양`**: 개발자 알파를 찬양합니다.
""")

def gethelps():
    return (GENERAL, CHARACTER, INGAME, ETC)
    