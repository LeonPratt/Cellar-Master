import os
import re
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

import sys
import json
import dbmanager

from ollama import chat, web_fetch, web_search, Client
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")

def infer_basic(img, testing=False, local=False):
    if testing:
        testdict = {
            "name": "The Virgilius",
            "year": 2001,
            "grape_variety": "Viognier",
            "region": "Eden Valley"
            }
        return testdict
    response = ""
    if local:
        print("local")
        unparsed_response = chat(
            model='gemma3:4b',
                messages=[
                    {
                    'role': 'user',
                    'content': """
                    Look at the wine bottle image.

                    Extract the following fields exactly as they appear on the label:

                    - producer: The winery or brand name.
                    - wine_name: The specific wine/cuvée name, excluding producer.
                    - vintage: The year.
                    - grape_variety: The grape(s).
                    - region: The wine region.

                    Important:
                    - Do not combine producer and wine name.
                    - Do not infer missing information.
                    - Do not rewrite names.
                    - Preserve the exact spelling and punctuation from the label.
                    - If a field is not visible, return "unknown".
                    - Return only JSON.""",
                    'images': [img]
                    }
                ]
            )
        response = unparsed_response['message']['content']
        with open("debug_log.txt", "a") as f:
            f.write(f"Unparsed response: {unparsed_response}\n")
            f.write(f"Parsed response: {response}\n")
    else:
        if OLLAMA_API_KEY == None:
            raise Exception("Ollama API key not set. Set it in .env")
        
        client = Client(
            host="https://ollama.com",
            headers={'Authorization': 'Bearer ' + OLLAMA_API_KEY}
        )
        messages = [
        {
            'role': 'user',
            'content': """
                    Look at the wine bottle image.

                    - producer: The winery or brand name.
                    - wine_name: The specific wine/cuvée name, excluding producer.
                    - vintage: The year.
                    - grape_variety: The grape(s).
                    - region: The wine region.

                    Important:
                    - Do not combine producer and wine name.
                    - If a field is written in capitals, rewrite it in title format.
                    - Do not infer missing information.
                    - Do not rewrite names.
                    - If a field is not visible, return "unknown".
                    - Return only JSON.""",
                    'images': [img]
        },
        ]
        for part in client.chat('gemma4:31b-cloud', messages=messages, stream=True):
            response += part['message']['content']
    return parseResponse(response)


def gen_extra_details(wine_details):
    print(wine_details)
    client = Client(
        host="https://ollama.com",
        headers={'Authorization': 'Bearer ' + OLLAMA_API_KEY}
    )

    available_tools = {'web_search': client.web_search, 'web_fetch': client.web_fetch}

    messages = [{
        "role": "user",
        "content": f"""
    You are a professional wine researcher and sommelier.

    Wine details:
    {wine_details}

    Your task is to identify the EXACT wine and vintage using the information above, then determine:

    1. Typical tasting notes.
    2. Recommended food pairings.
    3. The optimum drinking window.
    4. average price.

    Research requirements:
    - Use web_search first.
    - Use web_fetch on the most relevant sources.
    - Prioritise official producer websites.
    - Then use reputable wine merchants or critics.
    - Use CellarTracker and Vivino only as supporting evidence.
    - If multiple trustworthy sources disagree, use the consensus.
    - Never invent information.
    - If you cannot determine a field with reasonable confidence, return "unknown".

    Important:
    - Ensure the tasting notes and drinking window correspond to the SAME vintage whenever possible.
    - If no information exists for the exact vintage, use the nearest available vintage ONLY if the producer, wine and blend are effectively unchanged.
    - If you use another vintage, account for the age difference when estimating the drinking window.

    The drinking window should represent the period when the wine is at its absolute peak, NOT the entire period during which it is drinkable.

    If uncertain, err on the side of an EARLIER end date rather than a later one.

    Formatting rules:

    Return ONLY valid JSON.

    {{
        "tasting_notes": "...",
        "food_pairings": "...",
        "start_year": 0,
        "end_year": 0,
        "price": 0
    }}

    Rules:
    - tasting_notes is a "|" separated list.
    - food_pairings is a "|" separated list.
    - price is in GPB. '£' symbol must be stripped: £12.41 -> 12.41 (as a float)
    - price must be the average price at which it is actually avaliable to buy it at. Do not return a price if it is out of stock at that price.
    - Every item must contain at most three words.
    - Include between 5 and 12 tasting notes.
    - Include between 4 and 10 food pairings.
    - Do not include duplicate items.
    - Do not include explanations.
    - Do not include markdown.
    - start_year and end_year must be four-digit calendar years.
    - If any field cannot be determined confidently, return "unknown" for that field.
    Example:

    {{
        "tasting_notes":"blackcurrant|cedar|graphite|violet|cigar box|firm tannins",
        "food_pairings":"roast lamb|ribeye steak|venison|aged cheddar",
        "start_year":2028,
        "end_year":2042,
        "price":15.00
    }}
    """
    }]

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
            result = None
            try:
                result = function_to_call(**args)
            except Exception as e:
                result = f"Tool failed: {str(e)}"
            print('Result: ', str(result)[:200]+'...')
            messages.append({'role': 'tool', 'content': str(result)[:2000 * 4], 'tool_name': tool_call.function.name})
          else:
            messages.append({'role': 'tool', 'content': f'Tool {tool_call.function.name} not found', 'tool_name': tool_call.function.name})
      else:
        break

    
    return json.loads(response_json)

def parseResponse(response):
    match = re.search(r"\{.*\}", response, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find JSON in response: {response}")

    data = match.group(0)
    print(data)
    parsed = json.loads(data)

    year_value = parsed.get("vintage", 0)
    try:
        year_value = int(year_value)
    except (TypeError, ValueError):
        year_value = 0

    return {
        "producer":parsed.get("producer", "").strip(),
        "name": parsed.get("wine_name", "").replace("unknown", "").strip(),
        "year": year_value,
        "grape_variety": parsed.get("grape_variety", "").replace("unknown", "").strip(),
        "region": parsed.get("region", "").replace("unknown", "").strip(),
        "price":parsed.get("price","").replace("unknown","").strip()
    }

def Add_to_cellar(data):
    conn = dbmanager.connect()
    try:
        cellar = data["cellar"]
        wineid = dbmanager.wine_exists(conn, data["name"], data["year"])

        if wineid is None:
            extra_details = gen_extra_details(data)
            data["tasting_notes"] = extra_details["tasting_notes"]
            data["food_pairings"] = extra_details["food_pairings"].split("|")
            data["drink_window_start"] = extra_details["start_year"]
            data["drink_window_end"] = extra_details["end_year"]
            data["price"] = extra_details["price"]
            dbmanager.insert_new_wine(conn, data, cellar)
        else:
            dbmanager.insert_preexisting_wine(conn, wineid, cellar, data["quantity"])
    finally:
        conn.close()
        

def Remove_from_cellar(data):
    conn = dbmanager.connect()
    try:
        wineid = dbmanager.wine_exists(conn, data["name"], data["year"])

        if wineid is None:
            return False

        return dbmanager.remove_wine_from_cellar(
            conn, wineid, data["cellar"], data["quantity"]
        )
    finally:
        conn.close()

    





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

