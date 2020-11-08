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

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix=['rp!', 'sans!', 'mtt!', 'arik ', 'bliv pls ', 'bliv ', 'https://en.wikipedia.org/wiki/Insanity ', 'Rp!'],
    intents=intents, case_insensitive=True)
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
            await (bot.get_channel(GMChannel)).send("Mettaton 2.0.5 Loaded!")

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


@bot.command()
async def test(ctx):
    print("TEST")
    pass


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
@commands.cooldown(1, 3600, commands.BucketType.guild)
async def sans(ctx):
    if random.randint(0, 100) <= 10:
        await ctx.send(open('resources/ascii_papyrus.txt', encoding="utf-8").read())
    else:
        await ctx.send(open('resources/ascii_sans.txt', encoding="utf-8").read())


@bot.command()
async def papyrus(ctx):
    await ctx.send(f"Nice Try, <@{str(ctx.author.id)}>")

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
    await user.send(f"The status of character ID **{charID}** (Name: **{name}**) has been set to `{status}` by {ctx.author.mention}")


async def _changeStatus(ctx, charID='',charStatus='Pending' , reason=''):
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
    sql = '''UPDATE charlist SET status = 'Approved' WHERE charID is ?'''
    cursor.execute(sql, [charID])
    conn.commit()
    await alertUser(ctx, charInt, charStatus, reason)
    await ctx.send(f"Character `ID: {charID}` has been set to `{charStatus}`")

@bot.command()
async def approve(ctx,charID, *args):

    reason = ' '.join(args)
    await _changeStatus(ctx, charID=charID, charStatus='Approved', reason=reason)

@bot.command()
async def pending(ctx,charID, *args):

    reason = ' '.join(args)
    await _changeStatus(ctx, charID=charID, charStatus='Pending', reason=reason)

@bot.command()
async def deny(ctx,charID, *args):

    reason = ' '.join(args)
    await _changeStatus(ctx, charID=charID, charStatus='Denied', reason=reason)

@bot.command()
async def kill(ctx,charID, *args):

    reason = ' '.join(args)
    await _changeStatus(ctx, charID=charID, charStatus='Dead', reason=reason)


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
    cfields['prefilled'], = charData[-1:]

    embedV = await _view(ctx, charID, dmchannel=True, returnEmbed=True)
    try:
        await ctx.author.send("Here is your character currently.", embed=embedV)
    except:
        filePath = charToTxt(charID=charID, owner=owner, status=status, name=cfields['name'], age=cfields['age'],
                             gender=cfields['gender'], abil=cfields['abilities/tools'],
                             appear=cfields['appearance'], backg=cfields['background'], person=cfields['personality'],
                             prefilled=cfields['prefilled'], ctx=ctx)
        charFile = open(filePath, 'r')
        await ctx.author.send("Here is your character currently.", file=discord.File(filePath))
        charFile.close()
        clearLog()

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

            await user.send(f"Your character (ID {charID}) has been resubmitted and will be reviewed at the next available oppurtunity.")

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

    await ctx.send(":mailbox_with_mail: Please check your DMs!")
    for word in currentlyRegistering:
        print(word)

    if charID.isnumeric():
        await reRegister(ctx, charID)
        currentlyRegistering.remove(ctx.author.id)
        return

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

    channelID = GMChannel()

    channel = bot.get_channel(channelID)

    isResubmit = ''

    if resub is True:
        isResubmit = f'**RESUBMISSION FOR CHARACTER ID {charID}**\n'
    else:
        isResubmit = ''

    await channel.send(
        f"<@&771070676638629948>\n{isResubmit}Character application from {ctx.author} (ID: {ctx.author.id})\nTo change the status of this character, type `rp!<approve|pending|deny> 1378.`",
        embed=embedC)


def getMember(owner, ctx):
    member = ctx.message.guild.get_member(int(owner))
    return member


def charToTxt(charID, owner, status, name, age, gender, abil, appear, backg, person, prefilled, ctx):
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
    if prefilled != '': charTXT = charTXT + f"Prefilled: {prefilled}\n"

    charFile.write(charTXT)

    charFile.close()
    return path


