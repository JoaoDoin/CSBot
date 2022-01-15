import discord
import os
import json
import random
import asyncio
import math
import requests
from dotenv import load_dotenv
from datetime import timedelta
from discord.ext import commands, tasks
from discord_buttons_plugin import *
from lib.functions import *
from lib.handlejson import *
from lib.achievements import *
from lib.cards import *
#from lib.keep_alive import keep_alive

VERSION = "2.1.0.0"

def check_for_updates():
  data = requests.get("https://api.github.com/repos/JoaoDoin/CSBot/releases").json()[0]
  latest_version = int(data["tag_name"].replace(".", ""))
  current_version = int(VERSION.replace(".", ""))

  if latest_version > current_version:
    os.system("updater.exe")


check_for_updates()


intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix = "!", case_insensitive=True, intents=intents)
client.remove_command("help")

buttons = ButtonsClient(client)
func = Functions(client)
_json = Json()

cfg_guild = func.get_cfg("Guild")
cfg_channel = func.get_cfg("Channel")
cfg_activity = func.get_cfg("Activity")
anata = func.get_cfg("Anata")


def check_for_challenges():
  with open("cfg/achievements.json", "r") as f:
    challenges = json.load(f)

  db = sqlite3.connect("challengeprogress.db")
  c = db.cursor()

  for cid in challenges.keys():
    try:
      c.execute(f"ALTER TABLE challenges ADD COLUMN '{cid}' TEXT")
    except: 
      pass

  db.commit()
  db.close()


async def auto_register():
  guild = await client.fetch_guild(cfg_guild)
  members = guild.fetch_members(limit=None)
  async for member in members:
    try:
      Challenges(member.id).register()
    except:
      pass



@tasks.loop(minutes=1.0)
async def auto_reset():
  with open("cfg/autoreset.json", "r") as ar:
    i = json.load(ar)
  limit, running, timer = i["ResetIn"], i["Running"], i["Timer"]

  with open("cfg/team.json", "r") as t:
    j = json.load(t)
  team = j["Team"]

  if len(team) >= 1:
    running = True
  else:
    running = False

  if running:
    timer -= 1
  else:
    timer = limit

  if timer <= 0:
    timer = limit
    running = False
    func.reset_team()
    ch = client.get_channel(cfg_channel)
    await ch.send("Resetado :handshake:")

  i["Running"], i["Timer"] = running, timer
  with open("cfg/autoreset.json", "w") as ar:
    json.dump(i, ar, indent=4)



@client.event
async def on_ready():
  print('Logged in as "{}"'.format(client.user))
  await client.change_presence(activity=discord.Game(name=cfg_activity, url="https://twitch.tv/imshockwav3"))
  await auto_register()
  check_for_challenges()
  xingar_o_xhurru.start()
  auto_reset.start()



@client.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.MissingRequiredArgument):
    await ctx.send("Erro! :x: :scream:")



@client.event
async def on_message(msg):
  if msg.author == client.user: return

  if _json.read("cfg/config.json")["ReactMSG"] == True:
    reagir = _json.read("cfg/xingamentos.json")["Reagir"]

    if any(frase in msg.content.lower() for frase in reagir):
      await msg.add_reaction("🤝")

    if msg.author.id == 169619020885000193:
      await msg.add_reaction("🖕")

  await client.process_commands(msg)


@client.event
async def on_member_join(member):
  await auto_register()


# ========================================= #


@tasks.loop(minutes=30)
async def xingar_o_xhurru():
  if _json.read("cfg/config.json")["TimedMSG"] == True:
    with open('cfg/xingamentos.json', 'r') as f:
      i = json.load(f)
    x = i["Xingamentos"]
    xingamentos = [x[key] for key in x.keys()]

    ch = client.get_channel(cfg_channel)
    try:
      last_msg = await ch.fetch_message(ch.last_message_id)
    except:
      last_msg = None

    if last_msg == None or last_msg.author != client.user:
      await ch.send(embed=discord.Embed(description=random.choice(xingamentos), color=0xFFD700))


# ========================================= #


@client.command()
async def test(ctx):
  with open("cfg/5v5.json", "r") as f:
    i = json.load(f)
  Team1 = client.get_channel(835664145755406367)
  Team2 = client.get_channel(835664397560709141)
  guild = await client.fetch_guild(cfg_guild)
  members = guild.fetch_members(limit=None)

  async for member in members:
    try:
      if str(member.id) in i["Team1"]:
        await member.move_to(Team1)
      elif str(member.id) in i["Team2"]:
        await member.move_to(Team2)
    except:
      pass


