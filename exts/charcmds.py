# pylint: enable=unused-import
import discord
from discord.ext import commands
from utils.basecog import BaseCog
import typing
import datetime
import asyncio
import aiomysql
import re
from utils import pager, emojibuttons, timedelta, event_waiter
from utils.datamgr import CharMgr, CharacterType, Setting, SettingMgr, SettingDBMgr
from utils.mgrerrors import CharCreateError, CharCreateErrReasons
from db import charsettings

class Charcmds(BaseCog):
    def __init__(self, client):
        super().__init__(client)
        for cmd in self.get_commands():
            cmd.add_check(self.check.registered)
            if cmd.name not in ['캐릭터', '캐생', '로그이웃', '캐삭']:
                cmd.add_check(self.check.char_online)

    @commands.group(name='캐릭터', aliases=['캐'], invoke_without_command=True)
    async def _char(self, ctx: commands.Context, *, user: typing.Optional[discord.User]=None):
        if not user:
            user = ctx.author
        perpage = 5
        cmgr = CharMgr(self.pool)
        chars = await cmgr.get_chars(user.id)
        if not chars:
            if ctx.author.id == user.id:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_no_any_char'))
            else:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_no_any_char_other_user', user))
            return
        pgr = pager.Pager(chars, perpage)
        msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Char', user, pgr))
        self.msglog.log(ctx, '[캐릭터]')
        extemjs = []
        owner = False
        if user.id == ctx.author.id:
            owner = True
            extemjs = ['✨', '🎲']
        extemjs.append('❔')
        emjs = emojibuttons.PageButton.emojis + extemjs
        async def addreaction(m):
            if len(pgr.pages()) == 0:
                return
            elif len(pgr.pages()) <= 1:
                for emj in extemjs:
                    await m.add_reaction(emj)
            else:
                for emj in emjs:
                    await m.add_reaction(emj)
        await addreaction(msg)
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
        while True:
            try:
                reaction, _ = await self.client.wait_for('reaction_add', check=check, timeout=60*5)
            except asyncio.TimeoutError:
                try:
                    await msg.clear_reactions()
                except:
                    pass
            else:
                if reaction.emoji in extemjs:
                    if not ctx.channel.last_message or ctx.channel.last_message_id == msg.id:
                        await msg.edit(embed=await self.embedmgr.get(ctx, 'Char', user, pgr, mode='select'))
                    else:
                        results = await asyncio.gather(
                            msg.delete(),
                            ctx.send(embed=await self.embedmgr.get(ctx, 'Char', user, pgr, mode='select'))
                        )
                        msg = results[1]
                        await addreaction(msg)
                        reaction.message = msg

                if reaction.emoji == '✨' and owner:
                    await self._char_create(ctx)

                elif reaction.emoji == '🎲' and owner:
                    idxmsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_change_select_index'))
                    self.msglog.log(ctx, '[캐릭터: 캐릭터 변경: 번째수 입력]')
                    await idxmsg.add_reaction('❌')
                    canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=idxmsg, emojis=['❌'], timeout=60))
                    indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60, subcheck=lambda m: m.content.isdecimal()))

                    task = await event_waiter.wait_for_first(canceltask, indextask)
                    await idxmsg.delete()
                    if task == indextask:
                        idxtaskrst = indextask.result()
                        if int(idxtaskrst.content) <= len(pgr.get_thispage()):
                            idx = int(idxtaskrst.content) - 1
                            await self._char_change(ctx, name=pgr.get_thispage()[idx].name)

                elif reaction.emoji == '❔':
                    idxmsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_info_select_index'))
                    self.msglog.log(ctx, '[캐릭터: 캐릭터 정보: 번째수 입력]')
                    await idxmsg.add_reaction('❌')
                    canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=idxmsg, emojis=['❌'], timeout=60))
                    indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=60, subcheck=lambda m: m.content.isdecimal()))

                    task = await event_waiter.wait_for_first(canceltask, indextask)
                    await idxmsg.delete()
                    if task == indextask:
                        idxtaskrst = indextask.result()
                        if int(idxtaskrst.content) <= len(pgr.get_thispage()):
                            idx = int(idxtaskrst.content) - 1
                            await self._w_stat(ctx, charname=pgr.get_thispage()[idx].name)

                pgr.set_obj(await cmgr.get_chars(user.id))
                do = await emojibuttons.PageButton.buttonctrl(reaction, user, pgr)
                await asyncio.gather(do,
                    msg.edit(embed=await self.embedmgr.get(ctx, 'Char', user, pgr)),
                )
                    
    async def char_name_check(self, name: str):
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                if name == '취소':
                    return False
                elif not re.match('^[ |가-힣|a-z|A-Z|0-9]+$', name)  or '|' in name:
                    raise CharCreateError(CharCreateErrReasons.InvalidName)
                elif not (2 <= len(name) <= 10):
                    raise CharCreateError(CharCreateErrReasons.InvalidLength)
                elif await cur.execute('select * from chardata where name=%s', name) != 0:
                    raise CharCreateError(CharCreateErrReasons.NameAlreadyExists)
                else:
                    for pfx in self.client.command_prefix:
                        if pfx.rstrip().lower() in name.lower():
                            raise CharCreateError(CharCreateErrReasons.CannotIncludePrefix)

    @_char.command(name='생성')
    async def _char_create(self, ctx:commands.Context):
        cmgr = CharMgr(self.pool)
        charcount = len(await cmgr.get_chars(ctx.author.id))
        if charcount >= self.config['max_charcount']:
            await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_all_slots_full'))
            self.msglog.log(ctx, '[캐릭터 슬롯 부족]')
            return
        namemsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_create_name'))
        self.msglog.log(ctx, '[캐릭터 생성: 이름 짓기]')
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content
        try:
            m = await self.client.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            try:
                await namemsg.delete()
            except:
                pass
        else:
            charname = m.content
                
        try:
            ck = await self.char_name_check(m.content)
        except CharCreateError as exc:
            embed = await self.embedmgr.get(ctx, 'Char_create_fail', exc)
            if embed is not None:
                await ctx.send(embed=embed)
                self.msglog.log(ctx, '[캐릭터 생성: 이름 짓기: 이름 짓기 검사]')
                return
        else:
            try:
                await namemsg.delete()
            except:
                pass

            if ck is False:
                return
        
        typemsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_create_job', charname))
        emjs = ['⚔', '🏹', '🔯', '❌']
        for em in emjs:
            await typemsg.add_reaction(em)
        def rcheck(reaction, user):
            return user == ctx.author and typemsg.id == reaction.message.id and reaction.emoji in emjs
        self.msglog.log(ctx, '[캐릭터 생성: 직업 선택]')
        try:
            reaction, user = await self.client.wait_for('reaction_add', check=rcheck, timeout=20)
        except asyncio.TimeoutError:
            try:
                await typemsg.delete()
            except:
                pass    
        else:
            await typemsg.delete()
            e = reaction.emoji
            if e == '❌':
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Canceled', 7), delete_after=7)
                self.msglog.log(ctx, '[캐릭터 생성: 직업 선택: 취소됨]')
                return
            elif e == '⚔':
                chartype = CharacterType.Knight.name
            elif e == '🏹':
                chartype = CharacterType.Archer.name
            elif e == '🔯':
                chartype = CharacterType.Wizard.name
            
            charcount = len(await cmgr.get_chars(ctx.author.id))
            if charcount >= self.config['max_charcount']:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_all_slots_full'))
                self.msglog.log(ctx, '[캐릭터 생성: 슬롯 부족]')
                return
            
            try:
                char = await cmgr.add_character_with_raw(ctx.author.id, charname, chartype, check=self.char_name_check(charname))
            except CharCreateError as exc:
                embed = await self.embedmgr.get(ctx, 'Char_create_fail', exc)
                if embed is not None:
                    await ctx.send(embed=embed)
                    self.msglog.log(ctx, '[캐릭터 생성: 이름 짓기: 이름 짓기 검사]')
                    return
                
            if charcount == 0:
                await cmgr.change_character(ctx.author.id, char.uid)
            await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_create_done', charcount, charname))
            self.msglog.log(ctx, '[캐릭터 생성: 완료]')

    @_char.command(name='변경', aliases=['선택', '변', '선'])
    async def _char_change(self, ctx: commands.Context, *, name):
        cmgr = CharMgr(self.pool)
        char = list(filter(lambda x: x.name.lower() == name.lower(), await cmgr.get_chars(ctx.author.id)))
        if char:
            cname = char[0].name
            if not char[0].online:
                if not await cmgr.is_being_forgotten(char[0].uid):
                    await cmgr.change_character(ctx.author.id, char[0].uid)
                    await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_change_done', cname))
                    self.msglog.log(ctx, '[캐릭터 변경: 완료]')
                else:
                    await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_change_but_being_deleted', cname))
                    self.msglog.log(ctx, '[캐릭터 변경: 삭제 중인 캐릭터]')
            else:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_change_but_already_current', cname))
                self.msglog.log(ctx, '[캐릭터 변경: 이미 현재 캐릭터]')
        else:
            await ctx.send(embed=await self.embedmgr.get(ctx, 'CharNotFound', name))
            self.msglog.log(ctx, '[캐릭터 변경: 존재하지 않는 캐릭터]')

    @_char.command(name='삭제', aliases=['삭'])
    async def _char_delete(self, ctx: commands.Context, *, name):
        cmgr = CharMgr(self.pool)
        char = list(filter(lambda x: x.name.lower() == name.lower(), await cmgr.get_chars(ctx.author.id)))
        if not char:
            await ctx.send(embed=await self.embedmgr.get(ctx, 'CharNotFound', name))
            self.msglog.log(ctx, '[캐릭터 삭제: 존재하지 않는 캐릭터]')
            return
        cname = char[0].name
        if await cmgr.is_being_forgotten(char[0].uid):
            await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_delete_already_queued', cname))
            self.msglog.log(ctx, '[캐릭터 삭제: 이미 삭제 요청됨]')
            return
        msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_delete_ask', cname))
        emjs = ['⭕', '❌']
        for em in emjs:
            await msg.add_reaction(em)
        self.msglog.log(ctx, '[캐릭터 삭제: 캐릭터 삭제 경고]')
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=20, check=check)
        except asyncio.TimeoutError:
            try:
                await msg.delete()
            except:
                pass
        else:
            remj = reaction.emoji
            if remj == '⭕':
                await cmgr.schedule_delete(ctx.author.id, char[0].uid)
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_delete_added_queue', cname))
                self.msglog.log(ctx, '[캐릭터 삭제: 삭제 작업 예약됨]')
            elif remj == '❌':
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Canceled'))
                self.msglog.log(ctx, '[캐릭터 삭제: 취소됨]')

    @_char.command(name='삭제취소')
    async def _char_cancel_delete(self, ctx: commands.Context, *, name):
        cmgr = CharMgr(self.pool)
        char = list(filter(lambda x: x.name.lower() == name.lower(), await cmgr.get_chars(ctx.author.id)))
        if not char:
            await ctx.send(embed=await self.embedmgr.get(ctx, 'CharNotFound', name))
            self.msglog.log(ctx, '[캐릭터 삭제취소: 존재하지 않는 캐릭터]')
            return
        cname = char[0].name
        if not await cmgr.is_being_forgotten(char[0].uid):
            await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_cancel_delete_but_not_being_deleted', cname))
            self.msglog.log(ctx, '[캐릭터 삭제취소: 삭제중이 아닌 캐릭터]')
            return
        await cmgr.cancel_delete(char[0].uid)
        await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_cancel_delete_done', cname))
        self.msglog.log(ctx, '[캐릭터 삭제취소: 삭제 취소 완료]')
        return

    @_char.command(name='정보', aliases=['스탯', '능력치'])
    async def _w_stat(self, ctx: commands.Context, charname: typing.Optional[str] = None):
        cmd = self.client.get_command('내정보')
        await cmd(ctx, charname)

    @commands.command(name='캐생', aliases=['새캐'])
    async def _w_char_create(self, ctx: commands.Context):
        await self._char_create(ctx)

    @commands.command(name='캐삭')
    async def _w_char_delete(self, ctx: commands.Context, *, name):
        await self._char_delete(ctx, name=name)

    @_char_change.error
    @_char_delete.error
    @_w_char_delete.error
    @_char_cancel_delete.error
    async def _e_char(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'name':
                missing = '캐릭터의 이름'
            await ctx.send(embed=await self.embedmgr.get(ctx, 'MissingArgs', missing))

    @_char.command(name='이름변경', aliases=['닉변'])
    async def _char_changename(self, ctx: commands.Context, *, charname: typing.Optional[str]):
        cmgr = CharMgr(self.pool)
        if charname:
            char = await cmgr.get_character_by_name(charname, ctx.author.id)
            if not char:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'CharNotFound', charname))
                self.msglog.log(ctx, '[이름변경: 존재하지 않는 캐릭터]')
                return
        else:
            char = await cmgr.get_current_char(ctx.author.id)

        if char.last_nick_change is not None:
            td = datetime.datetime.now() - char.last_nick_change
            if td <= datetime.timedelta(days=1):
                cldstr = ' '.join(timedelta.format_timedelta(datetime.timedelta(days=1) - td).values())
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_changename_cooldown', cldstr))
                self.msglog.log(ctx, '[이름변경: 쿨다운 중]')
                return
        namemsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_changename_name', char.name))
        self.msglog.log(ctx, '[이름변경]')
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content
        try:
            m = await self.client.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            try:
                await namemsg.delete()
            except:
                pass
            self.msglog.log(ctx, '[이름변경: 시간 초과]')
        else:
            newname = m.content
            
            try:
                ck = await self.char_name_check(m.content)
            except CharCreateError as exc:
                embed = await self.embedmgr.get(ctx, 'Char_create_fail', exc)
                if embed is not None:
                    await ctx.send(embed=embed)
                    self.msglog.log(ctx, '[이름변경: 이름 짓기 검사]')
                    return
            else:
                try:
                    await namemsg.delete()
                except: pass
                if ck is False:
                    return
            
            msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_changename_continue_ask', newname))
            emjs = ['⭕', '❌']
            for em in emjs:
                await msg.add_reaction(em)
            def oxcheck(reaction, user):
                return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
            try:
                reaction, user = await self.client.wait_for('reaction_add', check=oxcheck, timeout=20)
            except asyncio.TimeoutError:
                try:
                    await msg.clear_reactions()
                except:
                    pass
            else:
                if reaction.emoji == '⭕':
                    await cmgr.change_nick(char.uid, newname)
                    await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_changename_done', newname))
                    self.msglog.log(ctx, '[이름변경: 완료]')
                elif reaction.emoji == '❌':
                    await ctx.send(embed=await self.embedmgr.get(ctx, 'Canceled'))
                    self.msglog.log(ctx, '[이름변경: 취소됨]')

    @commands.command(name='닉변')
    async def _w_char_changename(self, ctx: commands.Context, *, charname: typing.Optional[str]):
        await self._char_changename(ctx, charname=charname)

    @commands.command(name='로그아웃')
    async def _logout(self, ctx: commands.Context):
        cmgr = CharMgr(self.pool)
        char = await cmgr.get_current_char(ctx.author.id)
        msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_logout', char.name))
        self.msglog.log(ctx, '[로그아웃]')
        emjs = ['⭕', '❌']
        for em in emjs:
            await msg.add_reaction(em)
        def oxcheck(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
        try:
            reaction, user = await self.client.wait_for('reaction_add', check=oxcheck, timeout=20)
        except asyncio.TimeoutError:
            try:
                await msg.clear_reactions()
            except:
                pass
        else:
            if reaction.emoji == '⭕':
                await cmgr.logout_all(ctx.author.id)
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_logout_done'))
                self.msglog.log(ctx, '[로그아웃: 완료]')
            elif reaction.emoji == '❌':
                await ctx.send(embed=await self.embedmgr.get(ctx, 'Canceled'))
                self.msglog.log(ctx, '[로그아웃: 취소됨]')

    @_char.command(name='설정', aliases=['셋', '설'])
    async def _char_settings(self, ctx: commands.Context, *, charname: typing.Optional[str]=None):
        perpage = 8
        cmgr = CharMgr(self.pool)
        if charname:
            char = await cmgr.get_character_by_name(charname, ctx.author.id)
            if not char:
                await ctx.send(embed=await self.embedmgr.get(ctx, 'CharNotFound', charname))
                return
        else:
            char = await cmgr.get_current_char(ctx.author.id)

        sdgr = SettingDBMgr(self.datadb)
        smgr = SettingMgr(self.pool, sdgr, char.uid)
        pgr = pager.Pager(self.datadb.char_settings, perpage)
        
        msg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_setting', pgr, char))
        extemjs = ['✏']
        if len(pgr.pages()) <= 1:
            emjs = extemjs
        else:
            emjs = emojibuttons.PageButton.emojis + extemjs
        async def addreaction(msg):
            for em in emjs:
                await msg.add_reaction(em)
        await addreaction(msg)
        def check(reaction, user):
            return user == ctx.author and msg.id == reaction.message.id and reaction.emoji in emjs
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', check=check, timeout=60*5)
            except asyncio.TimeoutError:
                try:
                    await msg.clear_reactions()
                except:
                    pass
            else:
                if reaction.emoji in extemjs:
                    if not ctx.channel.last_message or ctx.channel.last_message_id == msg.id:
                        await msg.edit(embed=await self.embedmgr.get(ctx, 'Char_setting', pgr, char, mode='select'))
                    else:
                        results = await asyncio.gather(
                            msg.delete(),
                            ctx.send(embed=await self.embedmgr.get(ctx, 'Char_setting', pgr, char, mode='select'))
                        )
                        msg = results[1]
                        await addreaction(msg)
                        reaction.message = msg
                if reaction.emoji == '✏':
                    idxmsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_setting_edit'))
                    self.msglog.log(ctx, '[설정: 변경: 번째수 입력]')
                    await idxmsg.add_reaction('❌')
                    canceltask = asyncio.create_task(event_waiter.wait_for_reaction(self.client, ctx=ctx, msg=idxmsg, emojis=['❌'], timeout=20))
                    indextask = asyncio.create_task(event_waiter.wait_for_message(self.client, ctx=ctx, timeout=20))
                    
                    task = await event_waiter.wait_for_first(canceltask, indextask)
                    await idxmsg.delete()
                    if task == indextask:
                        idxtaskrst = indextask.result()
                        if idxtaskrst.content.isdecimal():
                            if 1 <= int(idxtaskrst.content) <= len(pgr.get_thispage()):
                                idx = int(idxtaskrst.content)-1
                                setting: Setting = pgr.get_thispage()[idx]
                                
                                if setting.type == bool:
                                    editmsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_setting_edit_info_bool', setting))
                                    editemjs = [self.emj.get(ctx, 'check'), self.emj.get(ctx, 'cross')]
                                    for em in editemjs:
                                        await editmsg.add_reaction(em)
                                    def onoff_check(reaction, user):
                                        return user == ctx.author and editmsg.id == reaction.message.id and reaction.emoji in editemjs
                                    try:
                                        rct, usr = await self.client.wait_for('reaction_add', check=onoff_check, timeout=60*2)
                                    except asyncio.TimeoutError:
                                        try:
                                            await editmsg.clear_reactions()
                                        except:
                                            pass
                                    else:
                                        if rct.emoji == editemjs[0]:
                                            await smgr.edit_setting(setting.name, True)
                                        elif rct.emoji == editemjs[1]:
                                            await smgr.edit_setting(setting.name, False)
                                elif setting.type == charsettings.Where_to_Levelup_Message:
                                    editopts = {}
                                    for k, v in setting.type.selections.items():
                                        editopts[v[0]] = k
                                    editmsg = await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_setting_edit_whereto_levelup', setting))
                                    for em in editopts.keys():
                                        await editmsg.add_reaction(em)
                                    def opt_check(reaction, user):
                                        return user == ctx.author and editmsg.id == reaction.message.id and reaction.emoji in editopts
                                    try:
                                        rct, usr = await self.client.wait_for('reaction_add', check=opt_check, timeout=60*2)
                                    except asyncio.TimeoutError:
                                        try:
                                            await editmsg.clear_reactions()
                                        except:
                                            pass
                                    else:
                                        await smgr.edit_setting(setting.name, editopts[rct.emoji])
                                    
                                await editmsg.delete()
                            else:
                                await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_setting_invalid_index', 7), delete_after=7)
                                self.msglog.log(ctx, '[설정: 변경: 올바르지 않은 번째수]')
                        else:
                            await ctx.send(embed=await self.embedmgr.get(ctx, 'Char_setting_only_number', 7), delete_after=7)
                            self.msglog.log(ctx, '[설정: 변경: 숫자만 입력]')

                if charname:
                    char = await cmgr.get_character_by_name(charname, ctx.author.id)
                    if not char:
                        await ctx.send(embed=await self.embedmgr.get(ctx, 'CharNotFound', charname))
                        return
                else:
                    char = await cmgr.get_current_char(ctx.author.id)
                
                do = await emojibuttons.PageButton.buttonctrl(reaction, user, pgr)
                if asyncio.iscoroutine(do):
                    await asyncio.gather(do,
                        msg.edit(embed=await self.embedmgr.get(ctx, 'Char_setting', pgr, char))
                    )

def setup(client):
    cog = Charcmds(client)
    client.add_cog(cog)