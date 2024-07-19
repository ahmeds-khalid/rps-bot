import nextcord
from nextcord.ext import commands
from nextcord.ui import view
from nextcord import Interaction
import os
import random

userChoice = 0
botValue = None

client = commands.Bot(command_prefix="!", intents=nextcord.Intents.all())

@client.event
async def on_ready():
    print("RPS bot is ready!!")

#UI

class Confirm(nextcord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @nextcord.ui.button(label="Rock", emoji="🪨", style=nextcord.ButtonStyle.gray)
    async def rock(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        UserChoice = 1
        self.value = "rock"
        self.stop()

    @nextcord.ui.button(label="Paper", emoji="📄", style=nextcord.ButtonStyle.danger)
    async def paper(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        UserChoice = 2
        self.value = "paper"
        self.stop()
    
    @nextcord.ui.button(label="Scissor", emoji="✂️", style=nextcord.ButtonStyle.blurple)
    async def scissor(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        UserChoice = 3
        self.value = "scissor"
        self.stop()

@client.slash_command(name="game", description="Start a classic rock paper scissors game", guild_ids=[1173218609682731038])
async def game(interaction: Interaction, ctx):
    view = Confirm()
    await interaction.response.send_message("Choose rock, paper, or scissors", view=view)

    await view.wait()

    if not view.value == None:
        botChoice = random.randint(1, 3)
        if botChoice == 1 and userChoice == 2:
            await interaction.send(interaction.user.display_name)
        # await interaction.send(botChoice)
    if userChoice == botChoice:
        win = "DRAW!"
    else:
        match view.value:
            case "rock":
                if botChoice == 2:
                    win = "Ai Won!"
                elif botChoice == 3:
                    win = interaction.user.display_name + " Won!"
            case "paper":
                if botChoice == 1:
                    win = interaction.user.display_name + " Won!"
                elif botChoice == 3:
                    win = "Ai Won!"
            case "scissor":
                if botChoice == 1:
                    win = "Ai Won!"
                elif botChoice == 2:
                    win = interaction.user.display_name + " Won!"
    
    if view.value == "rock":
        print("Confirmed")
    if view.value == False:
        print("Cancelled")
    
    if botChoice == 1:
        botValue = "Rock"
    elif botChoice == 2:
        botValue = "Paper"
    elif botChoice == 3:
        botValue = "Scissor"
    
    player = interaction.user.display_name, "'s Match"

    embed = nextcord.Embed(title=player, color=0xffffff)
    embed.add_field(name='Your Choice:', value= view.value, inline=False)
    embed.add_field(name='Ai Choice:', value= botValue, inline=False)
    embed.add_field(name='Result:', value= "<== " + win + " ==>", inline=False)

    # Send the embed as a message
    await interaction.response.send_message(embed=embed)

client.run("MTE4NzQwNzUyMTA5NTM2ODcxNQ.GR5T_Z.gLHPxpYzdp96qDo5P7BAkyIzBcjRmPMdL4Kz7c")