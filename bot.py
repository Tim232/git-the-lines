'''
Git the lines

A Discord bot that removes embeds and prints out specific lines of code
when a GitHub link is sent
'''

import os
import base64
import re

import requests
from discord.ext import commands

bot = commands.Bot(';')

github = re.compile(
    r'https:\/\/github\.com\/(?P<repo>.+)\/blob\/(?P<branch>.+?)\/(?P<file_path>.+?)' +
    r'(?P<extension>\.(?P<language>.+))*#L(?P<start_line>[0-9]+)(-L(?P<end_line>[0-9]+))*'
)

gitlab = re.compile(
    r'https:\/\/gitlab\.com\/(?P<repo>.+)\/\-\/blob\/(?P<branch>.+)\/(?P<file_path>.+?)' +
    r'(?P<extension>\.(?P<language>.+))*#L(?P<start_line>[0-9]+)(-(?P<end_line>[0-9]+))*'
)


@bot.command()
async def about(ctx):
    '''
    Describes the bot
    '''

    await ctx.message.channel.send(
        'Hi there! I\'m Git the lines. Simply send a GitHub ' +
        'or GitLab snippet and I\'ll send the code to Discord.'
    )


@bot.command()
async def invite(ctx):
    '''
    Sends a bot invite link
    '''

    await ctx.message.channel.send(
        'https://discord.com/api/oauth2/authorize?client_id=708364985021104198&permissions=75776&scope=bot'
    )


@bot.event
async def on_message(message):
    '''
    Checks if the message starts is a GitHub snippet, then removes the embed,
    then sends the snippet in Discord
    '''

    gh_match = github.search(message.content)
    gl_match = gitlab.search(message.content)
    if (gh_match or gl_match) and message.author.id != bot.user.id:
        if gh_match:
            d = gh_match.groupdict()
            response_json = requests.get(
                f'https://api.github.com/repos/{d["repo"]}/contents/{d["file_path"]}' +
                f'{d["extension"] if d["extension"] else ""}?ref={d["branch"]}',
                headers={'Accept': 'application/vnd.github.v3+json'}
            ).json()
        else:
            d = gl_match.groupdict()
            for x in d:
                if d[x]:
                    d[x] = d[x].replace('/', '%2F').replace('.', '%2E')
            response_json = requests.get(
                f'https://gitlab.com/api/v4/projects/{d["repo"]}/repository/files/{d["file_path"]}' +
                f'{d["extension"] if d["extension"] else ""}?ref={d["branch"]}'
            ).json()

        file_contents = base64.b64decode(
            response_json['content']).decode('utf-8')

        if d['end_line']:
            start_line = int(d['start_line'])
            end_line = int(d['end_line'])
        else:
            start_line = end_line = int(d['start_line'])

        split_file_contents = file_contents.split('\n')

        required = split_file_contents[start_line - 1:end_line]

        while all(line.startswith('\t') or line.startswith(' ') for line in required):
            required = list(map(lambda line: line[1:], required))

        required = '\n'.join(required).rstrip().replace('`', r'\`')

        if len(required) != 0:
            await message.channel.send(f'```{d["language"]}\n{required}```')
        else:
            await message.channel.send('``` ```')
        await message.edit(suppress=True)
    else:
        await bot.process_commands(message)


@bot.event
async def on_ready():
    '''
    Just prints when the bot is ready
    '''

    print(f'{bot.user} has connected to Discord!')


bot.run(os.environ['DISCORD_TOKEN'])
