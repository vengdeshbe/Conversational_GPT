from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import json
from pathlib import Path

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key = api_key)
history_path = Path.cwd() / "history.json"

users={}
###=============================
###Load Users details 
###==============================
def load_users():
    if not os.path.exists("history.json"):
        return {}
    else:
        with open("history.json","r") as f:
            return json.load(f)

 
def save_history(chat_response,user_id,history_path=history_path):
    parsed =[msg.model_dump(mode='json',exclude_none = True) for msg in chat_response]
    users[user_id]["history"]=parsed
    print(f"Data saved in {user_id} account")
    with open(history_path,"w") as f:
        json.dump(users,f,indent=4)
        print("data sotred in local files!....\n")
    # with open(history_path,"w") as f:
    #     json.dump(parsed,f,indent=4)
    #     print("\nhistory saved")
    #     print(f"Total records: {len(parsed)}")
    #     print(f"File name: {history_path}")
    #     print("File size:", history_path.stat().st_size, "bytes")




def load_history(user_id,history_path=history_path):
    if not os.path.exists(history_path):
        return []
    
    with open(history_path,"r") as f:
        users = json.load(f)
        return users[user_id]["history"]

def api_call(id):
    id_user = id
    chat = client.chats.create(
        model = "gemini-3.5-flash-lite",
        history = load_history(user_id = id_user),
        config= types.GenerateContentConfig(system_instruction="you are a helpful chat. your role is to give output politely. your name is TONY!")
        )
    return chat

users=load_users()

while True:
    user_id = input("Enter you user number that should starts with 'EKA'")
    if user_id.startswith("EKA"):
        if user_id not in users.keys():
            print(f"{user_id} is not present in our record. Account it is creating.....\n")
            users[user_id] = ({"summary":"", "history":[]})
            with open("history.json","w") as f:
                json.dump(users,f,indent=4)

            print(f"Account {user_id} is created successfully!..")
            break
        else:
            print(f"{user_id} is present in our record\n")
            break
    else:
        continue
    
chat = api_call(id=user_id) 

while True:
    query = input("How can i help you today?")
    if query.lower() in ["n", "exit", "quit"]:
        break
    
    res = chat.send_message(query)
    users[user_id]["history"].append(chat.get_history())

    print(f"Me: {query}")
    print(f"AI: {res.text}")

    save_history(chat.get_history(),user_id=user_id)

print(users)