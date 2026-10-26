from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import CoreUsers, Usermodule, Userpage
from decimal import Decimal
import json


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            return render(request, 'login.html', {'error': 'Please enter username and password'})

        user = CoreUsers.objects.filter(name=username, password=password).first()

        if user:
            request.session['user_id'] = str(user.id)
            request.session['user_name'] = str(user.name) if user.name else ''
            request.session['user_role'] = str(user.role) if user.role else ''
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})

    return render(request, 'login.html')


SYSTEM_CATALOG = [
    {
        'modulename': 'Chart of Accounts',
        'module_url': 'voucher-entry/',
        'displayorder': 1,
        'icon': 'bi-receipt-cutoff',
        'pages': [
            {'pagename': 'Voucher Entry', 'pageurl': 'voucher-entry/', 'icon': 'bi-receipt'},
            {'pagename': 'Chart of Accounts', 'pageurl': 'chart-of-accounts/', 'icon': 'bi-diagram-3'},
            {'pagename': 'Account Ledger', 'pageurl': 'account-ledger/', 'icon': 'bi-journal-bookmark'},
            {'pagename': 'Daily Expenses', 'pageurl': 'expenses/', 'icon': 'bi-cash-coin'},
        ]
    },
    {
        'modulename': 'New Accounts',
        'module_url': 'parties/',
        'displayorder': 2,
        'icon': 'bi-people',
        'pages': [
            {'pagename': 'Parties Management', 'pageurl': 'parties/', 'icon': 'bi-person-lines-fill'},
            {'pagename': 'Expense Head Setup', 'pageurl': 'expense-head/', 'icon': 'bi-tags'},
        ]
    },
    {
        'modulename': 'Inventory Management',
        'module_url': 'purchase_receiving/',
        'displayorder': 3,
        'icon': 'bi-boxes',
        'pages': [
            {'pagename': 'Purchase Receiving', 'pageurl': 'purchase_receiving/', 'icon': 'bi-cart-plus'},
            {'pagename': 'Sells Invoice', 'pageurl': 'sells/', 'icon': 'bi-cart-check'},
            {'pagename': 'Waste Entry', 'pageurl': 'waste_entry/', 'icon': 'bi-trash3'},
            {'pagename': 'Waste Payment', 'pageurl': 'waste-payment/', 'icon': 'bi-credit-card'},
        ]
    },
    {
        'modulename': 'Market Rate',
        'module_url': 'broiler-rate/',
        'displayorder': 4,
        'icon': 'bi-graph-up',
        'pages': [
            {'pagename': 'Broiler Rate', 'pageurl': 'broiler-rate/', 'icon': 'bi-currency-dollar'},
            {'pagename': 'Fat Rate', 'pageurl': 'fat-rate/', 'icon': 'bi-percent'},
            {'pagename': 'Waste Rate', 'pageurl': 'waste-rate/', 'icon': 'bi-trash'},
            {'pagename': 'Today Rate', 'pageurl': 'today-rate/', 'icon': 'bi-calendar-check'},
        ]
    },
    {
        'modulename': 'Opening',
        'module_url': 'opening/',
        'displayorder': 5,
        'icon': 'bi-box-arrow-in-down',
        'pages': [
            {'pagename': 'Opening Page', 'pageurl': 'opening/', 'icon': 'bi-door-open'},
            {'pagename': 'Cash Opening', 'pageurl': 'cash/', 'icon': 'bi-cash-stack'},
        ]
    },
    {
        'modulename': 'Reports',
        'module_url': 'party_ledger/',
        'displayorder': 6,
        'icon': 'bi-bar-chart-line',
        'pages': [
            {'pagename': 'Party Ledger', 'pageurl': 'party_ledger/', 'icon': 'bi-person-badge'},
            {'pagename': 'Cash Ledger', 'pageurl': 'cash_ledger/', 'icon': 'bi-wallet2'},
            {'pagename': 'Daily Cash Report', 'pageurl': 'cashreport/', 'icon': 'bi-calculator'},
            {'pagename': 'Purchase Report', 'pageurl': 'purchase_report/', 'icon': 'bi-file-earmark-text'},
            {'pagename': 'Sell Report', 'pageurl': 'sells_report/', 'icon': 'bi-file-earmark-bar-graph'},
            {'pagename': 'Net Position', 'pageurl': 'net_position/', 'icon': 'bi-shield-check'},
            {'pagename': 'Broiler Report', 'pageurl': 'broiler_report/', 'icon': 'bi-pie-chart'},
            {'pagename': 'Profit & Loss Report', 'pageurl': 'profit_loss_report/', 'icon': 'bi-graph-up-arrow'},
        ]
    },
    {
        'modulename': 'User Management',
        'module_url': 'user-management/',
        'displayorder': 7,
        'icon': 'bi-shield-lock',
        'pages': [
            {'pagename': 'User Management & Permissions', 'pageurl': 'user-management/', 'icon': 'bi-people-fill'},
            {'pagename': 'Hierarchy Control', 'pageurl': 'hierarchy/', 'icon': 'bi-diagram-2'},
        ]
    },
]

CATALOG_ICONS = {
    'Chart of Accounts': 'bi-receipt-cutoff',
    'Accounts & Vouchers': 'bi-receipt-cutoff',
    'New Accounts': 'bi-people',
    'Setup & Parties': 'bi-people',
    'Inventory Management': 'bi-boxes',
    'Market Rate': 'bi-graph-up',
    'Opening': 'bi-box-arrow-in-down',
    'Reports': 'bi-bar-chart-line',
    'User Management': 'bi-shield-lock',
    'Administration': 'bi-shield-lock',
}

PAGE_ICONS = {
    'voucher-entry/': 'bi-receipt',
    'chart-of-accounts/': 'bi-diagram-3',
    'account-ledger/': 'bi-journal-bookmark',
    'expenses/': 'bi-cash-coin',
    'parties/': 'bi-person-lines-fill',
    'expense-head/': 'bi-tags',
    'purchase_receiving/': 'bi-cart-plus',
    'sells/': 'bi-cart-check',
    'waste_entry/': 'bi-trash3',
    'waste-payment/': 'bi-credit-card',
    'broiler-rate/': 'bi-currency-dollar',
    'fat-rate/': 'bi-percent',
    'waste-rate/': 'bi-trash',
    'today-rate/': 'bi-calendar-check',
    'opening/': 'bi-door-open',
    'cash/': 'bi-cash-stack',
    'party_ledger/': 'bi-person-badge',
    'cash_ledger/': 'bi-wallet2',
    'cashreport/': 'bi-calculator',
    'purchase_report/': 'bi-file-earmark-text',
    'sells_report/': 'bi-file-earmark-bar-graph',
    'net_position/': 'bi-shield-check',
    'broiler_report/': 'bi-pie-chart',
    'profit_loss_report/': 'bi-graph-up-arrow',
    'user-management/': 'bi-people-fill',
    'hierarchy/': 'bi-diagram-2',
}


