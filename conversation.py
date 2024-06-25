# Read key from the file
from openai import OpenAI
from turbochat.gptprompts import *
import pandas as pd

with open("openai_key", "r") as f:
    # Read first line
    api_key = f.read().strip()


client = OpenAI(api_key=api_key)

chat_history = [
    {
        "role": "system",
        "content": '''
        You are role playing as a healthcare ASSISTANT.
        With every answer from the USER, you will be provided with the top 20 relevent data we already know about the USER.
        Use the user's prompt to stick to YOUR PERSONALITY and YOUR GOAL and never disobey YOUR STRICT RULES.

        There are three players: 
        1. ASSISTANT (you)
        2. USER
        3. SYSTEM

        [[YOUR PERSONALITY]]
        You collect as much information about the user as possible by asking QUESTIONS and chaining conversation.
        If conversation goes off topic, acknowledge the user's responses and get the conversation back to health and lifestyle.
        Suggest small goals to user in order to resolve their problem.
        User's medical history will be provided in the user's response, ALWAYS consider the user's past history while collecting user's information.

        [[YOUR GOAL]]
        Collect information regarding everything which is an indicator of a user's health.
        For example: their habits, mental, physical health, medical conditions, reports, tests, lifestyle choices preferences etc. 

        [[YOUR STRICT RULES]]
        You strictly follow these rules:
        - You only talk about one specific health indicator at a time.
        - You must guide your conversation with the USER according to the SYSTEM's instructions.
        - You must not let the USER know about the SYSTEM.
        - You must respond in short sentences. (1-3 lines maximum)
        - You must act caring, helpful and friendly.
        - In no way you must diagnose the USER as you are not a doctor.
        - Keep the tone of the conversation casual.
        '''
    },
    {
        "role": "assistant",
        "content": "Hi! How are you doing today?"
    }
]

def extract_user_health_information_entries(entries: list):
    df = pd.DataFrame(entries)
    df.columns = ["parameter_label", "parameter_type", "parameter_value"]
    return df

def extract_goal_registration_entries(entries: list):
    df = pd.DataFrame(entries)
    df.columns = ["goal_label", "goal_type", "goal_value"]
    return df

tool_data = Tools(
    [
        
        {
            "name": "collected_health_information_entries",
            "function": extract_user_health_information_entries,
            "definition": {
                "type": "function",
                "function": {
                    "name": "extract_user_health_information_entry",
                    "description": """
                        Extracts information related to user's mental/physical health, habits, lifestyle goals, medical information, everything related to the user's health from user response. Multiple information entries can be extracted.
                    """,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entries": {
                                "type": "array",
                                "description": "list of information entries",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        
                                        "health_parameter": {
                                            "type": "string",
                                            "description": """
                                                health parameter, 
                                                Example: BMI, weight, height, heart rate, stress level, etc,
                                            """
                                        },
                                        
                                        "health_parameter_category": {
                                            "type": "string",
                                            "description": """
                                                category of health parameter propertie
                                                Example: Diet, Report, Mental, Lifestyle, etc
                                            """
                                        },
                                        
                                        "health_parameter_value": {
                                            "type": "string",
                                            "description": """
                                                value of health parameter propertie
                                                Example: 127cm, 40Kg, High, Low, Irregular, balanced etc.
                                            """
                                        },
                                    
                                    },
                                    "required": [
                                        "health_parameter",
                                        "health_parameter_category",
                                        "health_parameter_value",
                                    ],
                                }
                            }
                        },
                    },
                    "required": ["entries"],
                },
            },
        }
    ]
)



