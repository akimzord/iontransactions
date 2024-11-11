import discord
from discord.ext import commands
from web3 import Web3
from web3.middleware import geth_poa_middleware
import requests
import asyncio
import datetime


bot_start_time = datetime.datetime.now(datetime.timezone.utc)

TOKEN = '#'
TOKEN_ADDRESS = '0x033c1C03718ba0F0871bB4DCC38b24F065D585bc'
CHANNEL_ID = '#'
API_KEY = '#'

intents = discord.Intents.all()
intents.typing = True
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)

bsc_rpc_url = 'https://bsc-dataseed.binance.org/'
w3 = Web3(Web3.HTTPProvider(bsc_rpc_url))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

async def check_new_transactions():
    await bot.wait_until_ready()
    channel = bot.get_channel(int(CHANNEL_ID))
    if not channel:
        print(f'Canal com ID {CHANNEL_ID} não encontrado.')
        return

    while not bot.is_closed():
        try:
            latest_block = w3.eth.block_number
            last_block = getattr(check_new_transactions, 'last_block', latest_block - 1)

            if latest_block > last_block:
                url = f'https://api.bscscan.com/api?module=account&action=tokentx&address={TOKEN_ADDRESS}&startblock={last_block + 1}&endblock={latest_block}&sort=desc&apikey={API_KEY}'
                response = requests.get(url)
                data = response.json()

                if data.get('status') == '1':
                    transactions = data['result']
                    for tx in transactions:
                        value = float(tx['value']) / 10**18
                        value_str = '{:.2f}'.format(value).rstrip('0').rstrip('.')

                        embed = discord.Embed(
                            title="New Deposit Detected",
                            description=f"A new deposit of {value_str} tokens has been detected in ION.",
                            color=0x00ff00  # Cor verde
                        )
                        embed.add_field(name="Transaction", value=tx["hash"], inline=False)
                        embed.add_field(name="From", value=tx["from"], inline=False)
                        embed.add_field(name="To", value=tx["to"], inline=False)

                        await channel.send(embed=embed)

                check_new_transactions.last_block = latest_block
            await asyncio.sleep(300)
        except Exception as e:
            print(f"Erro ao verificar novas transações: {str(e)}")

async def send_online_status():
    while not bot.is_closed():
        channel = bot.get_channel(int(CHANNEL_ID))
        if channel:
            # Calcula quanto tempo o bot está online
            now = datetime.datetime.now(datetime.timezone.utc)
            uptime = now - bot_start_time
            days = uptime.days
            seconds = uptime.seconds
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            await channel.send(f':mag_right: Searching for new deposits of ION Token. Please wait.\n\n'
                               f':robot: We are online at {days} days and {hours} hours.')
        await asyncio.sleep(3600)  # Aguarde 1 hora (3600 segundos)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}')
    await asyncio.gather(check_new_transactions(), send_online_status())

@bot.command()
async def about(ctx):
    await ctx.send("Developed by akimright")


bot.run(TOKEN)
