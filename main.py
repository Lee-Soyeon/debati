import openai
import os
import random
import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
from discord import Activity, ActivityType
import logging

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
slash = SlashCommand(bot, sync_commands=True)


@bot.event
async def on_ready():
    await bot.change_presence(activity=Activity(type=ActivityType.watching, name="Brains"))
    logging.info(f'{bot.user} is online and ready to answer your questions!')

openai.api_key = os.getenv('OPENAI_API_KEY')

@slash.slash(
    name="ask",
    description="Answers your questions!",
    options=[
        create_option(
            name="prompt",
            description="What is your question?",
            option_type=3,
            required=True
        ),
        create_option(
            name="model",
            description="What model do you want to ask from? (Default: ChatGPT)",
            option_type=3,
            required=False,
            choices=[
                {"name": 'ChatGPT (BEST OF THE BEST)', "value": 'chatgpt'},
                {"name": 'Davinci (Most powerful)', "value": 'davinci'},
                {"name": 'Curie', "value": 'curie'},
                {"name": 'Babbage', "value": 'babbage'},
                {"name": 'Ada (Fastest)', "value": 'ada'}
            ]
        ),
        create_option(
            name='ephemeral',
            description='Hides the bot\'s reply from others. (Default: Disable)',
            option_type=3,
            required=False,
            choices=[
                {"name": 'Enable', "value": 'Enable'},
                {"name": 'Disable', "value": 'Disable'}
            ]
        )
    ]
)
async def _ask(ctx: SlashContext, prompt: str, model: str = 'chatgpt', ephemeral: str = 'Disable'):
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question}
        ]
    )

    await ctx.send(response['choices'][0]['message']['content'])

bot.run(os.getenv('TOKEN'))
