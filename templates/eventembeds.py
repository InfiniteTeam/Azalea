import discord
import datetime
import math
from utils import pager, progressbar, permutil
from utils.embedmgr import aEmbedBase, aMsgBase
from utils.datamgr import StatMgr, ExpTableDBMgr
import io


class Levelup(aEmbedBase):
    async def ko(self, char, before, after):
        samgr = StatMgr(self.cog.pool, char.uid)
        edgr = ExpTableDBMgr(self.cog.datadb)
        level = await samgr.get_level(edgr)
        nowexp = char.stat.EXP
        req = edgr.get_required_exp(level + 1)
        accu = edgr.get_accumulate_exp(level + 1)
        prev_req = edgr.get_required_exp(level)
        if req - prev_req <= 0:
            percent = 0
        else:
            percent = math.trunc((req - accu + nowexp) / req * 1000) / 10

        embed = discord.Embed(
            title=f"🆙 `{char.name}` 의 레벨이 올랐습니다!",
            description="레벨이 **`{}`** 에서 **`{}`** (으)로 올랐습니다!".format(before, after),
            color=self.cog.color["info"],
        )
        embed.add_field(
            name="• 현재 경험치",
            value=">>> {}ㅤ **{}/{}** ({}%)\n레벨업 필요 경험치: **`{}`/`{}`**".format(
                progressbar.get(None, self.cog.emj, req - accu + nowexp, req, 10),
                format(req - accu + nowexp, ","),
                format(req, ","),
                percent,
                nowexp,
                accu,
            ),
        )
        embed.set_footer(text="자세한 정보는 '{}캐릭터 정보' 를 입력해 확인하세요!".format(self.cog.prefix))
        return embed


class Cmderror_MissingArg(aEmbedBase):
    async def ko(self, missing):
        return discord.Embed(
            title="❗ 명령어에 빠진 부분이 있습니다!",
            description=f"**`{missing}`이(가) 필요합니다!**\n자세한 명령어 사용법은 `{self.cog.prefix}도움` 을 통해 확인하세요!",
            color=self.cog.color["error"],
        )


class Cmderror_not_registered(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="❗ 등록되지 않은 사용자입니다!",
            description=f"`{self.cog.prefix}등록` 명령으로 등록해주세요!",
            color=self.cog.color["error"],
        )


class Cmderror_on_inspection(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="❗ 현재 Azalea는 점검 중입니다.",
            description=f"점검 중에는 운영자만 사용할 수 있습니다.",
            color=self.cog.color["error"],
        )


class Cmderror_no_char_online(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="❗ 캐릭터가 선택되지 않았습니다!",
            description=f"`{self.cog.prefix}캐릭터 변경` 명령으로 플레이할 캐릭터를 선택해주세요!",
            color=self.cog.color["error"],
        )


class Cmderror_params_not_exist(aEmbedBase):
    async def ko(self, param):
        return discord.Embed(
            title=f'❓ 존재하지 않는 명령 옵션입니다: {", ".join(str(param))}',
            description=f"`{self.cog.prefix}도움` 명령으로 전체 명령어를 확인할 수 있어요.",
            color=self.cog.color["error"],
        )


class Cmderror_no_private_message(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="⛔ 길드 전용 명령어",
            description="이 명령어는 길드 채널에서만 사용할 수 있습니다!",
            color=self.cog.color["error"],
        )


class Cmderror_private_only(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="⛔ DM 전용 명령어",
            description="이 명령어는 개인 메시지에서만 사용할 수 있습니다!",
            color=self.cog.color["error"],
        )


class Cmderror_missing_perms(aEmbedBase):
    async def ko(self, perms):
        perms = [permutil.format_perm_by_name(perm) for perm in perms]
        embed = discord.Embed(
            title="⛔ 멤버 권한 부족!",
            description=f"{self.ctx.author.mention}, 이 명령어를 사용하려면 다음과 같은 길드 권한이 필요합니다!\n> **`"
            + "`, `".join(perms)
            + "`**",
            color=self.cog.color["error"],
        )
        return embed


