import asyncio
import glob
import math
import os
import random
import discord
from discord.ext import commands
import sqlite3
from sqlite3 import Error
from collections.abc import Sequence
import ast
from dataclasses import dataclass
import time
import json

from discord.utils import get

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix=['rp!', 'sans!', 'mtt!', 'arik ', 'bliv pls ', 'bliv ', 'https://en.wikipedia.org/wiki/Insanity ',
                    'Rp!'],
    intents=intents, case_insensitive=True)
bot.remove_command("help")
currentlyRegistering = []


def GMChannel():
    with open('.config') as file:
        GMChannel = int(file.read())
        return GMChannel


@bot.event
async def on_ready():
    with open('.config') as file:
        GMChannel = int(file.read())
        clearLog()
        try:
            #await (bot.get_channel(GMChannel)).send("Mettaton 2.0.5 Loaded!")
            bot.loop.create_task(changeStatus())

        except:
            print(GMChannel)
            print("GMChannel is invalid!")

        file.close()


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print("Connection Failed! - " + e)

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


async def charadd(owner, name, age='', gender='', abil='', appear='', backg='', person='', prefilled='',
                  status='Pending', charID=''):
    character = (owner, status, name, age, gender, abil, appear, backg, person, prefilled)

    """
    :param conn:
    :param character:
    :return: charID
    """

    if charID == '':
        sql = '''INSERT INTO charlist(owner,status,name,age,gender,abil,appear,backg,person,prefilled) VALUES(?,?,?,?,?,?,?,?,?,?)'''
        cur = conn.cursor()
        cur.execute(sql, character)
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
        await ctx.send("You do not have permission to change the GM Channel!")
        return
    with open('.config', 'w') as outfile:
        outfile.write(str(ctx.message.channel.id))
        outfile.close()

    await ctx.send("Successfully set GM Channel!")


@bot.command()
async def approve(ctx, charID, *args):
    '''GM ONLY - Approves a specified character.'''
    reason = ' '.join(args)
    await _changeStatus(ctx, charID=charID, charStatus='Approved', reason=reason)


@bot.command()
async def pending(ctx, charID, *args):
    '''GM ONLY - Sets a specified character to Pending.'''
    reason = ' '.join(args)
    await _changeStatus(ctx, charID=charID, charStatus='Pending', reason=reason)


@bot.command()
async def deny(ctx, charID, *args):
    '''GM ONLY - Denies a specified character.'''
    reason = ' '.join(args)
    await _changeStatus(ctx, charID=charID, charStatus='Denied', reason=reason)


@bot.command()
async def kill(ctx, charID, *args):
    '''GM ONLY - Kills a specified character.'''
    reason = ' '.join(args)
    await _changeStatus(ctx, charID=charID, charStatus='Dead', reason=reason)


async def checkGM(ctx):
    role_names = [role.name for role in ctx.author.roles]

    if "Gamemaster" not in role_names:
        return False
    else:
        return True


async def alertUser(ctx, charID, status, reason):
    charData = _getChar(charID)

    ownerID, = charData[1:2]
    name, = charData[3:4]

    print('debug')

    user = ctx.guild.get_member(int(ownerID))

    if user == None:
        await ctx.send(
            f"I was unable to send a message to the owner of Character {charID}. User either does not exist or has left the server.")
        return

    try:
        await user.send(
            f"The status of character ID **{charID}** (Name: **{name[0:100]}**) has been set to `{status}` by {ctx.author.mention} for:\n{reason}")
    except:
        ctx.send(f"I was unable to send a message to the owner of Character {charID}. They may have their DMs closed!")


async def _changeStatus(ctx, charID='', charStatus='Pending', reason=''):
    if not await checkGM(ctx):
        await ctx.send("You do not have permission to do this!")
        return

    try:
        if charID.isnumeric():
            charInt = int(charID)
        else:
            await ctx.send("That is not a valid character ID!")
            return
    except:
        charInt = charID

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
    await ctx.send(f"Character `ID: {charID}` has been set to `{charStatus}`")


