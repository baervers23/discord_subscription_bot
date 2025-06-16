import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
import os
from dotenv import load_dotenv
from database import init_db, get_subscription, delete_subscription, redeem_code, get_all_subscriptions, check_expirations, add_subscription, get_connection, load_codes, save_codes, add_code_to_file
from utils import format_time_left, send_reminder

load_dotenv()
init_db()

ABO_ROLE_ID = int(os.getenv("ABO_ROLE_ID"))
TOKEN = int(os.getenv("DISCORD_TOKEN"))
GUILD_ID = int(os.getenv("GUILD_ID"))
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
    
@tasks.loop(hours=24)
async def run_expiration_checks():
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    role = guild.get_role(ABO_ROLE_ID)
    for user_id, end, delta in check_expirations():
        member = guild.get_member(user_id)
        if member and delta <= 0:
            await member.remove_roles(role)
        elif delta in [30, 7, 3]:
            await send_reminder(member, delta)

    now = datetime.now()
    # Hole alle aktiven Subscriptions (user_id, end_date)
    active_subs = [uid for uid, end_date in get_all_subscriptions() if datetime.fromisoformat(end_date) > now]
    abo_role = guild.get_role(ABO_ROLE_ID)
    
    for member in guild.members:
        if member.bot:
            continue
        if member.id in active_subs:
            if abo_role not in member.roles:
                await member.add_roles(abo_role, reason="Aktives Abo")
        else:
            if abo_role in member.roles:
                await member.remove_roles(abo_role, reason="Abo abgelaufen")

def trial_already_used(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT trial_used FROM subscriptions WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return False  # User hat kein Abo, also auch kein Trial genutzt
    return row[0] == 1  # trial_used == 1 bedeutet Trial schon genutzt

def mark_trial_used(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE subscriptions SET trial_used = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

@bot.tree.command(name="probeabo", description="Gibt dir ein 30-tägiges Probeabo (einmalig)")
async def probeabo(interaction: discord.Interaction):
    user_id = interaction.user.id

    # Prüfe, ob Trial schon genutzt wurde (funktion musst du definieren)
    if trial_already_used(user_id):
        await interaction.response.send_message("❌ Du hast dein Probeabo schon genutzt.", ephemeral=True)
        return

    # Probeabo hinzufügen: 1 Monat = 30 Tage
    add_subscription(user_id, 1)

    # Trial als benutzt markieren
    mark_trial_used(user_id)

    # Rolle hinzufügen
    role = interaction.guild.get_role(ABO_ROLE_ID)
    if role:
        member = interaction.user
        await member.add_roles(role)

    await interaction.response.send_message("✅ Probeabo aktiviert! Du hast jetzt 30 Tage Zugriff.", ephemeral=True)
    
@bot.tree.command(name="guthaben", description="Zeigt dein aktuelles Guthaben")
async def guthaben(interaction: discord.Interaction):
    abo = get_subscription(interaction.user.id)
    if abo:
        await interaction.response.send_message(f"📅 Dein Abo läuft noch bis zum {abo.date()} ({format_time_left(abo)} verbleibend).", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Du hast derzeit kein aktives Abo.", ephemeral=True)

@bot.tree.command(name="listcodes", description="Zeigt alle verfügbaren (nicht verwendeten) Einlösecodes")
async def listcodes(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_USER_ID:
        await interaction.response.send_message("🚫 Nur Admins dürfen Codes anzeigen!", ephemeral=True)
        return

    codes = load_codes()
    unused = {k: v for k, v in codes.items() if not v.get("used", False)}

    if not unused:
        await interaction.response.send_message("❌ Keine verfügbaren Codes gefunden.", ephemeral=True)
        return

    message = "**📋 Verfügbare Codes:**\n"
    for code, data in unused.items():
        months = data.get("months", "?")
        message += f"- `{code}` → {months} Monat(e)\n"

    await interaction.response.send_message(message, ephemeral=True)

@bot.tree.command(name="übersicht", description="Admin: Übersicht aller Subscriptions (nur für Admin)")
async def uebersicht(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_USER_ID:
        await interaction.response.send_message("🚫 Nur für Admins!", ephemeral=True)
        return

    subscriptions = get_all_subscriptions()
    if not subscriptions:
        await interaction.response.send_message("❌ Keine aktiven Subscriptions gefunden.", ephemeral=True)
        return

    msg = "**📋 Aktive Subscriptions:**"
    for user_id, end_date_str in subscriptions:
        end_dt = datetime.fromisoformat(end_date_str)
        left = format_time_left(end_dt)  # z.B. "5 Tage übrig"
        msg += f"\n<@{user_id}> – endet am {end_dt.date()} ({left})"

    await interaction.response.send_message(msg, ephemeral=True)
    
@bot.tree.command(name="addabo", description="Fügt einem User ein Abo hinzu")
@app_commands.describe(user="Benutzer auswählen", months="Abo-Dauer in Monaten")
async def addabo(interaction: discord.Interaction, user: discord.Member, months: int):
    if interaction.user.id != ADMIN_USER_ID:
        await interaction.response.send_message("🚫 Nur für Admins!", ephemeral=True)
        return
    
    add_subscription(user.id, months)
    await interaction.response.send_message(f"{user.mention} hat nun ein Abo für {months} Monat(e).", ephemeral=True)

@bot.tree.command(name="redeem", description="Geschenkkarte einlösen")
@app_commands.describe(code="Dein Geschenkcode")
async def redeem(interaction: discord.Interaction, code: str):
    await interaction.response.defer(ephemeral=True)
    result = redeem_code(interaction.user.id, code)
    if isinstance(result, datetime):
        guild = bot.get_guild(GUILD_ID)
        member = guild.get_member(interaction.user.id)
        role = guild.get_role(ABO_ROLE_ID)
        if role:
            await member.add_roles(role)
        await interaction.followup.send(f"✅ Code eingelöst! Neues Ablaufdatum: {result.date()}")
    else:
        await interaction.followup.send(f"❌ {result}")

@bot.tree.command(name="addcode", description="Fügt einen neuen Einlösecode hinzu")
@app_commands.describe(code="Einmaliger Code (z. B. SUPERABO3M)", months="Gültigkeitsdauer in Monaten")
async def addcode(interaction: discord.Interaction, code: str, months: int):
    if interaction.user.id != ADMIN_USER_ID:
        await interaction.response.send_message("🚫 Nur Admins dürfen Codes hinzufügen!", ephemeral=True)
        return

    code = code.upper()
    success = add_code_to_file(code, months)

    if success:
        await interaction.response.send_message(f"✅ Code `{code}` mit `{months}` Monat(en) wurde gespeichert.", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ Der Code `{code}` existiert bereits!", ephemeral=True) 

@bot.tree.command(name="cancelabo", description="Kündigt das Abo des ausgewählten Benutzer und entfernt die Rolle.")
@app_commands.describe(user="Benutzer auswählen")
async def cancelabo(interaction: discord.Interaction, user: discord.Member):
    if interaction.user.id != ADMIN_USER_ID:
        await interaction.response.send_message("🚫 Nur für Admins!", ephemeral=True)
        return
    
    delete_subscription(user.id)
    await interaction.response.send_message(f"✅ Das Abo von {user.mention} wurde erfolgreich gekündigt", ephemeral=True)

@bot.event
async def on_ready():
    run_expiration_checks.start()
    print(f"Bot ist eingeloggt als {bot.user}")
    await bot.tree.sync()
    print(f"✅ Slash-Befehle synchronisiert: {[cmd.name for cmd in bot.tree.get_commands()]}")

bot.run(TOKEN)
