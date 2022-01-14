import requests


url = "https://api.github.com/repos/JoaoDoin/RE4-Mod-Switcher/releases"
data = requests.get(url).json()[0]  

download_link = data["assets"][0]["browser_download_url"]
download = requests.get(download_link)

with open("RE4-Mod-Switcher.zip", "wb") as file:
    file.write(download.content)