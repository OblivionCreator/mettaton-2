import glob
import math
import os
import random
from pathlib import Path
from disnake.ext import tasks
from datetime import datetime
import disnake as discord
from disnake.ext import commands
import sqlite3
from sqlite3 import Error
from collections.abc import Sequence
import ast
from dataclasses import dataclass
import time
import json
from disnake import HTTPException, TextInputStyle
from disnake.utils import get
from configparser import ConfigParser
from resources import getdiff, webhook_manager
import validators
import re

intents = discord.Intents.all()
backupOngoing = False
pageSize = 20


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
        'autobackup': False,
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

        print(".config File not found! Creating the Config...")

        file = open('.config', 'x')

        configDict = configFields()

        cfgJson = json.dumps(configDict)

        file.write(cfgJson)

        print(
            "Config File has been created!\nTo set the GM Channel, type rp!setgmchannel in the specified channel.\nTo set the logging channel, type rp!setlogchannel in the specified channel.")


cst_prefix = getLang("Commands", "CMD_PREFIX")

bot = commands.Bot(
    command_prefix=['mtt!', 'Rp!', 'RP!', 'rP!', cst_prefix],
    intents=intents, case_insensitive=True,
    allowed_mentions=discord.AllowedMentions(users=False, everyone=False, replied_user=False, roles=True))

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
    return bool(conf["autobackup"])


def backup_init():
    global drive
    from pydrive.auth import GoogleAuth
    from pydrive.drive import GoogleDrive

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


def allowPrefilled():
    conf = getConfig()
    print(bool(conf["allowprefilled"]))
    return bool(conf["allowprefilled"])


async def getdm(ctx):
    response = await bot.wait_for('message', check=message_check(channel=ctx.author.dm_channel))
    attach = None
    if response.attachments:
        attach = str(response.attachments[0].url)
        finalResponse = attach + ' ' + response.content
    else:
        finalResponse = response.content
    return finalResponse


@commands.is_owner()
@bot.command(name=getLang("Commands", "CMD_CLEARCONFIG"))
async def clearconfig(ctx):
    config = configFields()

    file = open('.config', 'w')

    configDict = configFields()

    cfgJson = json.dumps(configDict)

    file.write(cfgJson)

    await ctx.send(getLang("ClearConfig", "CLEAR_CONFIG_SUCCESS"))
    return


# Deny List Handling

def getDenyList():
    conf = getConfig()
    return conf["denylist"]


# Returns current Deny List

@bot.command(name=getLang("Commands", "CMD_UPDATEDENY"))
async def update_deny(ctx, act, term=''):
    term = term.lower()

    if not await checkGM(ctx):
        await ctx.send(getLang("DenyList", "DENYLIST_FAILED_NO_PERMISSION"))
        return

    if act.lower() == getLang('DenyList', 'DENYLIST_LIST_ITEMS'):
        await ctx.send(f"{getLang('DenyList', 'DENYLIST_TERMS')}\n{listDeny()}")
        return

    if act == getLang('DenyList', 'DENYLIST_ADD_ITEM'):

        if term == '':
            await ctx.send(getLang("DenyList", "DENYLIST_FAILED_NO_TERMS"))
            return

        addSt = addDeny(term)
        if addSt == False:
            await ctx.send(getLang("DenyList", "DENYLIST_FAILED_DUPLICATE"))
            return
        await ctx.send(getLang("DenyList", "DENYLIST_SUCCESS_ADDED").format(term))
        return

    if act.lower() == 'remove':

        if term == '':
            await ctx.send(getLang("DenyList", "DENYLIST_FAILED_NO_TERMS"))

        if delDeny(term) == False:
            await ctx.send(getLang("DenyList", "DENYLIST_BAD_NAME"))
            return
        await ctx.send(getLang("DenyList", "DENYLIST_SUCCESS_REMOVED").format(term))
        return

    await ctx.send(getLang("DenyList", "DENYLIST_FAILED_INVALID_ACTION"))


def listDeny():
    denyList = getDenyList()

    if len(denyList) == 0:
        return getLang("DenyList", "DENYLIST_EMPTY")

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
    if doBackup():
        backup_init()
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
    "species"    TEXT,
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



async def charadd(owner, name, age='', gender='', abil='', appear='', backg='', person='', prefilled='', misc=None,
                  status='Pending', charID='', species=''):

    if not misc:
        misc = '{}'

    character = (owner, status, name, age, gender, abil, appear, species, backg, person, prefilled, misc)
    print(type(misc))
    """
    :param conn:
    :param character:
    :return: charID
    """

    if charID == '':
        sql = '''INSERT INTO charlist(owner,status,name,age,gender,abil,appear,species,backg,person,prefilled,misc) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)'''
        cur = conn.cursor()
        cur.execute(sql, character)
        conn.commit()
        return cur.lastrowid
    else:
        charwid = character + (int(charID),)
        sql = '''UPDATE charlist SET owner=?,status=?,name=?,age=?,gender=?,abil=?,appear=?,species=?,backg=?,person=?,prefilled=?,misc=? WHERE charID=?'''
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


@bot.command(name=getLang("Commands", "CMD_SETGMCHANNEL"))
async def _setGMCChannel(ctx):
    role_names = [role.name for role in ctx.author.roles]

    if not await checkGM(ctx):
        await ctx.send(getLang("GMChannel", "GMCHANNEL_NO_PERMISSION"))
        return

    updateConfig('gmchannel', ctx.channel.id)

    await ctx.send(getLang("GMChannel", "GMCHANNEL_SUCCESS"))


@bot.command(name=getLang("Commands", "CMD_SETLOGCHANNEL"))
async def _setLogChannel(ctx):
    if not await checkGM(ctx):
        await ctx.send(getLang("LogChannel", "LOGCHANNEL_NO_PERMISSION"))
        return

    updateConfig('logchannel', ctx.channel.id)
    await ctx.send(getLang("LogChannel", "LOGCHANNEL_SUCCESS"))


def updateConfig(field, value):
    with open('.config', 'r') as file:
        jsonOBJ = json.load(file)
        file.close()

    jsonOBJ[field] = value

    with open('.config', 'w') as file:
        json.dump(jsonOBJ, file)


statuses = {
    getLang("Status", "RAW_STATUS_PENDING"): getLang("Status", "STATUS_PENDING"),
    getLang("Status", "RAW_STATUS_APPROVE"): getLang("Status", "STATUS_APPROVED"),
    getLang("Status", "RAW_STATUS_DENY"): getLang("Status", "STATUS_DENIED"),
    getLang("Status", "RAW_STATUS_BOILERPLATE"): getLang("Status", "STATUS_DENIED"),
    getLang("Status", "RAW_STATUS_KILL"): getLang("Status", "STATUS_DEAD")
}


@bot.command(aliases=[getLang("Status", "RAW_STATUS_BOILERPLATE")])
async def bp(ctx, charID):
    ctx.invoked_with = getLang("Status", "RAW_STATUS_BOILERPLATE")
    await approve(ctx, charID, reason=getLang("Status", "STATUS_RESPONSE_BOILERPLATE").format(charID))


@bot.command(name=getLang("Status", "RAW_STATUS_APPROVE"),
             aliases=[getLang("Status", "STATUS_PENDING"), getLang("Status", "RAW_STATUS_DENY"),
                      getLang("Status", "RAW_STATUS_KILL")])
