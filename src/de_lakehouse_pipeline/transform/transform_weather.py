
def trans_weather(data: dict):
    name = data["name"] 
    temp = data["main"]["temp"]
    return f"{name}today temp is {temp}"
        
