

USER_PROMPT_CONTEXT_FIELD = {
    "name": "user_prompt",
    "field_type": "functional",
    "value": "get_user_prompt",
    "priority": 100
}


CURRENT_DATE_CONTEXT_FIELD = {
    "name": "current_date",
    "field_type": "functional",
    "value": "get_current_date"
}


CURRENT_DAY_CONTEXT_FIELD = {
    "name": "current_day",
    "field_type": "functional",
    "value": "get_current_day"
}


KEY_INFORMATION_STORE_FIELD = {
    "name": "key_information_store",
    "field_type": "functional",
    "value": "get_key_information_store",
    "priority": 1
}


DOCTOR_STORE_FIELD = {
    "name": "doctor_store",
    "field_type": "functional",
    "value": "get_doctor_store",
    "priority": 2
}


ASSISTANT_MESSAGE_GOAL_FIELD = {
    "name": "assistant_message_goal",
    "field_type": "static",
    "value": '''
DONT ASSUME ANYTHING. ASK QUESTIONS TO GET THE REQUIRED INFORMATION. LOOK ONLY IN RECENT CONVERSATION.
Keep asking these questions natruallly in the conversation until you have all these required information about the goal:

- confirm the goal description
- confirm the goal milestones
- Has there been some goal progress already?
- confirm the goal target date

You have the ability to use functions.
Once you have collected all the information described above and the user has confirmed the goal details,
Use extract_goal_details function to set the goal.
''',
    "priority": 99
}


ASSISTANT_MESSAGE_APPOINTMENT_FIELD = {
    "name": "assistant_message_appointment",
    "field_type": "static",
    "value": '''
DONT ASSUME ANYTHING. ASK QUESTIONS TO GET THE REQUIRED INFORMATION. LOOK ONLY IN RECENT CONVERSATION.
Keep asking these questions natruallly in the conversation until you have all these required information about the appointment or service purchase:

- confirm the exact doctor or service package
- confirm the appointment/purchase date and appointment/purchase time
- ensure that the appointment/service request matches the doctor/service provider's availability.

You have the ability to use functions. 
Once you have collected all the information described above and the user has confirmed the appointment/purchase details,
Use extract_request_details function to set the appointment/purchase.
''',
    "priority": 99
}




