

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