@client.command(aliases=["timer", "autoreset"])
async def timer_(ctx):
  with open("cfg/autoreset.json") as f:
    i = json.load(f)
  running, maximum, timer = i["Running"], i["ResetIn"], i["Timer"]
  if running:
    status = "Ativo"
  else:
    status = "Inativo"

  mt = str(timedelta(minutes=maximum)).split(":")
  rt = str(timedelta(minutes=timer)).split(":")
  maximum_time = f"{mt[0]}h{mt[1]}"
  remaining_time = f"{rt[0]}h{rt[1]}"

  await ctx.send(f'''
**Status:** `{status}`
**Reseta em:** `{maximum_time}`
**Tempo restante:** `{remaining_time}`
  ''')


@client.command()
async def nick(ctx, member : discord.Member, *, nick):
  await ctx.message.delete()
  if func.checkIfAdmin(ctx.author.id):
    await member.edit(nick=nick)


@client.command(aliases=["ic"])
async def increasechallenge(ctx, id : int):
  user = ctx.author.id
  status = Challenges(user).increase(id)
  if status is not None:
    await ctx.send(embed=discord.Embed(description=status, color=0xFFD700).set_footer(text=ctx.message.author, icon_url=""))



# ========================================= #


@client.command(aliases=['say'])
async def send(ctx, *, text : str):
  ch = client.get_channel(cfg_channel)
  if func.checkIfAdmin(ctx.author.id):
    try:
      await ctx.message.delete()
    except:
      pass
    await ch.send(text.replace("<everyone>", "@everyone").replace("<here>", "@here"))


# ========================================= #


# SETTINGS
# Comando geral
@client.group(aliases=['settings', 'cfg'], invoke_without_command=True)
async def config(ctx):
  if not func.checkIfAdmin(ctx.author.id): return
  await ctx.send("Opções: `admins`, `timedmsg`, `reactions`, `cards`, `queue`")

# Subgrupo CARDS
@config.group(aliases=['card'], invoke_without_command=True)
async def cards(ctx):
  if not func.checkIfAdmin(ctx.author.id): return
  await ctx.send("**Adicionar:** `!cfg cards add <@alguém/random> <link_img>`\n**Remover:** `!cfg cards remove <link_img>`")

@cards.command()
async def add(ctx, t : str, value : str): # Subcomando ADD CARDS
  if not func.checkIfAdmin(ctx.author.id): return
  target = t.lower().translate({ord(i): None for i in '<@!>'})

  cards = _json.read("cfg/cards.json")
  for key in cards:
    if value in cards[key]:
      await ctx.message.delete()
      return await ctx.send("Essa carta já existe.")
  
  if target in cards:
    cards[target].append(value)
  else:
    cards[target] = [value]
  
  await ctx.send("Adicionado.", delete_after=2)

  with open("cfg/cards.json", 'w') as f:
    json.dump(cards, f, indent=4)

  await ctx.message.delete()


@cards.command(aliases=['remover'])
async def remove(ctx, value : str): # Subcomando REMOVE CARDS
  if not func.checkIfAdmin(ctx.author.id): return

  cards = _json.read("cfg/cards.json")
  for key in cards:
    if value in cards[key]:
      cards[key].remove(value)

  await ctx.send("Removido.", delete_after=2)

  with open("cfg/cards.json", 'w') as f:
    json.dump(cards, f, indent=4)
  
  await ctx.message.delete()


# Subcomando QUEUE
@config.command(aliases=['fila'])
async def queue(ctx, value=None):
  if not func.checkIfAdmin(ctx.author.id): return

  cfg = _json.read("cfg/config.json")["Queue"]
  if value is None:
    if cfg == True:
      status = "ativada"
    else:
      status = "desativada"
    await ctx.send(f"A fila está {status}, use `TRUE` ou `FALSE` para mudar.")

  elif str(value).upper() == 'TRUE':
    _json.write("cfg/config.json", "Queue", True)
    await ctx.send("Fila ativada.")

  elif str(value).upper() == 'FALSE':
    _json.write("cfg/config.json", "Queue", False)
    await ctx.send("Fila desativada.")
  
  else:
    await ctx.send("Erro! :x: :scream:")


# Subcomando TIMED MESSAGES
@config.command(aliases=['timedmsgs', 'timedmessages', 'timedmessage'])
async def timedmsg(ctx, value=None):
  if not func.checkIfAdmin(ctx.author.id): return

  cfg = _json.read("cfg/config.json")["TimedMSG"]
  if value is None:
    if cfg == True:
      status = "ativadas"
    else:
      status = "desativadas"
    await ctx.send(f"As Timed Messages estão {status}, use `TRUE` ou `FALSE` para trocar.")

  elif str(value).upper() == 'TRUE':
    _json.write("cfg/config.json", "TimedMSG", True)
    await ctx.send("Timed Messages ativadas.")

  elif str(value).upper() == 'FALSE':
    _json.write("cfg/config.json", "TimedMSG", False)
    await ctx.send("Timed Messages desativadas.")
  
  else:
    await ctx.send("Erro! :x: :scream:")


