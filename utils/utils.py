def getBaseContext(baseContext):
    purpose = baseContext.get('purpose')
    relationship = baseContext.get('relationship')
    description = baseContext.get('description')
    return purpose, relationship, description

def getCscContext(cscContext):
    number_of_questions = cscContext.get('number_of_questions')
    return number_of_questions

def getBbContext(bbContext):
    number_of_questions = bbContext.get('number_of_questions')
    return number_of_questions

def getGameContext(request_json, game_type):
    if game_type == "csc":
        return getCscContext(request_json.get(f'{game_type}Context'))
    elif game_type == "bb":
        return getBbContext(request_json.get(f'{game_type}Context'))

def checkResponseSuccess(response):
    status = response[1]
    return status == 200 or status == 201

def format_qns_for_fe(questions):
    return [{"id": id, "content": content} for id, content in questions.items()]