import discord
import json
import math
from lib.handlejson import *

class Functions:
    def __init__(self, client):
        self.client = client
        self._json = Json()

    
    def checkIfAdmin(self, id):
        cfg = self._json.read("cfg/config.json")
        if int(id) in cfg["Admins"]: return True
        return False


    def get_cfg(self, arg):
        return self._json.read("cfg/config.json")[arg]


    def reset_team(self):
        cfg = self._json.read("cfg/team.json")
        cfg["Team"] = []
        cfg["Queue"] = []
        with open("cfg/team.json", 'w') as f:
            json.dump(cfg, f, indent=4)


    async def get_name_by_id(self, id):
        return str(await self.client.fetch_user(int(id)))[:-5]

    def get_mention_by_id(self, id):
        return f"<@{int(id)}>"

    def percentage(self, n1, n2):
        percentage = str(math.floor(100 * float(n1)/float(n2)))
        return f"{percentage}%"

    def restart_timer(self):
        i = self._json.read("cfg/autoreset.json")
        i["Timer"] = i["ResetIn"]
        with open("cfg/autoreset.json", "w") as f:
            json.dump(i, f, indent=4)