async def approve(ctx, charID, *, reason: str = ''):
    if reason == '' and not ctx.message.attachments:
        reason = getLang("Status", "STATUS_RESPONSE_NO_REASON")
    if len(reason) > 1750:
        await ctx.send(getLang("Status", "STATUS_RESPONSE_FAILED_LONG"))
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
        await ctx.send(getLang("Status", "STATUS_RESPONSE_FAILED_BAD_USER").format(charID))
        return
    try:
        await user.send(getLang("Status", "STATUS_RESPONSE_SUCCESS").format(charID, name[0:100], status, reason))
    except Exception:
        await ctx.send(getLang("Status", "STATUS_RESPONSE_FAILED_BAD_DM").format(charID))


async def _changeStatus(ctx, charID='', charStatus='Pending', reason=''):
    if not await checkGM(ctx):
        await ctx.send(getLang("Status", "STATUS_RESPONSE_FAILED_NO_PERMISSION"))
        return

    if charID.isnumeric():
        charInt = int(charID)
    else:
        await ctx.send(getLang("Status", "STATUS_RESPONSE_FAILED_BAD_ID"))
        return

    if ctx.message.attachments:
        reason = f"{reason}\n{str(ctx.message.attachments[0].url)}"

    cursor = conn.cursor()
    sql = '''UPDATE charlist SET status = ? WHERE charID is ?'''
    cursor.execute(sql, [charStatus, charInt])
    conn.commit()

    if charStatus == getLang("Status", "STATUS_APPROVED"):
        charData = _getCharDict(charInt)
        userid = charData["owner"]
        user = ctx.guild.get_member(int(userid))
        role = get(ctx.guild.roles, name=getLang("Misc", "rp"))
        await user.add_roles(role)

    await alertUser(ctx, charInt, charStatus, reason)
    await ctx.send(getLang("Status", "STATUS_CHANGE_SUCCESS").format(charID, charStatus))
    logChannel = bot.get_channel(LogChannel())
    await logChannel.send(getLang("Status", "STATUS_CHANGE_LOG").format(ctx.author, charInt, charStatus, reason))


async def reRegister(ctx, charID):
    cursor = conn.cursor()
    cursor.execute(f"SELECT owner FROM charlist WHERE charID IS {charID} AND status IS NOT 'Disabled'")

    owner = cursor.fetchone()

    if owner is None:
        await ctx.send(getLang("Register", "REGISTER_FAILED_BAD_CHARACTER"))
        return
    else:
        ownerP = owner[0]

    if int(ownerP) != ctx.author.id:
        await logMSG(getLang("Log", "lg_9").format(ctx.author.id, ownerP))
        await ctx.send(getLang("Register", "REGISTER_FAILED_BAD_OWNER"))
        return

    charData = _getCharDict(int(charID))

    if charData == 'INVALID CHARACTER':
        ctx.send(getLang("Register", "REGISTER_FAILED_BAD_CHARACTER"))

    cfields = {
        getLang("Fields", "name"): '',
        getLang("Fields", "gender"): '',
        getLang("Fields", "age"): '',
        getLang("Fields", "abilities/tools"): '',
        getLang("Fields", "appearance"): '',
        getLang("Fields", "background"): '',
        getLang("Fields", "personality"): '',
        getLang("Fields", "prefilled"): '',
        'misc': ''
    }

    owner = charData[getLang("Fields", "owner")]
    status = charData[getLang("Fields", "status")]
    cfields[getLang("Fields", "name")] = charData[getLang("Fields", "name")]
    cfields[getLang("Fields", "age")] = charData[getLang("Fields", "age")]
    cfields[getLang("Fields", "gender")] = charData[getLang("Fields", "gender")]
    cfields[getLang("Fields", "abilities/tools")] = charData[getLang("Fields", "abilities/tools")]
    cfields[getLang("Fields", "appearance")] = charData[getLang("Fields", "appearance")]
    cfields[getLang("Fields", "species")] = charData[getLang("Fields", "species")]
    cfields[getLang("Fields", "background")] = charData[getLang("Fields", "background")]
    cfields[getLang("Fields", "personality")] = charData[getLang("Fields", "personality")]
    cfields[getLang("Fields", "prefilled")] = charData[getLang("Fields", "prefilled")]
    cfields["misc"] = charData["misc"]

    embedV = await _view(ctx, charID, dmchannel=True, returnEmbed=True)

    try:
        await ctx.author.send(getLang("Register", "REGISTER_PREVIEW"), embed=embedV)
    except:
        filePath = charToTxt(charID=charData["charID"],
                             owner=charData[getLang("Fields", "owner")],
                             status=charData[getLang("Fields", "status")],
                             name=charData[getLang("Fields", "name")], age=charData[getLang("Fields", "age")],
                             gender=charData[getLang("Fields", "gender")],
                             abil=charData[getLang("Fields", "abilities/tools")],
                             appear=charData[getLang("Fields", "appearance")],
                             species=cfields[getLang("Fields", "species")],
                             backg=charData[getLang("Fields", "background")],
                             person=charData[getLang("Fields", "personality")],
                             prefilled=charData[getLang("Fields", "prefilled")], ctx=ctx)
        charFile = open(filePath, 'r')

        try:
            await ctx.author.send(getLang("Register", "REGISTER_PREVIEW"), file=discord.File(filePath))
        except:
            await ctx.send(getLang("Register", "REGISTER_FAILED_DM"))
            return
        charFile.close()
        clearLog()

    await ctx.send(getLang("Register", "REGISTER_DM_SENT"))

    user = ctx.author
    registerLoop = True
    misc = json.loads(cfields["misc"])

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

        fullList.remove('misc')

        if not allowPrefilled():
            if getLang("Fields", "prefilled") in blankList:
                blankList.remove(getLang("Fields", "prefilled"))

        for i in blankList:
            blankFields = f"{blankFields} `{i.capitalize()}`,"

        for i in fullList:
            fullFields = f"{fullFields} `{i.capitalize()}`,"

        presfields = ''

        if not blankFields == '':
            presfields = "\n" + getLang("Register", "REGISTER_REDO_FIELDS").format(blankFields)

        await user.send(getLang("Register", "REGISTER_FIELDS").format(fullFields, presfields))

        field = await getdm(ctx)
        selector = field.lower()

        if selector == getLang("Fields", "custom"):
            misc = await custom_Register(ctx, user, misc)
        elif selector == getLang("Fields", "prefilled") and selector not in fullList and not allowPrefilled():
            await user.send(getLang("Register", "REGISTER_BAD_FIELD"))
        elif selector in cfields:
            warn = ''
            if selector == 'misc':
                warn = getLang("Register", "REGISTER_MISC_WARNING")
            await user.send(f'{getLang("Register", "REGISTER_FIELD_INPUT").format(selector.capitalize())}{warn}')
            tempField = await getdm(ctx)
            if selector == getLang("Fields", "name"):
                if await canonCheck(tempField, ctx.author):
                    return
            cfields[selector] = tempField
            await user.send(getLang("Register", "REGISTER_FIELD_CHANGED").format(selector.capitalize()))
        elif selector == getLang("Fields", "preview"):
            try:
                await user.send(embed=previewChar(cfields=cfields, prefilled=None, name=cfields['name'], misc=misc))
            except:
                previewTxt = charToTxt(charID=0, owner=ctx.author.id, status='Preview',
                                       name=cfields[getLang("Fields", "name")],
                                       age=cfields[getLang("Fields", "age")],
                                       gender=cfields[getLang("Fields", "gender")],
                                       abil=cfields[getLang("Fields", "abilities/tools")],
                                       appear=cfields[getLang("Fields", "appearance")],
                                       species=cfields[getLang("Fields", "species")],
                                       backg=cfields[getLang("Fields", "background")],
                                       person=cfields[getLang("Fields", "personality")],
                                       prefilled=cfields[getLang("Fields", "prefilled")], misc=misc, ctx=ctx)
                await user.send(getLang("Register", "REGISTER_PREVIEW_LONG"), file=discord.File(previewTxt))
        elif selector.lower() == getLang("Register", "REGISTER_COMPLETE") or selector.lower() == getLang("Register",
                                                                                                         "REGISTER_STORE"):
            oldchr = _getCharDict(charID=charID)
            resub = await charadd(owner=owner, name=cfields[getLang("Fields", "name")],
                                  age=cfields[getLang("Fields", "age")],
                                  gender=cfields[getLang("Fields", "gender")],
                                  abil=cfields[getLang("Fields", "abilities/tools")],
                                  appear=cfields[getLang("Fields", "appearance")],
                                  species=cfields[getLang("Fields", "species")],
                                  backg=cfields[getLang("Fields", "background")],
                                  person=cfields[getLang("Fields", "personality")],
                                  prefilled=cfields[getLang("Fields", "prefilled")], charID=charID, misc=json.dumps(misc))
            await alertGMs(ctx, charID, resub=True, old=oldchr)
            await user.send(getLang("Register", "REGISTER_SUBMISSION").format(charID))
            registerLoop = False
            return
        elif selector == getLang("Register", "REGISTER_EXIT"):
            await user.send(getLang("Register", "REGISTER_REDO_EXIT"))
            return
        else:
            await user.send(getLang("Register", "REGISTER_BAD_FIELD"))


