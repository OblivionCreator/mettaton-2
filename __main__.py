import glob
import math
import os
import random
from pathlib import Path
from discord.ext import tasks
from datetime import datetime
import discord
from discord.ext import commands
import sqlite3
from sqlite3 import Error
from collections.abc import Sequence
import ast
from dataclasses import dataclass
import time
import json
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from discord import HTTPException
from discord.utils import get
from configparser import ConfigParser
from resources import getdiff, webhook_manager
import validators

intents = discord.Intents.default()
intents.members = True

backupOngoing = False

gauth = GoogleAuth()
gauth.LoadCredentialsFile("credentials.txt")
if gauth.credentials is None:

    gauth.GetFlow()
    gauth.flow.params.update({'access_type': 'offline'})
    gauth.flow.params.update({'approval_prompt': 'force'})

    gauth.LocalWebserverAuth()

elif gauth.access_token_expired:
    gauth.Refresh()
else:
    gauth.Authorize()
gauth.SaveCredentialsFile("credentials.txt")

drive = GoogleDrive(gauth)


def getConfig():
    try:
        with open('.config', 'r') as file:
            jsonOBJ = json.load(file)
            file.close()
    except FileNotFoundError:
        return False
    return jsonOBJ


def getLang(section, line):
    conf = getConfig()

    if conf == False:
        dir = "translation/lang_en.ini"
    else:
        dir = conf["language"]

    lang = ConfigParser()

    lang.read(dir)

    lineStr = lang.get(section, line)

    return lineStr


def configFields():
    curConfig = {
        'gmchannel': 0,
        'logchannel': 0,
        'autobackup': 0,
        'language': 'translation/lang_en.ini',
        'denylist': [],
        'allowprefilled': True
    }
    return curConfig


async def configLoader():
    try:
        with open('.config') as file:
            print("Loading Config...")

            conf = getConfig()
            confTemplate = configFields()

            for i in conf:
                confTemplate[i] = conf[i]

            gmchannel = bot.get_channel(GMChannel())
            logchannel = bot.get_channel(LogChannel())

            validGMChannel = True

            try:
                await logchannel.send(getLang("Log", "lg_1"))
            except:
                print(getLang("Log", "lg_2"))
                validGMChannel = False

            try:
                await logchannel.send(getLang("Log", "lg_3"))
            except:
                if validGMChannel:
                    gmc = await bot.get_channel(GMChannel())
                    await gmc.send(getLang("Log", "lg_4"))
                else:
                    print(getLang("Log", "lg_4"))
        file = open('.config', "w")
        file.write(json.dumps(confTemplate))
        file.close()

    except (FileNotFoundError, IOError):

        print(getLang("Log", "lg_5"))

        file = open('.config', 'x')

        configDict = configFields()

        cfgJson = json.dumps(configDict)

        file.write(cfgJson)

        print(getLang("Log", "lg_6"))


cst_prefix = getLang("Commands", "prefix")

bot = commands.Bot(
    command_prefix=['mtt!', 'Rp!', 'RP!', 'rP!', cst_prefix],
    intents=intents, case_insensitive=True)
bot.remove_command("help")
guild_ids = [770428394918641694]
currentlyRegistering = []


def GMChannel():
    conf = getConfig()
    return int(conf["gmchannel"])


def LogChannel():
    conf = getConfig()
    return int(conf["logchannel"])


def doBackup():
    conf = getConfig()
    return int(conf["autobackup"])


def allowPrefilled():
    conf = getConfig()
    print(bool(conf["allowprefilled"]))
    return bool(conf["allowprefilled"])


@commands.is_owner()
@bot.command(name=getLang("Commands", "clearconfig"))
async def clearconfig(ctx):
    config = configFields()

    file = open('.config', 'w')

    configDict = configFields()

    cfgJson = json.dumps(configDict)

    file.write(cfgJson)

    await ctx.send(getLang("ClearConfig", "cc_1"))
    return


# Deny List Handling

def getDenyList():
    conf = getConfig()
    return conf["denylist"]


# Returns current Deny List

@bot.command(name=getLang("Commands", "up_de"))
async def update_deny(ctx, act, term=''):
    term = term.lower()

    if not await checkGM(ctx):
        await ctx.send(getLang("DenyList", "dl_1"))
        return

    if act.lower() == 'list':
        await ctx.send(f"{getLang('DenyList', 'dl_2')}\n{listDeny()}")
        return

    if act == 'add':

        if term == '':
            await ctx.send(getLang("DenyList", "dl_3"))

        addSt = addDeny(term)
        if addSt == False:
            await ctx.send(getLang("DenyList", "dl_4"))
            return
        await ctx.send(getLang("DenyList", "dl_5").format(term))
        return

    if act.lower() == 'remove':

        if term == '':
            await ctx.send(getLang("DenyList", "dl_3"))

        if delDeny(term) == False:
            await ctx.send(getLang("DenyList", "dl_6"))
            return
        await ctx.send(getLang("DenyList", "dl_7").format(term))
        return

    await ctx.send(getLang("DenyList", "dl_8"))


def listDeny():
    denyList = getDenyList()

    if len(denyList) == 0:
        return getLang("DenyList", "dl_9")

    denySTR = ''

    for d in denyList:
        denySTR = f"{d}, {denySTR}"

    return denySTR


def addDeny(term):
    conf = getConfig()
    denyList = getDenyList()

    if term in denyList:
        return False

    denyList.append(term)
    conf["denylist"] = denyList

    with open('.config', 'w') as f:
        json.dump(conf, f)
        f.close()

    return True


def delDeny(term):
    conf = getConfig()
    denyList = getDenyList()

    if term not in denyList:
        return False

    denyList.remove(term)
    conf["denylist"] = denyList

    with open('.config', 'w') as f:
        json.dump(conf, f)
        f.close()

    return True

@bot.event
async def on_ready():
    await configLoader()
    changeStatus.start()
    autoBackup.start()

def create_connection(db_file):
    conn = None
    try:

        file = Path(database)

        if file.is_file():
            conn = sqlite3.connect(db_file)
        else:
            print(getLang("Log", "lg_7"))
            conn = sqlite3.connect(db_file)
            cur = conn.cursor()
            sql = '''CREATE TABLE "charlist" (
    "charID"    INTEGER NOT NULL UNIQUE,
    "owner"    TEXT NOT NULL,
    "status"    TEXT NOT NULL,
    "name"    TEXT NOT NULL,
    "age"    TEXT,
    "gender"    TEXT,
    "abil"    TEXT,
    "appear"    TEXT,
    "backg"    TEXT,
    "person"    TEXT,
    "prefilled"    TEXT,
    "misc"    TEXT,
    PRIMARY KEY("charID")
)'''
            cur.execute(sql)
            conn.commit()

        print(sqlite3.version)
    except Error as e:
        print(getLang("Log", "lg_8") + {str(e)})

    return conn


def clearLog():  # Deletes all files in charoverflow.
    files = glob.glob('charoverflow/*')
    for f in files:
        print(f)
        os.remove(f)


file = open("token.txt")
token = file.read()


