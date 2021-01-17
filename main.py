import asyncio
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


async def configLoader():
    try:
        with open('.config') as file:
            print("Config Loaded!")

            conf = getConfig()

            gmchannel = bot.get_channel(GMChannel())
            logchannel = bot.get_channel(LogChannel())

            validGMChannel = False

            try:
                await gmchannel.send("Bot has loaded successfully.")
            except:
                validGMChannel = True

            try:
                await logchannel.send("Logging has loaded successfully.")
            except:
                if validGMChannel:
                    await bot.get_channel(GMChannel())


    except (FileNotFoundError, IOError):
        file = open('.config', 'x')

        configDict = {
            'gmchannel': 0,
            'logchannel': 0
        }

        cfgJson = json.dumps(configDict)

        file.write(cfgJson)


bot = commands.Bot(
    command_prefix=['rp!', 'sans!', 'mtt!', 'arik ', 'bliv pls ', 'bliv ', 'https://en.wikipedia.org/wiki/Insanity ',
                    'Rp!'],
    intents=intents, case_insensitive=True)
bot.remove_command("help")
currentlyRegistering = []


def getConfig():
    with open('.config', 'r') as file:
        jsonOBJ = json.load(file)
        file.close()
    return jsonOBJ


def GMChannel():
    conf = getConfig()
    return int(conf["gmchannel"])


def LogChannel():
    conf = getConfig()
    return int(conf["logchannel"])


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
            print("Database does not exist! Generating new Database")
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
        print(f"Connection Failed! - " + {str(e)})

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
        await ctx.author.send("You should do this in a server, you know.")
    return ctx.guild is not None


@bot.check
async def globally_block_roles(ctx):
    blacklist = ["NPC"]
    return not any(get(ctx.guild.roles, name=name) in ctx.author.roles for name in blacklist)


@bot.check
async def block_during_backup(ctx):
    return not backupOngoing


@bot.check
async def block_help(ctx):
    if ctx.channel.name == 'help':
        await ctx.send(f"This is the help channel. Please go to #bots for any bot commands, <@{ctx.author.id}>")
        await ctx.message.delete()
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
        print(cur.lastrowid)
        return cur.lastrowid
    else:

        charwid = character + (int(charID),)
        sql = '''UPDATE charlist SET owner=?,status=?,name=?,age=?,gender=?,abil=?,appear=?,backg=?,person=?,prefilled=? WHERE charID=?'''
        cur = conn.cursor()
        cur.execute(sql, charwid)
        conn.commit()
        print(cur.lastrowid)
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
        return (seq,)


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


@bot.command(name='setGMChannel')
async def _setGMCChannel(ctx):
    role_names = [role.name for role in ctx.author.roles]

    if "Gamemaster" not in role_names:
        await ctx.reply("You do not have permission to change the GM Channel!")
        return

    updateConfig('gmchannel', ctx.channel.id)

    await ctx.reply("Successfully set GM Channel!")


@bot.command(name='setLogChannel')
async def _setLogChannel(ctx):
    if not await checkGM(ctx):
        await ctx.reply("You do not have permission to change the Log Channel!")
        return

    updateConfig('logchannel', ctx.channel.id)
    await ctx.reply("Successfully set logging channel!")


def updateConfig(field, value):
    with open('.config', 'r') as file:
        jsonOBJ = json.load(file)
        file.close()

    jsonOBJ[field] = value

    with open('.config', 'w') as file:
        json.dump(jsonOBJ, file)


@bot.command()
async def approve(ctx, charID, *, reason: str):
    '''GM ONLY - Approves a specified character.'''
    await _changeStatus(ctx, charID=charID, charStatus='Approved', reason=reason)


@bot.command()
async def pending(ctx, charID, *, reason: str):
    '''GM ONLY - Sets a specified character to Pending.'''
    await _changeStatus(ctx, charID=charID, charStatus='Pending', reason=reason)


@bot.command()
async def deny(ctx, charID, *, reason: str):
    '''GM ONLY - Denies a specified character.'''
    await _changeStatus(ctx, charID=charID, charStatus='Denied', reason=reason)


@bot.command()
async def kill(ctx, charID, *, reason: str):
    '''GM ONLY - Kills a specified character.'''
    await _changeStatus(ctx, charID=charID, charStatus='Dead', reason=reason)


@approve.error
@pending.error
@deny.error
@kill.error
async def _approveE(ctx, charID):
    await ctx.reply("You need to give a reason to change the status of a character!")


async def checkGM(ctx):
    role_names = [role.name for role in ctx.author.roles]

    if "Gamemaster" not in role_names:
        return False
    else:
        return True


async def alertUser(ctx, charID, status, reason):
    charData = _getCharDict(charID)

    ownerID = charData["Owner"]
    name = charData["Name"]

    print('debug')

    user = ctx.guild.get_member(int(ownerID))

    if user == None:
        await ctx.reply(
            f"I was unable to send a message to the owner of Character {charID}. User either does not exist or has left the server.")
        return

    try:
        await user.send(
            f"The status of character ID **{charID}** (Name: **{name[0:100]}**) has been set to `{status}` by {ctx.author.mention} for:\n{reason}")
    except:
        ctx.reply(f"I was unable to send a message to the owner of Character {charID}. They may have their DMs closed!")