async def custom_Register(ctx, user, misc):
    isFinished = False
    while not isFinished:
        ccFields = ''
        misc_stripped = {}

        if len(misc) > 0:
            for i in misc:
                misc_stripped[i.lower()] = misc[i]
                ccFields = f"{ccFields} `{i}`,"
        else:
            ccFields = getLang("Register", "REGISTER_CUSTOM_NO_FIELDS")
        await user.send(getLang("Register", "REGISTER_CUSTOM_ASK_GENERIC").format(len(misc), ccFields))

        field = await getdm(ctx)
        if field.lower() == getLang("Send", "SEND_MRC"):
            field = field.upper()
        elif field.lower().capitalize() == getLang("Send", "SEND_PORTRAIT"):
            field = field.lower().capitalize()
        elif field.lower() == 'done':
            isFinished = True
            continue
        await user.send(getLang("Register", "REGISTER_CUSTOM_ASK_SPECIFIC").format(field[0:100]))
        content = await getdm(ctx)
        if content.lower() == 'delete' and field in misc:
            misc.pop(field)
            print(misc)
        elif content.lower() == 'cancel':
            pass
        elif content.lower() == 'delete' and field not in misc:
            await user.send(getLang("Register", "REGISTER_CUSTOM_DELETE_FAILED").format(field))
        else:
            misc[field] = content
            await user.send(getLang("Register", "REGISTER_CUSTOM_SUCCESS").format(field[0:100]))
    return misc