def sync_user_catalog_permissions(user_id, is_admin=False):
    """Ensure modules and pages exist in Usermodule and Userpage for user_id"""
    # Clean up obsolete empty modules
    Usermodule.objects.filter(
        userid=user_id,
        modulename__in=['Receipt', 'Payment', 'Expenses', 'Waste Payment', 'Waste Entry']
    ).delete()

    for m in SYSTEM_CATALOG:
        aliases = [m['modulename']]
        if m['modulename'] == 'User Management':
            aliases.append('Administration')
        elif m['modulename'] == 'Chart of Accounts':
            aliases.append('Accounts & Vouchers')
        elif m['modulename'] == 'New Accounts':
            aliases.append('Setup & Parties')

        um = Usermodule.objects.filter(userid=user_id, modulename__in=aliases).first()
        if not um:
            um = Usermodule.objects.create(
                userid=user_id,
                modulename=m['modulename'],
                module_url=m['module_url'],
                showmodule=True if is_admin else False,
                can_module_add=True if is_admin else False,
                can_module_edit=True if is_admin else False,
                can_module_delete=True if is_admin else False,
                is_admin=is_admin,
                displayorder=m['displayorder'],
            )
        else:
            um.modulename = m['modulename']
            um.module_url = m['module_url']
            um.displayorder = m['displayorder']
            if is_admin:
                um.showmodule = True
                um.is_admin = True
            um.save()

        for idx, p in enumerate(m['pages'], 1):
            p_url = p['pageurl']
            url_variants = [p_url, p_url.rstrip('/'), p_url.lstrip('/')]
            up = Userpage.objects.filter(userid=user_id, pageurl__in=url_variants).first()
            if not up:
                Userpage.objects.create(
                    moduleid=um,
                    userid=user_id,
                    modulename=m['modulename'],
                    pagename=p['pagename'],
                    pageurl=p_url,
                    showpage=True if is_admin else False,
                    can_page_add=True if is_admin else False,
                    can_page_edit=True if is_admin else False,
                    can_page_delete=True if is_admin else False,
                    is_admin=is_admin,
                    displayorder=idx,
                )
            else:
                up.moduleid = um
                up.modulename = m['modulename']
                up.pagename = p['pagename']
                up.pageurl = p_url
                up.displayorder = idx
                if is_admin:
                    up.showpage = True
                    up.is_admin = True
                up.save()


def get_sidebar_data(user_id):
    """Sidebar data fetch karo - modules aur unke pages"""
    if not user_id:
        return []

    user = CoreUsers.objects.filter(id=user_id).first()
    is_admin = bool(user and str(user.role).strip().lower() == 'admin')

    # Automatically ensure user has all catalog modules and pages in DB!
    sync_user_catalog_permissions(user_id, is_admin=is_admin)

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
            raw_url = (page.pageurl or '').strip().lstrip('/')
            clean_url = raw_url if raw_url.endswith('/') or not raw_url else raw_url + '/'
            page_icon = PAGE_ICONS.get(clean_url, PAGE_ICONS.get(raw_url, 'bi-circle-fill'))

            page_list.append({
                'pageid': page.pageid,
                'pagename': page.pagename or '',
                'pageurl': clean_url,
                'icon': page_icon,
                'can_add': page.can_page_add,
                'can_edit': page.can_page_edit,
                'can_delete': page.can_page_delete,
            })

        clean_mod_url = (module.module_url or '').strip().lstrip('/')
        mod_icon = CATALOG_ICONS.get(module.modulename, 'bi-folder2')

        sidebar.append({
            'moduleid': module.moduleid,
            'modulename': module.modulename or '',
            'module_url': clean_mod_url,
            'icon': mod_icon,
            'can_add': module.can_module_add,
            'can_edit': module.can_module_edit,
            'can_delete': module.can_module_delete,
            'pages': page_list,
        })

    return sidebar


from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.shortcuts import render
from django.db.models import Sum, Count, DecimalField, F, ExpressionWrapper
from django.db.models.functions import Cast, Coalesce

from .models import (
    PurchaseReceiving,
    PurchaseReceivingView,
    SellsInvoice,
    Expensedetail,
    Mortality,
    Parties,
    Usermodule,
)


