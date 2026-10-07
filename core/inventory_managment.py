from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
import pytz
from .models import PurchaseReceiving, Parties, BroilerRate, PurchasePaymentHistory


def generate_purchase_number():
    last = PurchaseReceiving.objects.order_by('-id').first()
    if last and last.purchase_number:
        try:
            num = int(last.purchase_number.replace('PUR-', ''))
            return f"PUR-{num + 1:05d}"
        except ValueError:
            pass
    return "PUR-00001"


def purchase_receiving(request):
    if not request.session.get('user_id'):
        return redirect('login')

    # ------------------------------------------------------------------
    # AJAX: market rate
    # ------------------------------------------------------------------
    if request.GET.get('action') == 'get_market_rate':
        selected_date = request.GET.get('date')
        broiler = BroilerRate.objects.filter(date=selected_date).first()
        if broiler:
            rate = broiler.rate
        else:
            latest_broiler = BroilerRate.objects.order_by('-date', '-id').first()
            rate = latest_broiler.rate if latest_broiler else ''
        return JsonResponse({'rate': str(rate) if rate else ''})

    # ------------------------------------------------------------------
    # AJAX: party code
    # ------------------------------------------------------------------
    if request.GET.get('action') == 'get_party_code':
        vendor_name = request.GET.get('vendor_name', '').strip()
        if not vendor_name:
            return JsonResponse({'code': ''})
        party = Parties.objects.filter(company_name=vendor_name).first()
        return JsonResponse({
            'code': party.code if party and party.code else ''
        })

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------
    delete_id = request.GET.get('delete_id')
    if delete_id:
        purchase = PurchaseReceiving.objects.filter(id=delete_id).first()
        if purchase:
            old_amount = int(float(purchase.amount or 0))
            PurchasePaymentHistory.objects.filter(
                party_name=purchase.vendor_name,
                totall_amount=old_amount
            ).delete()
            purchase.delete()
            messages.success(request, "Purchase record deleted!")
        return redirect('purchase_receiving')

    # ------------------------------------------------------------------
    # POST
    # ------------------------------------------------------------------
    if request.method == "POST":
        record_id      = request.POST.get('record_id')
        vendor_name    = request.POST.get('vendor_name')
        party_code     = request.POST.get('party_code')
        date_input     = request.POST.get('date')
        vendor_rate    = request.POST.get('vendor_rate') or 0
        market_rate    = request.POST.get('market_rate') or 0
        weight         = request.POST.get('weight') or 0
        vehicle_number = request.POST.get('vehicle_number')
        status         = request.POST.get('status') or 'Active'
        description    = request.POST.get('description') or ''

        if not party_code and vendor_name:
            party_obj = Parties.objects.filter(company_name=vendor_name).first()
            party_code = party_obj.code if party_obj else None

        PK_TZ = pytz.timezone('Asia/Karachi')
        pakistan_time = timezone.now().astimezone(PK_TZ).replace(tzinfo=None)
        if date_input:
            selected_date = datetime.strptime(date_input, '%Y-%m-%d').date()
            final_datetime = datetime.combine(selected_date, pakistan_time.time())
        else:
            final_datetime = pakistan_time

        try:
            vendor_rate = Decimal(str(vendor_rate))
        except (InvalidOperation, ValueError):
            vendor_rate = Decimal('0')
        try:
            market_rate = Decimal(str(market_rate))
        except (InvalidOperation, ValueError):
            market_rate = Decimal('0')
        try:
            weight = Decimal(str(weight))
        except (InvalidOperation, ValueError):
            weight = Decimal('0')

        amount = vendor_rate * weight
        total_amt = int(float(amount))

        # ==========================================================
        # UPDATE
        # ==========================================================
        if record_id:
            purchase = PurchaseReceiving.objects.filter(id=record_id).first()
            if purchase:
                old_amount = int(float(purchase.amount or 0))

                # delete old history row for this purchase
                PurchasePaymentHistory.objects.filter(
                    party_code=party_code,
                    totall_amount=old_amount
                ).delete()

                # previous balance BEFORE this purchase
                last_entry = PurchasePaymentHistory.objects.filter(
                    party_code=party_code
                ).order_by('-id').first()

                prev_due = int(last_entry.due) if last_entry and last_entry.due else 0
                prev_adv = int(last_entry.advanced) if last_entry and last_entry.advanced else 0

                # ---------- APPLY ADVANCE only to purchase_receiving ----------
                if prev_adv > 0:
                    if prev_adv >= total_amt:
                        payed_for_receiving = total_amt
                        new_adv = (prev_adv - total_amt) + prev_due
                        new_due = 0
                    else:
                        payed_for_receiving = prev_adv
                        new_adv = 0
                        new_due = prev_due + (total_amt - prev_adv)
                else:
                    payed_for_receiving = 0
                    new_adv = 0
                    new_due = prev_due + total_amt

                # update receiving row (only here payed is set)
                purchase.vendor_name      = vendor_name
                purchase.vendor_code      = party_code or purchase.vendor_code
                purchase.date             = final_datetime
                purchase.vendor_rate      = vendor_rate
                purchase.market_rate      = market_rate
                if not purchase.remaining_weight:
                    purchase.remaining_weight = str(weight)
                purchase.weight           = weight
                purchase.vehicle_number   = vehicle_number
                purchase.status           = status
                purchase.amount           = str(amount)
                purchase.payed_amount     = str(payed_for_receiving)   # 👈 only here
                purchase.discription      = description
                purchase.save()

                # history row — payed_amount stays 0
                PurchasePaymentHistory.objects.create(
                    party_code    = party_code,
                    party_name    = vendor_name,
                    date          = final_datetime,
                    totall_amount = total_amt,
                    payed_amount  = 0,                # 👈 always 0
                    due           = new_due,
                    advanced      = new_adv,
                    remarks       = description[:500],
                )

                messages.success(request, "Purchase record updated!")

        # ==========================================================
        # CREATE
        # ==========================================================
        else:
            active_purchase = (
                PurchaseReceiving.objects
                .filter(status='Active')
                .order_by('-id')
                .first()
            )

            if active_purchase:
                try:
                    remaining = Decimal(str(active_purchase.remaining_weight or '0'))
                except (InvalidOperation, ValueError):
                    remaining = Decimal('0')

                if remaining > 0:
                    messages.error(
                        request,
                        f"❌ {active_purchase.vendor_name} ki purchase abhi active hai! "
                        f"Remaining: {remaining} kg. Pehle usko complete karo."
                    )
                    return redirect('purchase_receiving')
                else:
                    active_purchase.status = 'Done'
                    active_purchase.save()

            purchase_number = generate_purchase_number()

            # ---------- previous balance BEFORE this purchase ----------
            last_entry = PurchasePaymentHistory.objects.filter(
                party_code=party_code
            ).order_by('-id').first()

            prev_due = int(last_entry.due) if last_entry and last_entry.due else 0
            prev_adv = int(last_entry.advanced) if last_entry and last_entry.advanced else 0

            # ---------- APPLY ADVANCE ----------
            if prev_adv > 0:
                if prev_adv >= total_amt:
                    payed_for_receiving = total_amt
                    new_adv = (prev_adv - total_amt) + prev_due
                    new_due = 0
                else:
                    payed_for_receiving = prev_adv
                    new_adv = 0
                    new_due = prev_due + (total_amt - prev_adv)
            else:
                payed_for_receiving = 0
                new_adv = 0
                new_due = prev_due + total_amt

            PurchaseReceiving.objects.create(
                purchase_number  = purchase_number,
                vendor_code      = party_code,
                vendor_name      = vendor_name,
                date             = final_datetime,
                vendor_rate      = vendor_rate,
                market_rate      = market_rate,
                weight           = weight,
                remaining_weight = str(weight),
                vehicle_number   = vehicle_number,
                status           = status,
                amount           = str(amount),
                payed_amount     = str(payed_for_receiving),   # 👈 only here
                discription      = description,
            )

            # history row — payed_amount stays 0
            PurchasePaymentHistory.objects.create(
                party_code    = party_code,
                party_name    = vendor_name,
                date          = final_datetime,
                totall_amount = total_amt,
                payed_amount  = 0,                # 👈 always 0
                due           = new_due,
                advanced      = new_adv,
                remarks       = description[:500],
            )

            messages.success(request, f"Purchase saved! Number: {purchase_number}")

        return redirect('purchase_receiving')

    # ------------------------------------------------------------------
    # Edit Object
    # ------------------------------------------------------------------
    edit_obj = None
    edit_id = request.GET.get('edit_id')
    if edit_id:
        edit_obj = PurchaseReceiving.objects.filter(id=edit_id).first()

    # Active purchase
    active_purchase = None
    latest_active = (
        PurchaseReceiving.objects
        .filter(status='Active')
        .order_by('-id')
        .first()
    )
    if latest_active:
        try:
            remaining = Decimal(str(latest_active.remaining_weight or '0'))
        except (InvalidOperation, ValueError):
            remaining = Decimal('0')
        if remaining > 0:
            active_purchase = latest_active
        else:
            latest_active.status = 'Done'
            latest_active.save()

    vendor_list = Parties.objects.filter(
        Q(party_type__iexact='vendor') | Q(party_type__iexact='trader')
    ).order_by('company_name')

    history = PurchaseReceiving.objects.all().order_by('-id')
    next_purchase_number = generate_purchase_number()

    pk_tz = pytz.timezone('Asia/Karachi')
    today_pk_date = timezone.now().astimezone(pk_tz).date()

    today_broiler = BroilerRate.objects.filter(date=today_pk_date).first()
    if today_broiler:
        latest_market_rate = today_broiler.rate
    else:
        latest_broiler = BroilerRate.objects.order_by('-date', '-id').first()
        latest_market_rate = latest_broiler.rate if latest_broiler else ''

    context = {
        'edit_obj':             edit_obj,
        'active_purchase':      active_purchase,
        'vendor_list':          vendor_list,
        'history':              history,
        'current_date':         today_pk_date.strftime('%Y-%m-%d'),
        'next_purchase_number': next_purchase_number,
        'latest_market_rate':   latest_market_rate,
    }
    return render(request, 'Inventory_managment/purchase_receiving.html', context)