@bot.slash_command(name="newregister", guild_ids=[770428394918641694, 363821745590763520])
async def newregister(inter, character_id:int=None):
    application_embed = discord.Embed(color=discord.Color.yellow())
    field_data = {"Owner": f"{inter.author}", "Status": "Pending", "Name": "", "Age": "", "Gender": "",
                  "Abilities/Tools": "", "Appearance": "", "Species": "", "Backstory": "", "Personality": ""}
    custom_fields = {}
    canon_chars = getDenyList()
    if character_id:
        temp_data = _getCharDict(character_id)
        if isinstance(temp_data, dict) and temp_data[getLang("Fields", "owner")] == inter.author.id:
            for field in temp_data:
                if not temp_data[field]:
                    continue
                else:
                    application_embed.add_field(name=field, value=temp_data[field])
        else:
            character_id = 0
    else:
        character_id = 0
        for fi in field_data:
            application_embed.add_field(name=f"{fi}", value=f"{field_data[fi]}", inline=False)
        application_embed.title = f"Preview for ID {character_id}"

    register_ar_1 = discord.ui.ActionRow(
            discord.ui.Button(label="Basic Info", style=discord.ButtonStyle.blurple,
                              custom_id=f"basic-info_{character_id}"),
            discord.ui.Button(label="Details", style=discord.ButtonStyle.blurple,
                              custom_id=f"details_{character_id}"),
            discord.ui.Button(label="Add Field", style=discord.ButtonStyle.grey,
                              custom_id=f"add-field_{character_id}")
        )
    register_ar_2 = discord.ui.ActionRow(
            discord.ui.Button(label="Submit", style=discord.ButtonStyle.green, custom_id="submit", disabled=True),
            discord.ui.Button(label="Cancel", style=discord.ButtonStyle.red, custom_id=f"cancel")
        )
    i_channel = inter.channel
    app_thread = await i_channel.create_thread(name="Character Registration",
                                               type=discord.ChannelType.private_thread)
    app_message = await app_thread.send(embed=application_embed, components=[
        register_ar_1,
        register_ar_2
    ])
    await app_thread.send(inter.author.mention, allowed_mentions=discord.AllowedMentions(users=True))
    await inter.response.send_message("Started character creation!", ephemeral=True)

    async def update_preview(embed_inter, info):
        embed = embed_inter.embeds[0].copy()
        for f in range(len(embed.fields)):
            if embed.fields[f].name in info.keys():
                key = embed.fields[f].name
                embed.set_field_at(f, name=key, value=info[key], inline=False)
        await embed_inter.edit(embed=embed)

    async def check_completion(inter_msg,  ar, fields_dict):
        completed = True
        for f in fields_dict:
            if fields_dict[f] == "":
                completed = False
        if completed:
            submit_button, cancel_button = ar.children
            submit_button.disabled = False
            ar.clear_items()
            ar.append_item(submit_button)
            ar.append_item(cancel_button)
            await inter_msg.edit(components=[register_ar_1, ar])

    async def check_cfield_no(inter_msg, ar, cfields_dict):
        buttons = []
        cbutton_hidden = True
        for c in ar.children:
            buttons.append(c)
        for b in range(len(buttons)):
            if buttons[b].custom_id.startswith("custom_"):
                cbutton_i = b
                cbutton_hidden = False
            if buttons[b].custom_id.startswith("remove-field_"):
                rbutton_i = b
        if (len(cfields_dict) == 0) and (buttons[cbutton_i].disabled is not True):
            del buttons[cbutton_i]
            del buttons[rbutton_i-1]
            ar.clear_items()
            for but in buttons:
                ar.append_item(but)
            await inter_msg.edit(components=[ar, register_ar_2])
        elif (len(cfields_dict) > 0) and (cbutton_hidden is True):
            buttons.insert(2, discord.ui.Button(label="Custom", style=discord.ButtonStyle.blurple,
                                                custom_id=f"custom_{character_id}"))
            buttons.insert(4, discord.ui.Button(label="Remove Field", style=discord.ButtonStyle.grey,
                                                custom_id=f"remove-field_{character_id}"))
            ar.clear_items()
            for but in buttons:
                ar.append_item(but)
            await inter_msg.edit(components=[ar, register_ar_2])

    class RegisterBasicInfoFields(discord.ui.Modal):
        def __init__(self):
            components = [
                discord.ui.TextInput(
                    label="Character Name",
                    placeholder="The name of your character.",
                    custom_id="Name",
                    style=TextInputStyle.short,
                    max_length=50,
                    value=f"{field_data['Name']}"
                ),
                discord.ui.TextInput(
                    label="Character Age",
                    placeholder="The age of your character.",
                    custom_id="Age",
                    style=TextInputStyle.short,
                    max_length=50,
                    value=f"{field_data['Age']}"
                ),
                discord.ui.TextInput(
                    label="Character Gender",
                    placeholder="Your character's gender.",
                    custom_id="Gender",
                    style=TextInputStyle.short,
                    max_length=50,
                    value=f"{field_data['Gender']}"
                ),
                discord.ui.TextInput(
                    label="Character Species",
                    placeholder="Your character's species.",
                    custom_id="Species",
                    style=TextInputStyle.short,
                    max_length=50,
                    value=f"{field_data['Species']}"
                ),
            ]
            super().__init__(title="Basic Info", components=components)

        # The callback received when the user input is completed.
        async def callback(self, inter: discord.ModalInteraction):
            not_allowed = False
            for key, value in inter.text_values.items():
                if value in canon_chars:
                    await inter.response.send_message("Canon characters are not allowed!", ephemeral=True)
                    not_allowed = True
            if not not_allowed:
                for key, value in inter.text_values.items():
                    if key in field_data.keys():
                        field_data[key] = value
                await check_completion(app_message, register_ar_2, field_data)
                await update_preview(app_message, field_data)
                await inter.response.send_message(f"Character's basic info has been edited!", ephemeral=True)

    class RegisterDetailsFields(discord.ui.Modal):
        def __init__(self):
            components = [
                discord.ui.TextInput(
                    label="Character Abilities and Tools",
                    placeholder="Describe the strengths and weaknesses of your character's abilities and tools.",
                    custom_id="Abilities/Tools",
                    style=TextInputStyle.paragraph,
                    value=f"{field_data['Abilities/Tools']}"
                ),
                discord.ui.TextInput(
                    label="Character Appearance",
                    placeholder="Your character's appearance.",
                    custom_id="Appearance",
                    style=TextInputStyle.paragraph,
                    value=f"{field_data['Appearance']}"
                ),
                discord.ui.TextInput(
                    label="Character Backstory",
                    placeholder="The events leading up to your character's introduction into the RP.",
                    custom_id="Backstory",
                    style=TextInputStyle.paragraph,
                    value=f"{field_data['Backstory']}"
                ),
                discord.ui.TextInput(
                    label="Character Personality",
                    placeholder="Your character's personality.",
                    custom_id="Personality",
                    style=TextInputStyle.paragraph,
                    value=f"{field_data['Personality']}"
                ),
            ]
            super().__init__(title="Details", components=components)

        async def callback(self, inter: discord.ModalInteraction):
            for key, value in inter.text_values.items():
                if key in field_data.keys():
                    field_data[key] = value
            await check_completion(app_message, register_ar_2, field_data)
            await update_preview(app_message, field_data)
            await inter.response.send_message(f"Character's details have been edited!", ephemeral=True)

    class RegisterCustomFields(discord.ui.Modal):
        def __init__(self):
            components = []
            for c in custom_fields:
                ti = discord.ui.TextInput(
                    label=c,
                    custom_id=c,
                    style=TextInputStyle.paragraph,
                    value=custom_fields[c]
                )
                components.append(ti)
            super().__init__(title="Custom Fields", components=components)

        async def callback(self, inter: discord.ModalInteraction):
            for key, value in inter.text_values.items():
                custom_fields[key] = value
            await update_preview(app_message, custom_fields)
            await inter.response.send_message(f"Character's custom fields have been edited!", ephemeral=True)

    class RegisterNewField(discord.ui.Modal):
        def __init__(self):
            components = [
                discord.ui.TextInput(
                    label="New Field Name",
                    placeholder="The title of your custom field.",
                    custom_id="New Field Name",
                    style=TextInputStyle.short,
                ),
                discord.ui.TextInput(
                    label="New Field Text",
                    placeholder="The contents of your custom field.",
                    custom_id="New Field Text",
                    style=TextInputStyle.paragraph,
                )
            ]
            super().__init__(title="New Custom Field", components=components)

        async def callback(self, inter: discord.ModalInteraction):
            app_embed = app_message.embeds[0].copy()
            new_field = []
            dupe_field = False
            for key, value in inter.text_values.items():
                new_field.append(value)
            for f in app_embed.fields:
                if f.name == new_field[0]:
                    await inter.response.send_message("A field already exists with that name!", ephemeral=True)
                    dupe_field = True
            if not dupe_field:
                custom_fields[new_field[0]] = new_field[1]
                app_embed.add_field(name=new_field[0], value=new_field[1])
                await check_cfield_no(app_message, register_ar_1, custom_fields)
                await update_preview(app_message, custom_fields)
                await inter.response.send_message(f"Custom field has been added to application!", ephemeral=True)

    class RegisterRemoveMenu(discord.ui.Select):
        def __init__(self):
            options = []
            for c in custom_fields:
                option = discord.SelectOption(
                    label=c,
                    value=f"cfield_{c}"
                )
                options.append(option)
            super().__init__(options=options, placeholder="Field to delete...")

        #async def callback(self, inter):
        #    print("HEY COMPUTER WORK DAMN YOU")
        #    trgt_field = inter.values  # I doubt this will work, but how are you supposed to get the output?
        #    await update_preview(app_message, custom_fields)
        #    await inter.response.send_message(f"Custom field has been removed from application!", ephemeral=True)

    @bot.listen("on_dropdown")
    async def on_misc_remove(inter):
        app_embed = app_message.embeds[0].copy()
        if inter.data.values[0].startswith("cfield_"):
            cfield = inter.data.values[0].split("_")[-1]
            del custom_fields[cfield]
            for f in range(len(app_embed.fields)):
                if app_embed.fields[f].name == cfield:
                    app_embed.remove_field(f)
                    await app_message.edit(embed=app_embed)
            await check_cfield_no(app_message, register_ar_1, custom_fields)
            await inter.response.send_message(f"Custom field has been removed from application!", ephemeral=True)

    @bot.listen("on_button_click")
    async def on_register_button_click(inter):
        if inter.data.custom_id.startswith('basic-info_'):
            await inter.response.send_modal(modal=RegisterBasicInfoFields())
        elif inter.data.custom_id.startswith("details_"):
            await inter.response.send_modal(modal=RegisterDetailsFields())
        elif inter.data.custom_id.startswith("custom_"):
            await inter.response.send_modal(modal=RegisterCustomFields())
        elif inter.data.custom_id.startswith("add-field_"):
            if len(custom_fields) > 5:
                await inter.response.send_message("You've already made the maximum number of custom fields!")
            else:
                await inter.response.send_modal(modal=RegisterNewField())
        elif inter.data.custom_id.startswith("remove-field_"):
            await inter.response.send_message("What custom field would you like to delete?",
                                              components=RegisterRemoveMenu())
        elif inter.data.custom_id == "cancel":
            await inter.response.send_message("Are you sure you want to cancel character creation?", components=[
                discord.ui.Button(label="Yes", style=discord.ButtonStyle.green, custom_id="confirm_cancel"),
                discord.ui.Button(label="No", style=discord.ButtonStyle.red, custom_id="abort_cancel")
            ])
        elif inter.data.custom_id == "confirm_cancel":
            await inter.response.send_message("Character creation has been stopped.")
        elif inter.data.custom_id == "abort_cancel":
            await inter.response.send_message("Cancellation aborted.", delete_after=5)
            # cancel_message = await inter.original_response()
            # await discord.Message.delete(cancel_message, delay=5)
        elif inter.data.custom_id == "submit":
            await inter.response.send_message("Placeholder 'character has been submitted' message.")


@bot.command(pass_context=True, name=getLang("Commands", "CMD_REGISTER"),
             aliases=[getLang("Commands", "CMD_REREGISTER"), 'submit', 'resubmit'])
