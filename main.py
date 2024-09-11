import nextcord
from nextcord.ext import commands
from nextcord import Interaction, ButtonStyle
import random
import asyncio

intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class RPSGame:
    def __init__(self):
        self.games = {}
        self.scores = {}

    def create_game(self, player1_id, player2_id):
        game_id = f"{player1_id}-{player2_id}"
        self.games[game_id] = {"player1": player1_id, "player2": player2_id, "choices": {}}
        if player1_id not in self.scores:
            self.scores[player1_id] = 0
        if player2_id not in self.scores:
            self.scores[player2_id] = 0

    def set_choice(self, game_id, player_id, choice):
        if game_id in self.games and player_id in (self.games[game_id]["player1"], self.games[game_id]["player2"]):
            self.games[game_id]["choices"][player_id] = choice
            return True
        return False

    def get_winner(self, game_id):
        if game_id not in self.games or len(self.games[game_id]["choices"]) != 2:
            return None

        choices = {1: "rock", 2: "paper", 3: "scissors"}
        p1_id, p2_id = self.games[game_id]["player1"], self.games[game_id]["player2"]
        p1_choice = choices[self.games[game_id]["choices"][p1_id]]
        p2_choice = choices[self.games[game_id]["choices"][p2_id]]

        if p1_choice == p2_choice:
            return None
        elif (
            (p1_choice == "rock" and p2_choice == "scissors") or
            (p1_choice == "paper" and p2_choice == "rock") or
            (p1_choice == "scissors" and p2_choice == "paper")
        ):
            return p1_id
        else:
            return p2_id

    def update_score(self, player_id):
        self.scores[player_id] += 1

    def end_game(self, game_id):
        if game_id in self.games:
            del self.games[game_id]

game = RPSGame()

class RPSView(nextcord.ui.View):
    def __init__(self, game_id, player_id):
        super().__init__()
        self.game_id = game_id
        self.player_id = player_id
        self.value = None

    @nextcord.ui.button(label="Rock", emoji="🪨", style=ButtonStyle.gray)
    async def rock(self, button: nextcord.ui.Button, interaction: Interaction):
        await self.make_choice(interaction, 1, "rock")

    @nextcord.ui.button(label="Paper", emoji="📄", style=ButtonStyle.danger)
    async def paper(self, button: nextcord.ui.Button, interaction: Interaction):
        await self.make_choice(interaction, 2, "paper")

    @nextcord.ui.button(label="Scissors", emoji="✂️", style=ButtonStyle.blurple)
    async def scissors(self, button: nextcord.ui.Button, interaction: Interaction):
        await self.make_choice(interaction, 3, "scissors")

    async def make_choice(self, interaction: Interaction, choice_num, choice_name):
        if interaction.user.id != self.player_id:
            await interaction.response.send_message("This is not your game!", ephemeral=True)
            return
        
        if game.set_choice(self.game_id, self.player_id, choice_num):
            self.value = choice_name
            await interaction.response.edit_message(content=f"You chose {choice_name}!", view=None)
            self.stop()
        else:
            await interaction.response.send_message("An error occurred. The game might have ended.", ephemeral=True)

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.slash_command(name="rps", description="Start a classic rock paper scissors game")
async def rps(interaction: Interaction, opponent: nextcord.Member = None):
    if opponent:
        await play_multiplayer(interaction, opponent)
    else:
        await play_against_bot(interaction)

async def play_against_bot(interaction: Interaction):
    view = RPSView(f"bot-{interaction.user.id}", interaction.user.id)
    await interaction.response.send_message("Choose rock, paper, or scissors", view=view, ephemeral=True)

    await view.wait()

    if view.value is not None:
        bot_choice = random.choice(["rock", "paper", "scissors"])
        result = determine_winner(view.value, bot_choice)

        embed = create_embed(interaction.user.display_name, view.value, "Bot", bot_choice, result)
        await interaction.followup.send(embed=embed)