# Subcomando REACTIONS
@config.command(aliases=['reactions', 'reactmsg'])
async def reaction(ctx, value=None):
  if not func.checkIfAdmin(ctx.author.id): return

  cfg = _json.read("cfg/config.json")["ReactMSG"]
  if value is None:
    if cfg == True:
      status = "ativadas"
    else:
      status = "desativadas"
    await ctx.send(f"As reações do bot estão {status}, use `TRUE` ou `FALSE` para trocar.")

  elif str(value).upper() == 'TRUE':
    _json.write("cfg/config.json", "ReactMSG", True)
    await ctx.send("Reações ativadas.")

  elif str(value).upper() == 'FALSE':
    _json.write("cfg/config.json", "ReactMSG", False)
    await ctx.send("Reações desativadas.")
  
  else:
    await ctx.send("Erro! :x: :scream:")


# Subgrupo ADMINS
@config.group(aliases=['admin'], invoke_without_command=True)
async def admins(ctx):
  if not func.checkIfAdmin(ctx.author.id): return
  adm_list = _json.read("cfg/config.json")["Admins"]
  adm_names = [await func.get_name_by_id(id) for id in adm_list]
  await ctx.send("**Admins:** " + ", ".join(adm_names) + "\n**Adicionar:** `!cfg admins add <@alguém>`\n**Remover:** `!cfg admins remove <@alguém>`")

@admins.command(aliases=['add', 'adicionar']) # Subcomando ADICIONAR ADMINS
async def _add(ctx, target : discord.Member):
  if not func.checkIfAdmin(ctx.author.id): return

  adms = _json.read("cfg/config.json")["Admins"]
  if int(target.id) not in adms:
    _json.write("cfg/config.json", "Admins", int(target.id))
    await ctx.send("Adicionado.")
  else:
    await ctx.send(f"{target.mention} já é um ADM.")

@admins.command(aliases=['remove', 'remover']) # Subcomando REMOVER ADMINS
async def _remove(ctx, target : discord.Member):
  if not func.checkIfAdmin(ctx.author.id): return

  cfg = _json.read("cfg/config.json")
  if int(target.id) not in cfg["Admins"]:
    cfg["Admins"].remove(int(target.id))
    with open("cfg/config.json", 'w') as f:
      json.dump(cfg, f, indent=4)
    await ctx.send("Removido.")
  else:
    await ctx.send(f"{target.mention} não é um ADM.")



# ========================================= #


@client.command(aliases=["xingar"])
async def xingamento(ctx, *, text : str):
  user = str(ctx.author.id)
  
  if user == "169619020885000193":
      return await ctx.send(":middle_finger:")

  await ctx.message.delete() 

  with open("cfg/xingamentos.json", "r") as f:
    i = json.load(f)
  xingamentos = i["Xingamentos"]

  for id_ in xingamentos.keys():
    if user == id_:
      return await ctx.send("Você já xingou o Xhurru uma vez :clap: :partying_face:", delete_after=5)

  xingamentos.update({user: text})

  with open("cfg/xingamentos.json", "w") as f:
    json.dump(i, f, indent=4)

  challenge = Challenges(user).increase(0)
  if challenge is not None:
    await ctx.send(embed=discord.Embed(description=challenge, color=0xFFD700).set_footer(text="Usuário anônimo 🕵️‍♂️", icon_url=""))

  await ctx.send("Obrigado pela contribuição :relieved::pray:", delete_after=5)
  

# ========================================= #



