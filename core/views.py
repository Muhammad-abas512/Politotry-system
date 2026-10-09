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


def get_sidebar_data(user_id):
    """Sidebar data fetch karo - modules aur unke pages"""
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
    # Sales - Purchases - Expenses
    # ---------------------------------------------------------
    net_position = total_sales - total_purchase - total_expense

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

        'total_vendors': total_vendors,
        'total_customers': total_customers,
        'total_traders': total_traders,

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
    sidebar = get_sidebar_data(user_id)

    if request.method == 'GET':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            users = CoreUsers.objects.all().values(
                'id', 'name', 'role', 'phone_number', 'email', 'address', 'password'
            )
            clean_users = []
            for u in users:
                clean_user = {}
                for key, val in u.items():
                    if isinstance(val, Decimal):
                        clean_user[key] = str(val)
                    else:
                        clean_user[key] = val
                clean_users.append(clean_user)
            return JsonResponse({'users': clean_users})
        return render(request, 'user_management.html', {'sidebar': sidebar})

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'save':
                user_id_form = data.get('id')
                if user_id_form:
                    user = get_object_or_404(CoreUsers, id=user_id_form)
                    user.name = data.get('name')
                    user.password = data.get('password')
                    user.role = data.get('role')
                    user.phone_number = data.get('phone_number')
                    user.email = data.get('email')
                    user.address = data.get('address')
                    user.save()
                    return JsonResponse({'status': 'success', 'message': 'User updated successfully!'})
                else:
                    CoreUsers.objects.create(
                        name=data.get('name'),
                        password=data.get('password'),
                        role=data.get('role'),
                        phone_number=data.get('phone_number'),
                        email=data.get('email'),
                        address=data.get('address'),
                    )
                    return JsonResponse({'status': 'success', 'message': 'User saved successfully!'})

            elif action == 'delete':
                del_id = data.get('id')
                user = get_object_or_404(CoreUsers, id=del_id)
                user.delete()
                return JsonResponse({'status': 'success', 'message': 'User deleted successfully!'})

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
    if not request.session.get("user_id"):
        return redirect("login")

    # ========================================================
    # 1. SAVE RECEIPT (POST)
    # ========================================================
    if request.method == "POST":
        party_code_post = (request.POST.get("party_code") or "").strip()
        party_name_post = (request.POST.get("party_name") or "").strip()
        received_amt_input = request.POST.get("amount")
        payment_method = request.POST.get("payment_mode")
        description = (request.POST.get("description") or "").strip()
        entry_date_str = request.POST.get("date")

        try:
            # ---------------- Pakistan local time ----------------
            pk_now = _pk_now()

            if entry_date_str:
                try:
                    selected_date = datetime.strptime(
                        entry_date_str, "%Y-%m-%d"
                    ).date()
                    final_entry_date = datetime.combine(
                        selected_date, pk_now.time()
                    )
                except ValueError:
                    final_entry_date = pk_now
            else:
                final_entry_date = pk_now

            # ---------------- Amount validation ----------------
            amt_to_receive = _to_decimal(received_amt_input)
            if amt_to_receive <= 0:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Please enter a valid amount greater than 0.",
                    }
                )

            # ---------------- Party resolution ----------------
            party_code = party_code_post
            party_name = party_name_post

            if not party_code and party_name:
                p = (
                    Parties.objects.filter(company_name=party_name).first()
                    or Parties.objects.filter(owner_name=party_name).first()
                )
                if p:
                    party_code = p.code or ""
                    party_name = p.company_name or p.owner_name or party_name

            if not party_code:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Party code missing — please select a party from the modal.",
                    }
                )

            if not party_name:
                p = Parties.objects.filter(code=party_code).first()
                if p:
                    party_name = p.company_name or p.owner_name or ""

            # ==================================================
            # TRANSACTION (Atomic)
            # ==================================================
            with transaction.atomic():

                # -------- Previous due / advance --------
                last_hist = (
                    ReceiptHistory.objects.filter(part_code=party_code)
                    .order_by("-id")
                    .first()
                )
                prev_due = (
                    int(last_hist.due) if last_hist and last_hist.due else 0
                )
                prev_adv = (
                    int(last_hist.advance)
                    if last_hist and last_hist.advance
                    else 0
                )

                net_before = prev_due - prev_adv

                # ==================================================
                # FIFO — Oldest unpaid invoices clear first
                # ==================================================
                cash_pool = amt_to_receive

                unpaid_invoices = (
                    SellsInvoice.objects.select_for_update()
                    .filter(customer_name=party_name)
                    .order_by("entry_date", "id")
                )

                for inv in unpaid_invoices:
                    if cash_pool <= 0:
                        break

                    inv_received = _to_decimal(inv.received_amount)
                    inv_remaining = _to_decimal(inv.remaining_amount)

                    if inv_remaining <= 0:
                        inv_total = _to_decimal(inv.amount)
                        inv_remaining = inv_total - inv_received
                        if inv_remaining <= 0:
                            continue

                    apply_now = min(inv_remaining, cash_pool)

                    new_received = inv_received + apply_now
                    new_remaining = inv_remaining - apply_now

                    inv.received_amount = str(new_received)
                    inv.remaining_amount = str(new_remaining)
                    inv.save(
                        update_fields=["received_amount", "remaining_amount"]
                    )

                    Sellspayment.objects.create(
                        sell_no=inv.sells_no,
                        customer_name=inv.customer_name or party_name,
                        weight=inv.weight,
                        rate=inv.rate,
                        vehicle_no=inv.vehicle_no,
                        amount=inv.amount,
                        received_amount=str(apply_now),
                        description=description,
                        payment_method=payment_method,
                        entry_date=final_entry_date,
                    )

                    cash_pool -= apply_now

                # -------- New due / advance --------
                net_after = net_before - int(amt_to_receive)

                if net_after >= 0:
                    new_due, new_adv = net_after, 0
                else:
                    new_due, new_adv = 0, abs(net_after)

                # -------- Insert receipt_history --------
                ReceiptHistory.objects.create(
                    party_name=party_name,
                    part_code=party_code,
                    amount=0,
                    received_amount=str(amt_to_receive),
                    payment_method=payment_method,
                    date=final_entry_date,
                    due=new_due,
                    advance=new_adv,
                )

                # ==================================================
                # NEW ADDITION: CASHRECORD INTEGRATION
                # ==================================================
                # Database se sabse latest Cash Record nikalte hain
                last_cash = CashRecord.objects.order_by("-id").first()
                prev_cash_in_hand = (
                    last_cash.cash_in_hand
                    if (last_cash and last_cash.cash_in_hand)
                    else 0
                )
                prev_cash_in_bank = (
                    last_cash.cash_in_bank
                    if (last_cash and last_cash.cash_in_bank)
                    else 0
                )

                # Amount ko integer me convert karte hain
                received_amount_int = int(amt_to_receive)

                new_cash_in_hand = prev_cash_in_hand
                new_cash_in_bank = prev_cash_in_bank

                # Payment mode check kar ke relevant field update karenge
                if payment_method == "Cash":
                    new_cash_in_hand += received_amount_int
                elif payment_method == "Bank Transfer":
                    new_cash_in_bank += received_amount_int

                # ID sequence error (1364) se bachne ke liye safe next ID generate karenge
                max_cash_id = CashRecord.objects.aggregate(Max("id"))["id__max"]
                next_cash_id = 1 if max_cash_id is None else max_cash_id + 1

                # CashRecord table me details save karna
                CashRecord.objects.create(
                    id=next_cash_id,
                    cash_in_hand=new_cash_in_hand,
                    cash_in_bank=new_cash_in_bank,
                    date=final_entry_date,  # Selected date with time
                    discription=description,  # Remarks / Description column
                )

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    # ========================================================
    # 2. AJAX — PENDING PARTIES (from receipt_history)
    # ========================================================
    if request.GET.get("action") == "get_sales":
        history_qs = ReceiptHistory.objects.order_by("part_code", "-id")

        latest_entries = {}
        for row in history_qs:
            if row.part_code and row.part_code not in latest_entries:
                latest_entries[row.part_code] = row

        data = []
        for code, row in latest_entries.items():
            due = row.due or 0
            adv = row.advance or 0
            if due <= 0 and adv <= 0:
                continue
            data.append(
                {
                    "part_code": row.part_code or "",
                    "party_name": row.party_name or "",
                    "due": due,
                    "advance": adv,
                    "date": (
                        row.date.strftime("%d %b %Y") if row.date else "-"
                    ),
                }
            )

        data.sort(key=lambda x: (x["party_name"] or "").lower())
        return JsonResponse({"success": True, "data": data})

    # ========================================================
    # 3. DEFAULT PAGE
    # ========================================================
    pk_now = _pk_now()
    today_date = pk_now.strftime("%Y-%m-%d")
    parties = Parties.objects.all().order_by("company_name")

    context = {
        "parties": parties,
        "today_date": today_date,
    }
    return render(request, "receipt.html", context)
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import F, Max
from decimal import Decimal, InvalidOperation
from datetime import datetime
import pytz
from django.utils import timezone

