


def custome_jwt_response_payload_hander(token, user=None, request=None):
    return {
        "username": user.username,
        "user_id": user.id,
        "token": token
    }