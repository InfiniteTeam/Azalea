import discord
from discord.ext import commands

class Azalea(commands.AutoShardedBot):
    def __init__(self, command_prefix, error, help_command=commands.bot._default, description=None, **options):
        super().__init__(command_prefix, help_command, description, **options)
        self.error = error
        self.datas = {}

    def add_data(self, name, data):
        if name in self.datas.keys():
            raise self.error.GlobaldataAlreadyAdded(f"'{name}' 글로벌 데이터는 이미 추가되어 있습니다.")
        self.datas[name] = data

    def get_data(self, name):
        try:
            return self.datas[name]
        except KeyError:
            raise KeyError(f"'{name}' 글로벌 데이터가 존재하지 않습니다.")

    def set_data(self, name, value):
        try:
            self.datas[name] = value
        except KeyError:
            raise KeyError(f"'{name}' 글로벌 데이터가 존재하지 않습니다.")

    def remove_data(self, name):
        try:
            del self.datas[name]
        except KeyError:
            raise KeyError(f"'{name}' 글로벌 데이터가 존재하지 않습니다.")