async def _changeStatus(ctx, charID='', charStatus='Pending', reason=''):
    if not await checkGM(ctx):
        await ctx.reply("You do not have permission to do this!")
        return

    if charID.isnumeric():
        charInt = int(charID)
    else:
        await ctx.reply("That is not a valid character ID!")
        return

    logChannel = bot.get_channel(LogChannel())
    await logChannel.send(f"{ctx.author} set character ID {charInt} to status {charStatus}")

    cursor = conn.cursor()
    sql = '''UPDATE charlist SET status = ? WHERE charID is ?'''
    cursor.execute(sql, [charStatus, charInt])
    conn.commit()

    if charStatus == 'Approved':
        charData = _getCharDict(charInt)
        userid = charData["Owner"]
        user = ctx.guild.get_member(int(userid))
        role = get(ctx.guild.roles, name="Roleplayer")
        await user.add_roles(role)

    await alertUser(ctx, charInt, charStatus, reason)
    await ctx.reply(f"Character `ID: {charID}` has been set to `{charStatus}`")


async def reRegister(ctx, charID):
    cursor = conn.cursor()
    cursor.execute(f"SELECT owner FROM charlist WHERE charID IS {charID} AND status IS NOT 'Disabled'")

    owner = cursor.fetchone()

    if owner is None:
        await ctx.reply("That character does not exist!")
        return
    else:
        ownerP = owner[0]

    if int(ownerP) != ctx.author.id:
        print(ownerP)
        await ctx.reply("You do not own this character!")
        return

    charData = _getCharDict(int(charID))

    if charData == 'INVALID CHARACTER':
        ctx.reply("That is not a valid character!")

    cfields = {
        "name": '',
        "gender": '',
        "age": '',
        "abilities/tools": '',
        "appearance": '',
        "background": '',
        "personality": '',
        "prefilled": '',
    }

    owner = charData["Owner"]
    status = charData["Status"]
    cfields['name'] = charData["Name"]
    cfields['age'] = charData["Age"]
    cfields['gender'] = charData["Gender"]
    cfields['abilities/tools'] = charData["Abilities/Tools"]
    cfields['appearance'] = charData["Appearance"]
    cfields['background'] = charData["Background"]
    cfields['personality'] = charData["Personality"]
    cfields['prefilled'] = charData["Prefilled Application"]

    embedV = await _view(ctx, charID, dmchannel=True, returnEmbed=True)

    try:
        await ctx.author.send("Here is your character currently.", embed=embedV)
    except:
        filePath = charToTxt(charID=charID, owner=owner, status=status, name=cfields['name'], age=cfields['age'],
                             gender=cfields['gender'], abil=cfields['abilities/tools'],
                             appear=cfields['appearance'], backg=cfields['background'], person=cfields['personality'],
                             prefilled=cfields['prefilled'], ctx=ctx)
        charFile = open(filePath, 'r')

        try:
            await ctx.author.send("Here is your character currently.", file=discord.File(filePath))
        except:
            await ctx.reply("Unable to send a DM! Please check your privacy settings and try again.")
            return
        charFile.close()
        clearLog()

    await ctx.reply(":mailbox_with_mail: Please check your DMs!")

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

        for i in blankList:
            blankFields = f"{blankFields} `{i.capitalize()}`,"

        for i in fullList:
            fullFields = f"{fullFields} `{i.capitalize()}`,"

        presfields = ''

        if not blankFields == '':
            presfields = f"\nYou can also add one of the following fields that are not currently present within your application:\n {blankFields}"

        await user.send(
            f"What field would you like to modify? Current Fields:\n{fullFields}" + presfields + "\nTo preview your character, type `preview`. If you are done, type `done` to resubmit your character.")

        field = await getdm(ctx)
        selector = field.lower()

        if selector in cfields:
            await user.send(f"What would you like field {selector.capitalize()} to say?")
            cfields[selector] = await getdm(ctx)
            await user.send(f"Field {selector.capitalize()} has been changed.")
        elif selector == 'preview':
            try:
                await user.send(embed=previewChar(cfields=cfields, prefilled=None, name=cfields['name']))
            except:
                previewTxt = charToTxt(0, ctx.author.id, 'Preview', cfields["name"], cfields["age"], cfields["gender"],
                                       cfields["abilities/tools"], cfields["appearance"], cfields["background"],
                                       cfields["personality"], cfields["prefilled"], ctx, '')
                await user.send("Your character is too long to preview, so I have dumped it to a file!",
                                file=discord.File(previewTxt))
        elif selector == 'done':

            await user.send(
                f"Your character (ID {charID}) has been resubmitted and will be reviewed at the next available oppurtunity.")
            resub = await charadd(owner=owner, name=cfields["name"], age=cfields["age"],
                                  gender=cfields["gender"],
                                  abil=cfields["abilities/tools"],
                                  appear=cfields["appearance"], backg=cfields["background"],
                                  person=cfields["personality"],
                                  prefilled=cfields["prefilled"], charID=charID)

            await alertGMs(ctx, charID, resub=True)
            registerLoop = False
            return
        elif selector == 'exit':
            await user.send("Exiting Character Resubmission!")
            return
        else:
            await user.send("That is not a valid field!")


