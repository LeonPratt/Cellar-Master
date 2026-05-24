import ollama
from datetime import datetime

s= datetime.now()
response = ollama.chat(
    model='qwen3.5:4b',
    messages=[
        {
            'role': 'user',
            'content': 'look at this image of a wine bottle. Extract the name of the wine, the year it was produced, the grape variety, and the region it was produced in. If you cannot find any of this information, say "unknown". Return the information in a JSON format with the following structure: {"name": "name of the wine", "year": "year it was produced", "grape_variety": "grape variety", "region": "region it was produced in"}. If the year is unknown return 0 for the year.',
            'images': ["C:\\Users\\leona\\OneDrive\\Documents\\GitHub\\vinum\\testvirgilius_resized.jpg"]
        }
    ]
)
e = datetime.now()
print(response['message']['content'])
print(e-s)