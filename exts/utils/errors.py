from discord.ext import commands

class AzaleaError(Exception):
    pass

class NotRegistered(commands.CheckFailure):
    pass

class NotMaster(commands.CheckFailure):
    pass

class GlobaldataAlreadyAdded(AzaleaError):
    pass

class SentByBotUser(commands.CheckFailure):
    pass

class LockedExtensionUnloading(AzaleaError):
    pass

class ArpaIsGenius(AzaleaError):
    pass

class NoCharOnline(commands.CheckFailure):
    pass

class ParamsNotExist(AzaleaError):
    def __init__(self, param):
        self.param = param
        super().__init__('존재하지 않는 옵션값입니다: {}'.format(param))

class NotGuildChannel(commands.CheckFailure):
    pass

class ItemNotExistsInDB(AzaleaError):
    def __init__(self, uid):
        self.uid = uid
        super().__init__('DB에 존재하지 않는 아이템 ID: {}'.format(uid))

class MaxCountExceeded(AzaleaError):
    def __init__(self, uid, count, maxcount):
        self.uid = uid
        self.count = count
        self.maxcount = maxcount
        super().__init__('아이템 개수 {}개가 지정된 한도 {}개보다 많습니다: {}'.format(count, maxcount, uid))

class CmdNameNotFoundInDB(AzaleaError):
    def __init__(self, extname, cmdid):
        self.id = cmdid
        self.extname = extname
        super().__init__('"{}"확장의 명령어 아이디 "{}"의 이름 또는 별명값이 DB에 존재하지 않습니다'.format(extname, cmdid))

class MissingRequiredArgument(AzaleaError):
    def __init__(self, param, paramdesc):
        self.param = param
        self.paramdesc = paramdesc
        super().__init__('명령어 파라미터 "{}"({})이 필요합니다'.format(param.name, paramdesc))

class CannotLoginBeingDeleted(AzaleaError):
    pass

class CharacterNotFound(AzaleaError):
    pass

class ItemTagNotFound(AzaleaError):
    pass