@bot.command(pass_context=True, aliases=['reregister', 'submit', 'resubmit'])
async def register(ctx, charID=''):
    if ctx.author.id in currentlyRegistering:
        await ctx.reply("You are already registering a character!")
        return

    currentlyRegistering.append(ctx.author.id)

    if charID.isnumeric():
        await reRegister(ctx, charID)
        currentlyRegistering.remove(
            ctx.author.id)  # Fixed Bug with sending 'Please check your DMs!' as well as 'You do not own this character!' - Thanks @Venom134
        return

    await ctx.reply(":mailbox_with_mail: Please check your DMs!")
    for word in currentlyRegistering:
        print(word)

    print("DEBUG: REGISTER COMMAND FROM USER ID: ", ctx.author.id, " - ", ctx.author)
    user = ctx.author
    try:
        await user.send("**Let's submit your character.** \n \n"
                        "If you're submitting a regular character, please type `next` and follow the prompts. \n"
                        "If you already have a character typed out, please type `prefilled` to submit a prefilled application. *(Not Recommended)* \n"
                        "If you do not wish to register, type `exit` to quit at any point.")
    except:
        await ctx.reply("Unable to send a DM! Please check your privacy settings and try again!")
        currentlyRegistering.remove(user.id)
        return
    await _registerChar(ctx, user)


async def alertGMs(ctx, charID, resub=False):
    embedC = await _view(ctx, idinput=str(charID), returnEmbed=True)

    embedC.set_footer(text=f"To change the status of this character, type rp!<approve|pending|deny> {charID}.")

    channelID = GMChannel()

    channel = bot.get_channel(channelID)

    isResubmit = ''

    if resub is True:
        isResubmit = f'**RESUBMISSION FOR CHARACTER ID {charID}**\n'
    else:
        isResubmit = ''

    GMRole = discord.utils.get(ctx.guild.roles, name="Gamemaster")

    try:
        await channel.send(
            f"<@&{GMRole.id}>\n{isResubmit}Character application from {ctx.author} (ID: {ctx.author.id})\n",
            embed=embedC)
    except HTTPException as e:

        await logHandler(
            f"Unable to post raw character data on submission. Compressing to text file.\nFull Exception:\n{e}")

        charData = _getCharDict(charID)

        charJS = json.loads(charData["misc"])
        charSTR = ''

        for name, value in charJS.items():
            charSTR = f"{charSTR}\n{name}:{value}"

        filePath = charToTxt(charID=charData["charID"], owner=charData["Owner"], status=charData["Status"],
                             name=charData["Name"], age=charData["Age"], gender=charData["Gender"],
                             abil=charData["Abilities/Tools"],
                             appear=charData["Appearance"], backg=charData["Background"],
                             person=charData["Personality"], prefilled=charData["Prefilled Application"],
                             misc=charSTR, ctx=ctx)

        charFile = open(filePath, 'r')

        await channel.send(
            f"<@&363821920854081539>\n{isResubmit}Character application from {ctx.author} (ID: {ctx.author.id})\n",
            file=discord.File(filePath))
    except Exception as e:
        await logHandler(
            f"There was a fatal error trying to alert upon registration of a character. Full Exception:\n{e}")


def getMember(owner, ctx):
    member = ctx.message.guild.get_member(int(owner))
    return member


def charToTxt(charID, owner, status, name, age, gender, abil, appear, backg, person, prefilled, ctx, misc=''):
    curTime = int(time.time())

    path = f"charoverflow/{curTime}-{charID}.txt"

    charFile = open(path, 'x')

    charTXT = (f"Character Information for Character ID {charID}\n"
               f"Owner: {getMember(owner, ctx) or owner + ' (Owner has left server.)'}\n"
               f"Status: {status}\n\n"
               f"Name: {name}\n\n")
    if age != '': charTXT = charTXT + f"Age: {age}\n\n"
    if gender != '': charTXT = charTXT + f"Gender: {gender}\n\n"
    if abil != '': charTXT = charTXT + f"Abilities/Tools: {abil}\n\n"
    if appear != '': charTXT = charTXT + f"Appearance: {appear}\n\n"
    if backg != '': charTXT = charTXT + f"Background: {backg}\n\n"
    if person != '': charTXT = charTXT + f"Personality: {person}\n\n"
    if misc != '': charTXT = charTXT + misc
    if prefilled == '' or prefilled is None:
        pass
    else:
        charTXT = charTXT + f"Prefilled: {prefilled}\n\n"

    charFile.write(charTXT)

    charFile.close()
    return path


