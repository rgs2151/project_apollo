

EXTRACT_USER_RELATED_INFO = {
    "type": "function",
    "function": {
        "name": "extract_user_health_information_entry",
        "description": """
            This tool will run all the time to extract smallest of the user details in the specified format.
            from user response, extracts information related to user's mental/physical health, medical information, habits, everything related to the user's health. Multiple information entries can be extracted.
            All sorts of entries describing user's lifestyle, medication, state, symptoms is extracted.
            Do not extract information about user goals.
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
                                    extracted perameter that will determine user's state / probles / conditions
                                    Example: BMI, weight, height, heart rate, stress level, back pain, sleep schedule, etc,
                                """
                            },
                            
                            "health_parameter_category": {
                                "type": "string",
                                "description": """
                                    category of health parameter propertie
                                    Example: Diet, Report, Mental, Lifestyle, symptom, habit etc
                                """
                            },
                            
                            "health_parameter_value": {
                                "type": "string",
                                "description": """
                                    value of health parameter propertie
                                    Example: 127cm, 40Kg, High, Low, Irregular, balanced, bad breadth, severe etc.
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
}


APPOINTMENT_SERVICE_PURCHASE_EVENT = {
    "type": "function",
    "function": {
        "name": "trigger_if_user_wants_to_set_an_appointment_or_service_purchase",
        "description": """
            By looking at the entire conversation history, if over the course of the conversation, the user has requested to set an appointment with the doctor or has requested to purchase a service package, this tool will trigger.
            Trigger if user has requested to set an appointment with the doctor or has requsted to purchase a service package. 
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "enum": ["appointment", "service_purchase"],
                    "description": "Type of event requested by the user",
                },

                "event_description": {
                    "type": "string",
                    "description": "description of the event. For example, 'Requested diabeties appointment checkup' or 'Requested to purchase a XYZ package' etc",
                },

                "event_contact": {
                    "type": "string",
                    "description": "Name of the Doctor or service provider company",
                },

                "event_date": {
                    "type": "string",
                    "description": "Date of the event. in Python datetime Format: %Y-%m-%d",
                },

                "event_time": {
                    "type": "string",
                    "description": "Time of the event. in Python datetime Format: %H:%M:%S",
                },

            },
            "required": [
                "event_type",
                "event_description",
                "event_contact",
                "event_date",
                "event_time",
            ],
        },
    },
}


TOOL_MODE_SELECTOR = {
    "type": "function",
    "function": {
        "name": "detect_conversation_intent_mode",
        "description": """
        Set the conversation mode to a specific mode. 
        Conversation mode can be set to different modes like: 
        - normal: Normal conversation mode, where user and assistant can talk normally.
        - appointment_or_service_purchase: Conversation mode where user is setting an appointment or purchasing a service.
        - goal: Conversation mode where user is setting a goal.
        - advice: Conversation mode where user is asking for advice.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "description": """
                    conversation mode to set:
                    
                    - normal: 
                        Default conversation mode where the user speaks normaly
                    
                    - appointment_or_service_purchase: 
                        Detects if user wants or has intended to set an appointment or purchase a service from the user's recent conversation. 
                    
                    - goal: 
                        Detects if user wants or has intended to set a goal from the user's recent conversation. 
                        Goals can be related to tracking, managing, or aiming for some health, fitness, lifestyle, mental health, etc related target.
                        For example: If user says something like I want to keep track of my Blood Pressure, then that would be considered as a goal.
                    
                    - advice: 
                        Detects if user is asking for advice from the user's recent conversation. 
                        Asking for advice means user is looking for some user specific suggestions, summarization, or recommendations.
                        For example: If user says something like I need advice on how to reduce my stress level, then that would be considered as a goal.
                    
                    """,
                    "enum": ["normal", "appointment_or_service_purchase", "goal", "advice"]
                }
            },
            "required": ["mode"]
        }
    }
}


TOOL_APPOINTMENT_OR_PURCHASE_SERVICE = {
    "type": "function",
    "function": {
        "name": "extract_appointment_or_purchase_service_details",
        "description": """
            Use this funtion only if the user has requested to set an appointment with a specific doctor or has requsted to purchase a service package. 
            By looking at the recent conversation history, if the user has requested to set an appointment with the doctor 
            or has requested to purchase a service package, this tool will trigger.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "enum": ["appointment", "service"],
                    "description": "Type of event requested by the user",
                },

                "event_description": {
                    "type": "string",
                    "description": """
                    description of the event. 
                    For example, 'Requested appointment with Dr. ABC' or 'Requested to purchase a XYZ package' etc
                    """,
                },

                "event_contact": {
                    "type": "string",
                    "description": "Name of the Doctor or service provider company",
                },

                "event_contact_id": {
                    "type": "string",
                    "description": "ID of the Doctor or service provider company from your context",
                },

                "event_date": {
                    "type": "string",
                    "description": "Scheduled date of the event. What is the requested appointment date or purchase date. In Python datetime Format: %Y-%m-%d",
                },

                "event_time": {
                    "type": "string",
                    "description": "Scheduled time of the event. What is the requested appointment time or purchase time. in Python datetime Format: %H:%M:%S",
                },

            },
            "required": [
                "event_type",
                "event_description",
                "event_contact",
                "event_date",
                "event_time",
            ],
        },
    }
}


TOOL_EXTRACT_GOAL_DETAILS = {
    "type": "function",
    "function": {
        "name": "extract_goal_details",
        "description": """
            This tool sets the goal request from the user's recent conversation history.
            By looking at only the user's recent conversation and context, it extracts important key value pairs:

            - goal_type: Type of goal requested by the user
            - goal_description: description of the goal
            - goal_milestones: Milestones of the goal
            - goal_progress: Has there been some goal progress already?
            - goal_target_date: Target date of the goal

        """,
        "parameters": {
            "type": "object",
            "properties": {
                "goal_type": {
                    "type": "string",
                    "enum": ["health", "fitness", "lifestyle", "mental_health"],
                    "description": "Type of goal requested by the user",
                },

                "goal_description": {
                    "type": "string",
                    "description": """
                    description of the goal. 
                    For example, 'Want to reduce weight by 10 pounds' or 'Want to run 5 miles daily' etc
                    """,
                },

                "goal_milestones": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                    "description": "Milestones of the goal. What are the steps or milestones to achieve the goal",
                },

                "goal_progress": {
                    "type": "number",
                    "description": """
                    Has there been some goal progress already? If yes, what is the progress in percentage.
                    0 means no progress and 100 means goal is achieved.
                    Example: if user has already lost 2 pounds out of 10 pounds, then progress would be 20%
                    """,
                },

                "goal_target_date": {
                    "type": "string",
                    "description": "Target date of the goal. When does the user want to achieve the goal. In Python datetime Format: %Y-%m-%d",
                },

            },
            "required": [
                "goal_type",
                "goal_description",
                "goal_milestones",
                "goal_progress",
                "goal_target_date",
            ],
        },
    }
}




