import math
import random
import discord
from discord import guild, File
from discord.ext import commands
import sqlite3
from sqlite3 import Error
from collections.abc import Sequence
import ast
from dataclasses import dataclass
import time

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix=['rp!', 'sans!', 'mtt!', 'arik ', 'bliv pls ', 'bliv ', 'https://en.wikipedia.org/wiki/Insanity '],
    intents=intents)
currentlyRegistering = []


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print("Connection Failed! - " + e)

    return conn


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
                  status='Pending'):
    character = (owner, status, name, age, abil, appear, backg, person, prefilled)

    """
    :param conn:
    :param character:
    :return: charID
    """

    sql = '''INSERT INTO charlist(owner,status,name,age,gender,abil,appear,backg,person,prefilled) VALUES(?,?,?,?,?,?,?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, character)
    conn.commit()

    print(cur.lastrowid)
    return cur.lastrowid


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


@bot.command()
@commands.cooldown(1, 3600, commands.BucketType.guild)
async def sans(ctx):
    if random.randint(0, 100) <= 10:
        await ctx.send("░░░░░░░░░░░░░░░░░░░░░░░░██████████\n"
                       "░░░░░░░░░░░░░░░░░░░░████░░░░░░░░░░██\n"
                       "░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░░░░░██\n"
                       "░░░░░░░░░░░░░░░░██░░░░░░░░░░░░░░░░░░██\n"
                       "░░░░░░░░░░░░░░░░██░░░░░░░░░░░░██░░░░████\n"
                       "░░░░░░░░░░░░░░░░██░░░░░░░░██████░░██░░██\n"
                       "░░░░░░░░░░░░░░░░██░░░░██░░░░░░░░░░░░░░██\n"
                       "░░░░░░░░░░░░░░░░░░██░░░░██████░░░░██████\n"
                       "░░░░░░░░░░░░░░░░░░██░░░░░░░░░░░░██░░████\n"
                       "░░░░░░░░░░░░░░██████░░██░░░░░░░░░░░░██\n"
                       "░░░░░░░░██████░░░░░░██░░██████████████\n"
                       "██░░░░██░░░░██████████░░████░░██░░████████\n"
                       "██████░░░░██░░░░░░██░░██░░██░░██░░████░░░░██\n"
                       "██░░░░░░██░░░░░░░░░░██░░██░░████░░████░░░░░░██\n"
                       "██░░░░░░██░░░░░░░░░░██░░░░██░░░░██░░██░░░░░░██\n"
                       "░░██░░░░████████░░░░░░██░░░░████████████░░██░░██\n"
                       "░░░░██░░██░░░░░░████░░░░██████░░░░░░██░░██░░██\n"
                       "░░░░░░██████████░░██░░░░░░██░░░░░░██░░██░░████\n"
                       "░░░░░░░░░░████████░░░░░░██░░████████░░██████████\n"
                       "░░░░░░░░░░████░░██░░░░░░██████░░░░████████████████\n"
                       "░░░░░░░░████░░░░████░░░░░░░░░░░░░░░░░░██░░██████\n"
                       "░░░░░░░░████████░░██████░░░░░░░░░░░░██\n"
                       "░░░░░░░░░░████░░░░██░░████████████████\n"
                       "░░░░░░░░░░░░██░░██░░░░░░░░░░██░░██░░██\n"
                       "░░░░░░░░░░░░░░██████░░░░░░██████████\n"
                       "░░░░░░░░░░░░░░░░░░████░░░░██████\n"
                       "░░░░░░░░░░░░░░░░░░██░░░░██████████\n"
                       "░░░░░░░░░░░░░░░░░░░░████░░██████░░██\n"
                       "░░░░░░░░░░░░░░░░░░░░██░░██░░░░░░████\n"
                       "░░░░░░░░░░░░░░░░░░░░██░░░░██████░░██\n"
                       "░░░░░░░░░░░░░░░░░░░░░░████░░░░░░██\n"
                       "░░░░░░░░░░░░░░░░░░░░░░████████████\n"
                       "░░░░░░░░░░░░░░░░░░░░██████░░░░████\n"
                       "░░░░░░░░░░░░░░░░░░░░████░░░░████████\n"
                       "░░░░░░░░░░░░░░░░░░██████░░░░██░░░░██\n"
                       "░░░░░░░░░░░░░░░░██░░░░██░░░░████████\n"
                       "░░░░░░░░░░░░░░░░████████░░░░██░░░░██\n"
                       "░░░░░░░░░░░░░░░░████░░██░░░░████████\n"
                       "░░░░░░░░░░░░████░░░░████░░░░██░░░░██████\n"
                       "░░░░░░░░░░██░░░░░░░░░░██░░░░██░░██░░░░░░██\n"
                       "░░░░░░░░░░██░░░░░░░░████░░░░██░░░░░░░░░░██\n"
                       "░░░░░░░░░░████████████░░░░░░░░████████████\n\n"
                       "YOU EXPECTED SANS, BUT IT WAS ME! THE GREAT PAPYRUS!\n"
                       "(Papyrus ASCII by u/SuperKirbylover)")
    else:
        await ctx.send("░░░░░░░░██████████████████░░░░░░░░\n"
                       "░░░░████░░░░░░░░░░░░░░░░░░████░░░░\n"
                       "░░██░░░░░░░░░░░░░░░░░░░░░░░░░░██░░\n"
                       "░░██░░░░░░░░░░░░░░░░░░░░░░░░░░██░░\n"
                       "██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░██\n"
                       "██░░░░░░░░░░░░░░░░░░░░██████░░░░██\n"
                       "██░░░░░░░░░░░░░░░░░░░░██████░░░░██\n"
                       "██░░░░██████░░░░██░░░░██████░░░░██\n"
                       "░░██░░░░░░░░░░██████░░░░░░░░░░██░░\n"
                       "████░░██░░░░░░░░░░░░░░░░░░██░░████\n"
                       "██░░░░██████████████████████░░░░██\n"
                       "██░░░░░░██░░██░░██░░██░░██░░░░░░██\n"
                       "░░████░░░░██████████████░░░░████░░\n"
                       "░░░░░░████░░░░░░░░░░░░░░████░░░░░░\n"
                       "░░░░░░░░░░██████████████░░░░░░░░░░\n \n"
                       "(Sans ASCII by u/SuperKirbylover)")


@bot.command()
async def papyrus(ctx):
    await ctx.send("Nice Try, <@" + str(ctx.author.id) + ">")


@bot.command(pass_context=True)
async def register(ctx):
    if ctx.author.id in currentlyRegistering:
        await ctx.send("You are already registering a character!")
        return
    else:
        await ctx.send(
            ":mailbox_with_mail: Please check your DMs!")
        currentlyRegistering.append(ctx.author.id)
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
async def _view(ctx, idinput=''):
    if not idinput.isnumeric() or int(idinput) == 0:
        await ctx.send("That is not a valid character ID!")
    else:
        sanID = int(idinput)

        charData = await _getChar(sanID)

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
        try:
            await ctx.send(embed=embedVar)
        except:
            await ctx.send(f"This character was too too long, so I have dumped it to a file.")
            filePath = charToTxt(charID=sanID, owner=owner, status=status, name=name, age=age, gender=gender, abil=abil,
                                 appear=appear, backg=backg, person=person, prefilled=prefilled, ctx=ctx)

            charFile = open(filePath, 'r')
            await ctx.send(file=discord.File(filePath))


async def _getChar(charID):
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


@bot.command(name='set')
async def _set(ctx):
    pass


@bot.command(name='setprop')
async def _setprop(ctx):
    pass


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
    if not pageIdentifier.isnumeric():
        if page.isnumeric():
            pageID = int(page)
        else:
            pageID = 1
        if pageIdentifier == '':
            pageID = 0
        elif pageIdentifier == 'me':
            await getUserChars(ctx, ctx.author.id, pageSize, pageID=pageID)
            return
        elif ctx.message.mentions[0].id:
            await getUserChars(ctx, ctx.message.mentions[0].id, pageSize, pageID=pageID)
            return
        else:
            pageNo = 0
    else:
        pageNo = (int(pageIdentifier) - 1)

    cursor = conn.cursor()

    #  Gets the Character IDs from the Database

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
async def _delete(ctx):
    pass


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


async def _registerChar(ctx, user):
    isRegistering = True

    while isRegistering:
        resmsg = await getdm(ctx)
        resmsg = resmsg.lower()

        if resmsg == 'exit':
            await user.send("Character submission aborted.")
            currentlyRegistering.remove(user.id);
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
            if response.lower() == 'exit': await user.send(
                "Exiting Character Creation!"); isRegistering = False; currentlyRegistering.remove(user.id); return
            cfields["name"] = response  # Gets the raw message from response

            canonDeny = ["sans", "papyrus", "frisk", "flowey", "undyne", "alphys", "mettaton", "asgore", "asriel",
                         "chara", "muffet", "pepsi man", "toriel"]  # To do - Make this into a function.

            if response.lower() in canonDeny:
                await user.send(
                    "**Reminder! Canon Characters are not allowed. Please read the <#697160109700284456> and <#697153009599119493>**")

            await user.send("Now that your character has a name, let's start filling out some details.\n"
                            "What field would you like to edit?\n"
                            "Remaining fields to specify: `Age`, `Gender`, `Abilities/Tools`, `Appearance`, `Background`, `Personality`\n"
                            "Fields already specified: `Name`")

            while not charcomplete:

                # MAIN CHARACTER REGISTRATION LOOP

                response = await getdm(ctx)
                if response.lower() == 'exit': await user.send(
                    "Exiting Character Creation!"); isRegistering = False; currentlyRegistering.remove(user.id); return
                selector = response.lower()

                if response.lower() == 'done':
                    if not submitChar:
                        await user.send(
                            "You character is not complete! Please fill the remaining fields before trying to register your character.")
                    else:
                        submitChar = True

                        owner = ctx.author.id
                        prefilled = None

                        await user.send("Character has been submitted with ID: " + str(
                            await charadd(owner=owner, name=cfields["name"], age=cfields["age"],
                                          gender=cfields["gender"],
                                          abil=cfields["abilities/tools"],
                                          appear=cfields["appearance"], backg=cfields["background"],
                                          person=cfields["personality"],
                                          prefilled=prefilled)))
                        currentlyRegistering.remove(user.id)
                elif response.lower() == 'exit':
                    await user.send(
                        "Exiting Character Creation!")
                    isRegistering = False
                    currentlyRegistering.remove(user.id);
                    return
                elif selector in cfields:
                    await user.send("What would you like field `" + selector.capitalize() + "` to say?")
                    response = await getdm(ctx)
                    if response.lower() == 'exit': await user.send(
                        "Exiting Character Creation!"); isRegistering = False; currentlyRegistering.remove(
                        user.id); return

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
                        await user.send("Field `" + selector.capitalize() + "` has been changed.\n"
                                                                            "All fields have been completed. If you wish to submit your character, type `Done`. To preview your character, type `Preview`.\n"
                                                                            "Or if you wish to change a field, enter the field you wish to modify: " + specifyDone)
                        submitChar = True
                    else:
                        await user.send("Field `" + selector.capitalize() + "` has been changed.\n"
                                                                            "What field would you like to edit?\n"
                                                                            "Remaining fields to specify: " + toSpecify + "\n"
                                                                                                                          "Field(s) already specified: " + specifyDone)

                        # End of Interactive Fields Loop

                else:
                    await user.send("That is not a valid field!")

            return
        elif resmsg == 'prefilled':

            charcomplete = False

            await user.send(
                "Great! First of all, Before submitting your application, what is your characters name?")
            response = await getdm(ctx)
            if response.lower() == 'exit': await user.send(
                "Exiting Character Creation!"); isRegistering = False; currentlyRegistering.remove(user.id); return

            name = response

            await user.send(
                "Let's submit your character. \nPlease upload, link or paste in your character. Web links, text files and raw text are all accepted, and will be handled appropriately.")
            prefilled = await getdm(ctx)
            if prefilled.lower() == 'exit': await user.send(
                "Exiting Character Creation!"); isRegistering = False; currentlyRegistering.remove(user.id); return

            validcommands = ["prefilled application", "name"]

            while not charcomplete:
                await user.send(
                    "Your character is ready to submit. If you wish to change any fields, please state what you would like to change. If you would like to submit your character, enter `Done`\n"
                    "Fields: `Name`, `Prefilled Application`")
                response = await getdm(ctx)
                selector = response.lower()
                if selector == 'exit': await user.send(
                    "Exiting Character Creation!"); isRegistering = False; currentlyRegistering.remove(user.id); return

                if selector not in validcommands:
                    if selector == 'done':
                        await user.send("Great! Your character has been submitted with ID: **" + str(
                            await charadd(owner=ctx.author.id, name=name, prefilled=prefilled)) + "**")
                        currentlyRegistering.remove(user.id)
                        charcomplete = True
                        return
                    await user.send("That is not a valid field! Please try again.")
                elif selector == 'name':
                    await user.send("What would you like the name to be?")
                    response = await getdm(ctx)
                    if response.lower() == 'exit': await user.send(
                        "Exiting Character Creation!"); isRegistering = False; currentlyRegistering.remove(
                        user.id); return
                    name = response
                    await user.send("Your Characters name has been set to **" + name + "**")

                else:
                    await user.send(
                        "Please upload, link or paste in your character. Web links, text files and raw text are all accepted, and will be handled appropriately.")
                    response = await getdm(ctx)
                    if response.lower() == 'exit': await user.send(
                        "Exiting Character Creation!"); isRegistering = False; currentlyRegistering.remove(
                        user.id); return
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
