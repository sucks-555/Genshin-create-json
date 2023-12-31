import discord
import os
from main import *
from Generater import *
from dotenv import load_dotenv
import requests
import json

load_dotenv(".env")
bot = discord.Bot()

def update_json_file(file_path, new_data):
  if os.path.exists(file_path):
    try:
      with open(file_path, 'r', encoding='utf-8') as file:
        existing_data = json.load(file)
    except json.decoder.JSONDecodeError:
      existing_data = {}
  else:
    existing_data = {}
  existing_data.update(new_data)
  with open(file_path, 'w', encoding='utf-8') as file:
    json.dump(existing_data, file, ensure_ascii=False, indent=2)

class DeleteButton(discord.ui.Button):
  async def callback(self, interaction: discord.Interaction):
    await interaction.message.delete()

class CharaButton(discord.ui.Button):
  def __init__(self, label: str, uid: str, dict, lang: str, index):
    super().__init__(style=discord.ButtonStyle.blurple, label=label)
    self.dict = dict
    self.uid = uid
    self.index = index
    self.lang = lang
  async def callback(self, interaction: discord.Interaction):
    choices = ["攻撃力", "防御力", "HP", "元素チャージ効率", "元素熟知","会心のみ"]
    options = [discord.SelectOption(label=choice, value=choice) for choice in choices]
    select = discord.ui.Select(placeholder='Choose an option', options=options)
    select.callback = self.select_callback
    await interaction.response.send_message(f'ユーザーID: {self.uid}', view=discord.ui.View(select))

  async def select_callback(self, interaction: discord.Interaction):
    selected_option = interaction.data['values'][0]
    message = await interaction.response.send_message(f'選択されたオプション: {selected_option}')
    result = dataSetup(UID=self.uid, count=self.index, TYPE=selected_option)
    file_path = 'data.json'
    print(result)
    update_json_file(file_path, result)
    generation(read_json(file_path))
    embed = discord.Embed()
    embed.set_image(url=f"attachment://upload.png")
    await interaction.followup.send(file=discord.File(fp="Image.png", filename="upload.png", spoiler=False), embed=embed)
    await message.delete_original_response()

def Catch(uid, lang="ja"):
  catch = list()
  user = requests.get(f"https://enka.network/api/uid/{uid}?info")
  if user.status_code == 200:
    json_path = ["loc.json","characters.json"]
    try:
      with open(json_path[0], 'r', encoding='utf-8') as lfile: loc = json.load(lfile)
      with open(json_path[1], 'r', encoding='utf-8') as cfile: chara = json.load(cfile)
    except:
      loc = requests.get("https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/loc.json").json()
      chara = requests.get("https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/characters.json").json()
    user = user.json()
    info = user["playerInfo"]["showAvatarInfoList"]
    for count in range(len(info)):
      avatarId = info[count]["avatarId"]
      name = loc[lang][str(chara[str(avatarId)]["NameTextMapHash"])]
      level = info[count]["level"]
      catch.append({ "name": name, "level": level })
    return catch

@bot.command(description="Genshin build card")
async def build(ctx, uid: discord.Option(int), lang: str = "ja"):
  view = discord.ui.View()
  catch = Catch(uid=uid, lang=lang)
  if catch:
    for x in range(len(catch)):
      your_dict = f'{catch[x]["name"]} lv.{catch[x]["level"]}'
      btn = CharaButton(label=your_dict, uid=str(uid), dict=your_dict, index=x, lang=lang)
      view.add_item(btn)
    delete_button = DeleteButton(label='Delete', style=discord.ButtonStyle.red)
    view.add_item(delete_button)
    await ctx.respond("キャラ情報取得中", view=view)
  else:
    await ctx.respond(f"サーバーダウンしてるよ～")

bot.run(os.getenv("TOKEN"))
