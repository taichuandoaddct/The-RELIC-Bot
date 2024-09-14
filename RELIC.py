#!/usr/bin/env python
# coding: utf-8


#####Functionality 1: Prepare the bot to run
#Loads in packages
import discord
from discord.ext import commands
import json
import os
import asyncio
from dotenv import load_dotenv

#Load the environment variables with the bot token from the .env file
load_dotenv()


# Define a global dictionary to store the trackers
trackers = {}

# Load trackers from the 'persistent tracks' file at startup
if os.path.exists('persistent tracks'):
    with open('persistent tracks', 'r') as f:
        try:
            trackers = json.load(f)
            print("Trackers loaded from 'persistent tracks'.")
        except json.JSONDecodeError:
            print("No valid data found in 'persistent tracks' or the file is empty.")
            trackers = {}

# Define the necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Enable intents for message content (necessary for reading messages)

# Create a bot instance with the command prefix "/" and the defined intents
bot = commands.Bot(command_prefix="/", intents=intents)

#Command to shutdown the bot gracefully
@bot.command()
@commands.is_owner()  # Restricts this command to the bot owner
async def shutdown(ctx):
    await ctx.send("Trackers saved. Shutting down the bot...")

    # Save the current trackers to 'persistent tracks'
    with open('persistent tracks', 'w') as f:
        json.dump(trackers, f)
        print("Trackers saved to 'persistent tracks'.")

    # Adding a print statement to confirm shutdown
    print("Bot is shutting down...")
    await bot.close()



#####Functionality 2: Lookup items in the glossary.txt
# Define a generic command handler
@bot.command()
async def lookup(ctx, entry_name: str):
    try:
        # Check if the glossary exists
        if not os.path.exists('glossary.txt'):
            await ctx.send("The glossary file does not exist.")
            return

        # Load the glossary and look up the entry
        with open('glossary.txt', 'r') as file:
            data = file.read()
            if entry_name in data:
                # Find the entry in the glossary
                start = data.find(entry_name)
                end = data.find("=", start)
                if end == -1:  # Handle the case where no delimiter is found
                    end = len(data)

                # Extract the text from start to end
                result = data[start:end].strip()
                await ctx.send(result)
            else:
                await ctx.send(f"Entry '{entry_name}' not found.")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")



#####Functionality 3: Add commands for trackers
# This command makes a new tracker
@bot.command()
async def newtracker(ctx, name: str, length: int):
    print(f"newtracker command called with name: {name}, length: {length}")  # Debugging print
    if name in trackers:
        await ctx.send(f"A tracker with the name '{name}' already exists.")
    else:
        trackers[name] = {"length": length, "ticks": 0, "is_gm": False}  # Initialize with the total length and 0 ticks, not a GM tracker
        display = generate_tracker_display(0, length)  # Generate the initial display
        await ctx.send(f"Tracker '{name}' created with {length} boxes.\n{display}")


# This command ticks the trackers up
# Updated /tick command to handle GM trackers
@bot.command()
async def tick(ctx, name: str, ticks: int):
    if name not in trackers:
        await ctx.send(f"Tracker '{name}' does not exist.")
    else:
        tracker = trackers[name]
        if tracker["ticks"] + ticks > tracker["length"]:
            await ctx.send(f"Cannot tick more boxes than the tracker has. Tracker '{name}' only has {tracker['length'] - tracker['ticks']} boxes left.")
        else:
            tracker["ticks"] += ticks
            display = generate_tracker_display(tracker["ticks"], tracker["length"], tracker.get("is_gm", False))  # Generate the updated display
            await ctx.send(f"Tracker '{name}' updated: {tracker['ticks']}/{tracker['length']} boxes ticked.\n{display}")

            if tracker["ticks"] == tracker["length"]:
                await ctx.send(f"Tracker '{name}' is now complete!")


# This resets a given tracker back to 0
@bot.command()
async def reset(ctx, name: str):
    if name not in trackers:
        await ctx.send(f"Tracker '{name}' does not exist.")
    else:
        trackers[name]["ticks"] = 0  # Reset tick count to 0
        display = generate_tracker_display(0, trackers[name]["length"], trackers[name].get("is_gm", False))  # Generate the reset display
        await ctx.send(f"Tracker '{name}' has been reset to 0/{trackers[name]['length']} boxes.\n{display}")


# This removes a given tracker from the list of active trackers
@bot.command()
async def remove(ctx, name: str):
    if name not in trackers:
        await ctx.send(f"Tracker '{name}' does not exist.")
    else:
        del trackers[name]  # Remove the tracker from the dictionary
        await ctx.send(f"Tracker '{name}' has been removed.")


# This removes all trackers from the list
@bot.command()
async def removeall(ctx):
    trackers.clear()  # Clear the entire dictionary
    await ctx.send("All trackers have been removed and the list has been reset.")


# This listens for the name of a tracker and then prints that tracker's status
@bot.event
async def on_message(message):
    if message.content.startswith("/") and not message.author.bot:
        command = message.content[1:]  # Remove the slash ("/") at the beginning

        if command in trackers:
            tracker = trackers[command]
            display = generate_tracker_display(tracker["ticks"], tracker["length"], tracker.get("is_gm", False))  # Generate the display
            await message.channel.send(f"Tracker '{command}': {tracker['ticks']}/{tracker['length']} boxes ticked.\n{display}")
        else:
            await bot.process_commands(message)  # Process other commands normally


