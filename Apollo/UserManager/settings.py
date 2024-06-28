from datetime import timedelta


USER_MANAGER_SETTINGS = {
    
    "TESTING_MODE": False,
    
    "COOLDOWN": {
        "EMAIL_SECRET": timedelta(minutes=5),
        "PASSWORD_CHANGE_SECRET_REQUEST": timedelta(minutes=5)
    },
    
    "REDIRECT": {
        "EMAIL_VERIFICATION": "user-verify-email-redirect",
        "PASSWORD_CHANGE": "user-password-change-redirect"
    },
    
    "EMAIL": {
        "SEND": False,
        "TEMPLATE": "Please click the following link to verify your account: {link}",
        "SUBJECT": "verify your email",
        "FROM": "",
        "SMTP_USERNAME": "",
        "SMTP_PASSWORD": "",
    },
    
    "PASSWORD": {
        "EMAIL": {
            "TEMPLATE": "Please click the following link to reset your password: {link}",
            "SUBJECT": "reset password"
        }
    },
    
    "TOKEN": {
        # update the key on app init through enviornment variables
        "ENCRYPTION_KEY": "O8tY4J4XX9Rdvs2VZMAm8uw5QDXg9rsR0s97VACT_ak=",
        "TOKEN_EXPIERY_TIME": timedelta(days=7),
        "TOKEN_LIMIT": 3
    }

    
}