async def register(ctx, charID=''):
    if ctx.author.id in currentlyRegistering:
        await ctx.send(getLang("Register", "REGISTER_BUSY"))
        return

    currentlyRegistering.append(ctx.author.id)

    if charID.isnumeric():
        await reRegister(ctx, charID)
        currentlyRegistering.remove(
            ctx.author.id)  # Fixed Bug with sending 'Please check your DMs!' as well as 'You do not own this character!' - Thanks @Venom134
        return

    await ctx.send(getLang("Register", "REGISTER_DM_SENT"))

    await logMSG(getLang("Log", "lg_10").format(ctx.author))
    user = ctx.author
    try:
        sendStr = f'{getLang("Register", "REGISTER_START")}\n'
        if allowPrefilled():
            sendStr = f'{sendStr}{getLang("Register", "REGISTER_START_PREFILLED")}\n'
        sendStr = f'{sendStr}{getLang("Register", "REGISTER_START_EXIT")}'
        await user.send(sendStr)
    except:
        await ctx.send(getLang("Register", "REGISTER_FAILED_DM"))
        currentlyRegistering.remove(user.id)
        return
    await _registerChar(ctx, user)


async def alertGMs(ctx, charID, resub=False, old=None):
    embedC = await _view(ctx, idinput=str(charID), returnEmbed=True)

    ping = True

    if old:
        if old[getLang("Fields", "status")] == getLang("Status", "STATUS_PENDING"):
            ping = False

    embedC.set_footer(text=getLang("Register", "REGISTER_STATUS_CHANGE").format(charID))

    channelID = GMChannel()

    channel = bot.get_channel(channelID)

    isResubmit = ''

    if resub is True:
        isResubmit = f'\n{getLang("Register", "REGISTER_RESUBMIT").format(charID)}'

        new = _getCharDict(charID)
        newStr = ''
        oldStr = ''
        for o in old:
            oldStr = f"{oldStr}\n{o}: {old[o]}"
        for n in new:
            newStr = f"{newStr}\n{n}: {new[n]}"
        differences = getdiff.getDiffCheck(oldStr, newStr)
        isResubmit = f"{isResubmit}\n({getLang('Register', 'REGISTER_DIFFERENCE')} {differences} )\n"

    else:
        isResubmit = ''

    GMRole = discord.utils.get(ctx.guild.roles, name=getLang("Misc", "gm"))

    try:
        if ping:
            await channel.send(
                getLang("Register", "REGISTER_SUBMIT").format(GMRole.id, isResubmit, ctx.author, ctx.author.id),
                embed=embedC)
        else:
            await channel.send(
                getLang("Register", "REGISTER_SUBMIT_NODM").format(isResubmit, ctx.author, ctx.author.id),
                embed=embedC)

    except HTTPException as e:

        charData = _getCharDict(charID)

        charJS = json.loads(charData["misc"])

        filePath = charToTxt(charID=charData["charID"], owner=charData[getLang("Fields", "owner")],
                             status=charData[getLang("Fields", "status")],
                             name=charData[getLang("Fields", "name")], age=charData[getLang("Fields", "age")],
                             gender=charData[getLang("Fields", "gender")],
                             abil=charData[getLang("Fields", "abilities/tools")],
                             appear=charData[getLang("Fields", "appearance")],
                             species=charData[getLang("Fields", "species")],
                             backg=charData[getLang("Fields", "background")],
                             person=charData[getLang("Fields", "personality")],
                             prefilled=charData[getLang("Fields", "prefilled")],
                             misc=charJS, ctx=ctx)

        charFile = open(filePath, 'r')

        if ping:
            await channel.send(
                getLang("Register", "REGISTER_SUBMIT").format(GMRole.id, isResubmit, ctx.author, ctx.author.id),
                file=discord.File(filePath))
        else:
            await channel.send(
                getLang("Register", "REGISTER_SUBMIT_NODM").format(isResubmit, ctx.author, ctx.author.id),
                file=discord.File(filePath))
    except Exception as e:
        await logHandler(getLang("Log", "lg_11"))


def getMember(owner, ctx):
    member = ctx.message.guild.get_member(int(owner))
    return member


def charToTxt(charID, owner, status, name, age, gender, abil, species, appear, backg, person, prefilled, ctx, misc=''):
    curTime = int(time.time())

    miscStr = ''
    if misc != '':
        for i in misc:
            miscStr = f'{miscStr}{i}: {misc[i]}\n\n'

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
    if species != '': charTXT = charTXT + f"{getLang('Fields', 'species').capitalize()}: {species}\n\n"
    if backg != '': charTXT = charTXT + f"{getLang('Fields', 'background').capitalize()}: {backg}\n\n"
    if person != '': charTXT = charTXT + f"{getLang('Fields', 'personality').capitalize()}: {person}\n\n"
    if misc != '': charTXT = charTXT + miscStr
    if prefilled == '' or prefilled is None:
        pass
    else:
        charTXT = charTXT + f"{getLang('Fields', 'prefilled').capitalize()}: {prefilled}\n\n"

    charFile.write(charTXT)

    charFile.close()
    return path


@bot.command(name=getLang("Commands", "CMD_VIEW"), aliases=['cm', 'charmanage'])
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
            await ctx.send(getLang("View", "VIEW_FAILED_BAD_CHARACTER"))
            return

        color = 0x000000

        if (charData[getLang("Fields", "status")] == getLang("Status", "STATUS_PENDING")):
            color = 0xFFD800
        elif (charData[getLang("Fields", "status")] == getLang("Status", "STATUS_APPROVED")):
            color = 0x00FF00
        elif (charData[getLang("Fields", "status")] == getLang("Status", "STATUS_DENIED")):
            color = 0xFF0000

        member = ctx.message.guild.get_member(int(charData[getLang("Fields", "owner")]))

        embedVar = discord.Embed(title=getLang("View", "VIEW_CHARACTER_ID").format(sanID),
                                 description=getLang("View", "VIEW_REGISTER_ID").format(sanID), color=color)

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
                    embedVar.add_field(name=i.title(), value=charData[i],
                                       inline=False)  # Thanks @Casey C. Creeks#0938 for .title() reminder!

        if charData["misc"] == '{}':
            customFields = ''
            pass
        else:
            try:
                customFields = json.loads(charData["misc"])
                miscData = ''
                hasImg = False
                for name, value in customFields.items():
                    print(name, value)
                    valid = validators.url(value)
                    if name.lower().capitalize() == getLang("Send", "SEND_PORTRAIT") and valid == True:
                        embedVar.set_image(url=value)
                        hasImg = True
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
                await ctx.send(getLang("View", "VIEW_LONG_FILE_DUMP"))
            else:
                ctx.author.send(getLang("View", "VIEW_LONG_FILE_DUMP"))
            filePath = charToTxt(charID=charData["charID"], owner=charData[getLang("Fields", "owner")],
                                 status=charData[getLang("Fields", "status")],
                                 name=charData[getLang("Fields", "name")], age=charData[getLang("Fields", "age")],
                                 gender=charData[getLang("Fields", "gender")],
                                 abil=charData[getLang("Fields", "abilities/tools")],
                                 appear=charData[getLang("Fields", "appearance")],
                                 species=charData[getLang("Fields", "species")],
                                 backg=charData[getLang("Fields", "background")],
                                 person=charData[getLang("Fields", "personality")],
                                 prefilled=charData[getLang("Fields", "prefilled")],
                                 misc=customFields, ctx=ctx)

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
        getLang("Fields", "species"): None,
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


