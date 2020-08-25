import discord
from utils.basecog import BaseCog
from utils.mgrerrors import CharCreateError, CharCreateErrReasons
from utils import pager, timedelta
from utils.datamgr import StatMgr, ExpTableDBMgr, SettingDBMgr, SettingMgr
import datetime
from dateutil.relativedelta import relativedelta
from utils.embedmgr import aEmbedBase, aMsgBase
from db import charsettings


class Char_no_any_char(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="🎲 캐릭터가 하나도 없네요!",
            description="`{}캐릭터 생성` 명령으로 캐릭터를 생성해서 게임을 시작하세요!".format(self.cog.prefix),
            color=self.cog.color["warn"],
        )


class Char_no_any_char_other_user(aEmbedBase):
    async def ko(self, user):
        return discord.Embed(
            title=f"🎲 `{user.name}` 님은 캐릭터가 하나도 없네요!", color=self.cog.color["warn"]
        )


class Char(aEmbedBase):
    async def ko(self, user, pgr, *, mode="default"):
        edgr = ExpTableDBMgr(self.cog.datadb)
        chars = pgr.get_thispage()
        charstr = ""
        for idx, one in enumerate(chars):
            name = one.name
            samgr = StatMgr(self.cog.pool, one.uid)
            if mode == "select":
                name = f"{idx+1}. {name}"
            level = await samgr.get_level(edgr)
            chartype = one.type.value
            online = one.online
            onlinestr = ""
            if online:
                onlinestr = "(**현재 플레이중**)"
            deleteleftstr = ""
            if one.delete_request:
                tdleft = timedelta.format_timedelta(
                    (one.delete_request + relativedelta(hours=24))
                    - datetime.datetime.now()
                )
                deleteleft = " ".join(tdleft.values())
                deleteleftstr = "\n**`{}` 후에 삭제됨**".format(deleteleft)
            charstr += "**{}** {}\n레벨: `{}` \\| 직업: `{}` {}\n\n".format(
                name, onlinestr, level, chartype, deleteleftstr
            )
        embed = discord.Embed(
            title=f"🎲 `{user.name}`님의 캐릭터 목록",
            description=charstr,
            color=self.cog.color["info"],
        )
        embed.description = charstr + "```{}/{} 페이지, 전체 {}캐릭터```".format(
            pgr.now_pagenum() + 1, len(pgr.pages()), pgr.objlen()
        )
        embed.set_footer(text="✨: 새로 만들기 | 🎲: 캐릭터 변경 | ❔: 캐릭터 정보")
        return embed


class Char_change_select_index(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="🎲 캐릭터 변경 - 캐릭터 선택",
            description="변경할 캐릭터의 번째수를 입력해주세요.\n위 메시지에 캐릭터 앞마다 번호가 붙어 있습니다.\n❌를 클릭해 취소합니다.",
            color=self.cog.color["ask"],
        )


class Char_info_select_index(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="❔ 캐릭터 정보 - 캐릭터 선택",
            description="정보를 확인할 캐릭터의 번째수를 입력해주세요.\n위 메시지에 캐릭터 앞마다 번호가 붙어 있습니다.\n❌를 클릭해 취소합니다.",
            color=self.cog.color["ask"],
        )


class Char_all_slots_full(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="❌ 캐릭터 슬롯이 모두 찼습니다.",
            description="유저당 최대 캐릭터 수는 {}개 입니다.".format(
                self.cog.config["max_charcount"]
            ),
            color=self.cog.color["error"],
        )


class Char_create_name(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="🏷 캐릭터 생성 - 이름",
            description="새 캐릭터를 생성합니다. 캐릭터의 이름을 입력하세요.\n취소하려면 `취소` 를 입력하세요!",
            color=self.cog.color["ask"],
        )


class Char_create_job(aEmbedBase):
    async def ko(self, charname):
        return discord.Embed(
            title="🏷 캐릭터 생성 - 직업",
            color=self.cog.color["ask"],
            description="""\
                `{}` 의 직업을 선택합니다.
                ⚔: 전사
                🏹: 궁수
                🔯: 마법사

                ❌: 취소
            """.format(
                charname
            ),
        )


class Char_create_done(aEmbedBase):
    async def ko(self, charcount, charname):
        if charcount == 0:
            desc = "첫 캐릭터 생성이네요, 이제 게임을 시작해보세요!"
        else:
            desc = "`{}캐릭터 변경` 명령으로 이 캐릭터를 선텍해 게임을 시작할 수 있습니다!".format(self.cog.prefix)
        return discord.Embed(
            title="{} 캐릭터를 생성했습니다! - `{}`".format(
                self.cog.emj.get(self.ctx, "check"), charname
            ),
            description=desc,
            color=self.cog.color["success"],
        )


