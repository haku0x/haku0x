import nextcord
from nextcord.ext import tasks, commands
from typing import Any
import itertools
import aiohttp
import json

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

intents = nextcord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(intents=intents)

discord_token = config['token']
guild_id = int(config['guild_id'])
service_id = config['service_id']
api_token = config['api_token']
allowed_user_id = config['allowed_user_id']

statuses = ["Le Datalachs"]

BASE_URL = f"https://backend.datalix.de/v1/service/{service_id}"


def is_allowed(interaction: nextcord.Interaction) -> bool:
    return interaction.user.id == allowed_user_id


NO_PERMISSION = "Du hast keine Berechtigung, diesen Befehl auszuführen."


async def api_post(path: str) -> tuple[bool, str]:
    url = f"{BASE_URL}/{path}?token={api_token}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as response:
            text = await response.text()
            return response.status == 200, text


async def api_get(path: str) -> tuple[bool, Any]:
    if path:
        url = f"{BASE_URL}/{path}?token={api_token}"
    else:
        url = f"{BASE_URL}?token={api_token}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return True, await response.json()
            return False, await response.text()


# --- Power Control ---

@bot.slash_command(name="start", description="Startet den Server", guild_ids=[guild_id])
async def start(interaction: nextcord.Interaction):
    if not is_allowed(interaction):
        return await interaction.response.send_message(NO_PERMISSION, ephemeral=True)
    await interaction.response.send_message("Starte Server...")
    ok, result = await api_post("start")
    if ok:
        await interaction.followup.send("✅ Server wurde gestartet.")
    else:
        await interaction.followup.send(f"❌ Fehler beim Starten: {result}")


@bot.slash_command(name="stop", description="Stoppt den Server", guild_ids=[guild_id])
async def stop(interaction: nextcord.Interaction):
    if not is_allowed(interaction):
        return await interaction.response.send_message(NO_PERMISSION, ephemeral=True)
    await interaction.response.send_message("Stoppe Server...")
    ok, result = await api_post("stop")
    if ok:
        await interaction.followup.send("✅ Server wurde gestoppt.")
    else:
        await interaction.followup.send(f"❌ Fehler beim Stoppen: {result}")


@bot.slash_command(name="shutdown", description="Fährt den Server herunter", guild_ids=[guild_id])
async def shutdown(interaction: nextcord.Interaction):
    if not is_allowed(interaction):
        return await interaction.response.send_message(NO_PERMISSION, ephemeral=True)
    await interaction.response.send_message("Fahre Server herunter...")
    ok, result = await api_post("shutdown")
    if ok:
        await interaction.followup.send("✅ Server wurde heruntergefahren.")
    else:
        await interaction.followup.send(f"❌ Fehler beim Herunterfahren: {result}")


@bot.slash_command(name="reboot", description="Rebootet den Server", guild_ids=[guild_id])
async def reboot(interaction: nextcord.Interaction):
    if not is_allowed(interaction):
        return await interaction.response.send_message(NO_PERMISSION, ephemeral=True)
    await interaction.response.send_message("Reboote Server...")
    ok, result = await api_post("restart")
    if ok:
        await interaction.followup.send("✅ Server wurde neu gestartet.")
    else:
        await interaction.followup.send(f"❌ Fehler beim Reboot: {result}")


# --- Status & Info (neu) ---

@bot.slash_command(name="status", description="Zeigt den aktuellen Server-Status", guild_ids=[guild_id])
async def status(interaction: nextcord.Interaction):
    if not is_allowed(interaction):
        return await interaction.response.send_message(NO_PERMISSION, ephemeral=True)
    await interaction.response.defer()
    ok, data = await api_get("status")
    if ok:
        server_status = data.get("status", "unbekannt")
        color = nextcord.Color.green() if server_status == "running" else nextcord.Color.red()
        embed = nextcord.Embed(title="Server Status", color=color)
        embed.add_field(name="Status", value=server_status.capitalize(), inline=False)
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(f"❌ Fehler beim Abrufen des Status: {data}")


@bot.slash_command(name="ip", description="Zeigt die IP-Adressen des Servers", guild_ids=[guild_id])
async def ip(interaction: nextcord.Interaction):
    if not is_allowed(interaction):
        return await interaction.response.send_message(NO_PERMISSION, ephemeral=True)
    await interaction.response.defer()
    ok, data = await api_get("ip")
    if ok:
        embed = nextcord.Embed(title="Server IP-Adressen", color=nextcord.Color.blue())
        ipv4_list = data.get("ipv4", [])
        ipv6_list = data.get("ipv6", [])
        if ipv4_list:
            ipv4_text = "\n".join(f"`{e['ip']}`" for e in ipv4_list)
            embed.add_field(name="IPv4", value=ipv4_text, inline=False)
        if ipv6_list:
            ipv6_text = "\n".join(f"`{e['ip']}`" for e in ipv6_list)
            embed.add_field(name="IPv6", value=ipv6_text, inline=False)
        if not ipv4_list and not ipv6_list:
            embed.description = "Keine IP-Adressen gefunden."
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(f"❌ Fehler beim Abrufen der IP-Adressen: {data}")


