import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

import sys
import json
import dbmanager

from ollama import chat, web_fetch, web_search, Client
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")

def infer_basic(img, testing=False):

    if testing:
        testdict = {
            "name": "The Virgilius",
            "year": 2001,
            "grape_variety": "Viognier",
            "region": "Eden Valley"
            }
        return testdict
    if OLLAMA_API_KEY == None:
        raise Exception("Ollama API key not set. Set it in .env")
    
    client = Client(
        host="https://ollama.com",
        headers={'Authorization': 'Bearer ' + OLLAMA_API_KEY}
    )
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


def gen_extra_details(wine_details):
    print(wine_details)
    client = Client(
        host="https://ollama.com",
        headers={'Authorization': 'Bearer ' + OLLAMA_API_KEY}
    )

    available_tools = {'web_search': client.web_search, 'web_fetch': client.web_fetch}

    messages = [{'role': 'user', 'content': f"""Look at the following wine: {wine_details}. 
                Your job is to return taste notes, food pairings, as well as its optimum drinking window. 
                If you cannot find any of this information, say "unknown". 
                Return the information in a JSON format with the following structure: 
                {{"tasting_notes": "tasting notes for the wine", 
                "food_pairings": "food pairings for the wine", 
                "start_year": "start of optimum drinking window (in years after release)",
                "end_year": "end of optimum drinking window (in years after release)"}}.
                tasting_notes and food_pairings should be list form separated by: |.
                each item in the list should be no more than 3 words long.
                eg "tasting_notes":"peach|stone fruit|oak","food_pairings":"Roasted chicken|turkey|lamb|steak"
                The start year and end year should a year in relation to the vintage year, eg if a 2000 vintage was good to drink
                15 to 25 years after production, then start_year and end_year are 2015 and 2025 respectively.
                This optimal drinking window should be the absolute optimal. It is important that you undershoot the 
                optimal window than to overshoot it.
                """}]

    response_json = ""
    while True:
      response = client.chat(
        model='gpt-oss:20b-cloud',
        messages=messages,
        tools=[web_search, web_fetch],
        think=True
        )
      if response.message.thinking:
        print('Thinking: ', response.message.thinking)
      if response.message.content:
        response_json = response.message.content
        print('Content: ', response.message.content)
      messages.append(response.message)
      if response.message.tool_calls:
        print('Tool calls: ', response.message.tool_calls)
        for tool_call in response.message.tool_calls:
          function_to_call = available_tools.get(tool_call.function.name)
          if function_to_call:
            args = tool_call.function.arguments
            result = function_to_call(**args)
            print('Result: ', str(result)[:200]+'...')
            # Result is truncated for limited context lengths
            messages.append({'role': 'tool', 'content': str(result)[:2000 * 4], 'tool_name': tool_call.function.name})
          else:
            messages.append({'role': 'tool', 'content': f'Tool {tool_call.function.name} not found', 'tool_name': tool_call.function.name})
      else:
        break

    return json.loads(response_json)

def parseResponse(response):
    data = response[response.index("{")+1:response.index("}")]
    print(data)

    lines = data.split(",")
    def parseline(line):
        parsed = line.split(":")[1].replace('"','').strip(" ").strip("\n")
        return parsed 
    parsed = {
        "name":parseline(lines[0]),
        "year":int(parseline(lines[1])),
        "grape_variety":parseline(lines[2]),
        "region":parseline(lines[3]),
    }

    return parsed

def Add_to_cellar(data):
    conn = dbmanager.connect()
    wineid = dbmanager.wine_exists(conn, data["name"], data["year"])

    if wineid == None:
        extra_details = gen_extra_details(data)
        data["tasting_notes"] = extra_details["tasting_notes"]
        data["food_pairings"] = extra_details["food_pairings"].split("|")
        data["drink_window_start"] = extra_details["start_year"]
        data["drink_window_end"] = extra_details["end_year"]
        dbmanager.insert_new_wine(conn, data)

    else:
        dbmanager.insert_preexisting_wine(conn, wineid, data["quantity"])
        

def Remove_from_cellar(data):
    conn = dbmanager.connect()

    wineid = dbmanager.wine_exists(conn, data["name"], data["year"])

    if wineid == None:
       print("wine does not exist")
       return False

    else:
       dbmanager.remove_wine_from_cellar(conn, wineid, data["quantity"])

    





"""
```json
{
  "name": "The Virgilius",
  "year": 2001,
  "grape_variety": "Viognier",
  "region": "Eden Valley"
}
```

r = parseResponse(res)
k = gen_extra_details(r, True)
print(k)
"""

"""
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
"""