def dashboard_view(request):
    if not request.session.get('user_id'):
        return redirect('login')

    # ---------------------------------------------------------
    # USER / SIDEBAR
    # ---------------------------------------------------------
    user_id = request.session.get('user_id')
    user_name = request.session.get('user_name', 'User')
    user_role = request.session.get('user_role', '')

    sidebar = get_sidebar_data(user_id)

    # ---------------------------------------------------------
    # DATE FILTERS
    # ---------------------------------------------------------
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    try:
        from_date = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else None
    except ValueError:
        from_date = None
        date_from = ''

    try:
        to_date = datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else None
    except ValueError:
        to_date = None
        date_to = ''

    purchases_qs = PurchaseReceiving.objects.all()
    sales_qs = SellsInvoice.objects.all()
    expenses_qs = Expensedetail.objects.all()
    mortality_qs = Mortality.objects.all()
    wadya_qs = PurchaseReceivingView.objects.all()

    if from_date:
        purchases_qs = purchases_qs.filter(date__date__gte=from_date)
        sales_qs = sales_qs.filter(entry_date__date__gte=from_date)
        expenses_qs = expenses_qs.filter(date__date__gte=from_date)
        mortality_qs = mortality_qs.filter(entry_date__gte=from_date)
        wadya_qs = wadya_qs.filter(date__date__gte=from_date)

    if to_date:
        purchases_qs = purchases_qs.filter(date__date__lte=to_date)
        sales_qs = sales_qs.filter(entry_date__date__lte=to_date)
        expenses_qs = expenses_qs.filter(date__date__lte=to_date)
        mortality_qs = mortality_qs.filter(entry_date__lte=to_date)
        wadya_qs = wadya_qs.filter(date__date__lte=to_date)

    # ---------------------------------------------------------
    # PURCHASE TOTALS
    # ---------------------------------------------------------
    purchase_data = purchases_qs.aggregate(
        total=Coalesce(
            Sum('amount'),
            Decimal('0'),
            output_field=DecimalField(max_digits=30, decimal_places=2)
        ),
        paid=Coalesce(
            Sum('payed_amount'),
            Decimal('0'),
            output_field=DecimalField(max_digits=30, decimal_places=2)
        ),
    )

    total_purchase = purchase_data['total'] or Decimal('0')
    total_purchase_paid = purchase_data['paid'] or Decimal('0')

    # Remaining dynamically calculate kar rahe hain
    total_purchase_remaining = total_purchase - total_purchase_paid

    # ---------------------------------------------------------
    # SALES
    # SellsInvoice amounts CharField hain is liye Cast use ho raha hai
    # ---------------------------------------------------------
    sales_data = sales_qs.aggregate(
        total=Coalesce(
            Sum(
                Cast(
                    'amount',
                    DecimalField(max_digits=30, decimal_places=2)
                )
            ),
            Decimal('0'),
            output_field=DecimalField(max_digits=30, decimal_places=2)
        ),

        received=Coalesce(
            Sum(
                Cast(
                    'received_amount',
                    DecimalField(max_digits=30, decimal_places=2)
                )
            ),
            Decimal('0'),
            output_field=DecimalField(max_digits=30, decimal_places=2)
        ),

        remaining=Coalesce(
            Sum(
                Cast(
                    'remaining_amount',
                    DecimalField(max_digits=30, decimal_places=2)
                )
            ),
            Decimal('0'),
            output_field=DecimalField(max_digits=30, decimal_places=2)
        ),
    )

    total_sales = sales_data['total'] or Decimal('0')
    total_sales_received = sales_data['received'] or Decimal('0')
    total_sales_remaining = sales_data['remaining'] or Decimal('0')

    # ---------------------------------------------------------
    # EXPENSE
    # amount CharField hai
    # ---------------------------------------------------------
    expense_data = expenses_qs.aggregate(
        total=Coalesce(
            Sum(
                Cast(
                    'amount',
                    DecimalField(max_digits=30, decimal_places=2)
                )
            ),
            Decimal('0'),
            output_field=DecimalField(max_digits=30, decimal_places=2)
        )
    )

    total_expense = expense_data['total'] or Decimal('0')

    # ---------------------------------------------------------
    # MORTALITY
    # ---------------------------------------------------------
    mortality_data = mortality_qs.aggregate(
        weight=Coalesce(
            Sum('weight'),
            Decimal('0'),
            output_field=DecimalField(max_digits=30, decimal_places=2)
        ),
        amount=Coalesce(
            Sum('amount'),
            Decimal('0'),
            output_field=DecimalField(max_digits=30, decimal_places=2)
        ),
    )

    total_mortality_weight = mortality_data['weight'] or Decimal('0')
    total_mortality_amount = mortality_data['amount'] or Decimal('0')

    # ---------------------------------------------------------
    # NET POSITION
    # Total Debit (Dr) + Total Cash (Hand + Bank) - Total Credit (Cr)
    # ---------------------------------------------------------
    from .reports import get_net_position_data
    net_pos_summary = get_net_position_data(to_date=None)
    net_position = net_pos_summary['net_position']
    total_debit = net_pos_summary['total_debit']
    total_credit = net_pos_summary['total_credit']
    cash_in_hand = net_pos_summary['cash_in_hand']
    cash_in_bank = net_pos_summary['cash_in_bank']
    total_cash = net_pos_summary['total_cash']

    # ---------------------------------------------------------
    # PARTIES
    # party_type values case-insensitive rakhe hain
    # Apke DB mein agar Vendor/Customer/Trader naming different hai
    # to yahan values change kar dena.
    # ---------------------------------------------------------
    total_vendors = Parties.objects.filter(
        party_type__iexact='Vendor'
    ).count()

    total_customers = Parties.objects.filter(
        party_type__iexact='Customer'
    ).count()

    total_traders = Parties.objects.filter(
        party_type__iexact='Trader'
    ).count()

    # ---------------------------------------------------------
    # WADYA MAAL
    # remaining_weight CharField hai.
    # User requirement:
    # negative sign remove karke absolute values ka sum.
    #
    # Python side parsing rakha gaya hai taake "-100", "50.5" etc
    # safely handle ho saken.
    # ---------------------------------------------------------
    wadya_maal = Decimal('0')

    for value in wadya_qs.values_list('remaining_weight', flat=True):
        if value is None:
            continue

        try:
            cleaned_value = str(value).strip()
            cleaned_value = cleaned_value.replace(',', '')
            cleaned_value = cleaned_value.replace('kg', '')
            cleaned_value = cleaned_value.replace('KG', '')
            cleaned_value = cleaned_value.strip()

            number = Decimal(cleaned_value)

            # Minus remove
            wadya_maal += abs(number)

        except (InvalidOperation, ValueError, TypeError):
            continue

    # ---------------------------------------------------------
    # WASTE / FAT
    # Dummy values as requested
    # ---------------------------------------------------------
    waste_purchase = Decimal('12500')
    waste_sell = Decimal('9800')

    fat_purchase = Decimal('18500')
    fat_sell = Decimal('22100')

    # ---------------------------------------------------------
    # GRAPH
    # Sales + Expense grouped approximately by last records/date.
    # Simple database-independent approach.
    # ---------------------------------------------------------
    chart_labels = []
    chart_sales = []
    chart_expenses = []

    # Last 7 distinct dates from filtered data
    available_dates = set()

    for dt in sales_qs.values_list('entry_date', flat=True):
        if dt:
            available_dates.add(dt.date())

    for dt in expenses_qs.values_list('date', flat=True):
        if dt:
            available_dates.add(dt.date())

    chart_dates = sorted(available_dates)[-7:]

    for chart_date in chart_dates:
        day_sales = sales_qs.filter(
            entry_date__date=chart_date
        ).aggregate(
            total=Coalesce(
                Sum(
                    Cast(
                        'amount',
                        DecimalField(max_digits=30, decimal_places=2)
                    )
                ),
                Decimal('0'),
                output_field=DecimalField(max_digits=30, decimal_places=2)
            )
        )['total']

        day_expense = expenses_qs.filter(
            date__date=chart_date
        ).aggregate(
            total=Coalesce(
                Sum(
                    Cast(
                        'amount',
                        DecimalField(max_digits=30, decimal_places=2)
                    )
                ),
                Decimal('0'),
                output_field=DecimalField(max_digits=30, decimal_places=2)
            )
        )['total']

        chart_labels.append(chart_date.strftime('%d %b'))
        chart_sales.append(float(day_sales or 0))
        chart_expenses.append(float(day_expense or 0))

    context = {
        'user_name': user_name,
        'user_role': user_role,
        'sidebar': sidebar,

        'date_from': date_from,
        'date_to': date_to,

        'total_purchase': total_purchase,
        'total_purchase_paid': total_purchase_paid,
        'total_purchase_remaining': total_purchase_remaining,

        'total_sales': total_sales,
        'total_sales_received': total_sales_received,
        'total_sales_remaining': total_sales_remaining,

        'total_expense': total_expense,

        'total_mortality_weight': total_mortality_weight,
        'total_mortality_amount': total_mortality_amount,

        'net_position': net_position,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'cash_in_hand': cash_in_hand,
        'cash_in_bank': cash_in_bank,
        'total_cash': total_cash,

        'total_vendors': total_vendors,
        'total_customers': total_customers,
        'total_traders': total_traders,
        'total_parties': Parties.objects.count(),

        'wadya_maal': wadya_maal,

        'waste_purchase': waste_purchase,
        'waste_sell': waste_sell,

        'fat_purchase': fat_purchase,
        'fat_sell': fat_sell,

        'chart_labels': chart_labels,
        'chart_sales': chart_sales,
        'chart_expenses': chart_expenses,
    }

    return render(request, 'dashboard.html', context)