async def play_multiplayer(interaction: Interaction, opponent: nextcord.Member):
    if opponent.bot:
        await interaction.response.send_message("You can't challenge a bot to a multiplayer game!", ephemeral=True)
        return

    if opponent.id == interaction.user.id:
        await interaction.response.send_message("You can't challenge yourself!", ephemeral=True)
        return

    game_id = f"{interaction.user.id}-{opponent.id}"
    game.create_game(interaction.user.id, opponent.id)

    await interaction.response.send_message(f"{opponent.mention}, you've been challenged to a game of Rock Paper Scissors by {interaction.user.mention}! Do you accept?")

    def check(m):
        return m.author.id == opponent.id and m.content.lower() in ['yes', 'no']

    try:
        msg = await bot.wait_for('message', timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await interaction.followup.send("The opponent didn't respond in time. Game cancelled.")
        game.end_game(game_id)
        return

    if msg.content.lower() == 'no':
        await interaction.followup.send("The opponent declined the challenge. Game cancelled.")
        game.end_game(game_id)
        return

    await interaction.followup.send("Game accepted! Both players will now choose their moves.")

    player1_view = RPSView(game_id, interaction.user.id)
    player2_view = RPSView(game_id, opponent.id)

    player1_message = await interaction.user.send("Make your choice:", view=player1_view)
    player2_message = await opponent.send("Make your choice:", view=player2_view)

    await asyncio.gather(player1_view.wait(), player2_view.wait())

    # Edit the DM messages to remove the buttons
    await player1_message.edit(content="You've made your choice. Waiting for results...", view=None)
    await player2_message.edit(content="You've made your choice. Waiting for results...", view=None)

    winner_id = game.get_winner(game_id)
    if winner_id is None:
        result = "It's a draw!"
    else:
        winner = interaction.user if winner_id == interaction.user.id else opponent
        game.update_score(winner_id)
        result = f"{winner.display_name} Won!"

    embed = create_embed(interaction.user.display_name, game.games[game_id]["choices"][interaction.user.id],
                         opponent.display_name, game.games[game_id]["choices"][opponent.id], result)
    await interaction.channel.send(embed=embed)

    game.end_game(game_id)

def determine_winner(player_choice, bot_choice):
    if player_choice == bot_choice:
        return "It's a draw!"
    elif (
        (player_choice == "rock" and bot_choice == "scissors") or
        (player_choice == "paper" and bot_choice == "rock") or
        (player_choice == "scissors" and bot_choice == "paper")
    ):
        return "You Won!"
    else:
        return "Bot Won!"

def create_embed(player1_name, player1_choice, player2_name, player2_choice, result):
    choices = {1: "Rock", 2: "Paper", 3: "Scissors"}
    embed = nextcord.Embed(title="Rock Paper Scissors Result", color=nextcord.Color.random())
    embed.add_field(name=f'{player1_name}\'s Choice:', value=choices.get(player1_choice, player1_choice).capitalize(), inline=False)
    embed.add_field(name=f'{player2_name}\'s Choice:', value=choices.get(player2_choice, player2_choice).capitalize(), inline=False)
    embed.add_field(name='Result:', value=f"𒆜{result}𒆜", inline=False)
    return embed

@bot.slash_command(name="leaderboard", description="Show the RPS leaderboard")
async def leaderboard(interaction: Interaction):
    sorted_scores = sorted(game.scores.items(), key=lambda x: x[1], reverse=True)
    embed = nextcord.Embed(title="Rock Paper Scissors Leaderboard", color=nextcord.Color.gold())
    
    for i, (player_id, score) in enumerate(sorted_scores[:10], start=1):
        player = await bot.fetch_user(player_id)
        embed.add_field(name=f"{i}. {player.display_name}", value=f"Score: {score}", inline=False)
    
    await interaction.response.send_message(embed=embed)

bot.run("MTE4NzQwNzUyMTA5NTM2ODcxNQ.GR5T_Z.gLHPxpYzdp96qDo5P7BAkyIzBcjRmPMdL4Kz7c")