class Char_change_done(aEmbedBase):
    async def ko(self, charname):
        return discord.Embed(
            title="{} 현재 캐릭터를 `{}` 으로 변경했습니다!".format(
                self.cog.emj.get(self.ctx, "check"), charname
            ),
            color=self.cog.color["success"],
        )


class Char_change_but_being_deleted(aEmbedBase):
    async def ko(self, charname):
        return discord.Embed(
            title=f"❓ 삭제 중인 캐릭터입니다: `{charname}`",
            description="이 캐릭터는 삭제 중이여서 로그인할 수 없습니다. `{}캐릭터 삭제취소` 명령으로 취소할 수 있습니다.".format(
                self.cog.prefix
            ),
            color=self.cog.color["error"],
        )


class Char_change_but_already_current(aEmbedBase):
    async def ko(self, charname):
        return discord.Embed(
            title=f"❓ 이미 현재 캐릭터입니다: `{charname}`",
            description="이 캐릭터는 현재 플레이 중인 캐릭터입니다.",
            color=self.cog.color["error"],
        )


class Char_delete_already_queued(aEmbedBase):
    async def ko(self, name):
        return discord.Embed(
            title=f"❓ 이미 삭제가 요청된 캐릭터입니다: `{name}`",
            description=f"삭제를 취소하려면 `{self.cog.prefix}캐릭터 삭제취소` 명령을 입력하세요.",
            color=self.cog.color["error"],
        )


class Char_delete_ask(aEmbedBase):
    async def ko(self, name):
        return discord.Embed(
            title=f"⚠ `{name}` 캐릭터를 정말로 삭제할까요?",
            description="캐릭터는 삭제 버튼을 누른 후 24시간 후에 완전히 지워지며, "
            f"이 기간 동안에 `{self.cog.prefix}캐릭터 삭제취소` 명령으로 취소가 가능합니다.",
            color=self.cog.color["warn"],
        )


class Char_delete_added_queue(aEmbedBase):
    async def ko(self, name):
        return discord.Embed(
            title="{} `{}` 캐릭터가 24시간 후에 완전히 지워집니다.".format(
                self.cog.emj.get(self.ctx, "check"), name
            ),
            description=f"24시간 후에 완전히 지워지며, 이 기간 동안에 `{self.cog.prefix}캐릭터 삭제취소` 명령으로 취소가 가능합니다.",
            color=self.cog.color["success"],
        )


class Char_cancel_delete_but_not_being_deleted(aEmbedBase):
    async def ko(self, name):
        return discord.Embed(
            title=f"❓ 삭제중이 아닌 캐릭터입니다: `{name}`",
            description="이 캐릭터는 삭제 중인 캐릭터가 아닙니다.",
            color=self.cog.color["error"],
        )


class Char_cancel_delete_done(aEmbedBase):
    async def ko(self, name):
        return discord.Embed(
            title="{} 캐릭터 삭제를 취소했습니다!: `{}`".format(
                self.cog.emj.get(self.ctx, "check"), name
            ),
            color=self.cog.color["success"],
        )


class Char_changename_cooldown(aEmbedBase):
    async def ko(self, timeleft):
        return discord.Embed(
            title="⏱ 쿨타임 중입니다!",
            description=f"**`{timeleft}` 남았습니다!**\n닉네임은 24시간에 한 번 변경할 수 있습니다.",
            color=self.cog.color["info"],
        )


class Char_changename_name(aEmbedBase):
    async def ko(self, charname):
        return discord.Embed(
            title="🏷 캐릭터 이름 변경",
            description=f"`{charname}` 캐릭터의 이름을 변경합니다. 새 이름을 입력해주세요!\n취소하려면 `취소`를 입력하세요.",
            color=self.cog.color["ask"],
        )


class Char_changename_continue_ask(aEmbedBase):
    async def ko(self, newname):
        return discord.Embed(
            title=f"🏷 `{newname}` 으로 변경할까요?",
            description="변경하면 24시간 후에 다시 변경할 수 있습니다!",
            color=self.cog.color["ask"],
        )


class Char_changename_done(aEmbedBase):
    async def ko(self, newname):
        return discord.Embed(
            title="{} `{}` 으로 변경했습니다!".format(
                self.cog.emj.get(self.ctx, "check"), newname
            ),
            color=self.cog.color["success"],
        )


class Char_logout(aEmbedBase):
    async def ko(self, charname):
        return discord.Embed(
            title="📤 로그아웃",
            description=f"`{charname}` 캐릭터에서 로그아웃할까요?\n`{self.cog.prefix}캐릭터 변경` 명령으로 다시 캐릭터에 접속할 수 있습니다.",
            color=self.cog.color["ask"],
        )