@client.command()
async def cs(ctx):
  user = str(ctx.author.id)

  with open('cfg/team.json', 'r') as f:
    i = json.load(f)

  if user in i['Team']: 
    return await ctx.send("vc já tá no time burrokkkkkkkk")
  
  if len(i['Team']) + 1 > 5: 
    if func.get_cfg("Queue") == True:
      queue = _json.read("cfg/team.json")["Queue"]
      if user not in queue:
        _json.write("cfg/team.json", "Queue", user)
        return await ctx.send(f"{ctx.author.mention} tá de próximo kkkkk")
      else:
        return await ctx.send("vc já tá na fila burrokkkkkkkk")
    return await ctx.send("time cheio :flushed:")

  if len(i['Team']) <= 0:
    i['Team'] = [user]
  else:
    i['Team'].append(user)
    func.restart_timer()

  challenge = Challenges(user).increase(4)
  if challenge is not None:
    await ctx.send(embed=discord.Embed(description=challenge, color=0xFFD700).set_footer(text=ctx.message.author, icon_url=""))

  card = Cards(user).pick()

  team = [await func.get_name_by_id(p) for p in i['Team']]
  team_count = len(i['Team'])
  mentions = [f"<@{x}>" for x in i['Team']]

  await ctx.send(card)

  if team_count < 5:
    await ctx.send("<@&503830517863677952> **(" + str(team_count) + "/5)** " + ', '.join(team))
    
  else:
    await ctx.send("<@&503830517863677952> TEMOS UM TIME! :scream: " + ', '.join(mentions))


    for player in i["Team"]:
      if "201182192917938177" in i["Team"]:
        challenge = Challenges(player).increase(11)
        if challenge is not None:
          await ctx.send(embed=discord.Embed(description=challenge, color=0xFFD700).set_footer(text=await client.fetch_user(player), icon_url=""))
      
      if "231600835509878784" in i["Team"] and "201182192917938177" in i["Team"] and "307695230331912201" in i["Team"]:
        challenge = Challenges(player).increase(13)
        if challenge is not None:
          await ctx.send(embed=discord.Embed(description=challenge, color=0xFFD700).set_footer(text=await client.fetch_user(player), icon_url=""))


  i["Queue"] = []

  with open('cfg/team.json', 'w') as f:
    json.dump(i, f, indent=4)



# ========================================= #



@client.command()
async def sair(ctx):
  with open('cfg/team.json', 'r') as f:
    i = json.load(f)

  user = str(ctx.author.id)
  if user in i['Team'] or user in i["Queue"]:

    if user == "169619020885000193":
      return await ctx.send("Erro! :x: :scream:")

    else:
      if user in i["Queue"]:
        if func.get_cfg("Queue") == False: return await ctx.send("Erro! :x: :scream:")
        i["Queue"].remove(user)
        await ctx.send(f"<@{user}> saiu da fila.")
      
      else:
        i['Team'].remove(user)
        team = [await func.get_name_by_id(player) for player in i['Team']] 

        if func.get_cfg("Queue") == True and len(_json.read("cfg/team.json")["Queue"]) >= 1:
          new_player = str(i["Queue"][0])
          i["Team"].append(new_player)
          i["Queue"].remove(new_player)
          mentions = [f"<@{x}>" for x in i['Team']]
          await ctx.send(f"{ctx.author.mention} saiu do time e <@{new_player}> entrou.\n<@&503830517863677952> TEMOS UM TIME! :scream: " + ', '.join(mentions))
        else:
          await ctx.send("{} saiu do time.\n<@&503830517863677952> **({}/5)** ".format(ctx.author.mention, str(len(i['Team']))) + ', '.join(team))
          i["Queue"] = []

      with open('cfg/team.json', 'w') as f:
        json.dump(i, f, indent=4)

  else:
    return await ctx.send("Erro! :x: :scream:")



# ========================================= #



@client.command()
async def reset(ctx):
  if ctx.author.id == 169619020885000193: return await ctx.send("Erro! :x: :scream:")
  func.reset_team()
  func.restart_timer()
  await ctx.send("Resetado :handshake:")


@client.command()
async def perdemo(ctx):
  await ctx.send("https://media.giphy.com/media/3jKiDzeDe5nNYvH5QJ/giphy.gif")



# ========================================= #



@client.command(aliases=['time'])
async def team(ctx):
  with open('cfg/team.json', 'r') as f:
    i = json.load(f)
  team = [await func.get_name_by_id(id) for id in i['Team']]
  queue = [await func.get_name_by_id(id) for id in i['Queue']]

  if func.get_cfg("Queue") == False:
    i["Queue"] = []
    with open("cfg/team.json", 'w') as f:
      json.dump(i, f, indent=4)

  if len(team) <= 0:
    await ctx.send("Erro! :x: :scream:")
  
  else:
    e = discord.Embed(title="BÓ CS?", description="*TIME:*", color=0xFFD700)
    e.set_thumbnail(url="https://cdn.discordapp.com/attachments/304750934976888842/834940951720886282/bo_12.jpg")
    e.add_field(name="Contagem", value=str(len(team)) + " / 5", inline=False)
    e.add_field(name="Players", value=', '.join(team), inline=False)
    if len(i["Queue"]) >= 1:
      e.add_field(name="Fila", value=', '.join(queue), inline=False)
    await ctx.send(embed=e)

  
    
# ========================================= #



