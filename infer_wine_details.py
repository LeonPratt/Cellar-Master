import os
from dotenv import load_dotenv
load_dotenv()

import sys

from ollama import Client
import ollama 
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")


import base64
import cv2

"""
arg1: lcl/cloud
"""
def img_to_b64(img):
    _, buffer = cv2.imencode(".png", img)
    img_b64 = base64.b64encode(buffer).decode("utf-8")
    return img_b64

def local(img):
    response = ollama.chat(
    model='qwen3.5:4b',
    messages=[
        {
            'role': 'user',
            'content': 'look at this image of a wine bottle. Extract the name of the wine, the year it was produced, the grape variety, and the region it was produced in. If you cannot find any of this information, say "unknown". Return the information in a JSON format with the following structure: {"name": "name of the wine", "year": "year it was produced", "grape_variety": "grape variety", "region": "region it was produced in"}. If the year is unknown return 0 for the year.',
            'images': [img]
        }
    ]
)
    return response['message']['content']


def cloud(img):
    if OLLAMA_API_KEY == None:
        raise Exception("Ollama API key not set. Set it in .env")
    
    client = Client(
        host="https://ollama.com",
        headers={'Authorization': 'Bearer ' + OLLAMA_API_KEY}
    )

    if type(img) != str:
        img = img_to_b64(img)


    messages = [
    {
        'role': 'user',
        'content': 'look at this image of a wine bottle. Extract the name of the wine, the year it was produced, the grape variety, and the region it was produced in. If you cannot find any of this information, say "unknown". Return the information in a JSON format with the following structure: {"name": "name of the wine", "year": "year it was produced", "grape_variety": "grape variety", "region": "region it was produced in"}. If the year is unknown return 0 for the year.',
        'images': [img]
    },
    ]
    response = ""
    for part in client.chat('gemma3:4b-cloud', messages=messages, stream=True):
        response += part['message']['content']
    return response

def gen_extra_details(wine_details:dict, cloud:bool) -> dict:

    if cloud:
        client = Client(
            host="https://ollama.com",
            headers={'Authorization': 'Bearer ' + OLLAMA_API_KEY}
        )

        messages = [
        {
            'role': 'user',
            'content': f'Look at the following wine: {wine_details}. Your job is to return taste notes, food pairings, as well as its optimum drinking window. If you cannot find any of this information, say "unknown". Return the information in a JSON format with the following structure: {{"taste_notes": "taste notes for the wine", "food_pairings": "food pairings for the wine", "optimum_drinking_window": "optimum drinking window for the wine"}}. The tasting notes and food pairings should be in compact list form. All other points should be a short paragraph'
        },
        ]
        response = ""

        for part in client.chat('gemma3:4b-cloud', messages=messages, stream=True):
            response += part['message']['content']


        return response

def parseResponse(response):
    data = response[response.index("{")+1:response.index("}")]
    print(data)

    lines = data.split(",")
    def parseline(line):
        parsed = line.split(":")[1].replace('"','').strip(" ").strip("\n")
        return parsed 
    parsed = {
        "name":parseline(lines[0]),
        "year":parseline(lines[1]),
        "grape_variety":parseline(lines[2]),
        "region":parseline(lines[3]),
    }

    return parsed

res = """
```json
{
  "name": "The Virgilius",
  "year": 2001,
  "grape_variety": "Viognier",
  "region": "Eden Valley"
}
```
"""
r = parseResponse(res)
k = gen_extra_details(r, True)
print(k)



model_loc = sys.argv[1]
model_name = sys.argv[2]    
imname = "C:\\Users\\leona\\OneDrive\\Documents\\GitHub\\vinum\\test_photos\\testvirgilius_resized.jpg"
img = cv2.imread(imname)
if len(sys.argv) >= 4:
    img = sys.argv[3]

if model_loc == "lcl":
    local(img)

elif model_loc == "cld":
    print(cloud(img))