def close_connection(db_file):
    conn.close()


database = "mttchars.db"
conn = create_connection(database)


@bot.check
async def globally_block_dms(ctx):
    if ctx.guild is None and ctx.author.id not in currentlyRegistering:
        await ctx.author.send(getLang("Misc", "dm_response"))
    return ctx.guild is not None


@bot.check
async def globally_block_roles(ctx):
    blacklist = [getLang("Misc", "npc")]
    return not any(get(ctx.guild.roles, name=name) in ctx.author.roles for name in blacklist)


@bot.check
async def block_during_backup(ctx):
    return not backupOngoing


@bot.check
async def block_help(ctx):
    if await checkGM(ctx):
        return True
    if ctx.channel.name == 'help':
        await ctx.send(getLang("Misc", "helpBlock"))
        return False
    else:
        return True


async def charadd(owner, name, age='', gender='', abil='', appear='', backg='', person='', prefilled='',
                  status='Pending', charID=''):
    character = (owner, status, name, age, gender, abil, appear, backg, person, prefilled)

    """
    :param conn:
    :param character:
    :return: charID
    """

    if charID == '':
        charFinal = character + ('{}',)
        sql = '''INSERT INTO charlist(owner,status,name,age,gender,abil,appear,backg,person,prefilled,misc) VALUES(?,?,?,?,?,?,?,?,?,?,?)'''
        cur = conn.cursor()
        cur.execute(sql, charFinal)
        conn.commit()
        return cur.lastrowid
    else:

        charwid = character + (int(charID),)
        sql = '''UPDATE charlist SET owner=?,status=?,name=?,age=?,gender=?,abil=?,appear=?,backg=?,person=?,prefilled=? WHERE charID=?'''
        cur = conn.cursor()
        cur.execute(sql, charwid)
        conn.commit()
        return cur.lastrowid


async def charModify(field, fieldData):
    """
    :param conn:
    :param field:
    :param fieldData:
    :return:
    """

    sql = '''INSERT INTO charlist(owner,status,name,age,gender,abil,appear,backg,person,prefilled) VALUES(?,?,?,?,?,?,?,?,?,?)'''

    cur = conn.cursor()
    cur.execute(sql, )


def make_sequence(seq):
    if seq is None:
        return ()
    if isinstance(seq, Sequence) and not isinstance(seq, str):
        return seq
    else:
        return seq,


def message_check(channel=None, author=None, content=None, ignore_bot=True, lower=True):
    channel = make_sequence(channel)
    author = make_sequence(author)
    content = make_sequence(content)
    if lower:
        content = tuple(c.lower() for c in content)

    def check(message):
        if ignore_bot and message.author.bot:
            return False
        if channel and message.channel not in channel:
            return False
        if author and message.author not in author:
            return False
        actual_content = message.content.lower() if lower else message.content
        if content and actual_content not in content:
            return False
        return True

    return check


@bot.command(name=getLang("Commands", "setgm"))
async def _setGMCChannel(ctx):
    role_names = [role.name for role in ctx.author.roles]

    if not await checkGM(ctx):
        await ctx.send(getLang("GMChannel", "gmc_1"))
        return

    updateConfig('gmchannel', ctx.channel.id)

    await ctx.send(getLang("GMChannel", "gmc_2"))


@bot.command(name=getLang("Commands", "setlog"))
async def _setLogChannel(ctx):
    if not await checkGM(ctx):
        await ctx.send(getLang("LogChannel", "lc_1"))
        return

    updateConfig('logchannel', ctx.channel.id)
    await ctx.send(getLang("LogChannel", "lc_2"))


def updateConfig(field, value):
    with open('.config', 'r') as file:
        jsonOBJ = json.load(file)
        file.close()

    jsonOBJ[field] = value

    with open('.config', 'w') as file:
        json.dump(jsonOBJ, file)


statuses = {
    getLang("Status", "cmd_st_0"): getLang("Status", "conv_st_0"),
    getLang("Status", "cmd_st_1"): getLang("Status", "conv_st_1"),
    getLang("Status", "cmd_st_2"): getLang("Status", "conv_st_2"),
    getLang("Status", "cmd_st_3"): getLang("Status", "conv_st_2"),
    getLang("Status", "cmd_st_4"): getLang("Status", "conv_st_4")
}


@bot.command(aliases=[getLang("Status", "cmd_st_3")])
async def bp(ctx, charID):
    ctx.invoked_with = getLang("Status", "cmd_st_3")
    await approve(ctx, charID, reason=getLang("Status", "st_1").format(charID))


@bot.command(name=getLang("Status", "cmd_st_1"),
             aliases=[getLang("Status", "cmd_st_0"), getLang("Status", "cmd_st_2"), getLang("Status", "cmd_st_4")])
async def approve(ctx, charID, *, reason: str = ''):
    if reason == '' and not ctx.message.attachments:
        reason = getLang("Status", "st_2")
    if len(reason) > 1750:
        await ctx.send(getLang("Status", "st_3"))
        return
    await _changeStatus(ctx, charID=charID, charStatus=statuses[ctx.invoked_with], reason=reason)


async def checkGM(ctx):
    role_names = [role.name for role in ctx.author.roles]
    if getLang("Misc", "gm") not in role_names:
        return False
    else:
        return True


async def alertUser(ctx, charID, status, reason):
    charData = _getCharDict(charID)

    ownerID = charData["owner"]
    name = charData["name"]

    user = ctx.guild.get_member(int(ownerID))

    if user == None:
        await ctx.send(getLang("Status", "st_4"))
        return

    try:
        await user.send(getLang("Status", "st_5").format(charID, name[0:100], status, ctx.author.mention, reason))
    except Exception:
        await ctx.send(getLang("Status", "st_6").format(charID))


async def _changeStatus(ctx, charID='', charStatus='Pending', reason=''):
    if not await checkGM(ctx):
        await ctx.send(getLang("Status", "st_7"))
        return

    if charID.isnumeric():
        charInt = int(charID)
    else:
        await ctx.send(getLang("Status", "st_8"))
        return

    if ctx.message.attachments:
        reason = f"{reason}\n{str(ctx.message.attachments[0].url)}"

    cursor = conn.cursor()
    sql = '''UPDATE charlist SET status = ? WHERE charID is ?'''
    cursor.execute(sql, [charStatus, charInt])
    conn.commit()

    if charStatus == getLang("Status", "conv_st_1"):
        charData = _getCharDict(charInt)
        userid = charData["owner"]
        user = ctx.guild.get_member(int(userid))
        role = get(ctx.guild.roles, name=getLang("Misc", "rp"))
        await user.add_roles(role)

    await alertUser(ctx, charInt, charStatus, reason)
    await ctx.send(getLang("Status", "st_9").format(charID, charStatus))
    logChannel = bot.get_channel(LogChannel())
    await logChannel.send(getLang("Status", "st_10").format(ctx.author, charInt, charStatus, reason))