@client.command(aliases=['quicar', 'remover'])
async def chutar(ctx, member : discord.Member):
  target = str(member.id)

  with open('cfg/team.json', 'r') as f:
    i = json.load(f)

  if target in i['Team']:
    if ctx.author.id == 169619020885000193: return await ctx.send("Erro! :x: :scream:")
    if target != "169619020885000193": return await ctx.send("Erro! :x: :scream:\nEsse comando só pode ser utilizado no Xhurru.")

    challenge = Challenges(ctx.author.id).increase(7)
    if challenge is not None:
      await ctx.send(embed=discord.Embed(description=challenge, color=0xFFD700).set_footer(text=ctx.message.author, icon_url=""))

    i['Team'].remove(target)
    team = [await func.get_name_by_id(player) for player in i["Team"]]
    await ctx.send("https://cdn.discordapp.com/attachments/304750934976888842/835217643920424970/xhurrugif.gif")
    msg = await ctx.send("Pau no cu do {} :thumbsup:\n<@&503830517863677952> **({}/5)** ".format(member.mention, str(len(i['Team']))) + ', '.join(team))

    if func.get_cfg("Queue") == True:
      if len(i["Queue"]) >= 1:
        new_player = str(i["Queue"][0])
        i["Team"].append(new_player)
        i["Queue"].remove(new_player)
        await msg.edit(content="Pau no cu do {} :thumbsup:\n<@{}> entrou no time.\n<@&503830517863677952> **({}/5)** ".format(member.mention, new_player, str(len(i['Team']))) + ', '.join(team) + f", {await func.get_name_by_id(new_player)}")

    else:
      i["Queue"] = []

    with open('cfg/team.json', 'w') as f:
      json.dump(i, f, indent=4)

  else:
    await ctx.send("Erro! :x: :scream:")



# ========================================= #



@client.command(aliases=["achievements", "conquistas"])
async def achievements_(ctx, target : discord.Member = None):
  if target is None:
    user = ctx.author.id
  else:
    user = target.id
  username = await func.get_name_by_id(user)

  with open("cfg/achievements.json", "r") as f:
    i = json.load(f)

  challenges_per_page = 5
  max_pages = math.ceil(len(i.keys()) / challenges_per_page)

  db = sqlite3.connect("challengeprogress.db")
  c = db.cursor()

  r = c.execute(f"SELECT * FROM challenges WHERE user = {str(user)}")
  t = [str(v).replace("None", "0").translate({ord(i): None for i in "(),'"}) for v in r]
  progress = " ".join(t).split(" ")
  progress.pop(0)

  page = 1
  while True:
    embed=discord.Embed(title=f"Conquistas de __{username}__", description=f"`Página {page} de {max_pages}`", color=0xFFD700)

    challenge_list = list(i)
    count = (page * challenges_per_page) - challenges_per_page

    for _ in range(challenges_per_page):
      try:
        name, limit, description = i[challenge_list[count]]["Name"], i[challenge_list[count]]["Limit"], i[challenge_list[count]]["Description"]
      except:
        continue

      if int(progress[count]) >= limit:
        name = ":white_check_mark: " + name
      else:
        name = f"`{func.percentage(int(progress[count]), limit)}` {name}"

      embed.add_field(name=name, value=f"({progress[count]}/{limit}) {description}", inline=False)
      count += 1

    msg = await ctx.send(embed=embed)

    if page - 1 >= 1:
      await msg.add_reaction("⬅")
    if page + 1 <= max_pages:
      await msg.add_reaction("➡")
    valid_reactions = ["⬅", "➡"]

    def check(reaction, user):
      return user == ctx.message.author and reaction.message.id == msg.id and str(reaction.emoji) in valid_reactions

    try:
      reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
      if reaction.emoji == "⬅":
        await msg.delete()
        page -= 1
      if reaction.emoji == "➡":
        await msg.delete()
        page += 1

    except asyncio.TimeoutError:
      break
    
  c.close()
  db.close()



# ========================================= #


@buttons.click
async def btn_5v5_entrar(ctx):
  user = str(ctx.member.id)
  with open("cfg/5v5.json", "r") as f:
    i = json.load(f)

  if user in i["Players"]:
    return await ctx.reply("vc já entrou burrokkkkkkkk", flags=MessageFlags.EPHEMERAL)
  elif len(i["Players"]) >= 10:
    return await ctx.reply("Já temos 10 players, sabe-se lá como :flushed:", flags=MessageFlags.EPHEMERAL)
  else:
    i["Players"].append(user)
    players = [await func.get_name_by_id(player) for player in i["Players"]]
    with open("cfg/5v5.json", "w") as f:
      json.dump(i, f, indent=4) 
    await ctx.message.edit(content=f":loudspeaker:  **Convocando todos os cornos para um 5V5!** {anata}\n\n**({len(players)}/10)**\n```" + ", ".join(players) + "```")
    return await ctx.reply(f"{anata} {ctx.member.name} entrou pro 5v5 :partying_face:")
    


