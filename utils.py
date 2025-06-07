from datetime import datetime
import discord

def format_time_left(end):
    delta = end - datetime.utcnow()
    days = delta.days
    hours = delta.seconds // 3600
    return f"{days} Tage, {hours} Stunden"

async def send_reminder(member: discord.Member, tage: int):
    try:
        await member.send(f"📢 Erinnerung: Dein Abo läuft in {tage} Tagen ab!")
    except:
        pass
