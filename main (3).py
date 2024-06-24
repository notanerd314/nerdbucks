import discord # type: ignore
from discord.ext import commands, tasks # type: ignore
from discord.ui import Modal, InputText, View, Button # type: ignore
from functools import partial
import requests # type: ignore
import sympy as sp # type: ignore
import textwrap, traceback, io, contextlib
from loguru import logger as log # type: ignore
import random, json, os, datetime, html, asyncio, sys, textwrap
import sqlite3

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
nerdbot = commands.Bot(command_prefix='dev!', intents=intents)

guild = nerdbot.get_guild(1037164227430989874)

# sqls
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# JSON stuff idk just some stuff
    
path_1 = os.path.abspath('assets/swearwords.json')
with open(path_1, 'r') as swearfile:
    swear_words = json.load(swearfile)
    swear_words = swear_words["words"]

path_2 = os.path.abspath('assets/8ball.json')
with open(path_2, 'r') as eightballfile:
    _8ball = json.load(eightballfile)


# log me up

log.remove()
log.add(sys.stdout, format="[{time:YYYY-MM-DD HH:mm:ss}] <level>{level}</level> {message}", colorize=True)

# defines

def savedb():
    conn.commit()
        
def user_add(user, amount):
    the_guild = nerdbot.get_guild(1037164227430989874)
    member = the_guild.get_member(user)
    role = discord.utils.get(the_guild.roles, id=1248312715823419434)
    
    if role in member.roles:
        amount = int(round(amount * 1.25))
        log.debug("Added a user that has the Certified Nerd role.")
    
    current_balance = user_get(user)
    new_balance = current_balance + amount
    
    cursor.execute('''
    update users set balance = ? where user_id = ?
    ''', (new_balance, str(user)))
    savedb()
    
def user_vanilla_add(user, amount):
    current_balance = user_get(user)
    new_balance = current_balance + amount
    
    cursor.execute('''
    UPDATE users SET balance = ? WHERE user_id = ?
    ''', (new_balance, str(user)))
    savedb()
    
def user_subtract(user, amount):
    current_balance = user_get(user)
    new_balance = current_balance - amount
    
    cursor.execute('''
    UPDATE users SET balance = ? WHERE user_id = ?
    ''', (new_balance, str(user)))
    savedb()
    
def user_reset(user):
    cursor.execute('''
    UPDATE users SET balance = 0 WHERE user_id = ?
    ''', (str(user),))
    savedb()
    
def user_get(user) -> int:
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (str(user),))
    result = cursor.fetchone()
    return result[0] if result else 0

def UserExisted(user: int) -> bool:
    cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (str(user),))
    return cursor.fetchone() is not None
    
def user_create(user):
    cursor.execute('''
    INSERT INTO users (user_id, balance)
    VALUES (?, 0)
    ''', (str(user),))
    savedb()
    log.info(f'Added "{user}" to database.')
    
def evaluate(e):
    parsed = sp.sympify(e)
    result = parsed.evalf()
    return result

# SETUP
@nerdbot.event
async def on_ready():
    log.success(f"Successfully logged in as {nerdbot.user}. ID: {nerdbot.user.id}.")
    sp.init_printing(use_unicode=True, wrap_line=False, use_latex=False, num_columns=80, order='none')
    giveaway.start()
    
@nerdbot.event
async def on_member_remove(member):
    user_id = str(member.id)
    cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    savedb()
    log.info(f'Deleted data for user {member.id} from the database.')

@nerdbot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandError):
        await ctx.send(f"An error occurred, here's the error:\n```{error.__class__.__name__}: {str(error)}```")
        
@nerdbot.event
async def on_rate_limit(route, retry_after):
     log.warning(f"You have hit the rate limit. Route: {route}, Retry After: {retry_after:.2f} seconds")

def check_role(user):
    the_guild = nerdbot.get_guild(1037164227430989874)
    member = the_guild.get_member(user)

    nerd_dev = discord.utils.get(the_guild.roles, id=1247196712460746762)
    huge_nerd = discord.utils.get(the_guild.roles, id=1248547018503229460)
    server_booster = discord.utils.get(the_guild.roles, id=1039279471246717001)
    rich_nerd = discord.utils.get(the_guild.roles, id=1248310978760675540)
    cool_nerd = discord.utils.get(the_guild.roles, id=1248294822633279589)
    certifed_nerd = discord.utils.get(the_guild.roles, id=1248312715823419434)

    if nerd_dev in member.roles:
        return [discord.Colour.blurple(), "NerdBucks Developer"]
    elif huge_nerd in member.roles:
        return [discord.Colour.purple(), "HUGE NERD"]
    elif server_booster in member.roles:
        return [discord.Colour.nitro_pink(), "Server Booster"]
    elif rich_nerd in member.roles:
        return [discord.Colour.brand_green(), "Rich Nerd"]
    elif cool_nerd in member.roles:
        return [discord.Colour.dark_gold(), "Cool Nerd"]
    elif certifed_nerd in member.roles:
        return [discord.Colour.yellow(), "Certifed Nerd"]
    else:
        return [discord.Colour.gold(), ""]