async def reRegister(ctx, charID):
    cursor = conn.cursor()
    cursor.execute(f"SELECT owner FROM charlist WHERE charID IS {charID} AND status IS NOT 'Disabled'")

    owner = cursor.fetchone()

    if owner is None:
        await ctx.send("That character does not exist!")
        return
    else:
        ownerP = owner[0]

    if int(ownerP) != ctx.author.id:
        print(ownerP)
        await ctx.send("You do not own this character!")
        return

    charData = _getChar(int(charID))

    if charData == 'INVALID CHARACTER':
        ctx.send("That is not a valid character!")

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

    owner, = charData[1:2]
    status, = charData[2:3]
    cfields['name'], = charData[3:4]
    cfields['age'], = charData[4:5]
    cfields['gender'], = charData[5:6]
    cfields['abilities/tools'], = charData[6:7]
    cfields['appearance'], = charData[7:8]
    cfields['background'], = charData[8:9]
    cfields['personality'], = charData[9:10]
    cfields['prefilled'], = charData[10:11]

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
            ctx.send(":mailbox_with_mail: Please check your DMs!")
        except:
            await ctx.send("Unable to send a DM! Please check your privacy settings and try again.")
            return
        charFile.close()
        clearLog()

    await ctx.send(":mailbox_with_mail: Please check your DMs!")

    user = ctx.author
    registerLoop = True

    while (registerLoop):

        blankList = []
        fullList = []
        blankFields = ''
        fullFields = ''

        for i in cfields:
            temp = cfields.get(i)
            if temp == '':
                blankList.append(i)
            else:
                fullList.append(i)

        for i in blankList:
            blankFields = f"{blankFields} `{i.capitalize()}`,"

        for i in fullList:
            fullFields = f"{fullFields} `{i.capitalize()}`,"

        await user.send(
            f"What field would you like to modify? Current Fields:\n{fullFields}\n You can also add one of the following fields that are not currently present within your application:\n" + blankFields)

        field = await getdm(ctx)
        selector = field.lower()

        if selector in cfields:
            await user.send(f"What would you like field {selector.capitalize()} to say?")
            cfields[selector] = await getdm(ctx)
            await user.send(f"Field {selector.capitalize()} has been changed.")
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
        await ctx.send("You are already registering a character!")
        return

    currentlyRegistering.append(ctx.author.id)

    if charID.isnumeric():
        await reRegister(ctx, charID)
        currentlyRegistering.remove(
            ctx.author.id)  # Fixed Bug with sending 'Please check your DMs!' as well as 'You do not own this character!' - Thanks @Venom134
        return

    await ctx.send(":mailbox_with_mail: Please check your DMs!")
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
        await ctx.send("Unable to send a DM! Please check your privacy settings and try again!")
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

    await channel.send(
        f"<@&363821920854081539>\n{isResubmit}Character application from {ctx.author} (ID: {ctx.author.id})\n",
        embed=embedC)


def getMember(owner, ctx):
    member = ctx.message.guild.get_member(int(owner))
    return member


def charToTxt(charID, owner, status, name, age, gender, abil, appear, backg, person, prefilled, ctx, misc=''):
    curTime = int(time.time())

    path = f"charoverflow/{curTime}-{charID}.txt"

    charFile = open(path, 'x')

    charTXT = (f"Character Information for Character ID {charID}\n" \
               f"Owner: {getMember(owner, ctx) or owner + ' (Owner has left server.)'}\n" \
               f"Status: {status}\n" \
               f"Name: {name}\n")
    if age != '': charTXT = charTXT + f"Age: {age}\n"
    if gender != '': charTXT = charTXT + f"Gender: {gender}\n"
    if abil != '': charTXT = charTXT + f"Abilities/Tools: {abil}\n"
    if appear != '': charTXT = charTXT + f"Appearance: {appear}\n"
    if backg != '': charTXT = charTXT + f"Background: {backg}\n"
    if person != '': charTXT = charTXT + f"Personality: {person}\n"
    if misc != '': charTXT = charTXT + misc
    if prefilled == '' or prefilled is None:
        pass
    else:
        charTXT = charTXT + f"Prefilled: {prefilled}\n"

    charFile.write(charTXT)

    charFile.close()
    return path