async def reRegister(ctx, charID):
    cursor = conn.cursor()
    cursor.execute(f"SELECT owner FROM charlist WHERE charID IS {charID} AND status IS NOT 'Disabled'")

    owner = cursor.fetchone()

    if owner is None:
        await ctx.send(getLang("Register", "rg_1"))
        return
    else:
        ownerP = owner[0]

    if int(ownerP) != ctx.author.id:
        await logMSG(getLang("Log", "lg_9").format(ctx.author.id, ownerP))
        await ctx.send(getLang("Register", "rg_2"))
        return

    charData = _getCharDict(int(charID))

    if charData == 'INVALID CHARACTER':
        ctx.send(getLang("Register", "rg_1"))

    cfields = {
        getLang("Fields", "name"): '',
        getLang("Fields", "gender"): '',
        getLang("Fields", "age"): '',
        getLang("Fields", "abilities/tools"): '',
        getLang("Fields", "appearance"): '',
        getLang("Fields", "background"): '',
        getLang("Fields", "personality"): '',
        getLang("Fields", "prefilled"): '',
    }

    owner = charData[getLang("Fields", "owner")]
    status = charData[getLang("Fields", "status")]
    cfields[getLang("Fields", "name")] = charData["name"]
    cfields[getLang("Fields", "age")] = charData["age"]
    cfields[getLang("Fields", "gender")] = charData["gender"]
    cfields[getLang("Fields", "abilities/tools")] = charData["abilities/tools"]
    cfields[getLang("Fields", "appearance")] = charData["appearance"]
    cfields[getLang("Fields", "background")] = charData["background"]
    cfields[getLang("Fields", "personality")] = charData["personality"]
    cfields[getLang("Fields", "prefilled")] = charData["prefilled"]

    embedV = await _view(ctx, charID, dmchannel=True, returnEmbed=True)

    try:
        await ctx.author.send(getLang("Register", "rg_3"), embed=embedV)
    except:
        filePath = charToTxt(charID=charData["charID"],
                             owner=charData[getLang("Fields", "owner")],
                             status=charData[getLang("Fields", "status")],
                             name=charData[getLang("Fields", "name")], age=charData[getLang("Fields", "age")],
                             gender=charData[getLang("Fields", "gender")],
                             abil=charData[getLang("Fields", "abilities/tools")],
                             appear=charData[getLang("Fields", "appearance")],
                             backg=charData[getLang("Fields", "background")],
                             person=charData[getLang("Fields", "personality")],
                             prefilled=charData[getLang("Fields", "prefilled")], ctx=ctx)
        charFile = open(filePath, 'r')

        try:
            await ctx.author.send(getLang("Register", "rg_3"), file=discord.File(filePath))
        except:
            await ctx.send(getLang("Register", "rg_4"))
            return
        charFile.close()
        clearLog()

    await ctx.send(getLang("Register", "rg_5"))

    user = ctx.author
    registerLoop = True

    while (registerLoop):

        blankList = []
        fullList = []
        blankFields = ''
        fullFields = ''

        for i in cfields:
            temp = cfields.get(i)
            if temp == '' or temp is None:
                blankList.append(i)
            else:
                fullList.append(i)

        if not allowPrefilled():
            if getLang("Fields", "prefilled") in blankList:
                blankList.remove(getLang("Fields", "prefilled"))

        for i in blankList:
            blankFields = f"{blankFields} `{i.capitalize()}`,"

        for i in fullList:
            fullFields = f"{fullFields} `{i.capitalize()}`,"

        presfields = ''

        if not blankFields == '':
            presfields = "\n" + getLang("Register", "rg_6").format(blankFields)

        await user.send(getLang("Register", "rg_7").format(fullFields, presfields))

        field = await getdm(ctx)
        selector = field.lower()

        if selector == getLang("Fields", "prefilled") and selector not in fullList and not allowPrefilled():
            await user.send(getLang("Register", "rg_13"))
        elif selector in cfields:
            await user.send(getLang("Register", "rg_8").format(selector.capitalize()))
            cfields[selector] = await getdm(ctx)
            await user.send(getLang("Register", "rg_9").format(selector.capitalize()))
        elif selector == getLang("Fields", "preview"):
            try:
                await user.send(embed=previewChar(cfields=cfields, prefilled=None, name=cfields['name']))
            except:
                previewTxt = charToTxt(charID=0, owner=ctx.author.id, status='Preview',
                                       name=cfields[getLang("Fields", "name")],
                                       age=cfields[getLang("Fields", "age")],
                                       gender=cfields[getLang("Fields", "gender")],
                                       abil=cfields[getLang("Fields", "abilities/tools")],
                                       appear=cfields[getLang("Fields", "appearance")],
                                       backg=cfields[getLang("Fields", "background")],
                                       person=cfields[getLang("Fields", "personality")],
                                       prefilled=cfields[getLang("Fields", "prefilled")], ctx=ctx)

                await user.send(getLang("Register", "rg_10"), file=discord.File(previewTxt))
        elif selector == 'done':

            await user.send(getLang("Register", "rg_11").format(charID))
            oldchr = _getCharDict(charID=charID)
            resub = await charadd(owner=owner, name=cfields[getLang("Fields", "name")],
                                  age=cfields[getLang("Fields", "age")],
                                  gender=cfields[getLang("Fields", "gender")],
                                  abil=cfields[getLang("Fields", "abilities/tools")],
                                  appear=cfields[getLang("Fields", "appearance")],
                                  backg=cfields[getLang("Fields", "background")],
                                  person=cfields[getLang("Fields", "personality")],
                                  prefilled=cfields[getLang("Fields", "prefilled")], charID=charID)
            await alertGMs(ctx, charID, resub=True, old=oldchr)
            registerLoop = False
            return
        elif selector == getLang("Register", "rg_24"):
            await user.send(getLang("Register", "rg_12"))
            return
        else:
            await user.send(getLang("Register", "rg_13"))


@bot.command(pass_context=True, name=getLang("Commands", "reg"),
             aliases=[getLang("Commands", "rereg"), 'submit', 'resubmit'])
async def register(ctx, charID=''):
    if ctx.author.id in currentlyRegistering:
        await ctx.send(getLang("Register", "rg_14"))
        return

    currentlyRegistering.append(ctx.author.id)

    if charID.isnumeric():
        await reRegister(ctx, charID)
        currentlyRegistering.remove(
            ctx.author.id)  # Fixed Bug with sending 'Please check your DMs!' as well as 'You do not own this character!' - Thanks @Venom134
        return

    await ctx.send(getLang("Register", "rg_5"))

    await logMSG(getLang("Log", "lg_10").format(ctx.author))
    user = ctx.author
    try:
        sendStr = f'{getLang("Register", "rg_15")}\n'
        if allowPrefilled():
            sendStr = f'{sendStr}{getLang("Register", "rg_15_1")}\n'
        sendStr = f'{sendStr}{getLang("Register", "rg_15_2")}'
        await user.send(sendStr)
    except:
        await ctx.send(getLang("Register", "rg_4"))
        currentlyRegistering.remove(user.id)
        return
    await _registerChar(ctx, user)