class Char_logout_done(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title="{} 로그아웃했습니다!".format(self.cog.emj.get(self.ctx, "check")),
            description=f"`{self.cog.prefix}캐릭터 변경` 명령으로 다시 캐릭터에 접속할 수 있습니다.",
            color=self.cog.color["success"],
        )


class Char_setting(aEmbedBase):
    async def ko(self, pgr, char, *, mode="default"):
        sdgr = SettingDBMgr(self.cog.datadb)
        smgr = SettingMgr(self.cog.pool, sdgr, char.uid)
        settitles = []
        setvalue = []
        embed = discord.Embed(
            title="⚙ `{}` 캐릭터 설정".format(char.name), color=self.cog.color["info"]
        )
        now = pgr.get_thispage()
        for st in now:
            settitles.append(st.title)
            valuestr = str(await smgr.get_setting(st.name))
            if st.type == bool:
                for x in [("True", "켜짐"), ("False", "꺼짐")]:
                    valuestr = valuestr.replace(x[0], x[1])
            elif st.type == charsettings.Where_to_Levelup_Message:
                for k, v in st.type.selections.items():
                    valuestr = valuestr.replace(str(k), v[1])
            setvalue.append(valuestr)
        if mode == "select":
            embed.title += " - 선택 모드"
            embed.add_field(
                name="번호", value="\n".join(map(str, range(1, len(now) + 1)))
            )
        embed.add_field(name="설정 이름", value="\n".join(settitles))
        embed.add_field(name="설정값", value="\n".join(setvalue))
        return embed


class Char_setting_invalid_index(aEmbedBase):
    async def ko(self):
        embed = discord.Embed(
            title="❓ 설정 번째수가 올바르지 않습니다!",
            description="위 메시지에 항목 앞마다 번호가 붙어 있습니다.",
            color=self.cog.color["error"],
        )
        return embed


class Char_setting_only_number(aEmbedBase):
    async def ko(self):
        embed = discord.Embed(
            title=f"❓ 설정 번째수는 숫자만을 입력해주세요!", color=self.cog.color["error"]
        )
        return embed


class Char_setting_edit(aEmbedBase):
    async def ko(self):
        return discord.Embed(
            title='⚙ 설정 변경 - 항목 선택',
            description='변경할 항목의 번째 수를 입력해주세요.\n또는 ❌ 버튼을 클릭해 취소할 수 있습니다.',
            color=self.cog.color['ask']
        )


class Char_setting_edit_info_bool(aEmbedBase):
    async def ko(self, setting):
        embed = discord.Embed(title='⚙ '+ setting.title, description=setting.description + '\n\n', color=self.cog.color['ask'])
        embed.description += '{}: 켜짐\n{}: 꺼짐'.format(self.cog.emj.get(self.ctx, 'check'), self.cog.emj.get(self.ctx, 'cross'))
        return embed


class Char_setting_edit_whereto_levelup(aEmbedBase):
    async def ko(self, setting):
        embed = discord.Embed(title='⚙ '+ setting.title, description=setting.description + '\n\n', color=self.cog.color['ask'])
        for k, v in setting.type.selections.items():
            embed.description += '{}: {}\n'.format(v[0], v[1])
        return embed


class Char_create_fail(aEmbedBase):
    async def ko(self, exc: CharCreateError):
        if exc.reason == CharCreateErrReasons.InvalidName:
            embed = discord.Embed(
                title="❌ 사용할 수 없는 이름입니다!",
                description="캐릭터 이름은 반드시 한글, 영어, 숫자만을 사용해야 합니다.\n다시 시도해 주세요!",
                color=self.cog.color["error"],
            )
            return embed
        elif exc.reason == CharCreateErrReasons.InvalidLength:
            embed = discord.Embed(
                title="❌ 사용할 수 없는 이름입니다!",
                description="캐릭터 이름은 2~10글자이여야 합니다.\n다시 시도해 주세요!",
                color=self.cog.color["error"],
            )
            return embed
        elif exc.reason == CharCreateErrReasons.NameAlreadyExists:
            embed = discord.Embed(
                title="❌ 이미 사용중인 이름입니다!",
                description="다시 시도해 주세요!",
                color=self.cog.color["error"],
            )
            return embed
        else:
            exc.reason == CharCreateErrReasons.CannotIncludePrefix
            embed = discord.Embed(
                title="❌ 사용할 수 없는 이름입니다!",
                description="아젤리아 봇 접두사는 이름에 포함할 수 없습니다.\n다시 시도해 주세요!",
                color=self.cog.color["error"],
            )
            return embed