@bot.slash_command(name="info", description="Zeigt allgemeine Informationen zum Server", guild_ids=[guild_id])
async def info(interaction: nextcord.Interaction):
    if not is_allowed(interaction):
        return await interaction.response.send_message(NO_PERMISSION, ephemeral=True)
    await interaction.response.defer()
    ok, data = await api_get("")
    if ok:
        product = data.get("product", {})
        service = data.get("service", {})
        embed = nextcord.Embed(title="Server Info", color=nextcord.Color.blue())
        embed.add_field(name="Hostname", value=product.get("hostname", "–"), inline=True)
        embed.add_field(name="OS", value=product.get("os", "–"), inline=True)
        embed.add_field(name="Status", value=product.get("status", "–"), inline=True)
        embed.add_field(name="CPU Kerne", value=str(product.get("cores", "–")), inline=True)
        embed.add_field(name="RAM", value=str(product.get("memory", "–")), inline=True)
        embed.add_field(name="Disk", value=str(product.get("disk", "–")), inline=True)
        embed.add_field(name="Erstellt am", value=service.get("created_on", "–"), inline=True)
        embed.add_field(name="Läuft bis", value=service.get("expire_at", "–"), inline=True)
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(f"❌ Fehler beim Abrufen der Server-Informationen: {data}")


# --- Ping ---

@bot.slash_command(name="ping", description="Zeigt die Latenz des Bots", guild_ids=[guild_id])
async def ping(interaction: nextcord.Interaction):
    latency = round(bot.latency * 1000)
    embed = nextcord.Embed(
        title="Bot Ping",
        description=f"Die aktuelle Latenz des Bots beträgt: {latency}ms",
        color=nextcord.Color.blue()
    )
    embed.add_field(name="API Latenz:", value=f"{latency}ms", inline=True)
    current_date = nextcord.utils.utcnow().strftime('%d.%m.%Y')
    embed.set_footer(text=f"Aktuelles Datum: {current_date}")
    await interaction.response.send_message(embed=embed)


# --- DDoS ---

@bot.slash_command(name="ddos", description="Zeigt Informationen über DDoS-Angriffe", guild_ids=[guild_id])
async def ddos(interaction: nextcord.Interaction):
    if not is_allowed(interaction):
        return await interaction.response.send_message(NO_PERMISSION, ephemeral=True)
    await interaction.response.defer()
    ok, data = await api_get("incidents")
    if ok:
        incidents = data.get("data", [])
        if incidents:
            sorted_incidents = sorted(incidents, key=lambda x: float(x.get('mbps', 0) or 0), reverse=True)
            biggest = sorted_incidents[0]
            latest = incidents[-1]
            weakest = sorted_incidents[-1]
            embed = nextcord.Embed(title="DDoS-Angriffe", color=nextcord.Color.blue())
            embed.add_field(
                name="Größter Angriff",
                value=f"IP: {biggest['ip']}\nMBps: {biggest['mbps']}\nPPS: {biggest['pps']}\nMethode: {biggest['method']}",
                inline=False
            )
            embed.add_field(
                name="Letzter Angriff",
                value=f"IP: {latest['ip']}\nMBps: {latest['mbps']}\nPPS: {latest['pps']}\nMethode: {latest['method']}",
                inline=False
            )
            embed.add_field(
                name="Kleinster Angriff",
                value=f"IP: {weakest['ip']}\nMBps: {weakest['mbps']}\nPPS: {weakest['pps']}\nMethode: {weakest['method']}",
                inline=False
            )
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(embed=nextcord.Embed(
                title="DDoS-Angriffe",
                description="Aktuell liegen keine DDoS-Angriffsdaten vor.",
                color=nextcord.Color.blue()
            ))
    else:
        await interaction.followup.send("❌ Fehler beim Abrufen der DDoS-Daten. Bitte versuche es später erneut.")


# --- Backups ---

@bot.slash_command(name="list_backups", description="Zeigt eine Liste der Backups", guild_ids=[guild_id])
async def list_backups(interaction: nextcord.Interaction):
    if not is_allowed(interaction):
        return await interaction.response.send_message(NO_PERMISSION, ephemeral=True)
    await interaction.response.defer()
    ok, data = await api_get("backup")
    if ok:
        if data:
            embed = nextcord.Embed(title="Backup Liste", description="Liste der verfügbaren Backups", color=nextcord.Color.blue())
            for backup in data:
                name = backup.get("displayname", "Unbekannt")
                created = backup.get("created_on", "Unbekannt")
                embed.add_field(name=name, value=f"Erstellt am: {created}", inline=False)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("Keine Backups gefunden.")
    else:
        await interaction.followup.send("❌ Fehler beim Abrufen der Backup-Liste. Bitte versuche es später erneut.")


# --- Status-Rotation ---

@tasks.loop(seconds=10)
async def change_status():
    current_status = next(bot.status_cycle)
    await bot.change_presence(activity=nextcord.Game(name=current_status))


@bot.event
async def on_ready():
    print(f'Bot ist eingeloggt als {bot.user.name}')
    bot.status_cycle = itertools.cycle(statuses)
    change_status.start()


bot.run(discord_token)