@buttons.click
async def btn_5v5_sair(ctx):
  user = str(ctx.member.id)
  with open("cfg/5v5.json", "r") as f:
    i = json.load(f)

  if user in i["Players"]:
    i["Players"].remove(user)
    players = [await func.get_name_by_id(player) for player in i["Players"]]
    with open("cfg/5v5.json", "w") as f:
      json.dump(i, f, indent=4)
    if len(players) >= 1:
      await ctx.message.edit(content=f":loudspeaker:  **Convocando todos os cornos para um 5V5!** {anata}\n\n**({len(players)}/10)**\n```" + ", ".join(players) + "```")
    else:
      await ctx.message.edit(content=f":loudspeaker:  **Convocando todos os cornos para um 5V5!** {anata}")
    return await ctx.reply(f"{anata} {ctx.member.name} desistiu do 5v5 :pensive:")
  else:
    return await ctx.reply("vc nem entrou ainda burrokkkkkkkk", flags=MessageFlags.EPHEMERAL)




@client.group(aliases=["5v5", "5x5"], invoke_without_command=True)
async def _5v5(ctx):
  with open("cfg/5v5.json", "r") as f:
    i = json.load(f)
  players = [await func.get_name_by_id(player) for player in i["Players"]]

  content = f":loudspeaker:  **Convocando todos os cornos para um 5V5!** {anata}"
  if len(players) >= 1:
    content += f"\n\n**({len(players)}/10)**\n```" + ", ".join(players) + "```"

  await buttons.send(
    content = content,
    channel = ctx.channel.id,
    components = [
      ActionRow([
        Button(label="Entrar", style=ButtonType().Success, custom_id="btn_5v5_entrar"),
        Button(label="Sair", style=ButtonType().Danger, custom_id="btn_5v5_sair")
      ])
    ]
  )


  
@_5v5.command(aliases=["help"], invoke_without_command=True)
async def rrelp(ctx):
  e = discord.Embed(title="Rrelp 5x5", description=
  """
  Tanto *!5x5* quanto *!5v5* funcionam

  `!5x5` - Convoca Anata para um 5x5
  `!5x5 join` - Entra pro 5x5
  `!5x5 leave` - Sai do 5x5
  `!5x5 start` - Começa a escolha dos times
  `!5x5 reset` - Reseta os times/participantes
  `!5x5 maps` - Mostra os mapas que podem cair
  `!5x5 maps add` - Adiciona os mapas especificados
  `!5x5 maps del` - Remove os mapas especificados
  """, 
  color=0xFFD700)
  e.set_thumbnail(url="https://cdn.discordapp.com/attachments/304750934976888842/834940951720886282/bo_12.jpg")
  await ctx.send(embed=e)


@_5v5.group(aliases=["map"], invoke_without_command=True)
async def maps(ctx):
  with open("cfg/5v5.json", "r") as f:
    i = json.load(f)
  
  maps = [map.capitalize() for map in i["Maps"]]
  await ctx.send("```" + ", ".join(maps) + "```\nAdicionar mapas: `!5v5 maps add <m, a, p, a, s>`\nRemover mapas: `!5v5 maps del <m, a, p, a, s>`")

@maps.command(aliases=["adicionar"])
async def add(ctx, *, m : str):
  with open("cfg/5v5.json", "r") as f:
    i = json.load(f)

  maps = m.lower().replace(" ", "").split(",")
  msg_content = "Adicionando...\n\n"
  msg = await ctx.send(msg_content)

  for map in maps:
    if map not in i["Maps"]:
      msg_content += f":white_check_mark: {map.capitalize()}\n"
      i["Maps"].append(map)
    else:
      msg_content += f":x: {map.capitalize()}\n"
  else:
    await msg.edit(content=msg_content)

  with open("cfg/5v5.json", "w") as f:
    json.dump(i, f, indent=4)



@maps.command(aliases=["del", "delete", "remover"])
async def remove(ctx, *, m : str):
  with open("cfg/5v5.json", "r") as f:
    i = json.load(f)

  maps = m.lower().replace(" ", "").split(",")
  msg_content = "Removendo...\n\n"
  msg = await ctx.send(msg_content)

  for map in maps:
    if map in i["Maps"]:
      msg_content += f":white_check_mark: {map.capitalize()}\n"
      i["Maps"].remove(map)
    else:
      msg_content += f":x: {map.capitalize()}\n"
  else:
    await msg.edit(content=msg_content)

  with open("cfg/5v5.json", "w") as f:
    json.dump(i, f, indent=4)
  
  