async def alertGMs(ctx, charID, resub=False, old=None):
    embedC = await _view(ctx, idinput=str(charID), returnEmbed=True)

    ping = True

    if old:
        if old[getLang("Fields", "status")] == getLang("Status", "conv_st_0"):
            ping = False

    embedC.set_footer(text=getLang("Register", "rg_16").format(charID))

    channelID = GMChannel()

    channel = bot.get_channel(channelID)

    isResubmit = ''

    if resub is True:
        isResubmit = f'\n{getLang("Register", "rg_17").format(charID)}'

        new = _getCharDict(charID)
        newStr = ''
        oldStr = ''
        for o in old:
            oldStr = f"{oldStr}\n{o}: {old[o]}"
        for n in new:
            newStr = f"{newStr}\n{n}: {new[n]}"
        differences = getdiff.getDiffCheck(oldStr, newStr)
        isResubmit = f"{isResubmit}\n({getLang('Register', 'rg_38')} {differences})\n"

    else:
        isResubmit = ''

    GMRole = discord.utils.get(ctx.guild.roles, name=getLang("Misc", "gm"))

    try:
        if ping:
            await channel.send(getLang("Register", "rg_18").format(GMRole.id, isResubmit, ctx.author, ctx.author.id),
                               embed=embedC)
        else:
            await channel.send(getLang("Register", "rg_18_1").format(isResubmit, ctx.author, ctx.author.id),
                               embed=embedC)

    except HTTPException as e:

        charData = _getCharDict(charID)

        charJS = json.loads(charData["misc"])
        charSTR = ''

        for name, value in charJS.items():
            charSTR = f"{charSTR}\n{name}:{value}"

        filePath = charToTxt(charID=charData["charID"], owner=charData[getLang("Fields", "owner")],
                             status=charData[getLang("Fields", "status")],
                             name=charData[getLang("Fields", "name")], age=charData[getLang("Fields", "age")],
                             gender=charData[getLang("Fields", "gender")],
                             abil=charData[getLang("Fields", "abilities/tools")],
                             appear=charData[getLang("Fields", "appearance")],
                             backg=charData[getLang("Fields", "background")],
                             person=charData[getLang("Fields", "personality")],
                             prefilled=charData[getLang("Fields", "prefilled")],
                             misc=charSTR, ctx=ctx)

        charFile = open(filePath, 'r')

        if ping:
            await channel.send(getLang("Register", "rg_18").format(GMRole.id, isResubmit, ctx.author, ctx.author.id),
                               file=discord.File(filePath))
        else:
            await channel.send(getLang("Register", "rg_18_1").format(isResubmit, ctx.author, ctx.author.id),
                               file=discord.File(filePath))
    except Exception as e:
        await logHandler(getLang("Log", "lg_11"))


def getMember(owner, ctx):
    member = ctx.message.guild.get_member(int(owner))
    return member


def charToTxt(charID, owner, status, name, age, gender, abil, appear, backg, person, prefilled, ctx, misc=''):
    curTime = int(time.time())

    path = f"charoverflow/{curTime}-{charID}.txt"

    charFile = open(path, 'x')

    charTXT = (f"Character Information for Character ID {charID}\n"
               f"Owner: {getMember(owner, ctx) or owner + getLang('Fields', 'left').capitalize()}\n"
               f"{getLang('Fields', 'status').capitalize()}: {status}\n\n"
               f"{getLang('Fields', 'name').capitalize()}: {name}\n\n")
    if age != '': charTXT = charTXT + f"{getLang('Fields', 'age').capitalize()}: {age}\n\n"
    if gender != '': charTXT = charTXT + f"{getLang('Fields', 'gender').capitalize()}: {gender}\n\n"
    if abil != '': charTXT = charTXT + f"{getLang('Fields', 'abilities/tools').capitalize()}: {abil}\n\n"
    if appear != '': charTXT = charTXT + f"{getLang('Fields', 'appearance').capitalize()}: {appear}\n\n"
    if backg != '': charTXT = charTXT + f"{getLang('Fields', 'background').capitalize()}: {backg}\n\n"
    if person != '': charTXT = charTXT + f"{getLang('Fields', 'personality').capitalize()}: {person}\n\n"
    if misc != '': charTXT = charTXT + misc
    if prefilled == '' or prefilled is None:
        pass
    else:
        charTXT = charTXT + f"{getLang('Fields', 'prefilled').capitalize()}: {prefilled}\n\n"

    charFile.write(charTXT)

    charFile.close()
    return path


@bot.command(name=getLang("Commands", "view"), aliases=['cm', 'charmanage'])
async def _view(ctx, idinput='', dmchannel=False, returnEmbed=False):
    '''Brings up character information for the specified character.

    USAGE:
    rp!view <ID>'''

    miscData = ''

    if not idinput.isnumeric():
        charData = await _sqlSearch(ctx, True, field="name", search=idinput)
        charLen = len(charData)
        if charLen == 1:
            charV, = charData
            sanID = charV.id
            await _view(ctx, idinput=str(sanID))
            return
        else:
            await _search(ctx, idinput)
            return
    else:
        sanID = int(idinput)

        charData = _getCharDict(sanID)

        if charData == 'INVALID CHARACTER':
            await ctx.send(getLang("View", "v_1"))
            return

        color = 0x000000

        if (charData[getLang("Fields", "status")] == getLang("Status", "conv_st_0")):
            color = 0xFFD800
        elif (charData[getLang("Fields", "status")] == getLang("Status", "conv_st_1")):
            color = 0x00FF00
        elif (charData[getLang("Fields", "status")] == getLang("Status", "conv_st_2")):
            color = 0xFF0000

        member = ctx.message.guild.get_member(int(charData[getLang("Fields", "owner")]))

        embedVar = discord.Embed(title=getLang("View", "v_2").format(sanID),
                                 description=getLang("View", "v_3").format(sanID), color=color,
                                 inline=False)

        noDisplay = ['charID', 'misc', getLang("Fields", "owner")]

        charOwner = ctx.guild.get_member(int(charData[getLang("Fields", "owner")]))

        embedVar.add_field(name=getLang("Fields", "owner").capitalize(),
                           value=charOwner or f'{charData[getLang("Fields", "owner")]} {getLang("Fields", "left")}',
                           inline=False)

        for i in charData:
            if i not in noDisplay:
                if charData[i] == '' or charData[i] is None:
                    pass
                else:
                    embedVar.add_field(name=i.capitalize(), value=charData[i], inline=False)

        if charData["misc"] == '{}':
            pass
        else:
            try:
                customFields = json.loads(charData["misc"])
                miscData = ''
                for name, value in customFields.items():
                    print(name, value)
                    valid = validators.url(value)
                    if name.lower() == 'portrait' and valid == True:
                        embedVar.set_image(url=value)
                    else:
                        print(valid)
                        embedVar.add_field(name=name, value=value, inline=False)
                        miscData = f"{miscData}\n{name}: {value}"
            except:
                pass

        if returnEmbed is True:
            return embedVar

        try:
            if dmchannel is False:
                await ctx.send(embed=embedVar)
            else:
                await ctx.author.send(embed=embedVar)
        except HTTPException:
            if dmchannel is False:
                await ctx.send(getLang("View", "v_4"))
            else:
                ctx.author.send(getLang("View", "v_4"))
            filePath = charToTxt(charID=charData["charID"], owner=charData[getLang("Fields", "owner")],
                                 status=charData[getLang("Fields", "status")],
                                 name=charData[getLang("Fields", "name")], age=charData[getLang("Fields", "age")],
                                 gender=charData[getLang("Fields", "gender")],
                                 abil=charData[getLang("Fields", "abilities/tools")],
                                 appear=charData[getLang("Fields", "appearance")],
                                 backg=charData[getLang("Fields", "background")],
                                 person=charData[getLang("Fields", "personality")],
                                 prefilled=charData[getLang("Fields", "prefilled")],
                                 misc=miscData, ctx=ctx)

            charFile = open(filePath, 'r')
            if dmchannel is False:
                await ctx.send(file=discord.File(filePath))
            else:
                ctx.author.send(file=discord.File(filePath))
            charFile.close()
            clearLog()