from .models import (
    Parties,
    PurchaseReceiving,
    PurchasePayments,
    PurchasePaymentHistory,
    CashRecord,
)


def payment(request):
    # ==================================================
    # LOGIN CHECK
    # ==================================================
    if not request.session.get('user_id'):
        return redirect('login')

    # ==================================================
    # SAVE PAYMENT (POST)
    # ==================================================
    if request.method == 'POST':
        party_name        = (request.POST.get('party_name') or '').strip()
        party_code        = (request.POST.get('party_code') or '').strip()
        payment_date_str  = request.POST.get('payment_date')
        paying_amount_raw = (request.POST.get('paying_amount') or '').strip()
        payment_mode      = (request.POST.get('payment_mode') or '').strip()
        remarks           = (request.POST.get('remarks') or '').strip()
        clear_advance     = request.POST.get('clear_advance') == 'on'

        try:
            # ---------------- Amount validation ----------------
            if clear_advance:
                paying_amount = Decimal('0')
            else:
                try:
                    paying_amount = Decimal(paying_amount_raw)
                except (InvalidOperation, TypeError, ValueError):
                    raise ValueError("Please enter a valid payment amount.")
                if paying_amount <= 0:
                    raise ValueError("Payment amount must be greater than 0.")

            if not party_name and not party_code:
                raise ValueError("Please select a party.")

            # ---------------- Pakistan local time ----------------
            PK_TZ = pytz.timezone('Asia/Karachi')
            pakistan_now = timezone.now().astimezone(PK_TZ).replace(tzinfo=None)

            if payment_date_str:
                try:
                    selected_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
                    final_payment_datetime = datetime.combine(selected_date, pakistan_now.time())
                except ValueError:
                    final_payment_datetime = pakistan_now
            else:
                final_payment_datetime = pakistan_now

            # ---------------- Resolve Party Code ----------------
            if not party_code:
                party_obj = Parties.objects.filter(company_name=party_name).first() or \
                            Parties.objects.filter(owner_name=party_name).first()
                party_code = party_obj.code if party_obj else ''

            if not party_code:
                raise ValueError("Party code could not be resolved.")

            # ==================================================
            # TRANSACTION (Atomic Start)
            # ==================================================
            with transaction.atomic():

                # 1) Get Last History for Running Balance
                last_history = (
                    PurchasePaymentHistory.objects
                    .select_for_update()
                    .filter(party_code=party_code)
                    .order_by('-id')
                    .first()
                )

                prev_due = Decimal(last_history.due if last_history and last_history.due else 0)
                prev_adv = Decimal(last_history.advanced if last_history and last_history.advanced else 0)

                # 2) Calculate New Due / Advance
                if clear_advance:
                    refund_amount = prev_adv
                    new_due = 0
                    new_adv = 0
                    final_payed_val = refund_amount
                else:
                    net = (prev_due - prev_adv) - paying_amount
                    if net >= 0:
                        new_due, new_adv = net, 0
                    else:
                        new_due, new_adv = 0, abs(net)
                    final_payed_val = paying_amount

                amount_to_pay = int(final_payed_val)

                # ==================================================
                # CASHRECORD CHECK & VALIDATION
                # ==================================================
                last_cash = (
                    CashRecord.objects
                    .select_for_update()
                    .order_by('-id')
                    .first()
                )
                prev_cash_in_hand = (
                    int(last_cash.cash_in_hand)
                    if (last_cash and last_cash.cash_in_hand is not None)
                    else 0
                )
                prev_cash_in_bank = (
                    int(last_cash.cash_in_bank)
                    if (last_cash and last_cash.cash_in_bank is not None)
                    else 0
                )

                if payment_mode == 'Bank Transfer':
                    if amount_to_pay > prev_cash_in_bank:
                        raise ValueError(
                            f"cash in bank mai itni amount nhi hy jitni ap pay kr rai ho (Mojooda Cash in Bank: Rs. {prev_cash_in_bank:,})"
                        )
                    new_cash_in_bank = prev_cash_in_bank - amount_to_pay
                    new_cash_in_hand = prev_cash_in_hand
                else:
                    # Cash in Hand
                    if amount_to_pay > prev_cash_in_hand:
                        raise ValueError(
                            f"cash in hand mai itni amount nhi hy jitni ap pay kr rai ho (Mojooda Cash in Hand: Rs. {prev_cash_in_hand:,})"
                        )
                    new_cash_in_hand = prev_cash_in_hand - amount_to_pay
                    new_cash_in_bank = prev_cash_in_bank

                # 3) FIFO Logic: Update PurchaseReceiving
                if not clear_advance:
                    temp_amount = paying_amount
                    pending_purchases = PurchaseReceiving.objects.filter(
                        vendor_code=party_code
                    ).order_by('date', 'id')

                    for purchase in pending_purchases:
                        if temp_amount <= 0:
                            break

                        total_amt    = Decimal(purchase.amount or 0)
                        already_paid = Decimal(purchase.payed_amount or 0)
                        needed       = total_amt - already_paid

                        if needed > 0:
                            if temp_amount >= needed:
                                purchase.payed_amount = total_amt
                                temp_amount -= needed
                            else:
                                purchase.payed_amount = already_paid + temp_amount
                                temp_amount = 0

                            purchase.save()

                # 4) Insert into PurchasePaymentHistory
                PurchasePaymentHistory.objects.create(
                    party_code    = party_code,
                    party_name    = party_name,
                    date          = final_payment_datetime,
                    totall_amount = 0,
                    payed_amount  = int(final_payed_val),
                    due           = int(new_due),
                    advanced      = int(new_adv),
                    remarks       = (remarks or ('Advance cleared' if clear_advance else ''))[:500],
                )

                # 5) Log into PurchasePayments
                PurchasePayments.objects.create(
                    purchase_number = '',
                    party_code      = party_code,
                    part_name       = party_name,
                    date            = final_payment_datetime,
                    amount          = str(final_payed_val),
                    payment_mood    = payment_mode or 'Cash',
                    remarks         = (remarks or ('Advance cleared' if clear_advance else ''))[:50]
                )

                # 6) CASHRECORD ENTRY (New Row)
                if amount_to_pay > 0:
                    max_cash_id = CashRecord.objects.aggregate(Max("id"))["id__max"]
                    next_cash_id = 1 if max_cash_id is None else max_cash_id + 1

                    cash_description = (
                        remarks or ('Advance cleared' if clear_advance else f'Payment to {party_name}')
                    )[:450]

                    CashRecord.objects.create(
                        id=next_cash_id,
                        cash_in_hand=new_cash_in_hand,
                        cash_in_bank=new_cash_in_bank,
                        date=final_payment_datetime,
                        discription=cash_description,
                    )

            # Success Response
            msg = f"Payment Successful! Party: {party_name} | Paid: {final_payed_val}"
            messages.success(request, msg)
            return redirect('payment')

        except ValueError as e:
            messages.error(request, str(e))
            return redirect('payment')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('payment')

    # ==================================================
    # GET Logic (Latest Entries & Parties List)
    # ==================================================
    history_qs = PurchasePaymentHistory.objects.order_by('party_code', '-id')
    latest_entries = {}
    for row in history_qs:
        if row.party_code and row.party_code not in latest_entries:
            latest_entries[row.party_code] = row

    pending_parties = [
        row for row in latest_entries.values()
        if (row.due and row.due > 0) or (row.advanced and row.advanced > 0)
    ]
    pending_parties.sort(key=lambda x: (x.party_name or '').lower())

    parties_list = []
    for p in Parties.objects.all().order_by('company_name'):
        bal = latest_entries.get(p.code)
        p.balance_due = int(bal.due) if bal and bal.due else 0
        p.balance_adv = int(bal.advanced) if bal and bal.advanced else 0
        parties_list.append(p)

    last_cash = CashRecord.objects.order_by('-id').first()
    cash_in_hand = (
        int(last_cash.cash_in_hand)
        if (last_cash and last_cash.cash_in_hand is not None)
        else 0
    )
    cash_in_bank = (
        int(last_cash.cash_in_bank)
        if (last_cash and last_cash.cash_in_bank is not None)
        else 0
    )

    return render(request, 'payment.html', {
        'parties': parties_list,
        'pending_parties': pending_parties,
        'cash_in_hand': cash_in_hand,
        'cash_in_bank': cash_in_bank,
    })