@_5v5.command(aliases=["entrar"])
async def join(ctx):
  user = str(ctx.author.id)
  with open("cfg/5v5.json", "r") as f:
    i = json.load(f)

  if user in i["Players"]:
    return await ctx.send("vc já entrou burrokkkkkkkk")

  elif len(i["Players"]) >= 10:
    return await ctx.send("Já temos 10 players, sabe-se lá como :flushed:")

  else:
    i["Players"].append(user)
    with open("cfg/5v5.json", "w") as f:
      json.dump(i, f, indent=4) 

    players = [await func.get_name_by_id(player) for player in i["Players"]]
    await ctx.send(f"{anata} {ctx.author.name} entrou pro 5v5 :partying_face:\n\n**({len(players)}/10)**\n```" + ", ".join(players) + "```")


@_5v5.command(aliases=["quit", "sair"])
async def leave(ctx):
  user = str(ctx.author.id)
  with open("cfg/5v5.json", "r") as f:
    i = json.load(f)

  if user not in i["Players"]:
    return await ctx.send("vc nem entrou ainda burrokkkkkkkk")

  else:
    i["Players"].remove(user)
    with open("cfg/5v5.json", "w") as f:
      json.dump(i, f, indent=4)
    players = [await func.get_name_by_id(player) for player in i["Players"]]
    
    if len(players) >= 1:
      await ctx.send(f"{anata} {ctx.author.name} saiu do 5v5 :pensive:\n\n**({len(players)}/10)**\n```" + ", ".join(players) + "```")
    else:
      await ctx.send("**F**")
    



