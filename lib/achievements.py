import os, json
import random
import sqlite3
from lib.handlejson import *


class Challenges:
    def __init__(self, user_id):
        self.user = str(user_id)
        self.db = sqlite3.connect("challengeprogress.db")

    
    def register(self):
        with open("cfg/achievements.json", "r") as f:
            i = json.load(f)

        c = self.db.cursor()

        c.execute(f'''
        INSERT INTO challenges(user)
        SELECT {self.user}
        WHERE NOT EXISTS(SELECT 1 FROM challenges WHERE user = {self.user})
        ''')
            
        self.db.commit()
        self.db.close()


    def increase(self, challenge_id):
        try:
            with open("cfg/achievements.json", "r") as f:
                i = json.load(f)
            challenge_name = i[str(challenge_id)]["Name"]
            challenge_limit = i[str(challenge_id)]["Limit"]
            challenge_desc = str(i[str(challenge_id)]["Description"]).replace("*", "")
            
            cid = int(challenge_id)
            # Muda o ID dos challenges iguais para o ID maior (pra pegar o maior resultado)
            if cid in [v for v in (1, 2, 3, 4)]: 
                cid = 4
            if cid in [v for v in (5, 6)]:
                cid = 6

            c = self.db.cursor()
            c.execute(f"SELECT `{cid}` FROM challenges WHERE user = {self.user}")
            try:
                progress = int(str(c.fetchone()).translate({ord(i): None for i in "(),'"}))
            except:
                progress = 0


            # Caso específico para comando !cs
            if cid == 4:
                result = None
                for x in range(1, 5):
                    challenge_name = i[str(x)]["Name"]
                    challenge_limit = i[str(x)]["Limit"]
                    challenge_desc = str(i[str(x)]["Description"]).replace("*", "")

                    if progress < challenge_limit:
                        c.execute(f"UPDATE challenges SET `{x}` = {progress + 1} WHERE user = '{self.user}'")
                        if progress + 1 == i[str(x)]["Limit"]:
                            result = f":unlock: **Conquista desbloqueada!**\n\n**({challenge_limit}/{challenge_limit})** *{challenge_name}*\n`{challenge_desc}`"
                else:
                    self.db.commit()
                    self.db.close()
                    return result

            # Caso específico para comando !5v5
            if cid == 6:
                result = None
                for x in range(5, 7):
                    challenge_name = i[str(x)]["Name"]
                    challenge_limit = i[str(x)]["Limit"]
                    challenge_desc = str(i[str(x)]["Description"]).replace("*", "")

                    if progress < challenge_limit:
                        c.execute(f"UPDATE challenges SET `{x}` = {progress + 1} WHERE user = '{self.user}'")
                        if progress + 1 == i[str(x)]["Limit"]:
                            result = f":unlock: **Conquista desbloqueada!**\n\n**({challenge_limit}/{challenge_limit})** *{challenge_name}*\n`{challenge_desc}`"
                else:
                    self.db.commit()
                    self.db.close()
                    return result
     

            # Challenges únicos
            if progress >= challenge_limit: 
                self.db.close()
                return None

            if progress + 1 == challenge_limit:
                unlocked = True
                
            c.execute(f"UPDATE challenges SET `{cid}` = {progress + 1} WHERE user = '{self.user}'")
            self.db.commit()
            self.db.close()

            if unlocked:
                return f":unlock: **Conquista desbloqueada!**\n\n**({challenge_limit}/{challenge_limit})** *{challenge_name}*\n`{challenge_desc}`"
            else:
                return None

        except:
            return None

        

    def unlocked(self, challenge_id):
        pass


    def get(self):
        c = self.db.cursor()
        c.execute(f"SELECT * FROM challenges WHERE user = {self.user}")
        result = c.fetchall()
        return result

        # Verifica se/quantas vezes fez o challenge:

        