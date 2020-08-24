import discord
import datetime
import math
from utils import pager, progressbar
from utils.embedmgr import aEmbedBase, aMsgBase, set_delete_after_footer
from utils.datamgr import StatMgr, ExpTableDBMgr

class Levelup(aEmbedBase):
    async def ko(self, char, before, after):
        samgr = StatMgr(self.cog.pool, char.uid)
        edgr = ExpTableDBMgr(self.cog.datadb)
        level = await samgr.get_level(edgr)
        nowexp = char.stat.EXP
        req = edgr.get_required_exp(level+1)
        accu = edgr.get_accumulate_exp(level+1)
        prev_req = edgr.get_required_exp(level)
        if req-prev_req <= 0:
            percent = 0
        else:
            percent = math.trunc((req-accu+nowexp)/req*1000)/10

        embed = discord.Embed(title=f'🆙 `{char.name}` 의 레벨이 올랐습니다!', description='레벨이 **`{}`** 에서 **`{}`** (으)로 올랐습니다!'.format(before, after), color=self.cog.color['info'])
        embed.add_field(name='• 현재 경험치', value='>>> {}ㅤ **{}/{}** ({}%)\n레벨업 필요 경험치: **`{}`/`{}`**'.format(
            progressbar.get(None, self.cog.emj, req-accu+nowexp, req, 10),
            format(req-accu+nowexp, ','), format(req, ','), percent, nowexp, accu
        ))
        embed.set_footer(text="자세한 정보는 '{}캐릭터 정보' 를 입력해 확인하세요!".format(self.cog.prefix))
        return embed