@_5v5.command()
async def start(ctx):
  with open("cfg/5v5.json", "r") as f:
    i = json.load(f)
  i["Team1"] = []
  i["Team2"] = []
  players = [id for id in i["Players"]]

  if len(players) != 10: 
    return await ctx.send("Erro! :x: :scream:")

  if str(ctx.author.id) not in players:
    return await ctx.send("vc nem tá participando burrokkkkkkkk")

  else:
    async def result(r, c):
      return await ctx.send(embed=discord.Embed(description=r, color=0xFFD700).set_footer(text=c, icon_url=""))

    msg = await ctx.send(":zero: Time random\n:one: Capitão escolhe o time")
    await msg.add_reaction("0️⃣")
    await msg.add_reaction("1️⃣")
    valid_reactions = ["0️⃣", "1️⃣"]

    def check(reaction, user):
      return user == ctx.message.author and reaction.message.id == msg.id and str(reaction.emoji) in valid_reactions
    reaction, user = await client.wait_for('reaction_add', check=check)

    if reaction.emoji == "0️⃣":
      await msg.delete()
      while True:
        random.shuffle(players)
        map = random.choice(i["Maps"]).capitalize()
        t1 = [players[0], players[1], players[2], players[3], players[4]]
        t2 = [players[5], players[6], players[7], players[8], players[9]]
        t1_names = [await func.get_name_by_id(id) for id in t1]
        t2_names = [await func.get_name_by_id(id) for id in t2]

        r_msg = await ctx.send("**Time homossexual: **" + ", ".join(t1_names) + "\n**Time homoafetivo: **" + ", ".join(t2_names) + "\n\n**MAPA: **" + map)
        await r_msg.add_reaction("✅")
        await r_msg.add_reaction("🔄")
        valid_reactions = ["✅", "🔄"]

        def check(reaction, user):
          return user == ctx.message.author and reaction.message.id == r_msg.id and str(reaction.emoji) in valid_reactions
        reaction, user = await client.wait_for('reaction_add', check=check)

        if reaction.emoji == "🔄":
          await r_msg.delete()
          continue
        elif reaction.emoji == "✅":
          await r_msg.delete()
          t1m = [f"<@{x}>" for x in t1]
          t2m = [f"<@{x}>" for x in t2]


          for player in i["Players"]:
            caller = await client.fetch_user(player)

            challenge = Challenges(player).increase(5)
            if challenge is not None:
              await result(challenge, caller)

            if map == "Office" or map == "Agency":
              challenge = Challenges(player).increase(10)
              if challenge is not None:
                await result(challenge, caller)

            if "307695230331912201" in i["Players"] and map == "Inferno":
              challenge = Challenges(ctx.author.id).increase(12)
              if challenge is not None:
                await result(challenge, caller)

            if "231600835509878784" in i["Players"] and "201182192917938177" in i["Players"] and "307695230331912201" in i["Players"]:
              challenge = Challenges(player).increase(13)
              if challenge is not None:
                await result(challenge, caller)

          await ctx.send("**Time homossexual: **" + ", ".join(t1m) + "\n**Time homoafetivo: **" + ", ".join(t2m) + "\n\n**MAPA: **" + map)
          break


      i["Team1"] = t1
      i["Team2"] = t2
      i["Map"] = map
      with open("cfg/5v5.json", "w") as f:
        json.dump(i, f, indent=4)

    elif reaction.emoji == "1️⃣":
      await msg.delete()
      players = [id for id in i["Players"]]
      random.shuffle(players)
      t1 = [id for id in i["Team1"]]
      t2 = [id for id in i["Team2"]]
      t1.append(players[0])
      t2.append(players[1])
      players.remove(players[1])
      players.remove(players[0])
      cap1 = await client.fetch_user(t1[0])
      cap2 = await client.fetch_user(t2[0])

      await ctx.send(f"Capitães: `{cap1.name}`, `{cap2.name}`")

      valid_reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"]
      msg_content = f"Vez de {cap1.mention}\n\n"  


      turn = cap1
      while len(players) != 1:
        msg = await ctx.send(":clock1:")
        count = -1
        for player in players:
          count+=1
          msg_content += f"{valid_reactions[count]} {await func.get_name_by_id(players[count])}\n"
          await msg.add_reaction(valid_reactions[count])
          if (count % 2) == 0:
            await msg.edit(content=f":clock{(count + 1) + 2}:")
        else:
          await msg.edit(content=msg_content)
      
        def check(reaction, user):
          return user == turn and reaction.message.id == msg.id and str(reaction.emoji) in valid_reactions
        reaction, user = await client.wait_for('reaction_add', check=check)

        if reaction.emoji in valid_reactions:
          for index, item in enumerate(valid_reactions):
            if item == reaction.emoji:
              selected_player = players[index]

              if selected_player == "251835857407967233":
                challenge = Challenges(turn.id).increase(9)
                if challenge is not None:
                  await result(challenge, await client.fetch_user(turn.id))

          else:
            players.remove(selected_player)
        
        if turn == cap1:
          t1.append(selected_player)
          turn = cap2
        elif turn == cap2:
          t2.append(selected_player)
          turn = cap1

        t1_names = [await func.get_name_by_id(id) for id in t1]
        t2_names = [await func.get_name_by_id(id) for id in t2]
        msg_content = "**Time homoafetivo:** " + ", ".join(t1_names) + "\n**Time homossexual:** " + ", ".join(t2_names) + f"\n\nVez de {turn.mention}\n\n"
        await msg.delete()

      t2.append(players[0])
      players.remove(players[0])
      map = random.choice(i["Maps"]).capitalize()


      for player in i["Players"]:
        caller = await client.fetch_user(player)

        challenge = Challenges(player).increase(5)
        if challenge is not None:
          await result(challenge, caller)

        if player == str(cap1.id) or player == str(cap2.id):
          challenge = Challenges(player).increase(8)
          if challenge is not None:
            await result(challenge, caller)

        if map == "Office" or map == "Agency":
          challenge = Challenges(player).increase(10)
          if challenge is not None:
            await result(challenge, caller)

        if "307695230331912201" in i["Players"] and map == "Inferno":
          challenge = Challenges(ctx.author.id).increase(12)
          if challenge is not None:
            await result(challenge, caller)

        if "231600835509878784" in i["Players"] and "201182192917938177" in i["Players"] and "307695230331912201" in i["Players"]:
          challenge = Challenges(player).increase(13)
          if challenge is not None:
            await result(challenge, caller)


      await ctx.send("**Time homoafetivo:** " + ", ".join([f"<@{id}>" for id in t1]) + "\n**Time homossexual:** " + ", ".join([f"<@{id}>" for id in t2]) + "\n\n**Mapa: **" + map)

      i["Team1"] = t1
      i["Team2"] = t2
      i["Map"] = map
      with open("cfg/5v5.json", "w") as f:
        json.dump(i, f, indent=4)
      


@_5v5.command()
async def reset(ctx):
  with open("cfg/5v5.json", "r") as f:
    i = json.load(f)
  i["Players"] = []
  i["Team1"] = []
  i["Team2"] = []
  i["Map"] = ""
  with open("cfg/5v5.json", "w") as f:
    json.dump(i, f, indent=4)
  await ctx.send("**F**")



# ========================================= #



@client.command()
async def rrelp(ctx):
  e = discord.Embed(title="Rrelp - CSBot 2", description=
  """
  `!cs` - Entra no time
  `!sair` - Sai do time
  `!reset` - Reseta o time
  `!quicar` - Kicka alguém do time (só funciona no Xhurru)
  `!time` - Mostra quem tá no time
  `!conquistas` - Mostra o progresso das conquistas
  `!perdemo` - perdemo
  `!5x5 rrelp` - Mostra os comandos do 5x5
  """, 
  color=0xFFD700)
  e.set_thumbnail(url="https://cdn.discordapp.com/attachments/304750934976888842/834940951720886282/bo_12.jpg")
  await ctx.send(embed=e)



# ========================================= #



#keep_alive()
load_dotenv(".env")
client.run(os.getenv('TOKEN'))