@bot.command(name='view', aliases=['cm', 'charmanage', 'samwhy'])
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
            await ctx.reply("That is not a valid character!")
            return

        color = 0x000000

        if (charData["Status"] == 'Pending'):
            color = 0xFFD800
        elif (charData["Status"] == 'Approved'):
            color = 0x00FF00
        elif (charData["Status"] == 'Denied'):
            color = 0xFF0000

        member = ctx.message.guild.get_member(int(charData["Owner"]))

        embedVar = discord.Embed(title=f"Viewing Character {sanID}",
                                 description=f"Showing Information for Character ID: {sanID}", color=color,
                                 inline=False)

        noDisplay = ['charID', 'misc', 'Owner']

        charOwner = ctx.guild.get_member(int(charData["Owner"]))

        embedVar.add_field(name='Owner', value=charOwner or f'{charData["Owner"]} (User has left server)', inline=False)

        for i in charData:
            if i not in noDisplay:
                if charData[i] == '' or charData[i] is None:
                    pass
                else:
                    embedVar.add_field(name=i, value=charData[i], inline=False)

        if charData["misc"] == '{}':
            pass
        else:
            try:
                customFields = json.loads(charData["misc"])
                miscData = ''
                for name, value in customFields.items():
                    print(name)
                    embedVar.add_field(name=name, value=value, inline=False)
                    miscData = f"{miscData}\n{name}: {value}"
            except:
                pass

        if returnEmbed is True:
            return embedVar

        try:
            if dmchannel is False:
                await ctx.reply(embed=embedVar)
            else:
                await ctx.author.send(embed=embedVar)
        except:
            if dmchannel is False:
                await ctx.reply(f"This character was too long, so I have dumped it to a file.")
            else:
                ctx.author.send(f"This character was too too long, so I have dumped it to a file.")
            filePath = charToTxt(charID=charData["charID"], owner=charData["Owner"], status=charData["Status"],
                                 name=charData["Name"], age=charData["Age"], gender=charData["Gender"],
                                 abil=charData["Abilities/Tools"],
                                 appear=charData["Appearance"], backg=charData["Background"],
                                 person=charData["Personality"], prefilled=charData["Prefilled Application"],
                                 misc=miscData, ctx=ctx)

            charFile = open(filePath, 'r')
            if dmchannel is False:
                await ctx.reply(file=discord.File(filePath))
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
    print(checkStatus)

    if checkStatus == 'Disabled':
        print("Invalid Character")
        return charInvalid

    return charInfo


def _getCharDict(charID=0):
    cur = conn.cursor()

    charData = {
        "charID": None,
        "Owner": None,
        "Status": None,
        "Name": None,
        "Age": None,
        "Gender": None,
        "Abilities/Tools": None,
        "Appearance": None,
        "Background": None,
        "Personality": None,
        "Prefilled Application": None,
        "misc": None,
    }

    sql = '''SELECT * FROM charlist WHERE charID is ?'''

    cur.execute(sql, [charID])

    chars = cur.fetchone()
    print(chars)

    x = 0

    if chars is None:
        return 'INVALID CHARACTER'

    for i in charData:
        charData[i] = chars[x]
        x = x + 1

    if (charData['Status'] == 'Disabled'):
        return 'INVALID CHARACTER'

    return charData


@bot.command(name='set', aliases=['setprop'])
async def _set(ctx, charID, field, *, message: str):
    '''Sets a field to a specified value. For major character revisions, please use rp!reregister <ID>

    USAGE: rp!set <ID> <FIELD> <What you want the field to be>

    Valid Fields:

    Name
    Age
    Gender
    Abilities | Abilities/Tools
    Appearance
    Background
    Personality
    Prefilled | Prefilled Application

    Owner (GM ONLY)
    Status (GM ONLY)
    '''

    alertChannel = bot.get_channel(LogChannel())

    if field.lower() in fields:
        fSan = convertField(field.lower())

        if fSan == 'charID':
            await ctx.reply("You can not change the ID of a character!")
            return
    else:
        await _custom(ctx, charID=charID, field=field, message=message)
        return

    if message == '' or message == 'delete':
        message = ''
        if fSan == 'name':
            await ctx.reply("You can not remove a characters' name!")
            return
        elif fSan == 'misc':
            message = '{}'

    if fSan == 'owner' or fSan == 'status':
        if await checkGM(ctx) is False:
            await ctx.reply("You need to be a GM to change this!")
            return

    if charID.isnumeric():
        icharID = int(charID)
    else:
        await ctx.reply("That is not a valid character ID!")
        return

    ownerID = _charExists(icharID)

    if ownerID == False:
        await ctx.reply("This character does not exist!")
        return

    if not charPermissionCheck(ctx, ownerID):
        await ctx.reply("You do not have permission to modify this character!")
        return

    _setSQL(icharID, fSan, message)

    if message == '':
        await ctx.reply(f"Field {field.capitalize()} has been deleted.")
    else:
        await ctx.reply(f"Field {field.capitalize()} has been changed.")

    await alertChannel.send(
        f"{ctx.author} has modified Character ID: `{icharID}`. Field `{field.capitalize()}` has been set to:\n`{message}`")


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
        await ctx.reply("That is not a valid character ID!")
        return

    charData = _getCharDict(icharID)

    if charData == 'INVALID CHARACTER':
        await ctx.reply("That is not a valid character!")
        return

    if ctx.author.id != int(charData["Owner"]):
        await ctx.reply("You do not own this character!")
        return

    customFields = json.loads(charData["misc"])
    print(customFields)
    fieldDel = False

    if len(customFields) >= 12:
        await ctx.reply(
            "You can not have more than 12 custom fields! Either modify an existing field, or remove an unneeded field.")
        return

    if message.lower() == 'delete':
        try:
            customFields.pop(field)
            fieldDel = True
        except:
            await ctx.reply("This field does not exist!")
            return
    else:
        customFields[field] = message
    print(customFields)
    miscData = json.dumps(customFields)
    _setSQL(icharID, "misc", miscData)
    if fieldDel == False:
        await ctx.reply(f"Custom field {field} has been set.")
        await alertChannel.send(
            f"{ctx.author} has modified Character ID: `{icharID}`. Field `{field.capitalize()}` has been set to:\n`{message}`")
        return

    await ctx.reply(f"Custom field {field} has been deleted.")

    await alertChannel.send(
        f"{ctx.author} has modified Character ID: `{icharID}`. Field `{field.capitalize()}` has been deleted.")


