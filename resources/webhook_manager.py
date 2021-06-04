import json
import aiohttp
from discord import Webhook, AsyncWebhookAdapter
import validators

c_webhooks = []


async def send(ctx, name, message, custom_img=None):
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        img = attachment.url
    elif custom_img:
        img = custom_img
    else:
        img = ctx.author.avatar_url

    channel = ctx.message.channel

    await sendWH(name=name, img=img, message=message, channel=channel, author=ctx.author)
    try:
        await ctx.message.delete()
    except Exception as e:
        print(f"Unable to delete message due to exception:\n{e}")


async def sendWH(name, img, message, channel, author):
    webhook = False

    c_webhooks = getWebhookCache()

    async with aiohttp.ClientSession() as session:

        if c_webhooks:
            for c, w in c_webhooks:
                if c == channel.id:
                    webhook = Webhook.from_url(w, adapter=AsyncWebhookAdapter(session))
                    print("Webhook Found!")
                    continue
        else:
            c_webhooks = []

        if not webhook:
            webhook = await channel.create_webhook(name='NoWebhooks Generated Webhook',
                                                   reason=f'{author} ({author.id}) used MTT2 to send a message in {channel}')
            c_webhooks.append((channel.id, webhook.url))
            setWebhookCache(c_w=c_webhooks)

        await webhook.send(message, username=name, avatar_url=img)
        # await webhook.delete(reason="Auto-Delete Used Webhook")


def getWebhookCache():  # Gets cache of webhooks.
    try:
        with open("resources/temp/temp_webhooks.json", 'r') as file:
            try:
                c_w = json.loads(file.read())
                return c_w
            except Exception:
                return False
    except FileNotFoundError:
        return False


def setWebhookCache(c_w):  # Saves webhook cache.
    with open("resources/temp/temp_webhooks.json", 'w+') as file:
        file.write(json.dumps(c_w))