@bot.command(name='view', aliases=['cm', 'charmanage', 'samwhy'])
async def _view(ctx, idinput='', dmchannel=False, returnEmbed=False):
    '''Brings up character information for the specified character.

    USAGE:
    rp!view <ID>'''

    if not idinput.isnumeric() or int(idinput) == 0:
        await ctx.send("That is not a valid character ID!")
    else:
        sanID = int(idinput)

        charData = _getCharDict(sanID)

        if charData == 'INVALID CHARACTER':
            await ctx.send("That is not a valid character!")
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

        MiscData = ''

        if charData["misc"] == '{}':
            pass
        else:
            try:
                customFields = json.loads(charData["misc"])
                miscData = ''
                for i in customFields:
                    print(i)
                    embedVar.add_field(name=i, value=customFields[i], inline=False)
                    miscData = f"{miscData}\n{i}: {customFields[i]}"
            except:
                pass

        if returnEmbed is True:
            return embedVar

        try:
            if dmchannel is False:
                await ctx.send(embed=embedVar)
            else:
                await ctx.author.send(embed=embedVar)
        except:
            if dmchannel is False:
                await ctx.send(f"This character was too long, so I have dumped it to a file.")
            else:
                ctx.author.send(f"This character was too too long, so I have dumped it to a file.")
            filePath = charToTxt(charID=charData["charID"], owner=charData["Owner"], status=charData["Status"],
                                 name=charData["Name"], age=charData["Age"], gender=charData["Gender"],
                                 abil=charData["Abilities/Tools"],
                                 appear=charData["Appearance"], backg=charData["Background"],
                                 person=charData["Personality"], prefilled=charData["Prefilled Application"], misc=miscData, ctx=ctx)

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


async def fuckoffloki(ctx):
    for i in range(5):
        await ctx.author.send("LOKI PLS")
    await ctx.author.kick()


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

    if field.lower() in fields:
        fSan = convertField(field.lower())

        if fSan == 'charID':
            await ctx.send("You can not change the ID of a character!")
            return
    else:
        await ctx.send("That is not a valid field!")

    if message == '' or message == 'delete':
        message = ''
        if fSan == 'name':
            await ctx.send("You can not remove a characters' name!")
            return

    if fSan == 'owner' or fSan == 'status':
        if await checkGM(ctx) is False:
            await ctx.send("You need to be a GM to change this!")
            return

    if charID.isnumeric():
        icharID = int(charID)
    else:
        await ctx.send("That is not a valid character ID!")
        return

    ownerID = _charExists(icharID)

    if ownerID == False:
        await ctx.send("This character does not exist!")
        return

    if not charPermissionCheck(ctx, ownerID):
        await ctx.send("You do not have permission to modify this character!")
        return

    _setSQL(icharID, fSan, message)

    if message == '':
        await ctx.send(f"Field {field.capitalize()} has been deleted.")
    else:
        await ctx.send(f"Field {field.capitalize()} has been changed.")

    channel = bot.get_channel(GMChannel())

    if message == '':
        message == 'Deleted'

    await channel.send(
        f"{ctx.author} has modified Character ID: `{icharID}`. Field `{field.capitalize()}` has been set to:\n`{message}`")


def _setSQL(charID, field, content):
    cur = conn.cursor()

    sql = f'''UPDATE charlist SET {field} = ? WHERE charID is ?'''
    cur.execute(sql, [content, charID])
    conn.commit()