class Cmderror_missing_azalea_perms(aEmbedBase):
    async def ko(self, perms):
        embed = discord.Embed(
            title="⛔ Azalea 권한 부족!",
            description=f"{self.ctx.author.mention}, 이 명령어를 사용하려면 다음과 같은 Azalea 권한이 필요합니다!\n> **`"
            + "`, `".join(perms)
            + "`**",
            color=self.cog.color["error"],
        )
        return embed


class Cmderror_missing_bot_perms(aEmbedBase):
    async def ko(self, errstr):
        missings = permutil.find_missing_perms_by_tbstr(errstr)
        fmtperms = [permutil.format_perm_by_name(perm) for perm in missings]
        if missings:
            embed = discord.Embed(
                title="⛔ 봇 권한 부족!",
                description="이 명령어를 사용하는 데 필요한 봇의 권한이 부족합니다!\n`"
                + "`, `".join(fmtperms)
                + "`",
                color=self.cog.color["error"],
            )
        else:
            embed = discord.Embed(
                title="⛔ 봇 권한 부족!",
                description="이 명령어를 사용하는 데 필요한 봇의 권한이 부족합니다!\n부족한 권한이 무엇인지 감지하는 데 실패했습니다. [InfiniteTEAM 서포트 서버]({})로 문의하면 빠르게 도와드립니다.".format(
                    self.cog.config["support_url"]
                ),
                color=self.cog.color["error"],
            )

        return embed


class Cmderror_sendfail_too_long(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="❗ 메시지 전송 실패",
            description="보내려고 하는 메시지가 너무 길어 전송에 실패했습니다.",
            color=self.cog.color["error"],
        )


class Cmderror_sendfail_dm(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="❗ 메시지 전송 실패",
            description="DM(개인 메시지)으로 메시지를 전송하려 했으나 실패했습니다.\n혹시 DM이 비활성화 되어 있지 않은지 확인해주세요!",
            color=self.cog.color["error"],
        )


class Cmderror_errorembed_foruser(aEmbedBase):
    async def ko(self, uid):
        embed = discord.Embed(
            title="❌ 오류!",
            description=f"무언가 오류가 발생했습니다! 오류 코드:\n```{uid.hex}```\n",
            color=self.cog.color["error"],
        )
        embed.set_footer(
            text="오류 정보가 기록되었습니다. 나중에 개발자가 처리하게 되며 빠른 처리를 위해서는 [InfiniteTEAM 서포트 서버]({})에 문의하십시오.".format(
                self.cog.config["support_url"]
            )
        )
        return embed


class Cmderror_errcode(aMsgBase):
    async def ko(self, error):
        return '오류 코드: ' + str(error.__cause__.code)


class Cmderror_error_cause_msg(aMsgBase):
    async def ko(self):
        return "오류 발생 명령어: `" + self.ctx.message.content + "`"


class Cmderror_as_file_log(aEmbedBase):
    async def ko(self, uid, errstr):
        return discord.Embed(
            title="❌ 오류!",
            description=f"오류 ID: `{uid}`\n무언가 오류가 발생했습니다. 오류 메시지가 너무 길어 파일로 첨부됩니다.",
            color=self.cog.color["error"],
            file=discord.File(fp=io.StringIO(errstr), filename="errcontent.txt"),
        )


class Cmderror_errorembed_formaster(aEmbedBase):
    async def ko(self, uid, errstr):
        return discord.Embed(
            title="❌ 오류!",
            description=f"무언가 오류가 발생했습니다!\n```{uid.hex}```\n```python\n{errstr}```",
            color=self.cog.color["error"],
        )


class Cmderror_as_file(aEmbedBase):
    async def ko(self, errstr):
        return discord.Embed(
            title="❌ 오류!",
            description=f"무언가 오류가 발생했습니다. 오류 메시지가 너무 길어 파일로 첨부됩니다.",
            color=self.cog.color["error"],
            file=discord.File(fp=io.StringIO(errstr), filename="errcontent.txt"),
        )


class Cmderror_errdm_sent(aEmbedBase):
    async def ko(self, msg):
        return discord.Embed(
            title="❌ 오류!",
            description=f"개발자용 오류 메시지를 [DM]({msg.jump_url})으로 전송했습니다.",
            color=self.cog.color["error"],
        )

