import json
import aiohttp
import discord.ext.commands
from discord import Webhook
import validators

c_webhooks = []


async def send(ctx, name, message, custom_img=None):
    if isinstance(ctx, discord.ext.commands.Context) or isinstance(ctx, discord.Thread):
        message_obj = ctx.message
    elif isinstance(ctx, discord.Message):
        message_obj = ctx
    if message_obj.attachments:
        attachment = message_obj.attachments[0]
        img = attachment.url
    elif custom_img:
        img = custom_img
    else:
        img = message_obj.author.display_avatar

    channel = message_obj.channel

    await sendWH(name=name, img=img, message=message, channel=channel, author=ctx.author)
    try:
        await message_obj.delete()
    except Exception as e:
        print(f"Unable to delete message due to exception:\n{e}")


async def sendWH(name, img, message, channel, author):
    webhook = False
    is_thread = False
    c_webhooks = getWebhookCache()

    if isinstance(channel, discord.Thread):
        is_thread = channel
        channel = channel.parent

    async with aiohttp.ClientSession() as session:
        if c_webhooks:
            for c, w in c_webhooks:
                if c == channel.id:
                    webhook = Webhook.from_url(w, session=session)
                    print("Webhook Found!")
                    continue
        else:
            c_webhooks = []

        if not webhook:
            webhook = await channel.create_webhook(name='MTT2 Generated Webhook',
                                                   reason=f'{author} ({author.id}) used MTT2 to send a message in {channel}')
            c_webhooks.append((channel.id, webhook.url))
            setWebhookCache(c_w=c_webhooks)

        if is_thread:
            await webhook.send(message, username=name, avatar_url=img, thread=is_thread)
        else:
            await webhook.send(message, username=name, avatar_url=img)


def getWebhookCache():  # Gets cache of webhooks.
    try:
        with open("scripts/temp/temp_webhooks.json", 'r') as file:
            try:
                c_w = json.loads(file.read())
                return c_w
            except Exception:
                return False
    except FileNotFoundError:
        return False


def setWebhookCache(c_w):  # Saves webhook cache.
    with open("scripts/temp/temp_webhooks.json", 'w+') as file:
        file.write(json.dumps(c_w))