def logout_view(request):
    request.session.flush()
    return redirect('login')


def user_management(request):
    if not request.session.get('user_id'):
        return redirect('login')

    user_id = request.session.get('user_id')
    user_role = request.session.get('user_role', '')

    # Ensure admin has full catalog
    if str(user_role).lower() == 'admin':
        sync_user_catalog_permissions(user_id, is_admin=True)

    sidebar = get_sidebar_data(user_id)
    total_system_pages = sum(len(m['pages']) for m in SYSTEM_CATALOG)

    if request.method == 'GET':
        action = request.GET.get('action')

        # AJAX: Fetch permissions for a specific user to populate Setting modal
        if action == 'get_permissions':
            target_id = request.GET.get('user_id')
            target_user = get_object_or_404(CoreUsers, id=target_id)
            is_target_admin = str(target_user.role).lower() == 'admin'

            # Ensure user catalog rows exist
            sync_user_catalog_permissions(target_id, is_admin=is_target_admin)

            # Get granted URLs
            granted_urls = set(
                Userpage.objects.filter(userid=target_id, showpage=True).values_list('pageurl', flat=True)
            )

            catalog_data = []
            for m in SYSTEM_CATALOG:
                pages_data = []
                for p in m['pages']:
                    is_granted = True if is_target_admin else (p['pageurl'] in granted_urls)
                    pages_data.append({
                        'name': p['pagename'],
                        'pagename': p['pagename'],
                        'url': p['pageurl'],
                        'pageurl': p['pageurl'],
                        'icon': p.get('icon', 'bi-circle'),
                        'granted': is_granted
                    })
                catalog_data.append({
                    'module_name': m['modulename'],
                    'module_url': m['module_url'],
                    'icon': m.get('icon', 'bi-folder'),
                    'pages': pages_data
                })

            return JsonResponse({
                'success': True,
                'user_id': target_user.id,
                'user_name': target_user.name,
                'role': target_user.role,
                'is_admin': is_target_admin,
                'catalog': catalog_data
            })

        # Regular Page Render: All users shown in table below form
        users = CoreUsers.objects.all().order_by('id')
        user_list = []
        for u in users:
            is_adm = str(u.role).lower() == 'admin'
            if is_adm:
                allowed_count = total_system_pages
            else:
                allowed_count = Userpage.objects.filter(userid=u.id, showpage=True).count()

            user_list.append({
                'id': u.id,
                'name': u.name or '',
                'role': u.role or 'Staff',
                'phone_number': u.phone_number or '',
                'email': u.email or '',
                'address': u.address or '',
                'password': u.password or '',
                'allowed_count': allowed_count,
                'total_pages': total_system_pages,
            })

        return render(request, 'user_management.html', {
            'sidebar': sidebar,
            'users': user_list,
            'catalog': SYSTEM_CATALOG,
            'total_pages': total_system_pages
        })

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'save':
                user_id_form = data.get('id')
                name = (data.get('name') or '').strip()
                password = (data.get('password') or '').strip()
                role = (data.get('role') or 'Staff').strip()
                phone_number = (data.get('phone_number') or '').strip()
                email = (data.get('email') or '').strip()
                address = (data.get('address') or '').strip()

                if not name or not password:
                    return JsonResponse({'status': 'error', 'message': 'Username and Password are required'})

                if user_id_form:
                    user = get_object_or_404(CoreUsers, id=user_id_form)
                    user.name = name
                    user.password = password
                    user.role = role
                    user.phone_number = phone_number
                    user.email = email
                    user.address = address
                    user.save()

                    if role.lower() == 'admin':
                        sync_user_catalog_permissions(user.id, is_admin=True)

                    return JsonResponse({'status': 'success', 'message': f'User "{user.name}" updated successfully!'})
                else:
                    new_user = CoreUsers.objects.create(
                        name=name,
                        password=password,
                        role=role,
                        phone_number=phone_number,
                        email=email,
                        address=address,
                    )
                    # Initialize permissions
                    sync_user_catalog_permissions(new_user.id, is_admin=(role.lower() == 'admin'))
                    return JsonResponse({'status': 'success', 'message': f'User "{new_user.name}" created successfully!'})

            elif action == 'save_permissions':
                target_id = data.get('user_id')
                raw_selected = data.get('selected_pages') or data.get('page_urls') or []
                selected_urls = set(raw_selected)
                target_user = get_object_or_404(CoreUsers, id=target_id)
                is_target_admin = str(target_user.role).lower() == 'admin'

                for m in SYSTEM_CATALOG:
                    has_module_access = is_target_admin or any(p['pageurl'] in selected_urls for p in m['pages'])
                    um = Usermodule.objects.filter(userid=target_id, modulename=m['modulename']).first()
                    if not um:
                        um = Usermodule.objects.create(
                            userid=target_id,
                            modulename=m['modulename'],
                            module_url=m['module_url'],
                            showmodule=has_module_access,
                            can_module_add=is_target_admin,
                            can_module_edit=is_target_admin,
                            can_module_delete=is_target_admin,
                            is_admin=is_target_admin,
                            displayorder=m['displayorder']
                        )
                    else:
                        um.showmodule = has_module_access
                        um.save()

                    for idx, p in enumerate(m['pages'], 1):
                        p_url = p['pageurl']
                        url_variants = [p_url, p_url.rstrip('/'), p_url.lstrip('/')]
                        up = Userpage.objects.filter(userid=target_id, pageurl__in=url_variants).first()
                        if not up:
                            up = Userpage.objects.create(
                                moduleid=um,
                                userid=target_id,
                                modulename=m['modulename'],
                                pagename=p['pagename'],
                                pageurl=p_url,
                                showpage=is_target_admin or (p_url in selected_urls),
                                can_page_add=is_target_admin,
                                can_page_edit=is_target_admin,
                                can_page_delete=is_target_admin,
                                is_admin=is_target_admin,
                                displayorder=idx
                            )
                        else:
                            up.moduleid = um
                            up.modulename = m['modulename']
                            up.pagename = p['pagename']
                            up.pageurl = p_url
                            up.showpage = is_target_admin or (p_url in selected_urls)
                            up.displayorder = idx
                            up.save()

                return JsonResponse({'status': 'success', 'message': f'Permissions for "{target_user.name}" saved successfully!'})

            elif action == 'delete':
                del_id = data.get('id')
                if str(del_id) == str(user_id):
                    return JsonResponse({'status': 'error', 'message': 'You cannot delete your own logged-in account!'})

                user = get_object_or_404(CoreUsers, id=del_id)
                u_name = user.name
                Userpage.objects.filter(userid=del_id).delete()
                Usermodule.objects.filter(userid=del_id).delete()
                user.delete()
                return JsonResponse({'status': 'success', 'message': f'User "{u_name}" deleted successfully!'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def today_rate(request):
    if not request.session.get('user_id'):
        return redirect('login')
    user_id = request.session.get('user_id')
    sidebar = get_sidebar_data(user_id)
    return render(request, 'today_rate.html', {'sidebar': sidebar})






def hierarchy_management(request):
    if not request.session.get('user_id'):
        return redirect('login')

    user_id = request.session.get('user_id')
    sidebar = get_sidebar_data(user_id)

    if request.method == 'GET':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            action = request.GET.get('action')

            if action == 'get_modules':
                modules = Usermodule.objects.all().values(
                    'moduleid', 'userid', 'modulename', 'module_url',
                    'showmodule', 'can_module_add', 'can_module_edit',
                    'can_module_delete', 'is_admin', 'displayorder'
                ).order_by('displayorder')
                clean = []
                for m in modules:
                    cm = {}
                    for k, v in m.items():
                        if isinstance(v, Decimal):
                            cm[k] = str(v)
                        else:
                            cm[k] = v
                    clean.append(cm)
                return JsonResponse({'modules': clean})

            elif action == 'get_pages':
                module_id = request.GET.get('module_id')
                pages = Userpage.objects.filter(moduleid=module_id).values(
                    'pageid', 'moduleid', 'userid', 'modulename', 'pagename',
                    'pageurl', 'showpage', 'can_page_add', 'can_page_edit',
                    'can_page_delete', 'is_admin', 'displayorder'
                ).order_by('displayorder')
                clean = []
                for p in pages:
                    cp = {}
                    for k, v in p.items():
                        if isinstance(v, Decimal):
                            cp[k] = str(v)
                        else:
                            cp[k] = v
                    clean.append(cp)
                return JsonResponse({'pages': clean})

            elif action == 'get_all_users':
                users = CoreUsers.objects.all().values('id', 'name')
                clean = []
                for u in users:
                    cu = {}
                    for k, v in u.items():
                        if isinstance(v, Decimal):
                            cu[k] = str(v)
                        else:
                            cu[k] = v
                    clean.append(cu)
                return JsonResponse({'users': clean})

        return render(request, 'hierarchy.html', {'sidebar': sidebar})

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'save_module':
                module_id = data.get('moduleid')
                if module_id:
                    module = get_object_or_404(Usermodule, moduleid=module_id)
                    module.userid = data.get('userid')
                    module.modulename = data.get('modulename')
                    module.module_url = data.get('module_url')
                    module.showmodule = data.get('showmodule', True)
                    module.can_module_add = data.get('can_module_add', False)
                    module.can_module_edit = data.get('can_module_edit', False)
                    module.can_module_delete = data.get('can_module_delete', False)
                    module.is_admin = data.get('is_admin', False)
                    module.displayorder = data.get('displayorder', 0)
                    module.save()
                    return JsonResponse({'status': 'success', 'message': 'Module updated successfully!'})
                else:
                    Usermodule.objects.create(
                        userid=data.get('userid'),
                        modulename=data.get('modulename'),
                        module_url=data.get('module_url'),
                        showmodule=data.get('showmodule', True),
                        can_module_add=data.get('can_module_add', False),
                        can_module_edit=data.get('can_module_edit', False),
                        can_module_delete=data.get('can_module_delete', False),
                        is_admin=data.get('is_admin', False),
                        displayorder=data.get('displayorder', 0),
                    )
                    return JsonResponse({'status': 'success', 'message': 'Module saved successfully!'})

            elif action == 'delete_module':
                module_id = data.get('moduleid')
                module = get_object_or_404(Usermodule, moduleid=module_id)
                Userpage.objects.filter(moduleid=module_id).delete()
                module.delete()
                return JsonResponse({'status': 'success', 'message': 'Module and its pages deleted!'})

            elif action == 'save_page':
                page_id = data.get('pageid')
                module_obj = get_object_or_404(Usermodule, moduleid=data.get('moduleid'))
                if page_id:
                    page = get_object_or_404(Userpage, pageid=page_id)
                    page.moduleid = module_obj
                    page.userid = data.get('userid')
                    page.modulename = module_obj.modulename
                    page.pagename = data.get('pagename')
                    page.pageurl = data.get('pageurl')
                    page.showpage = data.get('showpage', True)
                    page.can_page_add = data.get('can_page_add', False)
                    page.can_page_edit = data.get('can_page_edit', False)
                    page.can_page_delete = data.get('can_page_delete', False)
                    page.is_admin = data.get('is_admin', False)
                    page.displayorder = data.get('displayorder', 0)
                    page.save()
                    return JsonResponse({'status': 'success', 'message': 'Page updated successfully!'})
                else:
                    Userpage.objects.create(
                        moduleid=module_obj,
                        userid=data.get('userid'),
                        modulename=module_obj.modulename,
                        pagename=data.get('pagename'),
                        pageurl=data.get('pageurl'),
                        showpage=data.get('showpage', True),
                        can_page_add=data.get('can_page_add', False),
                        can_page_edit=data.get('can_page_edit', False),
                        can_page_delete=data.get('can_page_delete', False),
                        is_admin=data.get('is_admin', False),
                        displayorder=data.get('displayorder', 0),
                    )
                    return JsonResponse({'status': 'success', 'message': 'Page saved successfully!'})

            elif action == 'delete_page':
                page_id = data.get('pageid')
                page = get_object_or_404(Userpage, pageid=page_id)
                page.delete()
                return JsonResponse({'status': 'success', 'message': 'Page deleted successfully!'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

from decimal import Decimal, InvalidOperation
from datetime import datetime
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
import pytz
from .models import (
    SellsInvoice,
    Sellspayment,
    Parties,
    ReceiptHistory,
)


# ============================================================
# HELPERS
# ============================================================
def _to_decimal(value):
    try:
        return Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def _pk_now():
    PK_TZ = pytz.timezone('Asia/Karachi')
    return timezone.now().astimezone(PK_TZ).replace(tzinfo=None)


from datetime import datetime
from django.db import transaction
from django.db.models import Max  # ID generation aur balance calculation ke liye
from django.http import JsonResponse
from django.shortcuts import redirect, render

# Apne models ke imports yahan check kar lein
from .models import (
    CashRecord,
    Parties,
    ReceiptHistory,
    SellsInvoice,
    Sellspayment,
)


def receipt(request):
    """
    Separate Receipt form is removed and unified into Voucher Entry (CRV / BRV).
    """
    if not request.session.get('user_id'):
        return redirect('login')
    messages.info(request, 'Separate Receipt form has been unified into Voucher Entry. Use CRV (Cash Receipt) or BRV (Bank Receipt).')
    return redirect('/voucher-entry/?type=CRV')


def payment(request):
    """
    Separate Payment form is removed and unified into Voucher Entry (CPV / BPV).
    """
    if not request.session.get('user_id'):
        return redirect('login')
    messages.info(request, 'Separate Payment form has been unified into Voucher Entry. Use CPV (Cash Payment) or BPV (Bank Payment).')
    return redirect('/voucher-entry/?type=CPV')


def waste_payment(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, 'waste_payment.html')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q, Max
from datetime import datetime
from decimal import Decimal
from .models import ExpenseHead, Expensedetail, ChartOfAccount, Voucher, VoucherDetail, CashRecord
from .accounts_views import generate_voucher_no, _update_account_balance, _get_pk_now


def _get_or_create_expense_account(head_code, head_name):
    acc = ChartOfAccount.objects.filter(level=4, name__iexact=head_name).first()
    if acc:
        return acc
    if head_code:
        acc = ChartOfAccount.objects.filter(level=4, code=head_code).first()
        if acc:
            return acc
    parent = ChartOfAccount.objects.filter(code='050204', level=3).first() or ChartOfAccount.objects.filter(level=3, account_type='Expense').first()
    if parent:
        last_child = ChartOfAccount.objects.filter(parent=parent, level=4).order_by('-code').first()
        if last_child and last_child.code.isdigit():
            next_code = str(int(last_child.code) + 1).zfill(len(last_child.code))
        else:
            next_code = f"{parent.code}001"
        return ChartOfAccount.objects.create(
            code=next_code,
            name=head_name,
            level=4,
            parent=parent,
            account_type='Expense',
            opening_balance=Decimal('0'),
            current_balance=Decimal('0'),
        )
    return ChartOfAccount.objects.filter(level=4, account_type='Expense').first()


def _parse_date_safe(date_val):
    if not date_val:
        return timezone.now().date()
    if isinstance(date_val, datetime):
        return date_val.date()
    from datetime import date as dt_date
    if isinstance(date_val, dt_date):
        return date_val
    if isinstance(date_val, str):
        date_str = date_val.strip()[:10]
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                return datetime.strptime(date_str, '%d-%m-%Y').date()
            except ValueError:
                pass
    return timezone.now().date()


def _post_expense_voucher(expense, v_type='CPV', bank_id=None, user_name='Admin'):
    amount = Decimal(str(expense.amount or '0'))
    if amount <= Decimal('0'):
        return None

    v_type = 'BPV' if v_type == 'BPV' else 'CPV'
    exp_date_obj = _parse_date_safe(expense.date)

    expense_acc = _get_or_create_expense_account(expense.head_code, expense.head_name)

    if v_type == 'BPV':
        if not bank_id:
            raise ValueError("Bank Account selection is required for BPV (Bank Payment)!")
        cr_acc = ChartOfAccount.objects.get(id=int(bank_id), level=4)
        if cr_acc.current_balance < amount:
            raise ValueError(f"Insufficient Bank Balance! '{cr_acc.name}' has only Rs. {cr_acc.current_balance:,.2f}, required Rs. {amount:,.2f}")
    else:
        cr_acc = ChartOfAccount.objects.filter(level=4, code__in=['010101001', '1110001']).first() or ChartOfAccount.objects.filter(level=4, name__icontains='Cash in Hand').first()
        if not cr_acc:
            raise ValueError("Cash in Hand account not found in Chart of Accounts!")

    voucher_no = generate_voucher_no(v_type)
    desc = expense.remarks or f"Daily Expense: {expense.head_name}"

    voucher = Voucher.objects.create(
        voucher_no=voucher_no,
        voucher_type=v_type,
        date=exp_date_obj,
        reference_no=f"EXP-{expense.id}",
        total_amount=amount,
        remarks=f"Expense #{expense.id} [{expense.head_name}]: {desc}",
        created_by=user_name,
    )

    # 1. Debit Expense Account
    VoucherDetail.objects.create(
        voucher=voucher,
        account=expense_acc,
        debit=amount,
        credit=Decimal('0'),
        narration=f"Expense: {expense.head_name} - {desc}",
        party_id=None,
    )
    _update_account_balance(expense_acc, amount, Decimal('0'))

    # 2. Credit Cash or Bank Account
    VoucherDetail.objects.create(
        voucher=voucher,
        account=cr_acc,
        debit=Decimal('0'),
        credit=amount,
        narration=f"Paid from {cr_acc.name} for {expense.head_name}",
        party_id=None,
    )
    _update_account_balance(cr_acc, Decimal('0'), amount)

    # 3. CashRecord Sync
    last_cash = CashRecord.objects.order_by('-id').first()
    prev_hand = int(last_cash.cash_in_hand or 0) if last_cash else 0
    prev_bank = int(last_cash.cash_in_bank or 0) if last_cash else 0

    if v_type == 'CPV':
        new_hand = prev_hand - int(amount)
        new_bank = prev_bank
    else:
        new_hand = prev_hand
        new_bank = prev_bank - int(amount)

    max_cash_id = CashRecord.objects.aggregate(Max('id'))['id__max']
    next_cash_id = 1 if max_cash_id is None else max_cash_id + 1

    aware_dt = timezone.make_aware(datetime.combine(exp_date_obj, _get_pk_now().time()))
    CashRecord.objects.create(
        id=next_cash_id,
        cash_in_hand=new_hand,
        cash_in_bank=new_bank,
        date=aware_dt,
        discription=f"[{v_type}] #{voucher_no}: Expense {expense.head_name} - {desc[:350]}",
    )

    expense.voucher_no = voucher_no
    expense.save(update_fields=['voucher_no'])
    return voucher


def _delete_expense_voucher(expense):
    voucher = None
    if expense.voucher_no:
        voucher = Voucher.objects.filter(voucher_no=expense.voucher_no).first()
    if not voucher:
        voucher = Voucher.objects.filter(reference_no=f"EXP-{expense.id}").first()

    if voucher:
        net_cash_hand_rev = Decimal('0')
        net_cash_bank_rev = Decimal('0')

        for line in voucher.details.all():
            _update_account_balance(line.account, line.credit, line.debit)

            acc_code = str(line.account.code)
            acc_name_lower = line.account.name.lower()
            if acc_code in ['010101001', '1110001'] or 'cash in hand' in acc_name_lower:
                net_cash_hand_rev += (line.credit - line.debit)
            elif acc_code.startswith('010101') or acc_code.startswith('1110') or 'bank' in acc_name_lower:
                net_cash_bank_rev += (line.credit - line.debit)

        if net_cash_hand_rev != 0 or net_cash_bank_rev != 0:
            last_cash = CashRecord.objects.order_by('-id').first()
            prev_hand = int(last_cash.cash_in_hand or 0) if last_cash else 0
            prev_bank = int(last_cash.cash_in_bank or 0) if last_cash else 0

            max_cash_id = CashRecord.objects.aggregate(Max('id'))['id__max']
            next_cash_id = 1 if max_cash_id is None else max_cash_id + 1

            CashRecord.objects.create(
                id=next_cash_id,
                cash_in_hand=prev_hand + int(net_cash_hand_rev),
                cash_in_bank=prev_bank + int(net_cash_bank_rev),
                date=timezone.now(),
                discription=f"Reversal of Expense Voucher #{voucher.voucher_no}",
            )

        voucher.delete()


def expenses(request):
    if not request.session.get('user_id'):
        return redirect('login')

    user_name = request.session.get('user_name', 'Admin')

    # ============ HANDLE ALL ACTIONS ============
    
    # 1. DELETE EXPENSE
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        try:
            expense_id = request.POST.get('expense_id')
            expense = get_object_or_404(Expensedetail, id=expense_id)
            with transaction.atomic():
                _delete_expense_voucher(expense)
                expense.delete()
            messages.success(request, '🗑️ Expense and linked voucher deleted successfully!')
        except Exception as e:
            messages.error(request, f'❌ Error deleting: {str(e)}')
        return redirect('expenses')

    # 2. UPDATE EXPENSE
    if request.method == 'POST' and request.POST.get('action') == 'update':
        try:
            expense_id = request.POST.get('expense_id')
            head_code = (request.POST.get('head_code') or '').strip()
            head_name = (request.POST.get('head_name') or '').strip()
            expense_date_str = (request.POST.get('expense_date') or '').strip()
            amount_str = (request.POST.get('amount') or '').strip()
            remarks = (request.POST.get('remarks') or '').strip()
            voucher_type = (request.POST.get('voucher_type') or 'CPV').strip().upper()
            bank_id = request.POST.get('bank_id')

            if not head_code and head_name:
                h = ExpenseHead.objects.filter(name__iexact=head_name).first()
                head_code = h.code if h else 'EXP'
            elif not head_name and head_code:
                h = ExpenseHead.objects.filter(code__iexact=head_code).first()
                head_name = h.name if h else head_code

            if not amount_str:
                messages.error(request, '⚠️ Please enter an amount!')
                return redirect('expenses')

            amount = Decimal(str(amount_str).replace(',', ''))
            exp_date_obj = _parse_date_safe(expense_date_str)
            aware_dt = timezone.make_aware(datetime.combine(exp_date_obj, _get_pk_now().time()))

            expense = get_object_or_404(Expensedetail, id=expense_id)

            with transaction.atomic():
                _delete_expense_voucher(expense)
                expense.head_code = head_code
                expense.head_name = head_name
                expense.date = aware_dt
                expense.amount = str(amount)
                expense.remarks = remarks
                expense.save()
                _post_expense_voucher(expense, v_type=voucher_type, bank_id=bank_id, user_name=user_name)
            
            messages.success(request, f'✏️ Expense updated successfully! (Voucher: {expense.voucher_no})')
        except Exception as e:
            messages.error(request, f'❌ Error updating: {str(e)}')
        return redirect('expenses')

    # 3. SAVE NEW EXPENSE
    if request.method == 'POST':
        try:
            head_code = (request.POST.get('head_code') or '').strip()
            head_name = (request.POST.get('head_name') or '').strip()
            expense_date_str = (request.POST.get('expense_date') or '').strip()
            amount_str = (request.POST.get('amount') or '').strip()
            remarks = (request.POST.get('remarks') or '').strip()
            voucher_type = (request.POST.get('voucher_type') or 'CPV').strip().upper()
            bank_id = request.POST.get('bank_id')

            if not head_code and head_name:
                h = ExpenseHead.objects.filter(name__iexact=head_name).first()
                head_code = h.code if h else 'EXP'
            elif not head_name and head_code:
                h = ExpenseHead.objects.filter(code__iexact=head_code).first()
                head_name = h.name if h else head_code

            if not head_code and not head_name:
                messages.error(request, '⚠️ Please select or enter an Expense Head!')
                return redirect('expenses')

            if not amount_str:
                messages.error(request, '⚠️ Please enter an amount!')
                return redirect('expenses')

            amount = Decimal(str(amount_str).replace(',', ''))
            if amount <= Decimal('0'):
                messages.error(request, '⚠️ Amount must be greater than 0!')
                return redirect('expenses')

            exp_date_obj = _parse_date_safe(expense_date_str)
            aware_dt = timezone.make_aware(datetime.combine(exp_date_obj, _get_pk_now().time()))

            with transaction.atomic():
                expense = Expensedetail.objects.create(
                    head_code=head_code,
                    head_name=head_name,
                    date=aware_dt,
                    amount=str(amount),
                    remarks=remarks
                )
                _post_expense_voucher(expense, v_type=voucher_type, bank_id=bank_id, user_name=user_name)

            messages.success(request, f'✅ Expense saved successfully with Voucher #{expense.voucher_no}!')
        except Exception as e:
            messages.error(request, f'❌ Error saving: {str(e)}')
        return redirect('expenses')

    # ============ GET REQUEST - LOAD PAGE ============
    
    # Get filter parameters
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    head_code = request.GET.get('head_code')
    search = request.GET.get('search')
    edit_id = request.GET.get('edit_id')
    action = request.GET.get('action')
    
    # 4. GET SINGLE EXPENSE FOR EDIT (AJAX)
    if action == 'get_expense' and edit_id:
        try:
            expense = get_object_or_404(Expensedetail, id=edit_id)
            v_type = 'CPV'
            bank_id = ''
            if expense.voucher_no:
                v = Voucher.objects.filter(voucher_no=expense.voucher_no).first()
                if v:
                    v_type = v.voucher_type
                    cr_line = v.details.filter(credit__gt=0).first()
                    if cr_line and v_type == 'BPV':
                        bank_id = cr_line.account_id
            data = {
                'success': True,
                'id': expense.id,
                'head_code': expense.head_code,
                'head_name': expense.head_name,
                'date': expense.date.strftime('%Y-%m-%d') if expense.date else '',
                'amount': expense.amount or '0',
                'remarks': expense.remarks or '',
                'voucher_type': v_type,
                'bank_id': bank_id,
                'voucher_no': expense.voucher_no or '',
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # 5. GET FILTERED EXPENSES (AJAX)
    if action == 'get_expenses':
        expenses_qs = Expensedetail.objects.all()

        # Apply date filters
        if from_date:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            expenses_qs = expenses_qs.filter(date__date__gte=from_date_obj)
        
        if to_date:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            expenses_qs = expenses_qs.filter(date__date__lte=to_date_obj)

        # Apply head code filter
        if head_code:
            expenses_qs = expenses_qs.filter(head_code__icontains=head_code)

        # Apply search filter
        if search:
            expenses_qs = expenses_qs.filter(
                Q(head_name__icontains=search) |
                Q(head_code__icontains=search) |
                Q(remarks__icontains=search) |
                Q(voucher_no__icontains=search)
            )

        expenses_qs = expenses_qs.order_by('-date')

        # Prepare JSON response
        data = []
        total = 0
        for exp in expenses_qs:
            amount_val = float(exp.amount or 0)
            total += amount_val
            v_type = 'BPV' if (exp.voucher_no and 'BPV' in exp.voucher_no) else 'CPV'
            data.append({
                'id': exp.id,
                'date': exp.date.strftime('%d %b %Y') if exp.date else '-',
                'date_str': exp.date.strftime('%Y-%m-%d') if exp.date else '',
                'head_code': exp.head_code or '',
                'head_name': exp.head_name or '',
                'remarks': exp.remarks or '',
                'amount': amount_val,
                'amount_formatted': f'Rs {amount_val:,.2f}',
                'voucher_no': exp.voucher_no or '-',
                'voucher_type': v_type,
            })

        return JsonResponse({
            'success': True,
            'data': data,
            'total': total,
            'count': len(data),
            'total_formatted': f'Rs {total:,.2f}'
        })

    # 6. DEFAULT PAGE LOAD
    expense_heads = ExpenseHead.objects.all().order_by('name')
    today = timezone.now().date()
    today_str = today.strftime('%Y-%m-%d')
    
    expenses_list = Expensedetail.objects.filter(
        date__date=today
    ).order_by('-date')
    
    total_amount = 0
    for exp in expenses_list:
        try:
            total_amount += float(exp.amount or 0)
        except:
            pass

    bank_accounts = ChartOfAccount.objects.filter(level=4, is_active=True).filter(
        Q(parent__code__in=['010101', '1110']) | Q(name__icontains='bank')
    ).exclude(code__in=['010101001', '1110001']).order_by('code')

    cash_acc = ChartOfAccount.objects.filter(level=4, code__in=['010101001', '1110001']).first() or ChartOfAccount.objects.filter(level=4, name__icontains='Cash in Hand').first()
    cash_in_hand_bal = cash_acc.current_balance if cash_acc else Decimal('0')

    context = {
        'expense_heads': expense_heads,
        'expenses': expenses_list,
        'bank_accounts': bank_accounts,
        'cash_in_hand_bal': cash_in_hand_bal,
        'total_amount': total_amount,
        'today_date': today_str,
        'from_date': today_str,
        'to_date': today_str,
    }
    return render(request, 'expenses.html', context)



def waste_entry(request):
    if not request.session.get('user_id'):
        return redirect('login')

    return render(request, 'waste_entry.html')