async def _custom_error(ctx, args):
    await ctx.reply("Unable to set a custom field to a blank value!")


@dataclass
class CharacterListItem:
    """Stores Basic Character Information in a Class"""
    id: int
    name: str
    owner: str


async def getUserChars(ctx, userID, pageSize, pageID):
    pageNo = int(pageID - 1)

    print(pageNo)
    cursor = conn.cursor()
    userInt = int(userID)
    cursor.execute(f"SELECT count(*) FROM charlist WHERE status IS NOT 'Disabled' AND owner IS {userID}")
    count = cursor.fetchone()[0]
    print(count)

    cursor.execute(
        f"SELECT charID, name, owner FROM charlist WHERE status IS NOT 'Disabled' AND owner IS {userInt} ORDER BY charID LIMIT {pageSize} OFFSET {pageNo * pageSize}")

    charList = [CharacterListItem(charID, name, owner) for charID, name, owner in cursor]
    charListStr = ''

    for i in charList:
        member = ctx.message.guild.get_member(int(i.owner))
        charListStr = f"{charListStr}**`{i.id}.`** {i.name[0:75]} (Owner: {member or i.owner})\n"

    if len(charList) == 0:
        await ctx.reply("No characters matched the query!")
        return

    await ctx.reply(
        f"List of characters belonging to {member or userID + ' (User has left server)'} (Page: {pageNo + 1} of {math.ceil(count / pageSize)})\n{charListStr}")


@bot.command(name='list')
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
    print(charList)

    charListStr = ''

    for i in charList:
        member = ctx.message.guild.get_member(int(i.owner))
        charListStr = f"{charListStr}**`{i.id}.`** {i.name[0:75]} (Owner: {member or i.owner})\n"

    await ctx.reply(f"List of all characters: (Page: {pageNo + 1} of {math.ceil(count / pageSize)})\n{charListStr}")


fields = ['owner', 'ownerid', 'status', 'name', 'charid', 'id', 'age', 'gender', 'abilities/tools', 'abilities',
          'appearance', 'background', 'personality', 'prefilled', 'prefilled application', 'custom', 'misc']


def convertField(selector):
    if selector == 'owner' or selector == 'ownerid':
        return 'owner'
    if selector == 'id' or selector == 'charid':
        return 'charID'
    if selector == 'appearance':
        return 'appear'
    if selector == 'background':
        return 'backg'
    if selector == 'abilities/tools' or selector == 'abilities':
        return 'abil'
    if selector == 'personality':
        return 'person'
    if selector == 'prefilled' or selector == 'prefilled application':
        return 'prefilled'
    if selector == 'misc' or selector == 'custom':
        return 'misc'
    return selector


@bot.command(name='search')
async def _search(ctx, selector='', extra1='', extra2=''):
    '''Searches for a character using fields provided.


    USAGE:
    rp!search <NAME> - Searches for characters with a specific name.
    rp!search <FIELD> <QUERY> - Searches a specific field for a search query.'''

    if selector == '':
        await ctx.reply("You have not entered anything to search!")
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
    print(charList)

    if rawR is True:
        print("Returning")
        return charList

    charListStr = ''

    for i in charList:
        member = ctx.message.guild.get_member(int(i.owner))
        charListStr = f"{charListStr}**`{i.id}.`** {i.name[0:30]} (Owner: {member or i.owner})\n"

    await ctx.reply(
        f"List of characters meeting search criteria (Page {pageNo + 1} of {math.ceil(count / 25)}):\n{charListStr}")