def _getChar(charID=0):  # Deprecated as of Version 2.1 - Use _getCharDict instead!
    cursor = conn.cursor()

    cursor.execute(f"SELECT count(*) FROM charlist")
    count = cursor.fetchone()[0]

    charInvalid = 'INVALID CHARACTER'

    if charID > count:
        return charInvalid

    cursor.execute(f"SELECT * FROM charlist WHERE charID IS {charID}")
    charInfo = cursor.fetchone()

    checkStatus, = charInfo[2:3]

    if checkStatus == 'Disabled':
        return charInvalid

    return charInfo


def _getCharDict(charID=0):
    cur = conn.cursor()

    charData = {
        "charID": None,
        getLang("Fields", "owner"): None,
        getLang("Fields", "status"): None,
        getLang("Fields", "name"): None,
        getLang("Fields", "age"): None,
        getLang("Fields", "gender"): None,
        getLang("Fields", "abilities/tools"): None,
        getLang("Fields", "appearance"): None,
        getLang("Fields", "background"): None,
        getLang("Fields", "personality"): None,
        getLang("Fields", "prefilled"): None,
        "misc": None,
    }

    sql = '''SELECT * FROM charlist WHERE charID is ?'''

    cur.execute(sql, [charID])

    chars = cur.fetchone()

    x = 0

    if chars is None:
        return 'INVALID CHARACTER'

    for i in charData:
        charData[i] = chars[x]
        x = x + 1

    if (charData[getLang("Fields", "status")] == 'Disabled'):
        return 'INVALID CHARACTER'

    return charData


@bot.command(name=getLang("Commands", "set"), aliases=['setprop'])
async def _set(ctx, charID, field, *, message: str):
    alertChannel = bot.get_channel(LogChannel())

    if field.lower() in fields:
        fSan = convertField(field.lower())

        if fSan == 'charID':
            await ctx.send(getLang("Set", "s_1"))
            return
    else:
        await _custom(ctx, charID=charID, field=field, message=message)
        return

    if message == '' or message == getLang("Set", "s_2"):
        message = ''
        if fSan == getLang("Fields", "name"):
            await ctx.send(getLang("Set", "s_3"))
            return
        elif fSan == 'misc':
            message = '{}'

    if fSan == 'owner' or fSan == 'status':
        if await checkGM(ctx) is False:
            await ctx.send(getLang("Set", "s_4"))
            return

    if charID.isnumeric():
        icharID = int(charID)
    else:
        await ctx.send(getLang("View", "v_1"))
        return

    ownerID = _charExists(icharID)

    if ownerID == False:
        await ctx.send(getLang("View", "v_1"))
        return

    if not charPermissionCheck(ctx, ownerID):
        await ctx.send(getLang("Set", "s_5"))
        return

    _setSQL(icharID, fSan, message)

    if message == '':
        await ctx.send(getLang("Set", "s_6").format(field.capitalize()))
    else:
        await ctx.send(getLang("Set", "s_7").format(field.capitalize()))

    await alertChannel.send(getLang("Log", "lg_12").format(ctx.author, icharID, field.capitalize(), message))


def _setSQL(charID, field, content):
    cur = conn.cursor()

    sql = f'''UPDATE charlist SET {field} = ? WHERE charID is ?'''
    cur.execute(sql, [content, charID])
    conn.commit()


async def _custom(ctx, charID='', field='', *, message: str):
    alertChannel = bot.get_channel(LogChannel())

    if charID.isnumeric():
        icharID = int(charID)
    else:
        await ctx.send(getLang("Custom", "cs_1"))
        return

    charData = _getCharDict(icharID)

    if charData == 'INVALID CHARACTER':
        await ctx.send(getLang("Custom", "cs_1"))
        return

    if ctx.author.id != int(charData["owner"]):
        await ctx.send(getLang("Custom", "cs_2"))
        return

    customFields = json.loads(charData["misc"])
    fieldDel = False

    if message.lower() == getLang("Set", "s_2"):
        try:
            customFields.pop(field)
            fieldDel = True
        except:
            await ctx.send(getLang("Custom", "cs_3"))
            return
    else:
        customFields[field] = message
    miscData = json.dumps(customFields)
    _setSQL(icharID, "misc", miscData)
    if fieldDel == False:
        await ctx.send(getLang("Custom", "cs_4").format(field))
        await alertChannel.send(getLang("Log", "lg_12").format(ctx.author, icharID, field.capitalize(), message))
        return

    await ctx.send(getLang("Custom", "cs_5").format(field))

    await alertChannel.send(getLang("Log", "lg_13").format(ctx.author, icharID, field.capitalize()))


async def _custom_error(ctx, args):
    await ctx.send(getLang("Custom", "cs_6"))


@dataclass
class CharacterListItem:
    """Stores Basic Character Information in a Class"""
    id: int
    name: str
    owner: str


async def getUserChars(ctx, userID, pageSize, pageID):
    pageNo = int(pageID - 1)

    cursor = conn.cursor()
    userInt = int(userID)
    cursor.execute(f"SELECT count(*) FROM charlist WHERE status IS NOT 'Disabled' AND owner IS {userID}")
    count = cursor.fetchone()[0]

    cursor.execute(
        f"SELECT charID, name, owner FROM charlist WHERE status IS NOT 'Disabled' AND owner IS {userInt} ORDER BY charID LIMIT {pageSize} OFFSET {pageNo * pageSize}")

    charList = [CharacterListItem(charID, name, owner) for charID, name, owner in cursor]
    charListStr = ''

    for i in charList:
        member = ctx.message.guild.get_member(int(i.owner))
        charListStr = getLang("GetChars", "gc_3").format(charListStr, i.id, i.name[0:75], member or i.owner) + '\n'

    if len(charList) == 0:
        await ctx.send(getLang("GetChars", "gc_1"))
        return

    await ctx.send(getLang("GetChars", "gc_2").format((member or userID + getLang("Fields", "left")), (pageNo + 1),
                                                      math.ceil(count / pageSize), charListStr))


