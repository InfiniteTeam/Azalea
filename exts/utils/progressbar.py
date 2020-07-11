import discord
from discord.ext import commands
from exts.utils import emojictrl

def get(ctx: commands.Context, emjctrl: emojictrl.Emoji, value, mx, totallen):
    print(value, mx)
    if mx == 0 or value < 0 or mx < 0:
        colorcount = 0
    else:
        colorcount = round(value/mx*totallen)
    colormid = []
    graymid = []
    end = emjctrl.get(ctx, 'pgb8')
    if colorcount == 0:
        start = emjctrl.get(ctx, 'pgb7')
    elif colorcount == 1:
        start = emjctrl.get(ctx, 'pgb4')
    else:
        start = emjctrl.get(ctx, 'pgb1')
        colormid = [emjctrl.get(ctx, 'pgb2')] * (colorcount-1)
        if totallen == colorcount:
            end = emjctrl.get(ctx, 'pgb3')
            del colormid[-1]
        else:
            colormid[-1] = emjctrl.get(ctx, 'pgb10')
    graymid = [emjctrl.get(ctx, 'pgb5')] * ((totallen) - len(colormid)-2)

    cmstr = ''.join(map(str, colormid))
    gmstr = ''.join(map(str, graymid))

    return str(start) + cmstr + gmstr + str(end)