@bot.command(name='delete')
async def _delete(ctx, charDel='', confirmation=''):
    '''Deletes a specified character.

    USAGE:
    rp!delete <ID>'''

    if charDel.isnumeric():
        if confirmation.lower() == 'confirm':
            await _deleteChar(ctx, int(charDel))
            return
        else:
            await ctx.reply("Are you sure you wish to delete this character? Please type `confirm` if you are sure.")
            response = await bot.wait_for("message", check=message_check())
            if response.content.lower() == 'confirm':
                await _deleteChar(ctx, int(charDel))
                return
    else:
        await ctx.reply("Invalid Character ID!")


@bot.command(name='undelete', aliases=['recover'])
async def _undelete(ctx, charID):
    if not await checkGM(ctx):
        await ctx.reply("You do not have permission to do this!")
        return

    if charID.isnumeric():
        icharID = int(charID)

    cursor = conn.cursor()

    cursor.execute("UPDATE charlist SET status = 'Pending' WHERE charID is ?", [icharID])
    conn.commit()
    await ctx.reply(f"Character {icharID} has been recovered.")


def charPermissionCheck(ctx, ownerID):
    role_names = role_names = [role.name for role in ctx.author.roles]

    authorID = ctx.author.id

    if int(ownerID) == authorID or "Gamemaster" in role_names:
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
        await ctx.reply("That character does not exist!")
        return

    cursor = conn.cursor()

    if charPermissionCheck(ctx, ownerID=ownerP) is True:
        cursor.execute(f"UPDATE charlist SET status = 'Disabled' WHERE charID is ?", [charID])
        conn.commit()
        await ctx.reply(f"Character {charID} has been deleted.")
    else:
        await ctx.reply("You do not own this character!")


async def getdm(ctx):
    response = await bot.wait_for('message', check=message_check(channel=ctx.author.dm_channel))
    attach = None
    if response.attachments:
        print(str(ctx.author) + " submitted an attachment!")
        attach = str(response.attachments[0].url)
        finalResponse = attach + ' ' + response.content
    else:
        print(str(ctx.author) + " submitted no attachments.")
        finalResponse = response.content
    return finalResponse


def previewChar(cfields=None, prefilled=None, name=None):
    embedVar = discord.Embed(title=f"Previewing Your Character",
                             description=f"Showing Preview for Character", color=0xffD800)

    if cfields is not None:
        embedVar.add_field(name="Name:", value=cfields['name'], inline=True)
        if cfields['age'] != '': embedVar.add_field(name="Age:", value=cfields['age'], inline=False)
        if cfields['gender'] != '': embedVar.add_field(name="Gender:", value=cfields['gender'], inline=False)
        if cfields['abilities/tools'] != '': embedVar.add_field(name="Abilities/Tools:",
                                                                value=cfields['abilities/tools'], inline=False)
        if cfields['appearance'] != '': embedVar.add_field(name="Appearance:", value=cfields['appearance'],
                                                           inline=False)
        if cfields['background'] != '': embedVar.add_field(name="Background:", value=cfields['background'],
                                                           inline=False)
        if cfields['personality'] != '': embedVar.add_field(name="Personality:", value=cfields['personality'],
                                                            inline=False)

    if prefilled:
        embedVar.add_field(name="Name:", value=name, inline=False)
        embedVar.add_field(name="Prefilled Application:", value=prefilled, inline=False)

    return embedVar


@bot.command()
async def invite(ctx):
    await ctx.reply("This bot is a private bot and is not currently available to invite.\n"
                    "If you wish to run it yourself, you can download the source code here:\n"
                    "https://github.com/OblivionCreator/mettaton-2.py\n"
                    "`THIS SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.`")


canonDeny = ["sans", "papyrus", "frisk", "flowey", "undyne", "alphys", "mettaton", "asgore", "asriel",
             "chara", "muffet", "pepsi man", "toriel", "kris", "ralsei", "shrek", "betty",
             "fallenfire", "gaster"]  # To do - Make this into a function.


async def canonCheck(response, user):
    global canonDeny
    response = response.lower()

    if any(canon_char in response for canon_char in canonDeny):  # Thanks Atlas!
        await user.send(
            "**Canon Characters are not allowed. Please read the <#697160109700284456> and <#697153009599119493>**\n"
            "Exiting Character Creation.")

        logChannel = bot.get_channel(LogChannel())

        await logChannel.send(
            f"{user} ({user.id}) tried submitting a canon character! (Name {response} matched one or more characters in the deny list.)")

        currentlyRegistering.remove(user.id)
        return True
    return False


