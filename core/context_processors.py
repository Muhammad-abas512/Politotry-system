from .models import Usermodule, Userpage


def sidebar_context(request):
    """
    Automatic sidebar data har template mein available hoga.
    Har view mein manually pass karne ki zaroorat nahi.
    """
    user_id = request.session.get('user_id')

    if not user_id:
        return {
            'sidebar': [],
            'user_name': '',
            'user_role': '',
        }

    modules = Usermodule.objects.filter(
        userid=user_id, showmodule=True
    ).order_by('displayorder')

    sidebar = []
    for module in modules:
        pages = Userpage.objects.filter(
            userid=user_id,
            moduleid=module.moduleid,
            showpage=True
        ).order_by('displayorder')

        page_list = []
        for page in pages:
            page_list.append({
                'pageid': page.pageid,
                'pagename': page.pagename or '',
                'pageurl': page.pageurl or '#',
                'can_add': page.can_page_add,
                'can_edit': page.can_page_edit,
                'can_delete': page.can_page_delete,
            })

        sidebar.append({
            'moduleid': module.moduleid,
            'modulename': module.modulename or '',
            'module_url': module.module_url or '#',
            'can_add': module.can_module_add,
            'can_edit': module.can_module_edit,
            'can_delete': module.can_module_delete,
            'pages': page_list,
        })

    return {
        'sidebar': sidebar,
        'user_name': request.session.get('user_name', ''),
        'user_role': request.session.get('user_role', ''),
    }