# ============================================================
# SELLS VIEW
# ============================================================

from decimal import Decimal, InvalidOperation
from datetime import datetime
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone
import pytz

from .models import (
    PurchaseReceiving,
    Parties,
    SellsInvoice,
    Mortality,
    ReceiptHistory,
)


# ------------------------------------------------------------------
# HELPERS (adjust if your file already has them)
# ------------------------------------------------------------------
def sell_decimal(value):
    try:
        return Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def sell_number(value):
    try:
        d = Decimal(str(value or 0))
        if d == d.to_integral_value():
            return str(int(d))
        return str(d.normalize())
    except Exception:
        return '0'


def get_pk_now():
    PK_TZ = pytz.timezone('Asia/Karachi')
    return timezone.now().astimezone(PK_TZ).replace(tzinfo=None)


# ============================================================
# SELLS VIEW
# ============================================================
def sells(request):

    # 1. Login Check
    if not request.session.get('user_id'):
        return redirect('login')

    # Latest PurchaseReceiving record
    active_purchase = (
        PurchaseReceiving.objects
        .order_by('-id')
        .first()
    )

    # ========================================================
    # 2. DELETE SELL
    # ========================================================
    delete_id = request.GET.get('delete_id')
    if delete_id:
        try:
            with transaction.atomic():
                sell_obj = (
                    SellsInvoice.objects
                    .select_for_update()
                    .filter(id=delete_id)
                    .first()
                )

                if not sell_obj:
                    messages.error(request, 'Sell record not found.')
                    return redirect('sells')

                purchase_number = (sell_obj.purchase_number or '').strip()

                purchase_obj = (
                    PurchaseReceiving.objects
                    .select_for_update()
                    .filter(purchase_number=purchase_number)
                    .first()
                )

                if purchase_obj:
                    current_remaining = sell_decimal(purchase_obj.remaining_weight)
                    deleted_weight    = sell_decimal(sell_obj.weight)
                    restored_remaining = current_remaining + deleted_weight

                    purchase_obj.remaining_weight = sell_number(restored_remaining)
                    purchase_obj.save(update_fields=['remaining_weight'])

                sell_obj.delete()

            messages.success(request, 'Sell deleted and stock restored successfully.')

        except Exception as e:
            messages.error(request, f'Delete Error: {str(e)}')

        return redirect('sells')

    # ========================================================
    # 3. MORTALITY POST
    # ========================================================
    if request.method == 'POST' and request.POST.get('action') == 'mortality':
        if not active_purchase:
            messages.error(request, 'No purchase record found.')
            return redirect('sells')

        try:
            with transaction.atomic():
                purchase_obj = (
                    PurchaseReceiving.objects
                    .select_for_update()
                    .filter(id=active_purchase.id)
                    .first()
                )

                if not purchase_obj:
                    raise ValueError('Purchase record not found.')

                remaining = sell_decimal(purchase_obj.remaining_weight)

                if remaining <= 0:
                    raise ValueError(
                        'Mortality can only be entered when remaining stock is greater than 0.'
                    )

                rate   = sell_decimal(purchase_obj.vendor_rate)
                amount = remaining * rate

                pk_now = get_pk_now()

                Mortality.objects.create(
                    purchase_no    = (purchase_obj.purchase_number or ''),
                    vehicle_number = (purchase_obj.vehicle_number or ''),
                    weight         = sell_number(remaining),
                    rate           = sell_number(rate),
                    amount         = sell_number(amount),
                    entry_date     = pk_now.date()
                )

                purchase_obj.remaining_weight = '0'
                purchase_obj.save(update_fields=['remaining_weight'])

            messages.success(request, 'Remaining stock moved to mortality.')

        except Exception as e:
            messages.error(request, str(e))

        return redirect('sells')

    # ========================================================
    # 4. NEW SELL POST
    # ========================================================
    if request.method == 'POST':
        customer_name = (request.POST.get('customer_name') or '').strip()
        vehicle_no    = (request.POST.get('vehicle_no') or '').strip()
        sell_weight   = sell_decimal(request.POST.get('weight'))
        sell_rate     = sell_decimal(request.POST.get('rate'))

        if not customer_name:
            messages.error(request, 'Please select Customer / Trader.')
            return redirect('sells')

        if sell_weight <= 0:
            messages.error(request, 'Sell weight must be greater than 0.')
            return redirect('sells')

        if sell_rate <= 0:
            messages.error(request, 'Rate must be greater than 0.')
            return redirect('sells')

        if not active_purchase:
            messages.error(request, 'Please create a Purchase Receiving record first.')
            return redirect('sells')

        try:
            with transaction.atomic():
                purchase_obj = (
                    PurchaseReceiving.objects
                    .select_for_update()
                    .filter(id=active_purchase.id)
                    .first()
                )

                if not purchase_obj:
                    raise ValueError('Purchase record not found.')

                latest_purchase = (
                    PurchaseReceiving.objects
                    .order_by('-id')
                    .first()
                )

                if latest_purchase and latest_purchase.id != purchase_obj.id:
                    raise ValueError(
                        'A new purchase has been received. '
                        'Page refresh karke sell dobara enter karein.'
                    )

                purchase_number = (purchase_obj.purchase_number or '').strip()
                if not purchase_number:
                    raise ValueError('Current purchase number is missing.')

                old_remaining     = sell_decimal(purchase_obj.remaining_weight)
                new_remaining     = old_remaining - sell_weight
                calculated_amount = sell_weight * sell_rate

                # ---------------- Generate Sell Number ----------------
                last_sell   = SellsInvoice.objects.order_by('-id').first()
                next_number = 1

                if last_sell and last_sell.sells_no:
                    try:
                        next_number = int(last_sell.sells_no) + 1
                    except (ValueError, TypeError):
                        next_number = (last_sell.id or 0) + 1

                sells_no = str(next_number).zfill(4)

                pk_now = get_pk_now()

                # =================================================
                # INSERT SELL RECORD
                # =================================================
                SellsInvoice.objects.create(
                    sells_no         = sells_no,
                    purchase_number  = purchase_number,
                    customer_name    = customer_name,
                    weight           = sell_number(sell_weight),
                    rate             = sell_number(sell_rate),
                    amount           = sell_number(calculated_amount),
                    received_amount  = '0',
                    remaining_amount = sell_number(calculated_amount),
                    vehicle_no       = (vehicle_no or purchase_obj.vehicle_number or ''),
                    entry_date       = pk_now
                )

                # =================================================
                # UPDATE PURCHASE REMAINING
                # =================================================
                purchase_obj.remaining_weight = sell_number(new_remaining)
                purchase_obj.save(update_fields=['remaining_weight'])

                # =================================================
                # 💰 INSERT INTO receipt_history
                # =================================================
                # Party code / name
                party_obj = Parties.objects.filter(
                    company_name=customer_name
                ).first()
                if not party_obj:
                    party_obj = Parties.objects.filter(
                        owner_name=customer_name
                    ).first()
                party_code = party_obj.code if party_obj else ''

                # Get last entry for this party → carry forward due/advance
                last_receipt = (
                    ReceiptHistory.objects
                    .filter(part_code=party_code)
                    .order_by('-id')
                    .first()
                )

                prev_due = int(last_receipt.due)     if last_receipt and last_receipt.due     else 0
                prev_adv = int(last_receipt.advance) if last_receipt and last_receipt.advance else 0

                # New sell adds to the party's outstanding balance
                net = (prev_due - prev_adv) + int(calculated_amount)

                if net >= 0:
                    new_due, new_adv = net, 0
                else:
                    new_due, new_adv = 0, abs(net)

                ReceiptHistory.objects.create(
                    party_name      = customer_name,
                    part_code       = party_code,
                    amount          = int(calculated_amount),   # 👈 sell amount
                    received_amount = '0',                       # not received yet
                    payment_method  = None,                      # not applicable
                    date            = pk_now,                    # current date/time
                    due             = new_due,
                    advance         = new_adv,
                )

            messages.success(
                request,
                f'Sell #{sells_no} saved | '
                f'Purchase #{purchase_number} | '
                f'Old Stock: {sell_number(old_remaining)} kg | '
                f'Sold: {sell_number(sell_weight)} kg | '
                f'New Stock: {sell_number(new_remaining)} kg'
            )

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

        return redirect('sells')

    # ========================================================
    # 5. GET DATA FOR DISPLAY
    # ========================================================
    customer_list = (
        Parties.objects
        .filter(
            Q(party_type__iexact='customer')
            | Q(party_type__iexact='trader')
        )
        .order_by('company_name')
    )

    history = SellsInvoice.objects.all().order_by('-id')

    for item in history:
        amount = sell_decimal(item.amount)
        if not item.amount:
            amount = sell_decimal(item.weight) * sell_decimal(item.rate)
        item.total_display = sell_number(amount)

    if active_purchase:
        current_remaining = sell_decimal(active_purchase.remaining_weight)
        available_stock   = sell_number(current_remaining)
        auto_vehicle      = active_purchase.vehicle_number or ''
        stock_negative    = (current_remaining < 0)
        stock_zero        = (current_remaining == 0)
    else:
        available_stock = '0'
        auto_vehicle    = ''
        stock_negative  = False
        stock_zero      = True

    pk_now = get_pk_now()

    context = {
        'active_purchase':      active_purchase,
        'customer_list':        customer_list,
        'history':              history,
        'available_stock':      available_stock,
        'auto_vehicle':         auto_vehicle,
        'stock_negative':       stock_negative,
        'stock_zero':           stock_zero,
        'current_date':         pk_now.strftime('%Y-%m-%d'),
        'current_date_display': pk_now.strftime('%d-%m-%Y'),
    }

    return render(
        request,
        'Inventory_managment/sells.html',
        context
    )








