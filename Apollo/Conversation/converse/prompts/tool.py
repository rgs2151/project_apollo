

# finds form user message: key in prompt
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



