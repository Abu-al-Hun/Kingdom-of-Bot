import discord
from discord.ext import commands
from discord.ui import Button, View
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from art import text2art  
from colorama import Fore, Style, init

"""
  ____  _  __  ____   ____   __     __  ____  
 / ___|| ||  |/ ___| / ___|  \ \   / / / ___| 
 \___ \| || | | |  _  \___ \   \ \ / /  \___ \ 
  ___) | || |_| |_| |  ___) |   \ V /    ___) |
 |____/|_(_)____/\____/ |____/     \_/    |____/ 
"""

# Load environment variables from .env file
load_dotenv()

# Set environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
JUMP_PANEL_CHANNEL_ID = int(os.getenv('JUMP_PANEL_CHANNEL_ID'))
NOTIFICATION_CHANNEL_ID = int(os.getenv('NOTIFICATION_CHANNEL_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))
REQUIRED_ROLE_ID = int(os.getenv('REQUIRED_ROLE_ID'))
JUMP_PANEL_IMAGE_URL = os.getenv('JUMP_PANEL_IMAGE_URL')
JUMPS_FILE = 'jumps.json'

# Create JSON file if it does not exist
def initialize_jumps_file():
    if not os.path.exists(JUMPS_FILE):
        with open(JUMPS_FILE, 'w') as f:
            json.dump({}, f, indent=4)

# Load and save jumps
def load_jumps():
    with open(JUMPS_FILE, 'r') as f:
        return json.load(f)

def save_jumps(jumps):
    with open(JUMPS_FILE, 'w') as f:
        json.dump(jumps, f, indent=4)

# Define the bot with the appropriate prefix
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent if required
bot = commands.Bot(command_prefix='!', intents=intents)

class JumpForm(discord.ui.Modal, title="Jump Form"):
    jump_name = discord.ui.TextInput(label="Jump Name", placeholder="Enter the jump name")
    jump_date = discord.ui.TextInput(label="Jump Date", placeholder="Enter the jump date (YYYY-MM-DD)")
    final_kingdom = discord.ui.TextInput(label="Final Kingdom", placeholder="Enter the final kingdom")
    jump_manager_id = discord.ui.TextInput(label="Manager ID", placeholder="Enter the manager's ID")

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        jump_name = self.jump_name.value
        jump_date_str = self.jump_date.value
        final_kingdom = self.final_kingdom.value
        jump_manager_id = self.jump_manager_id.value

        try:
            jump_date = datetime.strptime(jump_date_str, "%Y-%m-%d")
            today = datetime.now()

            if jump_date <= today:
                await interaction.response.send_message("Error: The jump date must be in the future.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("Error: Invalid date format. Please use YYYY-MM-DD.", ephemeral=True)
            return

        if len(final_kingdom) != 4 or not final_kingdom.isdigit():
            await interaction.response.send_message("Error: Final Kingdom must be a 4-digit number.", ephemeral=True)
            return

        jumps = load_jumps()

        if any(jump['final_kingdom'] == final_kingdom for jump in jumps.values()):
            await interaction.response.send_message("Error: The final kingdom number already exists.", ephemeral=True)
            return

        jump_id = str(len(jumps) + 1)
        jumps[jump_id] = {
            'user_id': user_id,
            'jump_name': jump_name,
            'jump_date': jump_date_str,
            'final_kingdom': final_kingdom,
            'jump_manager_id': jump_manager_id
        }
        save_jumps(jumps)

        details = (
            f"**User:** {interaction.user}\n"
            f"**Jump Name:** {jump_name}\n"
            f"**Jump Date:** {jump_date_str}\n"
            f"**Final Kingdom:** {final_kingdom}\n"
            f"**Manager ID:** {jump_manager_id}\n"
        )

        channel = bot.get_channel(JUMP_PANEL_CHANNEL_ID)
        if channel:
            embed = discord.Embed(title="New Jump Registration Request", description=details, color=discord.Color.blue())
            view = JumpApprovalView(interaction, user_id=user_id, jump_name=jump_name, jump_date=jump_date_str, final_kingdom=final_kingdom, jump_manager_id=jump_manager_id)
            await channel.send(embed=embed, view=view)
            await interaction.response.send_message("Your jump registration request has been sent for approval.", ephemeral=True)
        else:
            await interaction.response.send_message("Error: Could not find the jump panel channel.", ephemeral=True)

class JumpApprovalView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, *, user_id: str, jump_name: str, jump_date: str, final_kingdom: str, jump_manager_id: str):
        super().__init__(timeout=180)
        self.interaction = interaction
        self.user_id = user_id
        self.jump_name = jump_name
        self.jump_date = jump_date
        self.final_kingdom = final_kingdom
        self.jump_manager_id = jump_manager_id

        # Add the select menu to the view
        self.add_item(JumpApprovalSelect(
            user_id=self.user_id,
            jump_name=self.jump_name,
            jump_date=self.jump_date,
            final_kingdom=self.final_kingdom,
            jump_manager_id=self.jump_manager_id
        ))

class JumpApprovalSelect(discord.ui.Select):
    def __init__(self, *, user_id: str, jump_name: str, jump_date: str, final_kingdom: str, jump_manager_id: str):
        options = [
            discord.SelectOption(label="Approve", description="Approve the jump registration", value="approve"),
            discord.SelectOption(label="Reject", description="Reject the jump registration", value="reject")
        ]
        super().__init__(placeholder="Choose an action...", options=options)
        # Store the passed parameters as attributes
        self.user_id = user_id
        self.jump_name = jump_name
        self.jump_date = jump_date
        self.final_kingdom = final_kingdom
        self.jump_manager_id = jump_manager_id

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "approve":
            jumps = load_jumps()
            for jump_id, jump in jumps.items():
                if jump['user_id'] == self.user_id:
                    jumps[jump_id] = {
                        'user_id': self.user_id,
                        'jump_name': self.jump_name,
                        'jump_date': self.jump_date,
                        'final_kingdom': self.final_kingdom,
                        'jump_manager_id': self.jump_manager_id
                    }
                    save_jumps(jumps)
                    break

            await interaction.response.send_message("The jump registration has been updated successfully.", ephemeral=True)
            await interaction.message.delete()
        elif self.values[0] == "reject":
            jumps = load_jumps()
            jumps = {jump_id: jump for jump_id, jump in jumps.items() if jump['user_id'] != self.user_id}
            save_jumps(jumps)
            await interaction.response.send_message("The jump registration has been rejected.", ephemeral=True)
            await interaction.message.delete()

@bot.event
async def on_ready():
    try:
        # Print login information
        print(f'Logged in as {bot.user}')

        # Create ASCII Art text for "Data Team Skoda"
        ascii_art_text = text2art("Skoda")

        # Print the ASCII Art text in the console with light color
        print(Fore.LIGHTCYAN_EX + ascii_art_text + Style.RESET_ALL)
        print(Fore.LIGHTGREEN_EX + f"Logged in as {bot.user}" + Style.RESET_ALL)

        # Initialize the jumps file if it does not exist
        initialize_jumps_file()

        # Sync the bot's commands with the guild
        guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)

        # Change bot presence
        await bot.change_presence(
            status=discord.Status.do_not_disturb,  # Set status to 'Do Not Disturb'
            activity=discord.Activity(
                type=discord.ActivityType.listening,  # Set activity type to 'Listening'
                name="Skoda"  # Set activity name
            )
        )
    except Exception as e:
        print(Fore.LIGHTRED_EX + f"Error in on_ready event: {e}" + Style.RESET_ALL)

@bot.tree.command(name='jump_panel', description='Display the jump control panel')
async def jump_panel(interaction: discord.Interaction):
    if not any(role.id == REQUIRED_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message('You do not have the necessary permissions to use this command.', ephemeral=True)
        return

    title = "Jump Control Panel"
    description = "Choose the action you want to perform:"
    
    embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
    if JUMP_PANEL_IMAGE_URL:
        embed.set_image(url=JUMP_PANEL_IMAGE_URL)
    
    view = JumpView()
    await interaction.response.send_message(embed=embed, view=view)

class JumpView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(JumpSelect())

class JumpSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="📋┃Register Jump", description="Register a new jump", value="register_jump"),
            discord.SelectOption(label="❌┃Cancel Registration", description="Cancel a registered jump", value="cancel_registration")
        ]
        super().__init__(placeholder="Choose the action you want to perform...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_option = self.values[0]

        if selected_option == "register_jump":
            await interaction.response.send_modal(JumpForm())
        elif selected_option == "cancel_registration":
            user_id = str(interaction.user.id)
            jumps = load_jumps()
            jumps = {jump_id: jump for jump_id, jump in jumps.items() if jump['user_id'] != user_id}
            save_jumps(jumps)
            await interaction.response.send_message('Jump registration has been successfully canceled.', ephemeral=True)

@bot.tree.command(name='list_jumps', description='List all available jumps')
async def list_jumps(interaction: discord.Interaction):
    jumps = load_jumps()

    if jumps:
        title = "Available Jumps"
        description = ""
        for jump_id, jump in jumps.items():
            manager = interaction.guild.get_member(int(jump['jump_manager_id']))
            manager_mention = manager.mention if manager else "Unknown"
            description += (
                f"**Jump Name:** {jump['jump_name']}\n"
                f"**Jump Date:** {jump['jump_date']}\n"
                f"**Final Kingdom:** {jump['final_kingdom']}\n"
                f"**Manager:** {manager_mention}\n\n"
            )
        embed = discord.Embed(title="Available Jumps", description=description, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed,)
    else:
        await interaction.response.send_message('No jumps are currently available.', ephemeral=True)

bot.run(DISCORD_TOKEN)