async def _registerChar(ctx, user):
    '''USAGE:
    rp!register
    rp!register <ID> | reregister <ID>

    Registers a new character, or resubmits an existing character if an ID is input.

    Guides you through the command. Pleas_alere see #rules and #policy for more help.'''

    isRegistering = True

    while isRegistering:
        resmsg = await getdm(ctx)
        resmsg = resmsg.lower()

        if resmsg == 'exit':
            await user.send("Character submission aborted.")
            currentlyRegistering.remove(user.id)
            isRegistering = False
            return
        elif resmsg == 'next':

            charcomplete = False
            submitChar = False
            prefilled = None

            cfields = {
                "name": None,
                "gender": None,
                "age": None,
                "abilities/tools": None,
                "appearance": None,
                "background": None,
                "personality": None,
            }

            await user.send(
                "Great! Let's start filling out your character. First of all, what is your characters name?")

            response = await getdm(ctx)

            if await canonCheck(response, user):
                return

            cfields['name'] = response

            await user.send("Now that your character has a name, let's start filling out some details.\n"
                            "What field would you like to edit?\n"
                            "Remaining fields to specify: `Age`, `Gender`, `Abilities/Tools`, `Appearance`, `Background`, `Personality`\n"
                            "Fields already specified: `Name`")

            while not charcomplete:

                # MAIN CHARACTER REGISTRATION LOOP

                response = await getdm(ctx)
                if response.lower() == 'exit':
                    await user.send("Exiting Character Creation!")
                    isRegistering = False
                    currentlyRegistering.remove(user.id)
                    return
                selector = response.lower()

                if response.lower() == 'done':
                    if not submitChar:
                        await user.send(
                            "You character is not complete! Please fill the remaining fields before trying to submit your character.")
                    else:
                        submitChar = True
                        charcomplete = True

                        owner = ctx.author.id
                        prefilled = None

                        charID = await charadd(owner=owner, name=cfields["name"], age=cfields["age"],
                                               gender=cfields["gender"],
                                               abil=cfields["abilities/tools"],
                                               appear=cfields["appearance"], backg=cfields["background"],
                                               person=cfields["personality"],
                                               prefilled=prefilled)

                        await user.send("Character has been submitted with ID: " + str(charID))
                        currentlyRegistering.remove(user.id)
                        await alertGMs(ctx, charID)
                        return
                elif response.lower() == 'exit':
                    await user.send(
                        "Exiting Character Creation!")
                    isRegistering = False
                    currentlyRegistering.remove(user.id)
                    return
                elif response.lower() == 'preview':
                    try:
                        await user.send(embed=previewChar(cfields=cfields))
                    except:
                        await user.send("This character is too long to preview!")
                elif selector in cfields:
                    await user.send("What would you like field `" + selector.capitalize() + "` to say?")
                    response = await getdm(ctx)

                    if selector.lower() == 'name':
                        if await canonCheck(response, user):
                            break
                            return

                    if response.lower() == 'exit':
                        await user.send("Exiting Character Creation!")
                        isRegistering = False
                        currentlyRegistering.remove(user.id)
                        return

                    cfields[selector] = response

                    emptyFields = []
                    completeFields = []

                    for x in cfields:
                        if cfields[x] is None:
                            emptyFields.append(x)
                            print(x + " is empty!")
                        else:
                            completeFields.append(x)
                            print(x + " is complete!")
                    print("Checks Complete")

                    toSpecify = ''
                    specifyDone = ''

                    for word in emptyFields:
                        print(word)
                        toSpecify = (toSpecify + "`" + word.capitalize() + "`, ")

                    for word2 in completeFields:
                        print(word2)
                        specifyDone = (specifyDone + "`" + word2.capitalize() + "`, ")

                    if not toSpecify:
                        await user.send(
                            f"Field `{selector.capitalize()}` has been changed.\n"
                            "All fields have been completed. If you wish to submit your character, type `Done`. To preview your character, type `Preview`.\n"
                            f"Or if you wish to change a field, enter the field you wish to modify: {specifyDone}")
                        submitChar = True
                    else:
                        await user.send(
                            f"Field `{selector.capitalize()}` has been changed.\n"
                            "What field would you like to edit?\n"
                            f"Remaining fields to specify: {toSpecify}\n"
                            f"Field(s) already specified: {specifyDone}")

                else:
                    await user.send("That is not a valid field!")

            return
        elif resmsg == 'prefilled':

            charcomplete = False

            await user.send(
                "Great! First of all, Before submitting your application, what is your characters name?")
            response = await getdm(ctx)

            if await canonCheck(response, user):
                return

            if response.lower() == 'exit':
                await user.send("Exiting Character Creation!")
                isRegistering = False
                currentlyRegistering.remove(user.id)
                return

            name = response

            await user.send(
                "Let's submit your character. \nPlease upload, link or paste in your character. Web links, text files and raw text are all accepted, and will be handled appropriately.")
            prefilled = await getdm(ctx)
            if prefilled.lower() == 'exit':
                await user.send("Exiting Character Creation!")
                isRegistering = False
                currentlyRegistering.remove(user.id)
                return

            charFields = ["prefilled application", "name"]

            while not charcomplete:
                await user.send(
                    "Your character is ready to submit. If you wish to change any fields, please state what you would like to change. If you would like to submit your character, enter `Done` or to preview your character, enter `Preview`\n"
                    "Fields: `Name`, `Prefilled Application`")
                response = await getdm(ctx)
                selector = response.lower()

                if selector == 'exit':
                    await user.send("Exiting Character Creation!")
                    isRegistering = False
                    currentlyRegistering.remove(user.id)
                    return

                if selector not in charFields:
                    if selector == 'done':

                        charID = await charadd(owner=ctx.author.id, name=name, prefilled=prefilled)

                        await user.send("Great! Your character has been submitted with ID: **" + str(charID) + "**")
                        currentlyRegistering.remove(user.id)
                        await alertGMs(ctx, charID)
                        charcomplete = True
                        return
                    elif selector == 'preview':
                        try:
                            await user.send(embed=previewChar(prefilled=prefilled, name=name))
                        except:
                            await user.send("This character is too long to preview!")

                    else:
                        await user.send("That is not a valid field! Please try again.")
                elif selector == 'name':
                    await user.send("What would you like the name to be?")
                    response = await getdm(ctx)

                    if await canonCheck(response, user):
                        return

                    if response.lower() == 'exit':
                        await user.send("Exiting Character Creation!")
                        isRegistering = False
                        currentlyRegistering.remove(user.id)
                        return
                    name = response
                    await user.send("Your Characters name has been set.")

                else:
                    await user.send(
                        "Please upload, link or paste in your character. Web links, text files and raw text are all accepted, and will be handled appropriately.")
                    response = await getdm(ctx)
                    if response.lower() == 'exit':
                        await user.send("Exiting Character Creation!")
                        isRegistering = False
                        currentlyRegistering.remove(user.id)
                        return
                    prefilled = response
            return

        else:
            await user.send("Invalid response. Please try again.")


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