# Prints the state of all active trackers
@bot.command()
async def alltrackers(ctx):
    if not trackers:
        await ctx.send("There are no active trackers.")
    else:
        status_list = []
        for name, tracker in trackers.items():
            display = generate_tracker_display(tracker["ticks"], tracker["length"], tracker.get("is_gm", False))
            status_list.append(f"Tracker '{name}': {tracker['ticks']}/{tracker['length']} boxes ticked.\n{display}")
        status_message = "\n".join(status_list)
        await ctx.send(f"Current status of all active trackers:\n{status_message}")


# This command makes a new tracker with spoiler tags
@bot.command()
async def gmtracker(ctx, name: str, length: int):
    print(f"gmtracker command called with name: {name}, length: {length}")  # Debugging print
    if name in trackers:
        await ctx.send(f"A tracker with the name '{name}' already exists.")
    else:
        # Store the tracker with a flag indicating it's a GM tracker
        trackers[name] = {"length": length, "ticks": 0, "is_gm": True}
        display = generate_tracker_display(0, length, gm_tracker=True)  # Generate the initial display with spoiler tags
        await ctx.send(f"||Tracker '{name}' created with {length} boxes.||\n{display}")


# This prints all of the current commands
@bot.command()
async def printcommands(ctx):
    commands_list = (
        "/newtracker [name] [length] - Create a new tracker with a specified number of boxes.\n"
        "/gmtracker [name] [length] - Create a new tracker spoiler tags for the GM.\n"
        "/tick [name] [length] - Tick a specified number of boxes on the tracker.\n"
        "/reset [name] - Reset all boxes on the tracker to unticked.\n"
        "/remove [name] - Remove the tracker from the list of active trackers.\n"
        "/removeall - Remove all trackers and reset the list to blank.\n"
        "/alltrackers - Print the status of all active trackers.\n"
        "/[trackername] - Print the status of the specified tracker.\n"
        "/printcommands - Print this list of commands, their syntax, and what they do.\n"
        "/shutdown - Gracefully shuts down the bot (owner only).\n"
        "/lookup [name] - Lookup that text in the rules document (WIP)."
    )
    await ctx.send(f"Available commands:\n{commands_list}")


# Modified helper function to generate the tracker display with optional spoiler tags
def generate_tracker_display(ticked: int, total: int, gm_tracker: bool = False) -> str:
    filled_boxes = "■" * ticked
    empty_boxes = "□" * (total - ticked)
    display = filled_boxes + empty_boxes
    if gm_tracker:
        # Wrap each box with spoiler tags
        display = ''.join([f"||{box}||" for box in display])
    return display



#####Functionality 4: Read and curate NPCs from csv file
#Start with important the csv on startup
import csv

# Define a global list to store the NPCs
npc_list = []
# Load NPCs from the 'NPCList.csv' file at startup
def load_npc_list():
    global npc_list
    if os.path.exists('NPCList.csv'):
        with open('NPCList.csv', 'r') as file:
            reader = csv.DictReader(file)
            npc_list = list(reader)
            print(f"Loaded {len(npc_list)} NPCs from 'NPCList.csv'.")
    else:
        print("NPCList.csv file does not exist.")
# Load NPC list on startup
load_npc_list()

#Create the command to print all NPCs in the list
@bot.command()
async def printNPC(ctx, name: str):
    if name.lower() == "all":
        if npc_list:
            for npc in npc_list:
                formatted_npc = format_npc(npc)
                await ctx.send(formatted_npc + "\n")  # Add an extra line break after each NPC
        else:
            await ctx.send("No NPCs found.")
    else:
        # Handle printing a specific NPC
        for npc in npc_list:
            if npc["Name"].lower() == name.lower():
                formatted_npc = format_npc(npc)
                await ctx.send(formatted_npc)
                return
        await ctx.send(f"NPC '{name}' not found.")
#Helper function to format the data
def format_npc(npc):
    formatted_npc = "\n".join([f"{key}: {value}" for key, value in npc.items()])
    return formatted_npc


#Create the command to add NPCs
@bot.command()
async def addNPC(ctx, *args):
    # Ensure the correct number of arguments
    if len(args) != len(npc_list[0]):
        await ctx.send(f"Incorrect number of arguments provided. Expected {len(npc_list[0])} fields.")
        return

    # Create a new NPC using the provided arguments
    new_npc = {key: value.strip('"').strip("'") for key, value in zip(npc_list[0].keys(), args)}
    npc_list.append(new_npc)
    save_npc_list()
    await ctx.send(f"NPC '{new_npc['Name']}' added successfully.")

#Create the command to remove NPCs
@bot.command()
async def removeNPC(ctx, name: str):
    global npc_list
    initial_count = len(npc_list)
    npc_list = [npc for npc in npc_list if npc["Name"].lower() != name.lower()]

    if len(npc_list) < initial_count:
        save_npc_list()
        await ctx.send(f"NPC '{name}' removed successfully.")
    else:
        await ctx.send(f"NPC '{name}' not found.")

#Ensure that changes are saved back to the csv file
def save_npc_list():
    if npc_list:
        with open('NPCList.csv', 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=npc_list[0].keys())
            writer.writeheader()
            writer.writerows(npc_list)
            print("NPC list saved to 'NPCList.csv'.")
    else:
        print("NPC list is empty; nothing to save.")



#####Functionality Z" Start the bot with a proper event loop
# Start the bot using asyncio.run() to ensure the event loop is properly managed
#This is calling in the token from the .env file
bot_token = os.getenv('DISCORD_BOT_TOKEN')
async def main():
    await bot.start(bot_token)

if __name__ == "__main__":
    # Use asyncio.run() to handle the event loop
    asyncio.run(main())