# @bot.command(name='setprop')
# async def _setprop(ctx):
#    pass


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

    await ctx.send(
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

    await ctx.send(f"List of all characters: (Page: {pageNo + 1} of {math.ceil(count / pageSize)})\n{charListStr}")


fields = ['owner', 'ownerid', 'status', 'name', 'charid', 'id', 'age', 'gender', 'abilities/tools', 'abilities',
          'appearance', 'background', 'personality', 'prefilled', 'prefilled application', 'misc']


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
    if selector == 'prefilled' or selector == 'prefilled application' or selector == 'misc':
        return 'prefilled'
    return selector


@bot.command(name='search')
async def _search(ctx, selector='', extra1='', extra2=''):
    '''Searches for a character using fields provided.

    USAGE:
    rp!search <NAME> - Searches for characters with a specific name.
    rp!search <FIELD> <QUERY> - Searches a specific field for a search query.'''

    if selector == '':
        await ctx.send("You have not entered anything to search!")
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
        await _sqlSearch(ctx, field=fieldFinal, search=extra1, pageNo=pageNo)
    else:
        if extra1.isnumeric():
            pageNo = int(extra1) - 1
        else:
            pageNo = 0
        await _sqlSearch(ctx, search=selector, pageNo=pageNo)


async def _sqlSearch(ctx, field=None, search='', pageNo=0):
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

    charListStr = ''

    for i in charList:
        member = ctx.message.guild.get_member(int(i.owner))
        charListStr = f"{charListStr}**`{i.id}.`** {i.name[0:30]} (Owner: {member or i.owner})\n"

    await ctx.send(
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
            await ctx.send("Are you sure you wish to delete this character? Please type `confirm` if you are sure.")
            response = await bot.wait_for("message", check=message_check())
            if response.content.lower() == 'confirm':
                await _deleteChar(ctx, int(charDel))
                return
    else:
        await ctx.send("Invalid Character ID!")


@bot.command(name='undelete', aliases=['recover'])
async def _undelete(ctx, charID):
    if not await checkGM(ctx):
        await ctx.send("You do not have permission to do this!")
        return

    if charID.isnumeric():
        icharID = int(charID)

    cursor = conn.cursor()

    cursor.execute("UPDATE charlist SET status = 'Pending' WHERE charID is ?", [icharID])
    conn.commit()
    ctx.send(f"Character {icharID} has been recovered.")


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
        await ctx.send("That character does not exist!")
        return

    cursor = conn.cursor()

    if charPermissionCheck(ctx, ownerID=ownerP) is True:
        cursor.execute(f"UPDATE charlist SET status = 'Disabled' WHERE charID is ?", [charID])
        conn.commit()
        await ctx.send(f"Character {charID} has been deleted.")
    else:
        await ctx.send("You do not own this character!")


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


async def _registerChar(ctx, user):
    '''USAGE:
    rp!register
    rp!register <ID> | reregister <ID>

    Registers a new character, or resubmits an existing character if an ID is input.

    Guides you through the command. Please see #rules and #policy for more help.'''

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
            if response.lower() == 'exit':
                await user.send("Exiting Character Creation!")
                isRegistering = False
                currentlyRegistering.remove(user.id)
                return
            cfields["name"] = response  # Gets the raw message from response

            canonDeny = ["sans", "papyrus", "frisk", "flowey", "undyne", "alphys", "mettaton", "asgore", "asriel",
                         "chara", "muffet", "pepsi man", "toriel"]  # To do - Make this into a function.

            if response.lower() in canonDeny:
                await user.send(
                    "**Reminder! Canon Characters are not allowed. Please read the <#697160109700284456> and <#697153009599119493>**")
                cfields["name"] = f"{response} - CANON CHARACTER"

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


@bot.command(name='testspam')
@commands.is_owner()
async def _spamChars(ctx):
    i = 0
    while i <= 1000:
        await charadd(owner=110399543039774720, name='LOKI PAY YOUR ARTIST', age='SPAMTEST', gender='SPAMTEST',
                      abil='SPAMTEST',
                      appear='SPAMTEST', backg='SPAMTEST', person='SPAMTEST', status='TESTING STATUS')
        i = i + 1


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
    await ctx.send(result)

@bot.command()
async def help(ctx):
    await ctx.send("For help, please check out the Wiki on Github!\nhttps://github.com/OblivionCreator/mettaton-2.py/wiki")

## Fun Stuff ##

@bot.command()
@commands.cooldown(1, 3600, commands.BucketType.guild)
async def sans(ctx):
    if random.randint(0, 100) <= 10:
        await ctx.send(open('resources/ascii_papyrus.txt', encoding="utf-8").read())
    else:
        await ctx.send(open('resources/ascii_sans.txt', encoding="utf-8").read())


@bot.command()
@commands.cooldown(1, 60, commands.BucketType.guild)
async def papyrus(ctx):
    await ctx.send(f"Nice Try, <@{str(ctx.author.id)}>")


async def changeStatus():
    status = discord.Status.online

    statusChoice = ['Aik still hasn\'t played Undertale', 'Meme', 'with Bliv\'s feelings', 'with Bliv\'s Owner Role',
                    'old enough for soriel',
                    'haha he smope weef', 'SHUP', 'AMA', '...meme?', 'role!unban', '1000 blood', 'blame AIK',
                    'blame Bliv', 'blame Samario', 'blame Wisty', 'Venom is a Furry', 'blankets = lewd???',
                    'oblivion pinged everyone', 'oblivion pinged everyone... again', 'arrrr peee?', 'buzzy bee',
                    'this server contains chemicals known to the nation of Arkias to cause cancer.',
                    'No Thoughts. Dream Empty', 'Stuck in a Nightmare\'s Paradise', 'PUBBY',
                    'You have OneShot at this.', 'What plant is Lotus?', 'Default Dance', 'Mystiri is All',
                    'This server has been murder free for 0 Months', 'Pending', 'Vampire Celery', 'Bugsonas Are Real',
                    'Arik files tax returns', 'Are you here to RP or be cringe', 'VillagerHmm',
                    'Member Retention now at 1%', 'with Smol Bot', 'bnuuy']

    while True:
        await bot.change_presence(activity=discord.Game(random.choice(statusChoice)))
        await asyncio.sleep(300)


bot.run(token)
close_connection(database)

print("If this runs, something dun fucked up")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

# Consider: Input Validation - Stop from doing both prefilled & other