@bot.command(name=getLang("Commands", "list"))
async def _list(ctx, pageIdentifier='', page=''):
    '''Shows a list of all characters, sorted into pages of 15 Characters.
    Mentioning a user or user ID will bring up all characters belonging to that user.

    USAGE:
    rp!list <PAGE>
    rp!list <MENTION|USER ID> <PAGE>'''

    pageSize = 15
    if pageIdentifier.isnumeric():
        pageNo = int(pageIdentifier) - 1
    else:
        if page.isnumeric():
            pageID = int(page)
        else:
            pageID = 1
        if pageIdentifier == '' or None:
            pageID = 0
        elif pageIdentifier == 'me':
            await getUserChars(ctx, ctx.author.id, pageSize, pageID=pageID)
            return
        elif ctx.message.mentions[0].id:
            await getUserChars(ctx, ctx.message.mentions[0].id, pageSize, pageID=pageID)
            return
        else:
            pageNo = 0

    cursor = conn.cursor()
    #  Gets the Character IDs from the Database

    if 'pageNo' not in locals():
        pageNo = 0

    cursor.execute(f"SELECT count(*) FROM charlist WHERE status IS NOT 'Disabled'")
    count = cursor.fetchone()[0]

    cursor.execute(
        f"SELECT charID, name, owner FROM charlist WHERE status IS NOT 'Disabled' Order By charID limit {pageSize} OFFSET {pageNo * pageSize}")

    charList = [CharacterListItem(charID, name, owner) for charID, name, owner in cursor]

    charListStr = ''

    for i in charList:
        member = ctx.message.guild.get_member(int(i.owner))
        charListStr = getLang("List", "ls_2").format(charListStr, i.id, i.name[0:75], member or i.owner) + '\n'
    print(charListStr)
    await ctx.send(getLang("List", "ls_1").format(pageNo + 1, math.ceil(count / pageSize), charListStr))


fields = [getLang("Fields", 'owner'), 'ownerid', getLang("Fields", 'status'), getLang("Fields", 'name'), 'charid', 'id',
          getLang("Fields", 'age'), getLang("Fields", 'gender'), getLang("Fields", 'abilities/tools'), 'abilities',
          getLang("Fields", 'appearance'), getLang("Fields", 'background'), getLang("Fields", 'personality'),
          'prefilled', getLang("Fields", 'prefilled'), 'custom', 'misc']


def convertField(selector):
    if selector == getLang("Fields", "owner") or selector == 'ownerid':
        return 'owner'
    if selector == 'id' or selector == 'charid':
        return 'charID'
    if selector == getLang("Fields", "appearance"):
        return 'appear'
    if selector == getLang("Fields", 'background'):
        return 'backg'
    if selector == getLang("Fields", 'abilities/tools') or selector == 'abilities':
        return 'abil'
    if selector == getLang("Fields", 'personality'):
        return 'person'
    if selector == 'prefilled' or selector == getLang("Fields", 'prefilled'):
        return 'prefilled'
    if selector == 'misc' or selector == 'custom':
        return 'misc'
    return selector


@bot.command(name=getLang("Commands", "search"))
async def _search(ctx, selector='', extra1='', extra2=''):
    if selector == '':
        await ctx.send(getLang("Search", "sr_1"))
        return

    if (ctx.message.mentions):
        await _list(ctx, pageIdentifier=selector, page=extra1)
        return

    Sfield = False

    if selector.lower() in fields:

        fieldFinal = convertField(selector.lower())

        if extra2.isnumeric():
            pageNo = int(extra2) - 1
        else:
            pageNo = 0
        await _sqlSearch(ctx, field=fieldFinal, search=extra1, pageNo=pageNo, rawR=False)
    else:
        if extra1.isnumeric():
            pageNo = int(extra1) - 1
        else:
            pageNo = 0
        await _sqlSearch(ctx, False, search=selector, pageNo=pageNo)


async def _sqlSearch(ctx, rawR, field=None, search='', pageNo=0):
    cur = conn.cursor()

    if field is None:
        field = 'name'

    sqlC = f'''SELECT count(*) FROM charlist WHERE {field} LIKE ? AND status IS NOT 'Disabled' '''
    cur.execute(sqlC, ['%' + search + '%'])
    count = cur.fetchone()[0]

    sql = f'''SELECT charid, owner, name FROM charlist WHERE {field} LIKE ? AND status IS NOT 'Disabled' LIMIT 25 OFFSET ?'''
    cur.execute(sql, ['%' + search + '%', (25 * pageNo)])

    charList = [CharacterListItem(id=charID, name=name, owner=owner) for charID, owner, name in cur]

    if rawR is True:
        return charList

    charListStr = ''

    for i in charList:
        member = ctx.message.guild.get_member(int(i.owner))
        charListStr = getLang("GetChars", "gc_3").format(charListStr, i.id, i.name[0:75], member or i.owner) + '\n'

    await ctx.send(
        f'{getLang("Search", "sr_2").format(pageNo + 1, math.ceil(count / 25))} \n{charListStr}')


@bot.command(name=getLang("Commands", "delete"))
async def _delete(ctx, charDel='', confirmation=''):
    if charDel.isnumeric():
        if confirmation.lower() == getLang("Delete", "dl_1"):
            await _deleteChar(ctx, int(charDel))
            return
        else:
            await ctx.send(getLang("Delete", "dl_2"))
            response = await bot.wait_for("message", check=message_check())
            if response.content.lower() == getLang("Delete", "dl_1"):
                await _deleteChar(ctx, int(charDel))
                return
    else:
        await ctx.send("Invalid Character ID!")


@bot.command(name=getLang("Commands", "undelete"), aliases=[getLang("Commands", "recover")])
async def _undelete(ctx, charID):
    if not await checkGM(ctx):
        await ctx.send(getLang("Delete", "dl_3"))
        return

    if charID.isnumeric():
        icharID = int(charID)

    cursor = conn.cursor()

    cursor.execute("UPDATE charlist SET status = 'Pending' WHERE charID is ?", [icharID])
    conn.commit()
    await ctx.send(getLang("Delete", "dl_").format(icharID))


def charPermissionCheck(ctx, ownerID):
    role_names = role_names = [role.name for role in ctx.author.roles]

    authorID = ctx.author.id

    if int(ownerID) == authorID or getLang("Misc", "gm") in role_names:
        return True
    else:
        return False


def _charExists(charID):
    cursor = conn.cursor()
    cursor.execute(f"SELECT owner FROM charlist WHERE charID IS ? AND status IS NOT 'Disabled'", [charID])

    owner = cursor.fetchone()

    if owner is None:
        return False
    else:
        ownerP = owner[0]
        return ownerP


async def _deleteChar(ctx, charID):
    ownerP = _charExists(charID)

    if ownerP is False:
        await ctx.send(getLang("Delete", "dl_5"))
        return

    cursor = conn.cursor()

    if charPermissionCheck(ctx, ownerID=ownerP) is True:
        cursor.execute(f"UPDATE charlist SET status = 'Disabled' WHERE charID is ?", [charID])
        conn.commit()
        await ctx.send(f"Character {charID} has been deleted.")
    else:
        await ctx.send(getLang("Delete", "dl_6"))


