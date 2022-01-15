import requests
import zipfile
import shutil
import psutil
import os

print("Iniciando atualização.")

def is_running(process):
    return process in (i.name() for i in psutil.process_iter())

if is_running("CSBot.exe"):
    print("\nCSBot detectado, fechando...\n")
    os.system("TASKKILL /F /IM CSBot.exe")


url = "https://api.github.com/repos/JoaoDoin/CSBot/releases"
data = requests.get(url).json()[0]  

download_link = data["assets"][0]["browser_download_url"]
download = requests.get(download_link)

with open("CSBot.zip", "wb") as file:
    file.write(download.content)


print("\nMovendo arquivos...\n")


with zipfile.ZipFile("CSBot.zip", "r") as zip_ref:
    zip_ref.extractall("update")

allFiles = list()

for file in os.listdir("update"):
    fullPath = "update/" + file
    if os.path.isdir(fullPath):
        for subfile in os.listdir(fullPath):
            allFiles.append(file + "/" + subfile)
    else:
        allFiles.append(file)


for file in allFiles:
    if os.path.exists(file):
        os.remove(file)
    shutil.move(f"update/{file}", file)
    print(f'Atualizado: "{file}"')
else:
    os.remove("CSBot.zip")
    shutil.rmtree("update")


print("\nConcluido.")
os.system("pause")