@bot.command(name='view', aliases=['cm', 'charmanage', 'samwhy'])
async def _view(ctx, idinput='', dmchannel=False, returnEmbed=False):
    if not idinput.isnumeric() or int(idinput) == 0:
        await ctx.send("That is not a valid character ID!")
    else:
        sanID = int(idinput)

        charData = _getChar(sanID)

        if charData == 'INVALID CHARACTER':
            await ctx.send("That is not a valid character!")
            return

        print(charData)

        owner, = charData[1:2]
        status, = charData[2:3]
        name, = charData[3:4]
        age, = charData[4:5]
        gender, = charData[5:6]
        abil, = charData[6:7]
        appear, = charData[7:8]
        backg, = charData[8:9]
        person, = charData[9:10]
        prefilled, = charData[-1:]

        print(prefilled)

        member = ctx.message.guild.get_member(int(owner))

        embedVar = discord.Embed(title=f"Viewing Character {sanID}",
                                 description=f"Showing Information for Character ID: {sanID}", color=0xff0000)
        embedVar.add_field(name="Owner:", value=f"{member or (owner) + ' (User has left the server.)'}", inline=True)
        embedVar.add_field(name="Status:", value=status, inline=False)
        embedVar.add_field(name="Name:", value=name, inline=True)
        if age != '': embedVar.add_field(name="Age:", value=age, inline=False)
        if gender != '': embedVar.add_field(name="Gender:", value=gender, inline=False)
        if abil != '': embedVar.add_field(name="Abilities/Tools:", value=abil, inline=False)
        if appear != '': embedVar.add_field(name="Appearance:", value=appear, inline=False)
        if backg != '': embedVar.add_field(name="Background:", value=backg, inline=False)
        if person != '': embedVar.add_field(name="Personality:", value=person, inline=False)
        if prefilled != '': embedVar.add_field(name="Prefilled Application:", value=prefilled, inline=False)

        if returnEmbed is True:
            return embedVar

        try:
            if (dmchannel is False):
                await ctx.send(embed=embedVar)
            else:
                await ctx.author.send(embed=embedVar)
        except:
            if (dmchannel is False):
                await ctx.send(f"This character was too too long, so I have dumped it to a file.")
            else:
                ctx.author.send(f"This character was too too long, so I have dumped it to a file.")
            filePath = charToTxt(charID=sanID, owner=owner, status=status, name=name, age=age, gender=gender, abil=abil,
                                 appear=appear, backg=backg, person=person, prefilled=prefilled, ctx=ctx)

            charFile = open(filePath, 'r')
            if dmchannel is False:
                await ctx.send(file=discord.File(filePath))
            else:
                ctx.author.send(file=discord.File(filePath))
            charFile.close()
            clearLog()


def _getChar(charID=0):
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


async def fuckoffloki(ctx):
    for i in range(5):
        await ctx.author.send("LOKI PLS")
    await ctx.author.kick()


@bot.command(name='set', aliases=['setprop'])
async def _set(ctx, charID, *args):
    await ctx.send(f"{charID}, {args}")


# @bot.command(name='setprop')
# async def _setprop(ctx):
#    pass


@dataclass
class CharacterListItem:
    """Stores Character Information in a Class"""
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


@bot.command(name='search')
async def _search(ctx):
    pass


@bot.command(name='delete')
async def _delete(ctx, charDel='', confirmation=''):
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


def charPermissionCheck(ctx, ownerID):
    role_names = role_names = [role.name for role in ctx.author.roles]

    authorID = ctx.author.id

    if int(ownerID) == authorID or "Gamemaster" in role_names:
        return True
    else:
        return False


async def _deleteChar(ctx, charID):
    cursor = conn.cursor()
    cursor.execute(f"SELECT owner FROM charlist WHERE charID IS {charID} AND status IS NOT 'Disabled'")

    owner = cursor.fetchone()

    if owner is None:
        await ctx.send("That character does not exist!")
        return
    else:
        ownerP = owner[0]
        print(ownerP)

    if charPermissionCheck(ctx, ownerID=ownerP) is True:
        cursor.execute(f"UPDATE charlist SET status = 'Disabled' WHERE charID is {charID}")
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
                            f"Field `{selector.capitalize()} has been changed.\n"
                            "All fields have been completed. If you wish to submit your character, type `Done`. To preview your character, type `Preview`.\n"
                            f"Or if you wish to change a field, enter the field you wish to modify: {specifyDone}")
                        submitChar = True
                    else:
                        await user.send(
                            f"Field `{selector.capitalize()}` has been changed.\n`"
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


bot.run(token)
close_connection(database)

print("If this runs, something dun fucked up")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

# Consider: Input Validation - Stop from doing both prefilled & other
