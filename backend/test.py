from ollama import chat, web_fetch, web_search, Client
import json
import os
from dotenv import load_dotenv
load_dotenv(r"C:\Users\leona\OneDrive\Documents\GitHub\vinum\.env")

OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")


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
                The start year and end year should be in years after release, eg if a 2000 vintage was good to drink
                between 2015 and 2025 then start_year and end_year are 15 and 25 respectively.
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
    print("xxxxxxxxxxxxxxxxxxxxxxxxx")
    print(response_json)
    print(json.loads(response_json))


details = {
    "name": "The Virgilius",
    "year": 2001,
    "grape_variety": "Viognier",
    "region": "Eden Valley"
    }

gen_extra_details(details)