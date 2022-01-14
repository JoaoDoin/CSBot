import json, random
from lib.handlejson import *

class Cards:
    shiqo = "113657436400779269"
    djan = "251835857407967233"
    diogo = "273122822581256192"
    xhurru = "169619020885000193"
    
    combinations = {
        f"{shiqo}{djan}": ["https://i.imgur.com/sVf8NMC.jpeg"],
        f"{djan}{xhurru}": ["https://i.imgur.com/daVEznt.jpeg"],
        f"{shiqo}{diogo}": ["https://i.imgur.com/5st3uE5.jpeg"],
        f"{djan}{diogo}": ["https://i.imgur.com/eZXMP7h.jpeg"],
        f"{xhurru}{diogo}": ["https://i.imgur.com/jj8I3iN.jpeg"]
    }


    def __init__(self, caller):
        self.caller = str(caller)
        self._json = Json()

        
    def pick(self):
        team = self._json.read("cfg/team.json")["Team"]

        with open('cfg/cards.json', 'r') as f:
            i = json.load(f)
        card = random.choice(i['random'])

        for key in i.keys():
            if key == self.caller:
                all_cards = i[key]
                card = random.choice(i[key])

        available_fusions = [random.choice(self.combinations[fusion]) for fusion in self.combinations.keys() if self.caller in fusion and any(player in fusion for player in team)]

        if len(available_fusions) >= 1:
            for fusion in available_fusions:
                all_cards.append(fusion)

            card = random.choice(all_cards)

        return card


    def all_fusion(self):
        cfg = self._json.read("cfg/team.json")
        team = cfg["Team"]

        for combination in self.combinations.keys():
            if all(player in combination for player in team):
                return random.choice(self.combinations[combination])