@bot.command(name='eval')
@commands.is_owner()
async def eval_fn(ctx, *, cmd):
    '''LOCKED TO OBLIVION ONLY. DO NOT USE.

    Evalutes an expression.'''

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
    await ctx.reply(result)


@bot.command()
async def help(ctx):
    await ctx.reply(
        "For help, please check out the Wiki on Github!\nhttps://github.com/OblivionCreator/mettaton-2.py/wiki")


## Log Handling ##

async def logHandler(message):
    channel = bot.get_channel(LogChannel())
    await channel.send(message)


## Other ##

@bot.command()
async def replytest(ctx):
    await ctx.reply("TEST REPLY")


## Auto Backup ##

@tasks.loop(seconds=60)
async def autoBackup():
    t = datetime.now()
    c_t = t.strftime("%H:%M")
    if c_t == "00:00":
        await runBackup()


@bot.command(name='forcebackup')
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
    await channel.send("Starting Backup! The bot may not respond to commands.")
    status = discord.Status.idle
    await bot.change_presence(activity=discord.Game("Auto-Backup in Progress!"), status=status)

    print("Closing Database Connection...")
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
    print("Reopening Database Connection...")

    timerEnd = time.perf_counter()
    await channel.send(f"Backup Complete in {str((timerEnd - timerStart))[0:5]} seconds.")

    backupOngoing = False
    await statusChanger()


## Fun Stuff ##

@bot.command()
@commands.cooldown(1, 3600, commands.BucketType.guild)
async def sans(ctx):
    if random.randint(0, 100) <= 10:
        await ctx.reply(open('resources/ascii_papyrus.txt', encoding="utf-8").read())
    else:
        await ctx.reply(open('resources/ascii_sans.txt', encoding="utf-8").read())


@bot.command()
@commands.cooldown(1, 60, commands.BucketType.guild)
async def papyrus(ctx):
    await ctx.reply(f"Nice Try, <@{str(ctx.author.id)}>")


@tasks.loop(minutes=5)
async def changeStatus():
    await statusChanger()


async def statusChanger():
    status = discord.Status.online

    statusChoice = ['Aik has Played Undertale', 'Meme', 'with Bliv\'s feelings', 'with Bliv\'s Owner Role',
                    'old enough for soriel',
                    'haha he smope weef', 'SHUP', 'AMA', '...meme?', 'role!unban', '1000 blood', 'blame AIK',
                    'blame Bliv', 'blame Samario', 'blame Wisty', 'Venom is a Furry', 'blankets = lewd???',
                    'oblivion pinged everyone', 'oblivion pinged everyone... again', 'arrrr peee?', 'buzzy bee',
                    'this server contains chemicals known to the nation of Arkias to cause cancer.',
                    'No Thoughts. Dream Empty', 'Stuck in a Nightmare\'s Paradise', 'PUBBY',
                    'You have OneShot at this.', 'What plant is Lotus?', 'Default Dance', 'Mystiri is All',
                    'This server has been murder free for 0 Months', 'Pending', 'Vampire Celery', 'Bugsonas Are Real',
                    'Arik files tax returns', 'Are you here to RP or be cringe', 'VillagerHmm',
                    'Member Retention now at 1%', 'with Smol Bot', 'bnuuy', 'More lines than one of SJ\'s Characters',
                    'Dead Parents', 'with the edge.']

    await bot.change_presence(activity=discord.Game(random.choice(statusChoice)))


bot.run(token)
close_connection(database)

print(
    "Bot Shutting Down. This message should only show if you have stopped the bot manually. If you see this message and have not shut down the bot on purpose, please raise an issue on GitHub with as much information as possible!")
