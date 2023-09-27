from database import get_db
from nanoid import generate
from quart import jsonify
import logging
from utils.user import get_user_info
from utils.utils import checkResponseSuccess
import hashlib

async def generate_unique_room_id_from(game_type, user_email):
    # Hash the user's email and concat it with game type to generate a unique room id
    # This is to ensure that we don't have thousands of room ids lying around in the db
    max_room_id_length = 6
    room_id = game_type[:2] + str(hashlib.sha256(bytes(user_email, 'utf-8')).hexdigest()())[:max_room_id_length - 2]

    assert(len(room_id) == max_room_id_length)

    # TODO: think about collisions later. We prob just leave the room up for now until user creates a new one

    # while True:
    #     room_id = generate(size=6)
    #     room = await get_db()["Rooms"].find_one({'_id': room_id})
    #     if not room:
    #         logging.info(f"Unique room {room_id} found")
    #         break
    return room_id

async def set_room_published_status(room_id, set_is_published):
    existing_room = await get_db()["Rooms"].find_one({"_id": room_id})
    if not existing_room:
        return {"message": "Room not found"}, 404

    await get_db()["Rooms"].update_one({"_id": room_id},
                                        {'$set': {
                                        'is_published': set_is_published
                                        }})
    
    return {"message": f"Room {room_id} {'published' if set_is_published else 'unpublished'} successfully"}

async def add_questions_to_room_collection(questions, room_id, game_type):
    try:
        await get_db()["Rooms"].insert_one({
            '_id': room_id,
            'game_type': game_type,
            'is_published': False,
            'questions': questions
        })
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({"message": f"Error: adding questions to collection"}), 500
    
    user_info = await get_user_info()
    if not checkResponseSuccess(user_info):
        return user_info
    user_email = user_info[0].get("email")

    logging.info("{user_email}: Creating csc room")

    room_id = await generate_unique_room_id_from(game_type, user_email)

    # update user with room_id. Do we need this?
    await get_db()["Users"].update_one({"_id": user_email},
                                    {'$set': {
                                        'room_id': room_id
                                    }}, upsert=True
                                )

    user = await get_db()["Users"].find_one({"_id": user_email})
    questions = user["csc"]["questions"]
    # create room with all of user's details
    await get_db()["Rooms"].update_one({
        '_id': room_id,
        'user_id': user_email,
        'game_type': 'csc',
        'is_published': True,
        'questions': questions
    }, upsert=True)
    return {"id": room_id}, 201

async def create_room(game_type):
    user_info = await get_user_info()
    if not checkResponseSuccess(user_info):
        return user_info
    user_email = user_info[0].get('email')

    logging.info(f"{user_email}: Creating {game_type} room")

    # Check if there are any blank questions. If there are, return error
    user = await get_db()['Users'].find_one({"_id": user_email})
    questions = user[game_type]['questions']
    for _, content in questions.items():
        if content == "":
            return {"message": "Cannot create room with blank questions"}, 400

    room_id = await generate_unique_room_id_from(game_type, user_email)

    # update user with room_id. Do we need this?
    await get_db()['Users'].update_one({'_id': user_email},
                                    {'$set': {
                                        'room_id': room_id
                                    }}, upsert=True
                                )

    questions = user[game_type]['questions']
    # create room with all of user's details
    await get_db()['Rooms'].update_one(
        {'_id': room_id},
        {'$set': {'user_id': user_email,
        'game_type': game_type,
        'is_published': True,
        'questions': questions
        }}, upsert=True)
    return {"id": room_id}, 201