# WROTE THIS PEACE OF CODE SOME TIME AGO
# NOT IN USE YET IN PROJECT

import json
from datetime import datetime
import os
from enum import Enum

class Role(Enum):
    ASSISTANT = "assistant"
    USER ="user"
    SYSTEM ="system"
    FUNCTION ="function"


class Conversation:
    def __init__(self: object , historyFile = 'conversation_history.json', persist=True):
        self.historyFile = historyFile
        self.messages: list[dict] = []
        self.perist: bool = persist
        self.load_messages()

    def getNow(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def load_messages(self):
        
        if os.path.exists(self.historyFile):
            with open(self.historyFile, "r") as file:
                try:
                    old_messages = json.load(file)
                    self.messages = [*self.messages, *old_messages]
                    print(len(self.messages),' messages loaded')
                    # if there a more than 50 messages saved delete all but last 5
                    if (len(self.messages) >= 50):
                            del self.messages[6:]
                except json.JSONDecodeError:
                    print('json decoder error')
                    return []  # Return an empty list if the file is empty or corrupted
        else:
            # Create the file with an empty JSON object if it doesn't exist
            with open(self.historyFile, "w", encoding ='utf8') as file:
                json.dump({}, file)
            return []
    
    def add_message(self, role: Role, content: str):
        now = self.getNow()
        newM = {
            "role": role,
            "content": content,
            "created_at": now,
        }
        # eixprint('New Message added: ', newM)
        self.messages.append(newM)

    def clear_all(self):
        del self.messages
   
    def save_messages(self):
        with open(self.historyFile, "w", encoding ='utf8') as file:
            json.dump(self.messages, file, indent=4, separators=(',', ': '), ensure_ascii = False)
    
    def close(self):
        if(self.perist):
            self.save_messages()
        else:
            self.messages = []
            self.save_messages()


    
'''   
def add_message(self, message):
    self.messages.append(message)
    print(self.messages)
'''

'''
    def save_messages(self):
        print(vars(self.messages))
        with open(self.historyFile, "w", encoding ='utf8') as file:
            json.dump(vars(self.messages), file, indent=4, separators=(',', ': '), ensure_ascii = False)
'''
    
'''
class Message():
    def __init__(self , role: str, content: str):
        self.role = role
        self.content = content
        self.created_at = self.getNow()

    def getNow(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def __repr__(self):
        return f'Message(\'{self.role}\', {self.content}, {self.created_at})'
    
    def __str__(self):
        return f'(\n"role": "{self.role}",\n "content": "{self.content}",\n "created_at": "{self.created_at}\n")'
    
    def __dict__(self):
        return {"role": self.role, "content": self.content, "created_at": self.created_at}
'''



    