@bot.command(name=getLang("Commands", "CMD_SET"), aliases=['setprop'])
async def _set(ctx, charID='', field='', *, message: str = ''):
    alertChannel = bot.get_channel(LogChannel())

    if charID == '' or field == '':
        if charID == '':
            text = getLang("Set", "SET_FAILED_NO_ID")
        else:
            text = getLang("Set", "SET_FAILED_NO_FIELD")
        await ctx.send(getLang("Set", "SET_FAILED_INVALID_DATA").format(text))
        return

    if field.lower() in fields:
        fSan = convertField(field.lower())

        if fSan == 'charID':
            await ctx.send(getLang("Set", "SET_FAILED_ID_STATIC"))
            return
    else:
        await _custom(ctx, charID=charID, field=field, message=message)
        return

    if message == '' or message == getLang("Set", "SET_DELETE"):
        message = ''
        if fSan == getLang("Fields", "name"):
            await ctx.send(getLang("Set", "SET_FAILED_NAME_REQUIRED"))
            return
        elif fSan == 'misc':
            message = '{}'

    if fSan == 'owner' or fSan == 'status':
        if await checkGM(ctx) is False:
            await ctx.send(getLang("Set", "SET_FAILED_NO_PROPERTY_PERMISSION"))
            return

    if charID.isnumeric():
        icharID = int(charID)
    else:
        await ctx.send(getLang("View", "VIEW_FAILED_BAD_CHARACTER"))
        return

    ownerID = _charExists(icharID)

    if ownerID == False:
        await ctx.send(getLang("View", "VIEW_FAILED_BAD_CHARACTER"))
        return

    if not charPermissionCheck(ctx, ownerID):
        await ctx.send(getLang("Set", "SET_FAILED_NO_PERMISSION"))
        return

    _setSQL(icharID, fSan, message)

    if message == '':
        await ctx.send(getLang("Set", "SET_FIELD_DELETED").format(field.capitalize()))
    else:
        await ctx.send(getLang("Set", "SET_FIELD_CHANGED").format(field.capitalize()))

    await alertChannel.send(getLang("Log", "lg_12").format(ctx.author, icharID, field.capitalize(), message))


def _setSQL(charID, field, content):
    cur = conn.cursor()

    sql = f'''UPDATE charlist SET {field} = ? WHERE charID is ?'''
    cur.execute(sql, [content, charID])
    conn.commit()


async def _custom(ctx, charID='', field='', *, message: str):
    alertChannel = bot.get_channel(LogChannel())

    if field.lower().capitalize() == getLang("Send", "SEND_PORTRAIT"):
        field = field.lower().capitalize()
    elif field.lower() == getLang("Send", "SEND_MRC"):
        field = field.upper()

    if charID.isnumeric():
        icharID = int(charID)
    else:
        await ctx.send(getLang("Custom", "CUSTOM_FAILED_BAD_CHARACTER"))
        return

    charData = _getCharDict(icharID)

    if charData == 'INVALID CHARACTER':
        await ctx.send(getLang("Custom", "CUSTOM_FAILED_BAD_CHARACTER"))
        return

    if not charPermissionCheck(ctx, ctx.author.id):
        await ctx.send(getLang("Custom", "CUSTOM_FAILED_NOT_OWNER"))
        return

    customFields = json.loads(charData["misc"])
    fieldDel = False

    if message.lower() == getLang("Set", "SET_DELETE"):
        try:
            customFields.pop(field)
            fieldDel = True
        except:
            await ctx.send(getLang("Custom", "CUSTOM_FAILED_BAD_FIELD"))
            return
    else:
        customFields[field] = message
    miscData = json.dumps(customFields)
    _setSQL(icharID, "misc", miscData)
    if fieldDel == False:
        await ctx.send(getLang("Custom", "CUSTOM_SUCCESS_FIELD_SET").format(field))
        await alertChannel.send(getLang("Log", "lg_12").format(ctx.author, icharID, field.capitalize(), message))
        return

    await ctx.send(getLang("Custom", "CUSTOM_SUCCESS_FIELD_DELETED").format(field))

    await alertChannel.send(getLang("Log", "lg_13").format(ctx.author, icharID, field.capitalize()))


async def _custom_error(ctx, args):
    await ctx.send(getLang("Custom", "CUSTOM_FAILED_BLANK_FIELD"))


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
        charListStr = getLang("GetChars", "GET_CHAR_INFO").format(charListStr, i.id, i.name[0:75],
                                                                  member or i.owner) + '\n'

    if len(charList) == 0:
        await ctx.send(getLang("GetChars", "GET_FAILED_NONE_MATCHED"))
        return

    await ctx.send(getLang("GetChars", "GET_LIST").format((member or userID + getLang("Fields", "left")), (pageNo + 1),
                                                          math.ceil(count / pageSize), charListStr))


@bot.command(name=getLang("Commands", "CMD_LIST"))
async def _list(ctx, pageIdentifier='', page=''):
    if not page.isnumeric() and page != '' and not ctx.message.mentions:
        await ctx.send(f"{page} is not a valid page!")
        return

    '''Shows a list of all characters, sorted into pages of 20 Characters.
    Mentioning a user or user ID will bring up all characters belonging to that user.

    USAGE:
    rp!list <PAGE>
    rp!list <MENTION|USER ID> <PAGE>'''

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
        elif ctx.message.mentions:
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
        charListStr = getLang("List", "LIST_CHAR_INFO").format(charListStr, i.id, i.name[0:75],
                                                               member or i.owner) + '\n'
    print(charListStr)
    await ctx.send(getLang("List", "LIST_ALL").format(pageNo + 1, math.ceil(count / pageSize), charListStr))


fields = [getLang("Fields", 'owner'), 'ownerid', getLang("Fields", 'status'), getLang("Fields", 'name'), 'charid', 'id',
          getLang("Fields", 'age'), getLang("Fields", 'gender'), getLang("Fields", 'abilities/tools'), 'abilities',
          getLang("Fields", 'appearance'), getLang("Fields", 'background'), getLang("Fields", 'personality'),
          'prefilled', getLang("Fields", 'prefilled'), 'custom', 'misc', getLang("Fields", 'species')]


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


@bot.command(name=getLang("Commands", "CMD_SEARCH"))
async def _search(ctx, selector='', extra1='', extra2=''):
    if selector == '':
        await ctx.send(getLang("Search", "SEARCH_FAILED_NO_QUERY"))
        return

    if (ctx.message.mentions):
        await _list(ctx, selector, extra1)
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

    sql = f'''SELECT charid, owner, name FROM charlist WHERE {field} LIKE ? AND status IS NOT 'Disabled' LIMIT ? OFFSET ?'''
    cur.execute(sql, ['%' + search + '%', pageSize, (pageSize * pageNo)])

    charList = [CharacterListItem(id=charID, name=name, owner=owner) for charID, owner, name in cur]

    if rawR is True:
        return charList

    charListStr = ''

    for i in charList:
        member = ctx.message.guild.get_member(int(i.owner))
        charListStr = getLang("GetChars", "GET_CHAR_INFO").format(charListStr, i.id, i.name[0:75],
                                                                  member or i.owner) + '\n'

    await ctx.send(
        f'{getLang("Search", "SEARCH_LIST_MATCHING").format(pageNo + 1, math.ceil(count / pageSize))} \n{charListStr}')


@bot.command(name=getLang("Commands", "CMD_DELETE"))
async def _delete(ctx, charDel='', confirmation=''):
    if charDel.isnumeric():
        if confirmation.lower() == getLang("Delete", "DELETE_CONFIRM"):
            await _deleteChar(ctx, int(charDel))
            return
        else:
            await ctx.send(getLang("Delete", "DELETE_REQUEST_CONFIRMATION"))
            response = await bot.wait_for("message", check=message_check())
            if response.content.lower() == getLang("Delete", "DELETE_CONFIRM"):
                await _deleteChar(ctx, int(charDel))
                return
    else:
        await ctx.send("Invalid Character ID!")