@nerdbot.slash_command(name="balance", description="View your balance and see how many NerdBucks you have.")
async def balance(ctx, user: discord.Member = None):
    await ctx.defer()
    if user is None:
        user = ctx.author
        
    if not UserExisted(user.id):
        balance = 0
    else:
        balance = user_get(user.id)

    user_profile = check_role(user.id)
    cursor.execute('SELECT color FROM profile_colors WHERE user_id = ?', (str(user.id),))
    result = cursor.fetchone()

    if result:
        user_profile[0] = int(f"0x{result[0]}", 16)

    embed = discord.Embed(title=f"{user.display_name} Balance", description=f"**Coins: {balance}** <:nerdcoin:1246832073952464927>\n{user_profile[1]}", colour=user_profile[0])
    try:
        embed.set_thumbnail(url=user.display_avatar.url)
    except Exception:
        embed.set_thumbnail(url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fi.redd.it%2Fs9biyhs4lix61.jpg&f=1&nofb=1&ipt=d0b0159760c49cba7db452315748d78bef1ef9a1250b827b42a54a9a19a13530&ipo=images")

    await ctx.followup.send(embed=embed)
    log.info(f"{ctx.author.id} has checked their balance and got {balance}")

@nerdbot.slash_command(name="leaderboard", description="Make a leaderboard")
@commands.cooldown(1, 40, commands.BucketType.user)
async def leaderboard(ctx):
    await ctx.defer()
    cursor.execute('SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 15')
    leaderboard = cursor.fetchall()

    description = "Top **15** users:"

    for i, (user_id, balance) in enumerate(leaderboard, start=1):
        user = ctx.guild.get_member(int(user_id))
        description = f"{description}\n{i}. **{user.display_name}** -- {balance} <:nerdcoin:1246832073952464927>"

    embed = discord.Embed(title="NerdBucks Leaderboard", description=description, colour=discord.Colour.gold())
    await ctx.followup.send(embed=embed)
    log.info(f"{ctx.author.id} has requested the leaderboard.")

@leaderboard.error
async def nah_no_leaderboard(ctx,error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.")

@nerdbot.slash_command(name="nerd", description="🤓🤓🤓🤓🤓🤓🤓🤓🤓🤓🤓🤓🤓🤓🤓🤓🤓🤓🤓🤓🤓")
async def nerd(ctx):
    links = ["https://www.youtube.com/watch?v=Y0kdo9QWpKU&pp=ygUEbmVyZA%3D%3D","https://www.youtube.com/shorts/q_xJP_dwm-k", "https://www.youtube.com/shorts/PmnPIExL8TE", "https://www.youtube.com/watch?v=xzy_0m7jwRw&pp=ygUKbmVyZCBlbW9qaQ%3D%3D", "https://www.youtube.com/watch?v=kts-eOoePx8"]
    await ctx.respond(f"[Here's a random video about nerds]({random.choice(links)})")
    log.info(f"{ctx.author} requested a nerd video.")

@nerdbot.slash_command(name="work", description="Work for money, don't work too hard though.")
@commands.cooldown(1, 600, commands.BucketType.user)
async def work(ctx):
    await ctx.defer()
    money = random.randint(500, 900)
    
    if not UserExisted(ctx.author.id):
        user_create(ctx.author.id)
    
    user_add(ctx.author.id, money)
    
    await ctx.followup.send(f"You worked at the NerdComplex™ and got **{money}** <:nerdcoin:1246832073952464927>")
    log.info(f"{ctx.author.id} has worked.")
    
@work.error
async def cooldown_handler(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.defer()
        await ctx.followup.send(f'Working too hard is bad! Try again in **{int(error.retry_after // 60)} minutes and {int(error.retry_after % 60)} seconds**.')
        
@nerdbot.slash_command(name="beg", description="Beg like a brokie!")
@commands.cooldown(1, 20, commands.BucketType.user)
async def beg(ctx):
    await ctx.defer()
    if random.randint(1,5) == 3:
        embed = discord.Embed(title="I would not share the likes of you.", colour=discord.Colour.brand_red())
        await ctx.followup.send(embed=embed)
        log.info(f"{ctx.author.id} has begged unsuccessfully.")
    else:
        money = random.randint(1,100)
        responses = [f"You found {money} <:nerdcoin:1246832073952464927> on the ground, not bad!", f"A kind stranger gave you {money} <:nerdcoin:1246832073952464927>. Remember to say thank you okay?"]
        
        if not random.randint(1,13) == 6:
            embed = discord.Embed(title=random.choice(responses), colour=discord.Colour.brand_green())
        else:
            money = random.randint(1000,2000)
            embed = discord.Embed(title=f"MrBeast suddenly appears and gave you {money} <:nerdcoin:1246832073952464927>, OMG!", colour=discord.Colour.gold())
            
        if not UserExisted(ctx.author.id):
            user_create(ctx.author.id)
        
        user_add(ctx.author.id, money)
        await ctx.followup.send(embed=embed)
        log.info(f"{ctx.author.id} has begged successfully and got {money}.")
        
@beg.error
async def cooldown_handler2(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.defer()
        await ctx.followup.send(f'Stop begging, brokie. Try again in **{int(error.retry_after % 60)} seconds**.')
        
@nerdbot.slash_command(name="daily", description="Claim your daily prize!")
@commands.cooldown(1, 86400, commands.BucketType.user)
async def daily(ctx):
    await ctx.defer()
    dailyprize = random.randint(1300,3000)
    
    if not UserExisted(ctx.author.id):
        user_create(ctx.author.id)
    
    user_add(ctx.author.id, dailyprize)
    
    embed = discord.Embed(title="You've claimed your daily prize!", description=f"**You get:**\n{dailyprize} <:nerdcoin:1246832073952464927>", colour=discord.Colour.gold())
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1248546047085776906/1248640506175553676/image.png?ex=66646697&is=66631517&hm=35f5e3df7cdfc0b74e78d339e129fc420d844ef6cf7796b2b6f1f92c95617f45&")
    await ctx.followup.send(embed=embed)
    log.info(f"{ctx.author.id} has claimed their daily prize.")
    
@daily.error
async def no_daily_lol(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.defer()
        await ctx.followup.send(f"No need to rush. Claim again in **{int(error.retry_after // 3600)} hours, {int(error.retry_after // 60 % 60)} minutes and {int(error.retry_after % 60)} seconds**.")

@nerdbot.slash_command(name="rob", description="Rob an user.")
@commands.cooldown(1, 1200, commands.BucketType.user)
async def rob(ctx, user: discord.Member):
    await ctx.defer()
    victim = user_get(user.id)

    money_get = random.randint(victim // 100 * 8, victim // 100 * 29)
    
    if not UserExisted(ctx.author.id):
        user_create(ctx.author.id)
    
    if victim < 1000:
        embed = discord.Embed(title="Not worth it", description=f"**{user}** is too poor. So why risk your life stealing less than **40** <:nerdcoin:1246832073952464927>?", colour=discord.Colour.dark_red())
        await ctx.followup.send(embed=embed)
        return
	
    a_guild = nerdbot.get_guild(1037164227430989874)
    member = a_guild.get_member(user.id)
    role = discord.utils.get(a_guild.roles, id=1248310978760675540)
    if not role in member.roles:
        chance = 6
        log.debug(f"{ctx.author.id} tried to robbed an user with no Rich Nerd.")
    else:
        chance = 3
        log.debug(f"{ctx.author.id} tried to robbed an user with Rich Nerd.")
        
    chances = random.randint(1,chance)
    
    if chances == 2:
        pay = victim // 100 * 25
        if pay > user_get(ctx.author.id):
            embed = discord.Embed(title="Oopsies...", description=f"**{user}** caught you and you have to give all of your money. Bummer.", colour=discord.Colour.brand_red())
            user_reset(ctx.author.id)
            user_vanilla_add(user.id, pay)
        else:            
            embed = discord.Embed(title="Oopsies...", description=f"**{user}** caught you and you have to give **{pay}** <:nerdcoin:1246832073952464927>. Darn it!", colour=discord.Colour.brand_red())
            user_subtract(ctx.author.id, pay)
            user_vanilla_add(user.id, pay)
        log.info(f"{ctx.author.id} got caught while robbing.")
    else:
        embed = discord.Embed(title="Let's go!", description=f"You succesfully sneaked in and stole **{money_get}** <:nerdcoin:1246832073952464927>!", colour=discord.Colour.gold())
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1248546047085776906/1248546047626580009/image.png?ex=66640e9e&is=6662bd1e&hm=7e4c83f698a03e234c8737f22775c5335d5e3baaffc6199a284b215308cdb54d&=&format=webp&quality=lossless&width=420&height=165")
        user_vanilla_add(ctx.author.id, money_get)
        user_subtract(user.id, money_get)
        
        huge_nerd = discord.utils.get(a_guild.roles, id=1248547018503229460)
        if huge_nerd in member.roles:
            try:
                embed1 = discord.Embed(title="ALERT!", description=f"**{ctx.author.display_name}** HAS ROBBED YOU **{money_get}** <:nerdcoin:1246832073952464927>! TAKE REVENGE!", colour=discord.Colour.brand_red())
                await user.send(embed=embed1)
            except discord.Forbidden:
                log.error(f"Failed to send {user.id} a rob notification.")
                
        log.info(f"{ctx.author.id} robbed an user.")
    
    await ctx.followup.send(embed=embed)
    
@rob.error
async def stop_robbing(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.defer()
        await ctx.followup.send(f'Stop robbing, makes me angry. Try again in **{int(error.retry_after // 60)} minutes and {int(error.retry_after % 60)} seconds**.')

@nerdbot.slash_command(name="lottery", description="Gamble to get the good stuff or be sad forever (200 nerdbucks per play)")
@commands.cooldown(1, 60, commands.BucketType.user)
async def lottery(ctx):
    await ctx.defer()
    
    if not UserExisted(ctx.author.id):
        user_create(ctx.author.id)
    
    if user_get(ctx.author.id) < 200:
        await ctx.followup.send("You don't have enough money to play!")
        return
    
    # Subtract the cost of playing the lottery
    user_subtract(ctx.author.id, 200)
    
    # Define emojis and create the slot result
    emojis = ["<:lotterynerd:1249960852228935691>", "<:7_:1249960849691377674>", "<:bar:1249960846847639642>"]
    slot = [random.choice(emojis) for _ in range(3)]
    
    # Determine the outcome and adjust user's balance accordingly
    if slot == ["<:7_:1249960849691377674>", "<:7_:1249960849691377674>", "<:7_:1249960849691377674>"]:
        money = 7777
        user_vanilla_add(ctx.author.id, money)
        title = "OMG"
        description = f"You've won the lottery and you got {money} <:nerdcoin:1246832073952464927>! Here's the result:\n# {' '.join(slot)}"
        color = discord.Colour.gold()
        thumbnail_url = "https://cdn.discordapp.com/attachments/1248546047085776906/1248546048780271666/image.png?ex=66640e9e&is=6662bd1e&hm=18120ca17ad489c558d6036294468a089e424a6e84a89bc391047c7c88aa2abd&"
    elif slot == ["<:lotterynerd:1249960852228935691>", "<:lotterynerd:1249960852228935691>", "<:lotterynerd:1249960852228935691>"]:
        money = random.randint(3000, 5500)
        user_add(ctx.author.id, money)
        title = "OMG"
        description = f"You've won the lottery and you got {money} <:nerdcoin:1246832073952464927>! Here's the result:\n# {' '.join(slot)}"
        color = discord.Colour.gold()
        thumbnail_url = "https://cdn.discordapp.com/attachments/1248546047085776906/1248546048780271666/image.png?ex=66640e9e&is=6662bd1e&hm=18120ca17ad489c558d6036294468a089e424a6e84a89bc391047c7c88aa2abd&"
    elif slot == ["<:bar:1249960846847639642>", "<:bar:1249960846847639642>", "<:bar:1249960846847639642>"]:
        money = random.randint(1000, 2500)
        user_add(ctx.author.id, money)
        title = "OMG"
        description = f"You've won the lottery and you got {money} <:nerdcoin:1246832073952464927>! Here's the result:\n# {' '.join(slot)}"
        color = discord.Colour.gold()
        thumbnail_url = "https://cdn.discordapp.com/attachments/1248546047085776906/1248546048780271666/image.png?ex=66640e9e&is=6662bd1e&hm=18120ca17ad489c558d6036294468a089e424a6e84a89bc391047c7c88aa2abd&"
    else:
        title = "Aww man..."
        description = f"You lost the lottery lol. Here's the result:\n# {' '.join(slot)}"
        color = discord.Colour.brand_red()
        thumbnail_url = "https://cdn.discordapp.com/attachments/1248546047085776906/1248640505881821296/image.png?ex=66646697&is=66631517&hm=3aa000b7f152490f592057553b5b2575c247b759640b9ec1707eff92340c641f&"
    
    embed = discord.Embed(title=title, description=description, colour=color)
    embed.set_thumbnail(url=thumbnail_url)
    
    await ctx.followup.send(embed=embed)
    log.debug(f"{ctx.author.id} lottery result: {' '.join(slot)}")


@lottery.error
async def stop_gambling(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.defer()
        await ctx.followup.send(f'Slow down the gambling addiction. Try again in **{int(error.retry_after // 60)} minutes and {int(error.retry_after % 60)} seconds**.')
        
@nerdbot.slash_command(name="roulette", description="Play a game of roulette.")
@commands.cooldown(1, 60, commands.BucketType.user)
async def roulette(ctx, bet: int):
    if not UserExisted(ctx.author.id):
        await ctx.respond("You don't have any money to bet!")
        return
    
    if bet < 100:
        await ctx.respond("The bet amount should be at least 100 <:nerdcoin:1246832073952464927>.")
        return
    
    if bet > 7500:
        await ctx.respond("TOO MUCH MONEY TO BET DUDE!")
        return
    
    if bet > user_get(ctx.author.id):
        await ctx.respond("You don't have enough money to bet!")
        return
    
    await ctx.defer()
    roulette = ["win", "lose", "jackpot"]
    answer = random.choices(roulette, weights=[30, 69, 1], k=1)[0]
    
    if answer == "win":
        money = int(round(bet*1.5))
        user_vanilla_add(ctx.author.id, bet*1.5)
        await ctx.followup.send(f"You've won the roulette 🎉! You get **{round(money)}** <:nerdcoin:1246832073952464927> from the roulette.")
    elif answer == "lose":
        user_subtract(ctx.author.id, bet)
        await ctx.followup.send(f"Sorry, you've lost the roulette.. You lost **{bet}** <:nerdcoin:1246832073952464927> from the roulette.")
    elif answer == "jackpot":
        money = bet*5
        user_vanilla_add(ctx.author.id, bet*5)
        await ctx.followup.send(f"JACKPOT 🎉! You get **{money}** <:nerdcoin:1246832073952464927> from the roulette! OMG.")
        
    log.info(f"{ctx.author.id} {answer} from the roulette.")
    
@roulette.error
async def no_roulette(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.defer()
        await ctx.followup.send(f'Spin it later bro. Try again in **{int(error.retry_after // 60)} minutes and {int(error.retry_after % 60)} seconds**.')
        
@nerdbot.slash_command(name="transfer", description="Transfer NerdBucks to another user.")
@commands.cooldown(1, 45, commands.BucketType.user)
async def transfer(ctx, user: discord.Member, amount: int, reason: str = None):
    if user == ctx.author:
        await ctx.respond("You can't transfer money to yourself.")
        return
    
    if amount < 1:
        await ctx.respond("Invalid amount, please specify a **positive amount**.")
        return

    if amount > int(user_get(ctx.author.id)):
        await ctx.respond("Invalid amount, THAT'S TOO MUCH MONEY!")
        return
    
    if reason is None:
        reason = "No reason"
    
    if len(reason) > 300:
        await ctx.respond("Reason too long, keep it short, man.")
        return

    if not UserExisted(user.id):
        await ctx.respond("An error occured, maybe transfer another user?")
        return
    
    if any(element in reason for element in swear_words):
        await ctx.respond("DON'T SWEAR IN REASONS DUDE!")
        return
    
    user_vanilla_add(user.id, amount)
    user_subtract(ctx.author.id, amount)

    try:
        embed = discord.Embed(title="Notification", description=f"**{ctx.author}** transfered you **{amount}** nerdcoins. Reason:\n ```{reason}```", colour=discord.Colour.blurple())
        await user.send(embed=embed)
    except discord.Forbidden:
        log.error(f"Failed to send {user.id} a transfer notification.")
	
    await ctx.defer()
    
    embed1 = discord.Embed(title="Success", description=f"Transferred {user} **{amount}** <:nerdcoin:1246832073952464927> for reason:\n```{reason}```", colour=discord.Colour.gold())
    embed1.set_thumbnail(url="https://cdn.discordapp.com/attachments/1248546047085776906/1248546048222302209/image.png?ex=66640e9e&is=6662bd1e&hm=120fd9b32d579a602a001727f060fdc60cd6e2b99809c2c4bdfe0c4d14dde410&")
    
    await ctx.followup.send(embed=embed1)
    log.info(f"User {ctx.author.id} transferred {amount} nerdcoins to {user.id} for reason: {reason}")


@transfer.error
async def generous_to_my_database(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.defer()
        await ctx.followup.send(f'I know you have a generous heart, but can you please be generous to my database? Try again in **{int(error.retry_after // 60)} minutes and {int(error.retry_after % 60)} seconds**.')

# TRIVIA

def get_trivia():
    response = requests.get(f"https://opentdb.com/api.php?amount=1&type=multiple")
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            return data['results'][0]
    return ["error is 21391239021jnfdjcwojfsdsd",response.status_code]

class Trivia(View):
    def __init__(self, correct_answer, command_user_id, answers, embed):
        super().__init__(timeout=15)
        self.correct_answer = correct_answer
        self.command_user_id = command_user_id
        self.answers = answers
        self.result = None
        self.embed = embed
        self.create_buttons()
        
    async def stopbutton(self, interaction):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)
        
    async def handle_button_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.command_user_id:
            if button.label == self.correct_answer:
                embed1 = discord.Embed(description=f"Correct answer! You get **450** nerdcoins as a return.\n## <a:you_nerd:1040186746488504340>")
                if not UserExisted(self.command_user_id):
                    user_create(self.command_user_id)
                
                user_add(self.command_user_id, 450)
                await interaction.response.edit_message(embeds=[self.embed, embed1])
            else:
                embed1 = discord.Embed(description=f"The correct answer is actually **{self.correct_answer}**. :sob:")
                await interaction.response.edit_message(embeds=[self.embed, embed1])
            self.result = True
            await self.stopbutton(interaction)
        else:
            await interaction.response.send_message("This command was sent from another user, so you cannot play.", ephemeral=True)
            
    def create_buttons(self):
        for answer in self.answers:
            button = discord.ui.Button(label=answer, style=discord.ButtonStyle.blurple)
            button.callback = lambda interaction, button=button: self.handle_button_click(interaction, button)
            self.add_item(button)

@nerdbot.slash_command(name="trivia", description="Answer a trivia question to get 450 nerdcoins")
@commands.cooldown(1, 30, commands.BucketType.user)
async def trivia(ctx):
    await ctx.defer()
    jsontrivia = get_trivia()
    if "error is 21391239021jnfdjcwojfsdsd" in jsontrivia:
        log.error(f"Failed to fetch trivia question. Response code: {jsontrivia[1]}")
        await ctx.followup.send("Failed to fetch trivia question. Please try again.", ephemeral=True)
        return
    
    questiontype = jsontrivia['type']
    question = html.unescape(jsontrivia['question'])
    correct_answer = html.unescape(jsontrivia['correct_answer'])
    difficulty = jsontrivia['difficulty']
    category = html.unescape(jsontrivia['category'])
    
    if difficulty == "easy":
        colour = discord.Colour.brand_green()
    elif difficulty == "medium":
        colour = discord.Colour.gold()
    elif difficulty == "hard":
        colour = discord.Colour.brand_red()
    
    embed = discord.Embed(title="Trivia", description=f"You have **15** seconds to answer before the buttons not working...\n## {question}\nDifficulty: {difficulty}\nCategory: {category}", colour=colour)
    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1248546047085776906/1248546049082003537/image.png?ex=66640e9e&is=6662bd1e&hm=1e6f4dc7e739c2aa97c60d2ea09a333ad56e5297b28b9cf0c26e25f4f241c6c0&=&format=webp&quality=lossless&width=297&height=155")
    
    incorrect_answers = jsontrivia['incorrect_answers']
    for x in range(3):
        incorrect_answers[x] = html.unescape(incorrect_answers[x])

    answers = incorrect_answers + [correct_answer]
    random.shuffle(answers)

    view = Trivia(correct_answer, ctx.author.id, answers, embed)
    log.info(f"{ctx.author.id} has created a trivia question.")
    await ctx.followup.send(embed=embed, view=view)

@trivia.error
async def no_trivia(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.defer()
        await ctx.followup.send(f'Gameshow ended. Try again in **{int(error.retry_after // 60)} minutes and {int(error.retry_after % 60)} seconds**.')
        
@nerdbot.slash_command(name="ping", description="tried of writing descriptions... understand it yourself")
async def ping(ctx):
    await ctx.defer()
    log.info(f"Bot ping is {round(nerdbot.latency * 1000)}ms.")
    await ctx.followup.send(f"Pong! Bot latency is **{round(nerdbot.latency * 1000)}ms**")
    
@nerdbot.slash_command(name="calculate", description="Calculate an expression, 50 nerdbucks per calculation.")
@commands.cooldown(1, 10, commands.BucketType.user)
async def calculate(ctx, *, expression: str):
    await ctx.defer()
    try:
        result = float(evaluate(expression))
        result = str(result)
        if '69' in result:
            result = f"{result}, *nice.*"
    except Exception as e:
        result = f"Invalid expression.\nError: ```{e}```"

    embed = discord.Embed(title="Calculator",
                      description=f"The result of the expression `{expression}` is:\n# {result}",
                      colour=discord.Colour.gold(),
                        )
    embed.set_footer(text="stop cheating in math")
    log.info(f"{ctx.author.id} has used the calculator and typed: {expression}.")
    await ctx.followup.send(embed=embed)
    
@calculate.error
async def do_not_cheat_in_math(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.defer()
        await ctx.followup.send(f'Bro thinks he can cheat in math :skull:. Try again in **{int(error.retry_after % 60)} seconds**.')
    
class PrizeButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.claimed = False

    @discord.ui.button(emoji="<:nerdcoin:1246832073952464927>", label="Claim nerdbucks!", style=discord.ButtonStyle.primary)
    async def claim_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self.claimed:
            user_id_str = str(interaction.user.id)
            self.claimed = True
            
            if not UserExisted(user_id_str):
                user_create(user_id_str)
            
            money = random.randint(700,1500)
            user_add(int(user_id_str), money)
            embed = discord.Embed(title="Winner", description=f"**{interaction.user.mention}** has opened the lootbox and gets **{money}** <:nerdcoin:1246832073952464927>!", colour=discord.Colour.gold())
            await interaction.response.edit_message(embed=embed, view=None)


class PrizeButtonEmoji(discord.ui.View):
    def __init__(self, emojis):
        super().__init__(timeout=None)
        self.claimed = False
        self.emojis = emojis
        self.create_buttons()

    async def handle_button_click(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not self.claimed:
            if button.label == "🎁":
                user_id_str = str(interaction.user.id)
                self.claimed = True
                    
                if not UserExisted(user_id_str):
                    user_create(user_id_str)
                    
                money = random.randint(700,1500)
                user_add(int(user_id_str), money)
                embed = discord.Embed(title="Winner", description=f"**{interaction.user.mention}** has opened the lootbox and gets **{money}** <:nerdcoin:1246832073952464927>!", colour=discord.Colour.gold())
                await interaction.response.edit_message(embed=embed, view=None)
            else:
                await interaction.response.send_message("That's not the right emoji!", ephemeral=True)

    def create_buttons(self):
        for emoji in self.emojis:
            button = discord.ui.Button(label=emoji, style=discord.ButtonStyle.secondary)
            button.callback = partial(self.handle_button_click, button)
            self.add_item(button)

# shopping for life
class Dropdown(discord.ui.Select):
    def __init__(self, user):
        options = [
            discord.SelectOption(label='Certified Nerd', description='Gets a cool role and a 1.25x multiplier', emoji='🤓', value="5"),
            discord.SelectOption(label='Cool Nerd', description='Unlocks a secret channel to talk with other cool nerds', emoji='<:cool_nerd:1037333814906736660>', value="10"),
            discord.SelectOption(label='Rich Nerd', description='Robbers gets a higher chance of getting caught while robbing you', emoji='<:money_mouth_nerd:1130194487013032036>', value="50"),
            discord.SelectOption(label='HUGE NERD', description='Change profile color, image perms omg and a notification when someone robs you.', emoji='<:chad_nerd:1067155906334310551>', value="100")
        ]

        super().__init__(placeholder='Choose your item you want to buy...', min_values=1, max_values=1, options=options)
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This dropdown is not for you! Make a new shop command lol.", ephemeral=True)
            return

        selected_option = self.values[0]
        if selected_option == "5":
            role_name = 1248312715823419434
        elif selected_option == "10":
            role_name = 1248294822633279589
        elif selected_option == "50":
            role_name = 1248310978760675540
        elif selected_option == "100":
            role_name = 1248547018503229460

        if user_get(self.user.id) >= int(selected_option) * 10000:
            pass
        else:
            await interaction.response.send_message(f"You don't have enough money to buy that role!", ephemeral=True)
            return
        
        role = discord.utils.get(interaction.guild.roles, id=role_name)
        try:
            await self.user.add_roles(role)
        except Exception as e:
            log.error("An error has occurred.")
            await interaction.response.send_message(f"An error occurred\n```{e}```")
            raise e

        user_subtract(self.user.id, int(selected_option) * 10000)
        log.info(f"{self.user.id} shopped an item.")
        await interaction.response.send_message("You shopped an item successfully!")

class DropdownView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=250)
        self.user_id = user_id
        self.add_item(Dropdown(self.user_id))

@nerdbot.slash_command(name="shop", description="Buy roles or stuff idk")
@commands.cooldown(1,300,commands.BucketType.user)
async def shop(ctx):
    if not UserExisted(ctx.author.id):
        await ctx.respond(f"You don't have enough money to shop!", ephemeral=True)
        return

    await ctx.defer()
    embed = discord.Embed(title="NerdShop",
                      description="Choose an item to buy!",
                      colour=0xf5b400)

    embed.add_field(name="Certified Nerd",
                    value="**Price:** 50000 <:nerdcoin:1246832073952464927>\n**Description:** Gets a cool role and a 1.25x multiplier",
                    inline=False)
    embed.add_field(name="Cool Nerd",
                    value="**Price:** 100000 <:nerdcoin:1246832073952464927>\n**Description:** Unlocks a secret channel to talk with other cool nerds",
                    inline=False)
    embed.add_field(name="Rich Nerd",
                    value="**Price:** 500000 <:nerdcoin:1246832073952464927>\n**Description:** Robbers gets a higher chance of getting caught while robbing you",
                    inline=False)
    embed.add_field(name="HUGE NERD",
                    value="**Price:** 1000000 <:nerdcoin:1246832073952464927>\n**Description:** Change profile color, image perms omg and a notification when someone robs you.",
                    inline=False)

    await ctx.followup.send(embed=embed, view=DropdownView(ctx.author))

@shop.error
async def badass(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.defer()
        await ctx.followup.send(f'Shop later bro. Try again in **{int(error.retry_after // 60)} minutes {int(error.retry_after % 60)} seconds**.')

@nerdbot.slash_command(name="crime", description="Do a crime")
@commands.cooldown(1, 900, commands.BucketType.user)
async def crime(ctx):
    await ctx.defer()
    crime_rate = random.randint(1,3) # rate "3" is crime fail in 1 and "4" for in 2
    if crime_rate == 1:
        responses = [
            "You robbed a person's wallet and got ", 
            "You took an item from a person then sold it and got ", 
            "You touched grass as a Discord Mod (it's a crime) and got ", 
            "You said truthfully that you're not a nerd and got ",
            "You pickpocked a person and got ",
            "You sold food that the teacher won't allow and got ",
            "You cut a tree illegally and got ",
            "You took the money from a poor person and got "
                     ]
        money = random.randint(800,4866)
        embed = discord.Embed(title=f"{random.choice(responses)}{money} <:nerdcoin:1246832073952464927>", description="I am not proud of you at all.")
        user_add(ctx.author.id, money)
        await ctx.followup.send(embed=embed)
    elif crime_rate == 2:
        responses = [
            "You robbed a bank and got ", 
            "You stole a car and got ", 
            "You sold illegal items in the dark web and got ", 
            "You hacked into a goverment's code and got ",
            "You hacked my discord bot's database and got ",
            "You `[CENSORED]` and got ",
            "You burned a forest and got "
                     ]
        money = random.randint(1000,7800)
        embed = discord.Embed(title=f"{random.choice(responses)}{money} <:nerdcoin:1246832073952464927>", description="I am not proud of you at all.")
        user_add(ctx.author.id, money)
        await ctx.followup.send(embed=embed)
    elif crime_rate == 3:
        responses = [
            "You tried to hack my discord bot but I caught you and lost ",
            "You tried to stole a package outdoors but Mark Rober glitter-bombed you and you lost ",
            "You actually robbed a person but your friend robs you and you lost ",
            "You tried to uhhh... i forgot but you lost ",
            "You tried to rob a bank but got caught so you lost ",
            "You tired to take the money from a poor person but the poor person beats you up and you lost ",
            "You vandalized a public park and got charged ",
            "Someone stole your parking space so you smashed their car and got charged ",
            "You shopliftted three giant bottles of coke for your gaming night but you got caught so you lost "
        ]
        money = random.randint(1000,6500)
        embed = discord.Embed(title=f"{random.choice(responses)}{money} <:nerdcoin:1246832073952464927>", description="I am not proud of you at all.")
        user_subtract(ctx.author.id, money)
        await ctx.followup.send(embed=embed)

@crime.error
async def badass(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.defer()
        await ctx.followup.send(f'STOP BEING A BADASS DUDE. Try again in **{int(error.retry_after // 60)} minutes {int(error.retry_after % 60)} seconds**.')

@nerdbot.slash_command(name="change-color", description="Change the color of your profile in hex color format (ONLY FOR HUGE NERD)")
async def change_color(ctx, color: str):
    role = discord.utils.get(ctx.guild.roles, id=1248547018503229460)
    if not role in ctx.author.roles:
        await ctx.respond("You must get the HUGE NERD role in enable to use this command.")
        return
    
    try:
        a = int(f"0x{color}", 16)
    except Exception as e:
        await ctx.respond(f"Invalid color format. Please provide a valid hex color.")
        return


    cursor.execute("SELECT * FROM profile_colors WHERE user_id = ?", (str(ctx.author.id),))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO profile_colors (user_id, color) VALUES (?, ?)", (str(ctx.author.id), color))
    else:
        cursor.execute("UPDATE profile_colors SET color = ? WHERE user_id = ?", (color, str(ctx.author.id)))
    conn.commit()

    embed = discord.Embed(title=f"{ctx.author.display_name} Balance", description=f"**Coins: 69420** <:nerdcoin:1246832073952464927>\nHUGE NERD", colour=int(f"0x{color}", 16))
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    await ctx.respond(f"Your profile color has been changed to `#{color}`. Here's a preview of the profile:", embed=embed)

@nerdbot.slash_command(name="8ball", description="magic 8 ball will answer your yes or no questions")
async def eightball(ctx, question: str):
    response8ball = random.choice(_8ball)
    embed = discord.Embed(title="Magic Eight Ball", url="https://www.youtube.com/watch?v=mFOracFClBg")
    embed.add_field(name="Question", value=question)
    embed.add_field(name="Answer", value=f"{response8ball} :8ball:")
    await ctx.respond(embed=embed)

# devcommands            
devs = [1233989963046195282]
    
@nerdbot.command()
async def addbal(ctx, user: int, amount: int):
    """Add money to user"""
    if not ctx.author.id in devs:
        await ctx.send(f'You are not a developer bruh :skull:')
        return
    
    user_vanilla_add(user, amount)
    await ctx.send(f'Sucessfully added "{user}" **{amount}** nerdbucks.')
    
@nerdbot.command()
async def removebal(ctx, user: int, amount: int):
    """Remove money from user"""
    if not ctx.author.id in devs:
        await ctx.send(f'You are not a developer bruh :skull:')
        return
    
    user_subtract(user, amount)
    await ctx.send(f'Sucessfully removed "{user}" **{amount}** nerdbucks.')
    
@nerdbot.command(name='exec')    
async def _exec(ctx, *, body: str):
    """Execute Python code"""
    if not ctx.author.id in devs:
        await ctx.send(f'You are not a developer bruh :skull:')
        return
    
    env = {
        'bot': nerdbot,
        'ctx': ctx,
        'channel': ctx.channel,
        'author': ctx.author,
        'guild': ctx.guild,
        'message': ctx.message
    }

    env.update(globals())

    # Function to clean up code block formatting
    def cleanup_code(content):
        """Remove code blocks from the content."""
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])
        return content

    body = cleanup_code(body)
    stdout = io.StringIO()

    code = f'async def func():\n{textwrap.indent(body, "  ")}'

    try:
        exec(code, env)
    except Exception as e:
        return await ctx.send(f'Error in exec: ```\n{e.__class__.__name__}: {e}\n```')

    func = env['func']
    try:
        with contextlib.redirect_stdout(stdout):
            await func()
    except Exception as e:
        value = stdout.getvalue()
        error = f'```\n{value}{traceback.format_exc()}\n```'
        await ctx.send(error)
    else:
        value = stdout.getvalue()
        if value:
            await ctx.send(f'```\n{value}\n```')

@nerdbot.command(name="update")
async def update(ctx):
    """Update commands funny ahhhhhh"""
    if not ctx.author.id in devs:
        await ctx.send('You are not a developer bruh 💀')
        return
    
    try:
        await nerdbot.sync_commands()
        await ctx.send("Slash commands updated successfully!")
        log.success("Updated commands.")
    except Exception as e:
        await ctx.send(f"Failed to reload slash commands:\n```{e}```")
        log.error("An error has occurred:")
        raise e
        
@nerdbot.command(name="restart")
async def shutdown(ctx):
    """restart bot, bot dies oh no"""
    if not ctx.author.id in devs:
        await ctx.send(f'You are not a developer bruh :skull:')
        return
    
    log.success("Restarting bot...")
    await ctx.send("Bot restarting, will back lol")
    await nerdbot.close()
    
@nerdbot.command(name="shutdown")
async def force_shutdown(ctx):
    """NO PLEASE NO"""
    if not ctx.author.id in devs:
        await ctx.send(f'You are not a developer bruh :skull:')
        return
    
    await ctx.send("Forcing shutdown using `exit()`...")
    exit()


@tasks.loop(minutes=17)
async def giveaway():
    channel = nerdbot.get_channel(1039054002823888896)
    giveaway_type = random.randint(1, 2)
    if giveaway_type == 1:
        embed = discord.Embed(title="Nerd Lootbox!", description="Whoever gets the lootbox first wins it!", colour=discord.Colour.blurple())
        view = PrizeButton()
    elif giveaway_type == 2:
        emojis = ["🏦", "🎮", "🤓", "💸", "🎁"]
        random.shuffle(emojis)
        embed = discord.Embed(title="Nerd Lootbox!", description="Whoever clicks the lootbox icon first wins it!", colour=discord.Colour.blurple())
        view = PrizeButtonEmoji(emojis)
        
    log.info(f"A lootbox has spawned in #general. Type: {giveaway_type}")
        
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1248546047085776906/1248640506175553676/image.png?ex=66646697&is=66631517&hm=35f5e3df7cdfc0b74e78d339e129fc420d844ef6cf7796b2b6f1f92c95617f45&")

    await channel.send(embed=embed, view=view)

nerdbot.run("YOUR_BOT_TOKEN")