async def getdm(ctx):
    response = await bot.wait_for('message', check=message_check(channel=ctx.author.dm_channel))
    attach = None
    if response.attachments:
        attach = str(response.attachments[0].url)
        finalResponse = attach + ' ' + response.content
    else:
        finalResponse = response.content
    return finalResponse


def previewChar(cfields=None, prefilled=None, name=None):
    embedVar = discord.Embed(title=getLang("Register", "pr_1"),
                             description=getLang("Register", "pr_2"), color=0xffD800)

    if cfields is not None:
        embedVar.add_field(name=getLang("Fields", "name").capitalize() + ':', value=cfields[getLang("Fields", 'name')],
                           inline=True)
        if cfields['age'] != '': embedVar.add_field(name=getLang("Fields", "age").capitalize() + ':',
                                                    value=cfields[getLang("Fields", 'age')], inline=False)
        if cfields['gender'] != '': embedVar.add_field(name=getLang("Fields", "gender").capitalize() + ':',
                                                       value=cfields[getLang("Fields", 'gender')], inline=False)
        if cfields['abilities/tools'] != '': embedVar.add_field(
            name=getLang("Fields", "abilities/tools").capitalize() + ':',
            value=cfields[getLang("Fields", 'abilities/tools')], inline=False)
        if cfields['appearance'] != '': embedVar.add_field(name=getLang("Fields", "appearance").capitalize() + ':',
                                                           value=cfields[getLang("Fields", 'appearance')],
                                                           inline=False)
        if cfields['background'] != '': embedVar.add_field(name=getLang("Fields", "background").capitalize() + ':',
                                                           value=cfields[getLang("Fields", 'background')],
                                                           inline=False)
        if cfields['personality'] != '': embedVar.add_field(name=getLang("Fields", "personality").capitalize() + ':',
                                                            value=cfields[getLang("Fields", 'personality')],
                                                            inline=False)

    if prefilled:
        embedVar.add_field(name=getLang("Fields", "name").capitalize() + ':', value=name, inline=False)
        embedVar.add_field(name=getLang("Fields", "prefilled").capitalize() + ':', value=prefilled, inline=False)

    return embedVar


@bot.command(name=getLang("Commands", "invite"))
async def invite(ctx):
    await ctx.send(getLang("Misc", "invite"))


async def canonCheck(response, user):
    global canonDeny
    response = response.lower()

    if any(canon_char in response for canon_char in getDenyList()):  # Thanks Atlas!
        await user.send(getLang("Misc", "autodeny"))

        logChannel = bot.get_channel(LogChannel())

        await logChannel.send(getLang("Log", "lg_14").format(user, user.id, response))

        currentlyRegistering.remove(user.id)
        return True
    return False


async def _registerChar(ctx, user):

    isRegistering = True

    while isRegistering:
        resmsg = await getdm(ctx)
        resmsg = resmsg.lower()

        if resmsg == getLang("Register", "rg_24"):
            await user.send(getLang("Register", "rg_19"))
            currentlyRegistering.remove(user.id)
            isRegistering = False
            return
        elif resmsg == getLang("Register", "rg_39"):

            charcomplete = False
            submitChar = False
            prefilled = None

            cfields = {
                getLang("Fields", "name"): None,
                getLang("Fields", "gender"): None,
                getLang("Fields", "age"): None,
                getLang("Fields", "abilities/tools"): None,
                getLang("Fields", "appearance"): None,
                getLang("Fields", "background"): None,
                getLang("Fields", "personality"): None,
            }

            await user.send(getLang("Register", "rg_20"))

            response = await getdm(ctx)

            if await canonCheck(response, user):
                return

            cfields[getLang("Fields", "name")] = response

            await user.send(getLang("Register", "rg_21"))

            while not charcomplete:

                # MAIN CHARACTER REGISTRATION LOOP

                response = await getdm(ctx)
                if response.lower() == getLang("Register", "rg_24"):
                    await user.send(getLang("Register", "rg_19"))
                    isRegistering = False
                    currentlyRegistering.remove(user.id)
                    return
                selector = response.lower()

                if response.lower() == 'done':
                    if not submitChar:
                        await user.send(getLang("Register", "rg_22"))
                    else:
                        submitChar = True
                        charcomplete = True

                        owner = ctx.author.id
                        prefilled = None

                        charID = await charadd(owner=owner, name=cfields[getLang("Fields", "name")],
                                               age=cfields[getLang("Fields", "age")],
                                               gender=cfields[getLang("Fields", "gender")],
                                               abil=cfields[getLang("Fields", "abilities/tools")],
                                               appear=cfields[getLang("Fields", "appearance")],
                                               backg=cfields[getLang("Fields", "background")],
                                               person=cfields[getLang("Fields", "personality")],
                                               prefilled=prefilled)

                        await user.send(getLang("Register", "rg_23").format(int(charID)))
                        currentlyRegistering.remove(user.id)
                        await alertGMs(ctx, charID)
                        return
                elif response.lower() == getLang("Register", "rg_24"):
                    await user.send(getLang("Register", "rg_19"))
                    isRegistering = False
                    currentlyRegistering.remove(user.id)
                    return
                elif response.lower() == getLang("Register", "rg_25"):
                    try:
                        await user.send(embed=previewChar(cfields=cfields))
                    except:
                        await user.send(getLang("Register", "rg_26"))
                elif selector in cfields:
                    await user.send(getLang("Register", "rg_27").format(selector.capitalize()))
                    response = await getdm(ctx)

                    if selector.lower() == getLang("Fields", "name"):
                        if await canonCheck(response, user):
                            break
                            return

                    if response.lower() == getLang("Register", "rg_24"):
                        await user.send(getLang("Register", "rg_19"))
                        isRegistering = False
                        currentlyRegistering.remove(user.id)
                        return

                    cfields[selector] = response

                    emptyFields = []
                    completeFields = []

                    for x in cfields:
                        if cfields[x] is None:
                            emptyFields.append(x)
                        else:
                            completeFields.append(x)

                    toSpecify = ''
                    specifyDone = ''

                    for word in emptyFields:
                        toSpecify = (toSpecify + "`" + word.capitalize() + "`, ")

                    for word2 in completeFields:
                        specifyDone = (specifyDone + "`" + word2.capitalize() + "`, ")

                    if not toSpecify:
                        await user.send(getLang("Register", "rg_28").format(selector.capitalize(), specifyDone))
                        submitChar = True
                    else:
                        await user.send(
                            getLang("Register", "rg_29").format(selector.capitalize(), toSpecify, specifyDone))
                else:
                    await user.send(getLang("Register", "rg_30"))

            return
        elif resmsg == getLang("Fields", "prefilled") and allowPrefilled():

            charcomplete = False

            await user.send(getLang("Register", "rg_31"))
            response = await getdm(ctx)

            if await canonCheck(response, user):
                return

            if response.lower() == getLang("Register", "rg_24"):
                await user.send(getLang("Register", "rg_19"))
                isRegistering = False
                currentlyRegistering.remove(user.id)
                return

            name = response

            await user.send(getLang("Register", "rg_32"))
            prefilled = await getdm(ctx)
            if prefilled.lower() == getLang("Register", "rg_24"):
                await user.send(getLang("Register", "rg_19"))
                isRegistering = False
                currentlyRegistering.remove(user.id)
                return

            charFields = [getLang("Fields", "prefilled"), getLang("Fields", "name")]

            while not charcomplete:
                await user.send(getLang("Register", "rg_33"))
                response = await getdm(ctx)
                selector = response.lower()

                if selector == getLang("Register", "rg_24"):
                    await user.send(getLang("Register", "rg_19"))
                    isRegistering = False
                    currentlyRegistering.remove(user.id)
                    return

                if selector not in charFields:
                    if selector == 'done':

                        charID = await charadd(owner=ctx.author.id, name=name, prefilled=prefilled)

                        await user.send(getLang("Register", "rg_34").format(str(charID)))
                        currentlyRegistering.remove(user.id)
                        await alertGMs(ctx, charID)
                        charcomplete = True
                        return
                    elif selector == getLang("Register", "rg_25"):
                        try:
                            await user.send(embed=previewChar(prefilled=prefilled, name=name))
                        except:
                            await user.send(getLang("Register", "rg_26"))

                    else:
                        await user.send(getLang("Register", "rg_30"))
                elif selector == getLang("Fields", "name"):
                    await user.send(getLang("Register", "rg_35"))
                    response = await getdm(ctx)

                    if await canonCheck(response, user):
                        return

                    if response.lower() == getLang("Register", "rg_24"):
                        await user.send(getLang("Register", "rg_19"))
                        isRegistering = False
                        currentlyRegistering.remove(user.id)
                        return
                    name = response
                    await user.send(getLang("Register", "rg_36"))

                else:
                    await user.send(getLang("Register", "rg_32"))
                    response = await getdm(ctx)
                    if response.lower() == getLang("Register", "rg_24"):
                        await user.send(getLang("Register", "rg_19"))
                        isRegistering = False
                        currentlyRegistering.remove(user.id)
                        return
                    prefilled = response
            return

        else:
            await user.send(getLang("Register", "rg_37"))