@bot.command(name=getLang("Commands", "CMD_RESTORE"), aliases=[getLang("Commands", "CMD_RESTORE_UNDELETE")])
async def _undelete(ctx, charID):
    if not await checkGM(ctx):
        await ctx.send(getLang("Delete", "DELETE_FAILED_NO_PERMISSION"))
        return

    if charID.isnumeric():
        icharID = int(charID)

    cursor = conn.cursor()

    cursor.execute("UPDATE charlist SET status = 'Pending' WHERE charID is ?", [icharID])
    conn.commit()
    await ctx.send(getLang("Delete", "DELETE_RECOVERED").format(icharID))


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
        await ctx.send(getLang("Delete", "DELETE_FAILED_BAD_CHARACTER"))
        return

    cursor = conn.cursor()

    if charPermissionCheck(ctx, ownerID=ownerP) is True:
        cursor.execute(f"UPDATE charlist SET status = 'Disabled' WHERE charID is ?", [charID])
        conn.commit()
        await ctx.send(f"Character {charID} has been deleted.")
    else:
        await ctx.send(getLang("Delete", "DELETE_FAILED_NOT_OWNER"))


def previewChar(cfields=None, prefilled=None, name=None, misc=None):
    embedVar = discord.Embed(title=getLang("Register", "REGISTER_SHOW_PREVIEW_NOID"),
                             description=getLang("Register", "REGISTER_SHOW_PREVIEW_ID"), color=0xffD800)

    if misc:
        cfields["misc"] = misc

    if cfields is not None:
        embedVar.add_field(name=getLang("Fields", "name").capitalize() + ':', value=cfields[getLang("Fields", 'name')],
                           inline=True)
        if cfields['age'] != '': embedVar.add_field(name=getLang("Fields", "age").capitalize() + ':',
                                                    value=cfields[getLang("Fields", 'age')], inline=False)
        if cfields['gender'] != '': embedVar.add_field(name=getLang("Fields", "gender").capitalize() + ':',
                                                       value=cfields[getLang("Fields", 'gender')], inline=False)
        if cfields['abilities/tools'] != '': embedVar.add_field(
            name=getLang("Fields", "abilities/tools").title() + ':',
            value=cfields[getLang("Fields", 'abilities/tools')], inline=False)
        if cfields['appearance'] != '': embedVar.add_field(name=getLang("Fields", "appearance").capitalize() + ':',
                                                           value=cfields[getLang("Fields", 'appearance')],
                                                           inline=False)
        if cfields['species'] != '': embedVar.add_field(name=getLang("Fields", "species").capitalize() + ':',
                                                            value=cfields[getLang("Fields", 'species')],
                                                            inline=False)
        if cfields['backstory'] != '': embedVar.add_field(name=getLang("Fields", "backstory").capitalize() + ':',
                                                           value=cfields[getLang("Fields", 'background')],
                                                           inline=False)
        if cfields['personality'] != '': embedVar.add_field(name=getLang("Fields", "personality").capitalize() + ':',
                                                            value=cfields[getLang("Fields", 'personality')],
                                                            inline=False)
        tempVar = json.loads(cfields["misc"])
        for i in tempVar:
            embedVar.add_field(name=i, value=tempVar[i], inline=False)

    if prefilled:
        embedVar.add_field(name=getLang("Fields", "name").capitalize() + ':', value=name, inline=False)
        embedVar.add_field(name=getLang("Fields", "prefilled").capitalize() + ':', value=prefilled, inline=False)

    return embedVar


@bot.command(name=getLang("Commands", "CMD_INVITE"))
async def invite(ctx):
    await ctx.send(getLang("Misc", "invite"))


async def canonCheck(response, user):
    global canonDeny
    response = response.lower()

    response = re.sub(r'[\W_]+', '', response)

    print(response)

    if any(canon_char in response for canon_char in getDenyList()):  # Thanks, Atlas!
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

        if resmsg == getLang("Register", "REGISTER_EXIT"):
            await user.send(getLang("Register", "REGISTER_ABORTED"))
            currentlyRegistering.remove(user.id)
            isRegistering = False
            return
        elif resmsg == getLang("Register", "REGISTER_NEXT"):

            charcomplete = False
            submitChar = False
            prefilled = None

            cfields = {
                getLang("Fields", "name"): None,
                getLang("Fields", "gender"): None,
                getLang("Fields", "age"): None,
                getLang("Fields", "abilities/tools"): None,
                getLang("Fields", "appearance"): None,
                getLang("Fields", "species"): None,
                getLang("Fields", "background"): None,
                getLang("Fields", "personality"): None,
            }

            await user.send(getLang("Register", "REGISTER_ASK_NAME"))

            response = await getdm(ctx)

            if await canonCheck(response, user):
                return

            cfields[getLang("Fields", "name")] = response

            await user.send(getLang("Register", "REGISTER_ASK_FIELDS_GENERIC"))

            while not charcomplete:

                # MAIN CHARACTER REGISTRATION LOOP

                response = await getdm(ctx)
                selector = response.lower()

                if selector == getLang("Register", "REGISTER_EXIT"):
                    await user.send(getLang("Register", "REGISTER_ABORTED"))
                    isRegistering = False
                    currentlyRegistering.remove(user.id)
                    return

                if selector == getLang("Register", "REGISTER_COMPLETE") or response.lower() == getLang(
                        "Register", "REGISTER_STORE"):
                    if not submitChar:
                        await user.send(getLang("Register", "REGISTER_INCOMPLETE"))
                    else:
                        submitChar = True
                        charcomplete = True

                        owner = ctx.author.id
                        prefilled = None

                        if selector == getLang("Register", "REGISTER_STORE"):
                            charStatus = getLang("Status", "STATUS_DENIED")
                        else:
                            charStatus = getLang("Status", "STATUS_PENDING")

                        charID = await charadd(owner=owner, name=cfields[getLang("Fields", "name")],
                                               age=cfields[getLang("Fields", "age")],
                                               status=charStatus,
                                               gender=cfields[getLang("Fields", "gender")],
                                               abil=cfields[getLang("Fields", "abilities/tools")],
                                               appear=cfields[getLang("Fields", "appearance")],
                                               species=cfields[getLang("Fields", "species")],
                                               backg=cfields[getLang("Fields", "background")],
                                               person=cfields[getLang("Fields", "personality")],
                                               prefilled=prefilled)

                        currentlyRegistering.remove(user.id)

                        if selector == getLang("Register", "REGISTER_COMPLETE"):
                            await user.send(getLang("Register", "REGISTER_SUCCESS_ID").format(int(charID)))
                            await alertGMs(ctx, charID)
                        else:
                            await user.send(getLang("Register", "REGISTER_SUCCESS_STORE").format(int(charID)))
                        return
                elif selector == getLang("Register", "REGISTER_EXIT"):
                    await user.send(getLang("Register", "REGISTER_ABORTED"))
                    isRegistering = False
                    currentlyRegistering.remove(user.id)
                    return
                elif selector == getLang("Register", "REGISTER_VIEW_PREVIEW"):
                    try:
                        await user.send(embed=previewChar(cfields=cfields))
                    except:
                        await user.send(getLang("Register", "REGISTER_PREVIEW_FAILED_LONG"))
                elif selector in cfields:
                    await user.send(getLang("Register", "REGISTER_ASK_FIELDS_SPECIFIC").format(selector.capitalize()))
                    response = await getdm(ctx)

                    if selector == getLang("Fields", "name"):
                        if await canonCheck(response, user):
                            break
                            return

                    if selector == getLang("Register", "REGISTER_EXIT"):
                        await user.send(getLang("Register", "REGISTER_ABORTED"))
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
                        await user.send(
                            getLang("Register", "REGISTER_FIELD_CHANGED_COMPLETE").format(selector.capitalize(),
                                                                                          specifyDone))
                        submitChar = True
                    else:
                        await user.send(
                            getLang("Register", "REGISTER_FIELD_CHANGED_INCOMPLETE").format(selector.capitalize(),
                                                                                            toSpecify, specifyDone))
                else:
                    await user.send(getLang("Register", "REGISTER_BAD_FIELD"))

            return
        elif resmsg == getLang("Fields", "prefilled") and allowPrefilled():

            charcomplete = False

            await user.send(getLang("Register", "REGISTER_PREFILLED_ASK_NAME"))
            response = await getdm(ctx)

            if await canonCheck(response, user):
                return

            if response.lower() == getLang("Register", "REGISTER_EXIT"):
                await user.send(getLang("Register", "REGISTER_ABORTED"))
                isRegistering = False
                currentlyRegistering.remove(user.id)
                return

            name = response

            await user.send(getLang("Register", "REGISTER_PREFILLED_ASK_CHARACTER"))
            prefilled = await getdm(ctx)
            if prefilled.lower() == getLang("Register", "REGISTER_EXIT"):
                await user.send(getLang("Register", "REGISTER_ABORTED"))
                isRegistering = False
                currentlyRegistering.remove(user.id)
                return

            charFields = [getLang("Fields", "prefilled"), getLang("Fields", "name")]

            while not charcomplete:
                await user.send(getLang("Register", "REGISTER_PREFILLED_COMPLETE"))
                response = await getdm(ctx)
                selector = response.lower()

                if selector == getLang("Register", "REGISTER_EXIT"):
                    await user.send(getLang("Register", "REGISTER_ABORTED"))
                    isRegistering = False
                    currentlyRegistering.remove(user.id)
                    return

                if selector not in charFields:
                    if selector == getLang("Register", "REGISTER_COMPLETE"):

                        charID = await charadd(owner=ctx.author.id, name=name, prefilled=prefilled)

                        await user.send(getLang("Register", "REGISTER_PREFILLED_SUCCESS_ID").format(str(charID)))
                        currentlyRegistering.remove(user.id)
                        await alertGMs(ctx, charID)
                        charcomplete = True
                        return
                    elif selector == getLang("Register", "REGISTER_VIEW_PREVIEW"):
                        try:
                            await user.send(embed=previewChar(prefilled=prefilled, name=name))
                        except:
                            await user.send(getLang("Register", "REGISTER_PREVIEW_FAILED_LONG"))

                    else:
                        await user.send(getLang("Register", "REGISTER_BAD_FIELD"))
                elif selector == getLang("Fields", "name"):
                    await user.send(getLang("Register", "REGISTER_PREFILLED_ASK_NAME_GENERIC"))
                    response = await getdm(ctx)

                    if await canonCheck(response, user):
                        return

                    if response.lower() == getLang("Register", "REGISTER_EXIT"):
                        await user.send(getLang("Register", "REGISTER_ABORTED"))
                        isRegistering = False
                        currentlyRegistering.remove(user.id)
                        return
                    name = response
                    await user.send(getLang("Register", "REGISTER_PREFILLED_NAME_SUCCESS"))

                else:
                    await user.send(getLang("Register", "REGISTER_PREFILLED_ASK_CHARACTER"))
                    response = await getdm(ctx)
                    if response.lower() == getLang("Register", "REGISTER_EXIT"):
                        await user.send(getLang("Register", "REGISTER_ABORTED"))
                        isRegistering = False
                        currentlyRegistering.remove(user.id)
                        return
                    prefilled = response
            return

        else:
            await user.send(getLang("Register", "REGISTER_INVALID"))