def context_responder_model(past_conversation_summ = "", past_n_conversation = "", imm_topic = "", topic_knowledge = ""):

    return f'''
    [Personality]

    You are role playing as a healthcare asistant.
    There are three players, YOU, the USER and the SYSTEM.

    You strictly follow these rules:
    - You must guide your conversation with the USER according to the SYSTEM's instructions.
    - You must not let the USER know about the SYSTEM.
    - You must respond in short sentences. (1-3 lines maximum)
    - You must act caring, helpful and friendly.
    - In no way you must diagnose the USER.

    You will be provided with a small summary of the USER's past conversation with you.
    You will be given instructions from the SYSTEM on how to respond to the USER.
    If the conversation is coming to a deadend, always enquire about their health details.

    [User's Summary]
    {past_conversation_summ}

    [User's immidiate Conversation]
    {past_n_conversation}

    [System's Instruction]

    Talk about and further inquire these topics:
    [[Topic of conversation]]
    {imm_topic}
    
    [[What you already know about the user on this topic]]
    {topic_knowledge}
    
    [Your Message to the user (1-3 lines)]
    '''

def manager_model_part( rag_k ):
    global chat_history

    past_conversation_history = ""

    for chat in chat_history:
        past_conversation_history += f"{chat['role']}: {chat['content']}\n"

    summary = client.chat.completions.create(
        model="gpt-4o",
        messages=[ {"role": "system", "content": "summarize this conversation less than 20 words: "+ past_conversation_history} ]
    )
    summary = summary.to_dict()["choices"][0]["message"]["content"]

    imm_topic = client.chat.completions.create(
        model="gpt-4o",
        messages=[ {"role": "system", "content": "Based on this conversation, what should be the immidiate natural progression in topic of conversation to enquire about the most healthcare data? conversation:" + summary} ]
    )
    imm_topic = imm_topic.to_dict()["choices"][0]["message"]["content"]

    topic_knowledge = client.chat.completions.create(
        model="gpt-4o",
        messages=[ {"role": "system", "content": "Based on this datapoints, create a summary of what you know about this topic from user: " + rag_k} ]
    )
    topic_knowledge = topic_knowledge.to_dict()["choices"][0]["message"]["content"]

    return summary, imm_topic, topic_knowledge

def make_user_input(user_input, rag_response ):

    return {
        "role": "user",
        "content": f'''
        Respond only to <<USER RESPONSE>> while maintaining your PERSONALITY.
        Understand and use the information provided in <<RELEVANT USER HEALTH INFORMATION FROM DATABASE>>.
        If user asks roughly "what do you know about them", respond with the information in <<RELEVANT USER HEALTH INFORMATION FROM DATABASE>>
        
        <<RELEVANT USER HEALTH INFORMATION FROM DATABASE>>:
        {rag_response}

        <<USER RESPONSE>>
        USER RESPONSE: {user_input}
        '''
    }

def extract_from_prompt(prompt, database):

    to_the_front = [None, None]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[ {"role": "user", "content":"Understand and anlayze this prompt. Your response should strictly not be more than 5 words: "+prompt}],
        tools = tool_data.get_tools(),
        tool_choice="required" # auto, required, disabled
    )

    stash = {}
    stash = tool_data.get_results(response, stash)

    if "collected_health_information_entries" in stash.keys():
        to_the_front[0] = stash["collected_health_information_entries"][0].to_dict("records")
        database.update(stash["collected_health_information_entries"][0])

    print("stash: ", stash)

    return to_the_front


def ingest_user_input(user_input, database):
    # Do a series of steps
    # 1. Extract the new data from the user input
    # 2. Call rag to get relelevent data that we currently have on the user
    # 3. Check if system needs to insert a new direction change for the conversation
    # 4. Append the system alert and then augmented user propt to the conversation 
    # 5. Send the conversation to the gpt
    # 6. Append the response to the conversation

    global chat_history

    flag_for_front = extract_from_prompt(user_input, database)

    print("prompt: ", user_input)

    rag_return = database.get(user_input, 10)
    
    relevent_existing_data = rag_return.to_markdown()

    print("relevent_existing_data: ")
    print(relevent_existing_data)
    
    # IF system wants to interject, this is where it does it

    chat_history.append(make_user_input(user_input, relevent_existing_data))

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=chat_history
    )

    # drop the last append
    chat_history.pop()
    chat_history.append({"role": "user", "content": user_input})

    to_the_user = response.to_dict()["choices"][0]["message"]

    chat_history.append(to_the_user)

    return to_the_user["content"], flag_for_front

def ingest_data_file(file):
    
    # Do a series of steps

    return None