#  EVAL COMMAND. - https://gist.github.com/nitros12/2c3c265813121492655bc95aa54da6b9

def insert_returns(body):
    # insert return stmt if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)


@bot.command(name=getLang("Commands", "eval"))
@commands.is_owner()
async def eval_fn(ctx, *, cmd):
    fn_name = "_eval_expr"

    cmd = cmd.strip("` ")

    # add a layer of indentation
    cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

    # wrap in async def body
    body = f"async def {fn_name}():\n{cmd}"

    parsed = ast.parse(body)
    body = parsed.body[0].body

    insert_returns(body)

    env = {
        'bot': ctx.bot,
        'discord': discord,
        'commands': commands,
        'ctx': ctx,
        '__import__': __import__
    }
    exec(compile(parsed, filename="<ast>", mode="exec"), env)

    result = (await eval(f"{fn_name}()", env))
    await ctx.send(result)

@bot.command(name=getLang("Commands", "help"))
async def help(ctx):
    await ctx.send(getLang("Misc", "help"))

## Log Handling ##

async def logHandler(message):
    channel = bot.get_channel(LogChannel())
    await channel.send(message)


async def getLogChannel():
    return bot.get_channel(LogChannel())


async def logMSG(message):
    try:
        await (await getLogChannel()).send(message)
    except Exception as e:
        print(getLang("Log", "lg_15").format(message, e))


## Auto Backup ##

@tasks.loop(seconds=60)
async def autoBackup():
    t = datetime.now()
    c_t = t.strftime("%H:%M")
    if c_t == "00:00":
        await runBackup()


@bot.command(name=getLang("Commands", "fbackup"))
@commands.is_owner()
async def _forceBackup(ctx):
    await runBackup()


async def runBackup():
    global database
    global backupOngoing
    global conn

    backupOngoing = True

    channel = bot.get_channel(int(GMChannel()))
    date = datetime.now()
    timerStart = time.perf_counter()
    try:
        await channel.send(getLang("Backup", "bu_1"))
    except Exception as e:
        await logMSG(getLang("Backup", "bu_2"))
    status = discord.Status.idle
    await bot.change_presence(activity=discord.Game(getLang("Backup", "bu_3")), status=status)

    await logMSG(getLang("Backup", "bu_4"))
    close_connection(database)

    folderName = 'Mettaton Backups'

    folders = drive.ListFile(
        {
            'q': "title='" + folderName + "' and mimeType='application/vnd.google-apps.folder' and trashed=false"}).GetList()

    backupName = f"mttchars-{date.strftime('%Y-%m-%d %H:%M:%S')}"

    for folder in folders:
        if folder['title'] == folderName:
            dBackup = drive.CreateFile({'title': backupName, "parents": [{"id": folder['id']}]})
            dBackup.SetContentFile(database)
            dBackup.Upload()

    conn = create_connection(database)
    await logMSG(getLang("Backup", "bu_5"))

    timerEnd = time.perf_counter()
    try:
        await channel.send(getLang("Backup", "bu_6").format(str((timerEnd - timerStart))[0:5]))
    except Exception as e:
        await logMSG(getLang("Backup", "bu_7"))

    backupOngoing = False
    await statusChanger()


# rip rp!sans


@tasks.loop(minutes=5)
async def changeStatus():
    await statusChanger()


async def statusChanger():
    status = discord.Status.online

    from datetime import date

    dt = date.today()
    d1 = dt.strftime("%d")

    statusChoiceRaw = getLang("StatusLines", "status")
    statusChoice = statusChoiceRaw.splitlines()
    await bot.change_presence(activity=discord.Game(random.choice(statusChoice)))


## Other ##

@bot.command(name=getLang("Commands", "send"))
async def send(ctx, id, *, message: str):
    charData = _getCharDict(id)
    if charData == 'INVALID CHARACTER':
        try:
            await ctx.author.send(getLang("Send", "sn_1"))
        except Exception as e:
            await logMSG(getLang("Send", "sn_2").format(ctx.author, ctx.author.id, e))
        await ctx.message.delete()
        return

    if ctx.author.id != int(charData["owner"]):
        try:
            await ctx.author.send(getLang("Send", "sn_3"))
        except Exception as e:
            await logMSG(getLang("Send", "sn_2").format(ctx.author, ctx.author.id, e))
        await ctx.message.delete()
        return

    if charData[getLang("Fields", "status")] != getLang("Status", "conv_st_1"):
        try:
            await ctx.author.send(getLang("Send", "sn_4"))
        except Exception as e:
            await logMSG(getLang("Send", "sn_2").format(ctx.author, ctx.author.id, e))
        await ctx.message.delete()
        return

    name = charData[getLang("Fields", "name")]
    name = name[0:80]

    custom_img = None

    portJS = json.loads(charData["misc"])
    if getLang("Send", "sn_5") in portJS:
        custom_img = portJS[getLang("Send", "sn_5")]

    await webhook_manager.send(ctx, name, message, custom_img)


bot.run(token)
close_connection(database)
print(getLang("Misc", "shutdown"))
