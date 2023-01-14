def get_bot_token():
    token = "TOKEN"
    with open(".env") as f:
        line = f.read().strip()
        token = line.split("=")[1]
    return token