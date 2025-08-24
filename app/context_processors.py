from .models import Store

def user_store(request):
    if request.user.is_authenticated:
        return {'user_store': Store.get_user_store(request.user)}
    return {'user_store': None}