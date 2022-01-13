import discord
import os
from better_profanity import profanity
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

bot = discord.Client()


class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return
        if profanity.contains_profanity(message.content):
            author_banable = True
            print(message.author.roles)
            for x in message.author.roles:
                if x.name == "Developer":
                    author_banable = False
                if x.name == "Moderator":
                    author_banable = False
                if x.name == "Admin":
                    author_banable = False
                if x.name == "🖥 Team NativeBase":
                    author_banable = False
                if x.name == "Community Executive":
                    author_banable = False
            print(author_banable)
            await message.channel.send("No profanity please! {} You would be banned if you say that.".format(message.author.mention))
            await message.delete()
            culprit_details = supabase.table('profanity_bot_ban_list').select(
                "profanity_strikes, profanity_contents").eq("discord_auth_id", message.author.id).execute()
            # assert len(culprit_details.get("data", [])) > 0
            print(culprit_details)
            if len(culprit_details[0]) > 0:
                profanity_strikes = culprit_details[0][0]["profanity_strikes"]
                profanity_contents = culprit_details[0][0]["profanity_contents"]
                profanity_strikes += 1
                if profanity_strikes <= 100:
                    supabase.table('profanity_bot_ban_list').update({"profanity_strikes": profanity_strikes, "profanity_contents": "{},{}".format(profanity_contents, message.content)}).eq(
                        "discord_auth_id", message.author.id).execute()
                elif profanity_strikes > 100:  # keeping 100 for now as a safety measure
                    if(author_banable):
                        await message.author.ban()
                        await message.channel.send("{} has been banned for using profanity!".format(message.author.mention))
                    supabase.table('profanity_bot_ban_list').update({"profanity_strikes": profanity_strikes}, "profanity_contents": "{},{}".format(profanity_contents, message.content)).eq(
                        "discord_auth_id", message.author.id).execute()
            else:
                supabase.table("profanity_bot_ban_list").insert(
                    {"discord_auth_id": message.author.id, "user_name": message.author.name, "profanity_strikes": 1, "profanity_contents": message.content}).execute()
            # assert data.get("status_code") in (200, 201)
        # await message.reply(message.content, mention_author=True)
        if message.content.startswith('!reset profanity'):
            await message.delete()
            supabase.table('profanity_bot_ban_list').delete().execute()
            await message.channel.send("Profanity strikes reset!")


client = MyClient()
client.run(os.environ.get("DISCORD_TOKEN"))