#  EVAL COMMAND. - https://gist.github.com/nitros12/2c3c265813121492655bc95aa54da6b9

def insert_returns(body):
    # insert return stmt if the last expression is an expression statement
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


@bot.command(name=getLang("Commands", "CMD_EVAL"))
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


@bot.command(name=getLang("Commands", "CMD_HELP"))
async def help(ctx):
    await ctx.send(getLang("Misc", "help"))


## Log Handling ##

async def logHandler(message):
    channel = bot.get_channel(LogChannel())
    if channel:
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


@bot.command(name=getLang("Commands", "CMD_FORCE_BACKUP"))
@commands.is_owner()
async def _forceBackup(ctx):
    if doBackup():
        await runBackup()
    else:
        await ctx.send(getLang("Misc", "MISC_BACKUP_DISABLED"))


@bot.event
async def on_message(message):
    if message.content.startswith('$'):
        full_content = message.content[1:]
        if len(full_content) == 0:
            return
        name_split = full_content.split(':')
        name = f'%{name_split[0]}%'
        name_split.pop(0)
        content = ':'.join(name_split)
        if len(content) == 0 or len(name) == 2:
            return
        sql = '''SELECT charID FROM charlist WHERE owner IS ? AND status IS ? AND name LIKE ?'''
        cur = conn.cursor()
        cur.execute(sql, [message.author.id, 'Approved', name])
        temp = cur.fetchone()
        if not temp:
            if message.channel.category.name.lower() == 'the void':
                await send(message, id=None, message=content, raw_name=name[1:-1])
                return
            else:
                await message.author.send(getLang('Send', 'SEND_FAILED_NO_CHARS').format(name[1:-1]))
                return
        id, = temp
        await send(message, id=id, message=content)
    else:
        await bot.process_commands(message)


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

@bot.command(name=getLang("Commands", "CMD_SEND_WEBHOOK"))
async def send(ctx, id, *, message: str, raw_name=None):

    if id:
        charData = _getCharDict(id)
        if charData == 'INVALID CHARACTER':
            try:
                await ctx.author.send(getLang("Send", "SEND_FAILED_BAD_CHARACTER"))
            except Exception as e:
                await logMSG(getLang("Send", "SEND_FAILED_LOG").format(ctx.author, ctx.author.id, e))
            await ctx.message.delete()
            return

        if ctx.author.id != int(charData["owner"]):
            try:
                await ctx.author.send(getLang("Send", "SEND_FAILED_NOT_OWNER"))
            except Exception as e:
                await logMSG(getLang("Send", "SEND_FAILED_LOG").format(ctx.author, ctx.author.id, e))
            await ctx.message.delete()
            return

        if charData[getLang("Fields", "status")] != getLang("Status", "STATUS_APPROVED"):
            try:
                await ctx.author.send(getLang("Send", "SEND_FAILED_NOT_APPROVED"))
            except Exception as e:
                await logMSG(getLang("Send", "SEND_FAILED_LOG").format(ctx.author, ctx.author.id, e))
            await ctx.message.delete()
            return

        portJS = json.loads(charData["misc"])
        custom_img = None

        # Checks if in MRC and applies MRC nickname instead.

        if (ctx.channel.name).lower() == getLang("Send", "SEND_MRC") and getLang("Send", "SEND_MRC").casefold() in (
                i.casefold() for
                i in portJS):
            i_l = {}
            for i in portJS:
                i_l[i.lower()] = portJS[i]
            name = i_l[getLang("Send", "SEND_MRC")]
        else:
            name = charData[getLang("Fields", "name")]

        if getLang("Send", "SEND_PORTRAIT").lower().capitalize() in portJS:
            custom_img = portJS[getLang("Send", "SEND_PORTRAIT")]

    else:
        name = raw_name
        custom_img = None
    name = name[0:80]

    await webhook_manager.send(ctx, name, message, custom_img)


bot.run(token)
close_connection(database)
print(getLang("Misc", "shutdown"))
