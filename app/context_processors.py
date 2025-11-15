from .models import Store

def user_store(request):
    if request.user.is_authenticated:
        # Get all stores for this user
        stores = Store.objects.filter(owner=request.user).order_by("id")

        # Try active store from session
        active_store_id = request.session.get("active_store_id")
        active_store = None
        if active_store_id:
            active_store = stores.filter(id=active_store_id).first()

        # Fallback to first store if no active store
        if not active_store:
            active_store = stores.first()
            if active_store:
                request.session["active_store_id"] = active_store.id

        return {'active_store': active_store, 'user_stores': stores}

    return {'active_store': None, 'user_stores': []}
