

# finds form user message: key in prompt
EXTRACT_USER_RELATED_INFO = {
    "type": "function",
    "function": {
        "name": "extract_user_health_information_entry",
        "description": """
            from USER RESPONSE, extracts information related to user's mental/physical health, medical information, habits, everything related to the user's health. Multiple information entries can be extracted.
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
}

