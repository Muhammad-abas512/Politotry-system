from .views import get_sidebar_data


def sidebar_context(request):
    """
    Automatic sidebar data har template mein available hoga.
    Har view mein manually pass karne ki zaroorat nahi.
    Sidebar ab seedha user_permissions table aur user role se filter hota hai.
    """
    user_id = request.session.get('user_id')

    if not user_id:
        return {
            'sidebar': [],
            'user_name': '',
            'user_role': '',
        }

    sidebar = get_sidebar_data(user_id)

    return {
        'sidebar': sidebar,
        'user_name': request.session.get('user_name', ''),
        'user_role': request.session.get('user_role', ''),
    }