def waste_payment(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, 'waste_payment.html')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime
from .models import ExpenseHead, Expensedetail

def expenses(request):
    if not request.session.get('user_id'):
        return redirect('login')

    # ============ HANDLE ALL ACTIONS ============
    
    # 1. DELETE EXPENSE
    if request.method == 'POST' and request.POST.get('action') == 'delete':
        try:
            expense_id = request.POST.get('expense_id')
            expense = get_object_or_404(Expensedetail, id=expense_id)
            expense.delete()
            messages.success(request, '🗑️ Expense deleted successfully!')
        except Exception as e:
            messages.error(request, f'❌ Error deleting: {str(e)}')
        return redirect('expenses')

    # 2. UPDATE EXPENSE
    if request.method == 'POST' and request.POST.get('action') == 'update':
        try:
            expense_id = request.POST.get('expense_id')
            head_code = request.POST.get('head_code')
            head_name = request.POST.get('head_name')
            expense_date = request.POST.get('expense_date')
            amount = request.POST.get('amount')
            remarks = request.POST.get('remarks', '')

            expense = get_object_or_404(Expensedetail, id=expense_id)
            expense.head_code = head_code
            expense.head_name = head_name
            expense.date = expense_date if expense_date else timezone.now()
            expense.amount = amount
            expense.remarks = remarks
            expense.save()
            
            messages.success(request, '✏️ Expense updated successfully!')
        except Exception as e:
            messages.error(request, f'❌ Error updating: {str(e)}')
        return redirect('expenses')

    # 3. SAVE NEW EXPENSE
    if request.method == 'POST':
        try:
            head_code = request.POST.get('head_code')
            head_name = request.POST.get('head_name')
            expense_date = request.POST.get('expense_date')
            amount = request.POST.get('amount')
            remarks = request.POST.get('remarks', '')

            if not head_code or not amount:
                messages.error(request, '⚠️ Head and Amount are required!')
                return redirect('expenses')

            Expensedetail.objects.create(
                head_code=head_code,
                head_name=head_name,
                date=expense_date if expense_date else timezone.now(),
                amount=amount,
                remarks=remarks
            )

            messages.success(request, '✅ Expense saved successfully!')
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
            data = {
                'success': True,
                'id': expense.id,
                'head_code': expense.head_code,
                'head_name': expense.head_name,
                'date': expense.date.strftime('%Y-%m-%d') if expense.date else '',
                'amount': expense.amount or '0',
                'remarks': expense.remarks or '',
            }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # 5. GET FILTERED EXPENSES (AJAX)
    if action == 'get_expenses':
        expenses = Expensedetail.objects.all()

        # Apply date filters
        if from_date:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            expenses = expenses.filter(date__date__gte=from_date_obj)
        
        if to_date:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            expenses = expenses.filter(date__date__lte=to_date_obj)

        # Apply head code filter
        if head_code:
            expenses = expenses.filter(head_code__icontains=head_code)

        # Apply search filter
        if search:
            expenses = expenses.filter(
                Q(head_name__icontains=search) |
                Q(head_code__icontains=search) |
                Q(remarks__icontains=search)
            )

        expenses = expenses.order_by('-date')

        # Prepare JSON response
        data = []
        total = 0
        for exp in expenses:
            amount_val = float(exp.amount or 0)
            total += amount_val
            data.append({
                'id': exp.id,
                'date': exp.date.strftime('%d %b %Y') if exp.date else '-',
                'date_str': exp.date.strftime('%Y-%m-%d') if exp.date else '',
                'head_code': exp.head_code or '',
                'head_name': exp.head_name or '',
                'remarks': exp.remarks or '',
                'amount': amount_val,
                'amount_formatted': f'Rs {amount_val:,.2f}',
            })

        return JsonResponse({
            'success': True,
            'data': data,
            'total': total,
            'count': len(data),
            'total_formatted': f'Rs {total:,.2f}'
        })

    # 6. DEFAULT PAGE LOAD
    # Fetch all expense heads for dropdown
    expense_heads = ExpenseHead.objects.all().order_by('name')
    
    # Get today's date
    today = timezone.now().date()
    today_str = today.strftime('%Y-%m-%d')
    
    # Fetch expenses - by default current date
    expenses_list = Expensedetail.objects.filter(
        date__date=today
    ).order_by('-date')
    
    # Calculate total
    total_amount = 0
    for exp in expenses_list:
        try:
            total_amount += float(exp.amount or 0)
        except:
            pass

    context = {
        'expense_heads': expense_heads,
        'expenses': expenses_list,
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