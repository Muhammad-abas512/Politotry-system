from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db import transaction
import pytz
from .models import (
    PurchaseReceiving, Parties, BroilerRate, PurchasePaymentHistory,
    ChartOfAccount, Voucher, VoucherDetail, SellsInvoice,
    Mortality, ReceiptHistory
)
from .accounts_views import sync_single_party_to_coa, _update_account_balance


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


def sync_purchase_voucher(purchase, is_delete=False):
    """
    Synchronizes a PurchaseReceiving entry to a Double-Entry Accounting Voucher:
    Debit: Broiler Purchases (5110001)
    Credit: Party Level 4 Account (1120000X)
    """
    try:
        voucher_no = f"PUR-{purchase.purchase_number}"
        existing_v = Voucher.objects.filter(voucher_no=voucher_no).first()

        if existing_v:
            for line in existing_v.details.all():
                _update_account_balance(line.account, line.credit, line.debit)
            existing_v.delete()

        if is_delete:
            return

        party_obj = None
        if purchase.vendor_code:
            party_obj = Parties.objects.filter(code=purchase.vendor_code).first()
        if not party_obj and purchase.vendor_name:
            party_obj = (
                Parties.objects.filter(company_name=purchase.vendor_name).first()
                or Parties.objects.filter(owner_name=purchase.vendor_name).first()
            )

        if not party_obj:
            return

        party_acc = sync_single_party_to_coa(party_obj)
        pur_acc = ChartOfAccount.objects.filter(code__in=['050101001', '5110001'], level=4).first()
        if not pur_acc:
            pur_acc = ChartOfAccount.objects.filter(level=4, name__icontains='Broiler Purchase').first()

        pur_amt = Decimal(str(purchase.amount or 0))
        if pur_amt <= 0 or not party_acc or not pur_acc:
            return

        v_date = purchase.date.date() if purchase.date else timezone.localdate()
        rem = f"Purchase #{purchase.purchase_number} - {purchase.vendor_name} ({purchase.weight}kg @ Rs. {purchase.vendor_rate})"
        if purchase.discription:
            rem += f" - {purchase.discription}"

        v = Voucher.objects.create(
            voucher_no=voucher_no,
            voucher_type='JV',
            date=v_date,
            reference_no=purchase.vehicle_number or '',
            total_amount=pur_amt,
            remarks=rem[:450],
            created_by='System / Purchase'
        )

        # Debit: Broiler Purchases
        VoucherDetail.objects.create(
            voucher=v,
            account=pur_acc,
            debit=pur_amt,
            credit=Decimal('0'),
            narration=f"Purchase #{purchase.purchase_number}: {purchase.weight}kg @ {purchase.vendor_rate}"
        )
        _update_account_balance(pur_acc, pur_amt, Decimal('0'))

        # Credit: Party Account
        VoucherDetail.objects.create(
            voucher=v,
            account=party_acc,
            debit=Decimal('0'),
            credit=pur_amt,
            party=party_obj,
            narration=f"Purchase Bill #{purchase.purchase_number}"
        )
        _update_account_balance(party_acc, Decimal('0'), pur_amt)

    except Exception as e:
        print(f"Error syncing purchase voucher: {e}")


def sync_sell_voucher(sell_obj, is_delete=False):
    """
    Synchronizes a SellsInvoice entry to a Double-Entry Accounting Voucher:
    Debit: Party Level 4 Account (1120000X)
    Credit: Broiler Sales (4110001)
    """
    try:
        voucher_no = f"SLS-{sell_obj.sells_no}"
        existing_v = Voucher.objects.filter(voucher_no=voucher_no).first()

        if existing_v:
            for line in existing_v.details.all():
                _update_account_balance(line.account, line.credit, line.debit)
            existing_v.delete()

        if is_delete:
            return

        party_obj = None
        if sell_obj.customer_code:
            party_obj = Parties.objects.filter(code=sell_obj.customer_code).first()
        if not party_obj and sell_obj.customer_name:
            party_obj = (
                Parties.objects.filter(company_name=sell_obj.customer_name).first()
                or Parties.objects.filter(owner_name=sell_obj.customer_name).first()
            )

        if not party_obj:
            return

        party_acc = sync_single_party_to_coa(party_obj)
        sales_acc = ChartOfAccount.objects.filter(code__in=['040101001', '4110001'], level=4).first()
        if not sales_acc:
            sales_acc = ChartOfAccount.objects.filter(level=4, name__icontains='Broiler Sales').first()

        sell_amt = Decimal(str(sell_obj.amount or 0))
        if sell_amt <= 0 or not party_acc or not sales_acc:
            return

        v_date = sell_obj.entry_date.date() if sell_obj.entry_date else timezone.localdate()
        rem = f"Sale #{sell_obj.sells_no} on Pur #{sell_obj.purchase_number} - {sell_obj.customer_name} ({sell_obj.weight}kg @ Rs. {sell_obj.rate})"

        v = Voucher.objects.create(
            voucher_no=voucher_no,
            voucher_type='JV',
            date=v_date,
            reference_no=sell_obj.vehicle_no or '',
            total_amount=sell_amt,
            remarks=rem[:450],
            created_by='System / Sell'
        )

        # Debit: Party Account
        VoucherDetail.objects.create(
            voucher=v,
            account=party_acc,
            debit=sell_amt,
            credit=Decimal('0'),
            party=party_obj,
            narration=f"Sale Invoice #{sell_obj.sells_no}: {sell_obj.weight}kg @ {sell_obj.rate}"
        )
        _update_account_balance(party_acc, sell_amt, Decimal('0'))

        # Credit: Broiler Sales
        VoucherDetail.objects.create(
            voucher=v,
            account=sales_acc,
            debit=Decimal('0'),
            credit=sell_amt,
            narration=f"Broiler Sale #{sell_obj.sells_no}"
        )
        _update_account_balance(sales_acc, Decimal('0'), sell_amt)

    except Exception as e:
        print(f"Error syncing sell voucher: {e}")


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
            has_sales = SellsInvoice.objects.filter(purchase_number=purchase.purchase_number).exists()
            has_mortality = Mortality.objects.filter(purchase_no=purchase.purchase_number).exists()
            rem = sell_decimal(purchase.remaining_weight)
            orig_w = sell_decimal(purchase.weight)
            if has_sales or has_mortality or rem < orig_w:
                messages.error(
                    request,
                    f"❌ Purchase #{purchase.purchase_number} delete nahi ho sakti kyunke isme se sale ya deduction ho chuki hai! (Purchase Locked)"
                )
                return redirect('purchase_receiving')

            old_amount = int(float(purchase.amount or 0))
            PurchasePaymentHistory.objects.filter(
                party_name=purchase.vendor_name,
                totall_amount=old_amount
            ).delete()
            sync_purchase_voucher(purchase, is_delete=True)
            purchase.delete()
            messages.success(request, f"Purchase #{purchase.purchase_number} deleted successfully!")
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
                # 1. Mortality check: if mortality is entered, purchase cannot be edited
                has_mortality = Mortality.objects.filter(purchase_no=purchase.purchase_number).exists()
                if has_mortality:
                    messages.error(
                        request,
                        f"❌ Purchase #{purchase.purchase_number} edit nahi ho sakti kyunke iski mortality dali ja chuki hai!"
                    )
                    return redirect('purchase_receiving')

                # 2. Remaining stock check: if remaining stock <= 0 (e.g. 500/500 sold), cannot edit
                curr_rem = sell_decimal(purchase.remaining_weight)
                if curr_rem <= 0:
                    messages.error(
                        request,
                        f"❌ Purchase #{purchase.purchase_number} edit nahi ho sakti kyunke iska stock mukammal sell ho chuka hai (Remaining: {curr_rem} kg)!"
                    )
                    return redirect('purchase_receiving')

                # 3. Calculate already sold weight from sales invoices
                sales_qs = SellsInvoice.objects.filter(purchase_number=purchase.purchase_number)
                sold_weight = sum(sell_decimal(s.weight) for s in sales_qs)

                # 4. Check if new weight entered is greater than already sold weight
                if sold_weight > 0 and weight <= sold_weight:
                    messages.error(
                        request,
                        f"❌ Purchase weight ({sell_number(weight)} kg) pehle se sold weight ({sell_number(sold_weight)} kg) se zyada hona zaroori hai!"
                    )
                    return redirect(f"{request.path}?edit_id={purchase.id}")

                new_remaining = weight - sold_weight
                new_status = 'Active' if new_remaining > 0 else 'Done'

                old_amount = int(float(purchase.amount or 0))
                old_vendor_name = purchase.vendor_name
                old_vendor_code = purchase.vendor_code
                old_vehicle = purchase.vehicle_number
                old_date = purchase.date

                # Delete old history row
                PurchasePaymentHistory.objects.filter(
                    Q(remarks__icontains=purchase.purchase_number) |
                    Q(party_code=old_vendor_code or party_code, totall_amount=old_amount)
                ).delete()

                # Previous balance BEFORE this purchase
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

                # Update purchase record
                purchase.vendor_name      = vendor_name
                purchase.vendor_code      = party_code or purchase.vendor_code
                purchase.date             = final_datetime
                purchase.vendor_rate      = vendor_rate
                purchase.market_rate      = market_rate
                purchase.weight           = weight
                purchase.remaining_weight = sell_number(new_remaining)
                purchase.vehicle_number   = vehicle_number
                purchase.status           = new_status
                purchase.amount           = str(amount)
                purchase.payed_amount     = str(payed_for_receiving)
                purchase.discription      = description
                purchase.save()

                # Re-sync double entry purchase voucher
                sync_purchase_voucher(purchase)

                # Re-sync associated sales if date or vehicle changed
                if sales_qs.exists():
                    if old_date and final_datetime.date() != old_date.date():
                        for s in sales_qs:
                            s_time = s.entry_date.time() if s.entry_date else final_datetime.time()
                            s.entry_date = datetime.combine(final_datetime.date(), s_time)
                            s.save(update_fields=['entry_date'])
                            sync_sell_voucher(s)

                    if vehicle_number and vehicle_number != old_vehicle:
                        sales_qs.filter(
                            Q(vehicle_no=old_vehicle) | Q(vehicle_no__isnull=True) | Q(vehicle_no='')
                        ).update(vehicle_no=vehicle_number)

                # Re-create history row
                PurchasePaymentHistory.objects.create(
                    party_code    = party_code,
                    party_name    = vendor_name,
                    date          = final_datetime,
                    totall_amount = total_amt,
                    payed_amount  = 0,
                    due           = new_due,
                    advanced      = new_adv,
                    remarks       = f"Purchase #{purchase.purchase_number}: {description[:400]}" if description else f"Purchase #{purchase.purchase_number}",
                )

                messages.success(
                    request,
                    f"✅ Purchase #{purchase.purchase_number} updated successfully! "
                    f"New Weight: {sell_number(weight)} kg | Sold: {sell_number(sold_weight)} kg | Remaining: {sell_number(new_remaining)} kg | Rate: Rs. {vendor_rate}"
                )

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

            new_pur = PurchaseReceiving.objects.create(
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
            sync_purchase_voucher(new_pur)

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
    edit_sold_weight = Decimal('0')
    edit_id = request.GET.get('edit_id')
    if edit_id:
        edit_obj = PurchaseReceiving.objects.filter(id=edit_id).first()
        if edit_obj:
            has_mortality = Mortality.objects.filter(purchase_no=edit_obj.purchase_number).exists()
            rem = sell_decimal(edit_obj.remaining_weight)

            if has_mortality:
                messages.error(
                    request,
                    f"❌ Purchase #{edit_obj.purchase_number} edit nahi ho sakti kyunke iski mortality dali ja chuki hai!"
                )
                return redirect('purchase_receiving')

            if rem <= 0:
                messages.error(
                    request,
                    f"❌ Purchase #{edit_obj.purchase_number} edit nahi ho sakti kyunke iska stock mukammal (500/500 ya zyada) sell ho chuka hai (Remaining: {rem} kg)!"
                )
                return redirect('purchase_receiving')

            sales_qs = SellsInvoice.objects.filter(purchase_number=edit_obj.purchase_number)
            edit_sold_weight = sum(sell_decimal(s.weight) for s in sales_qs)

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

    vendor_list = Parties.objects.all().order_by('company_name')

    history = PurchaseReceiving.objects.all().order_by('-id')
    mortality_pur_numbers = set(
        Mortality.objects.values_list('purchase_no', flat=True).distinct()
    )

    # Pre-calculate sales weight per purchase number
    sales_qs = SellsInvoice.objects.exclude(purchase_number__isnull=True).exclude(purchase_number='').values('purchase_number', 'weight')
    sales_by_pur = {}
    for s in sales_qs:
        p_no = (s['purchase_number'] or '').strip()
        sales_by_pur[p_no] = sales_by_pur.get(p_no, Decimal('0')) + sell_decimal(s['weight'])

    for item in history:
        try:
            w = Decimal(str(item.weight or '0'))
            rem = Decimal(str(item.remaining_weight or '0'))
        except Exception:
            w, rem = Decimal('0'), Decimal('0')

        p_no = (item.purchase_number or '').strip()
        sold_w = sales_by_pur.get(p_no, max(Decimal('0'), w - rem))
        has_mort = (p_no in mortality_pur_numbers)

        item.has_mortality = has_mort
        item.sold_weight = sell_number(sold_w)
        item.sold_weight_num = sold_w

        # User rules:
        # 1. Mortality entered -> cannot edit
        # 2. Remaining stock <= 0 (e.g. 500/500 sold) -> cannot edit
        # 3. As long as remaining stock > 0 and no mortality -> CAN EDIT!
        item.can_edit = (not has_mort) and (rem > 0)
        item.is_locked = not item.can_edit

        # Cannot delete if sales or mortality exist
        item.can_delete = (not has_mort) and (sold_w == 0) and (rem >= w)

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
        'edit_sold_weight':     sell_number(edit_sold_weight),
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
def sells(request):

    # 1. Login Check
    if not request.session.get('user_id'):
        return redirect('login')

    # Edit sell object if edit_id is passed in GET
    edit_sell = None
    edit_id = request.GET.get('edit_id')
    if edit_id:
        edit_sell = SellsInvoice.objects.filter(id=edit_id).first()

    # Active purchase: default to the latest purchase, or the one associated with the sell being edited
    active_purchase = None
    if edit_sell and edit_sell.purchase_number:
        active_purchase = PurchaseReceiving.objects.filter(purchase_number=edit_sell.purchase_number).first()

    if not active_purchase:
        selected_pur_id = request.GET.get('purchase_id')
        if selected_pur_id:
            active_purchase = PurchaseReceiving.objects.filter(id=selected_pur_id).first()

    if not active_purchase:
        # First preference: Latest active purchase with remaining_weight > 0
        all_candidates = PurchaseReceiving.objects.order_by('-date', '-id')
        for c in all_candidates:
            if sell_decimal(c.remaining_weight) > 0 and c.status == 'Active':
                active_purchase = c
                break

    if not active_purchase:
        # Second preference: Any purchase with remaining_weight > 0
        all_candidates = PurchaseReceiving.objects.order_by('-date', '-id')
        for c in all_candidates:
            if sell_decimal(c.remaining_weight) > 0:
                active_purchase = c
                break

    if not active_purchase:
        active_purchase = (
            PurchaseReceiving.objects
            .order_by('-date', '-id')
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

                sync_sell_voucher(sell_obj, is_delete=True)

                if sell_obj.customer_code:
                    old_amt = int(float(sell_obj.amount or 0))
                    ReceiptHistory.objects.filter(
                        part_code=sell_obj.customer_code,
                        amount=old_amt,
                        received_amount='0'
                    ).delete()

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
    # 4. SELL POST (NEW OR EDIT)
    # ========================================================
    if request.method == 'POST':
        sell_id          = request.POST.get('sell_id')
        customer_name    = (request.POST.get('customer_name') or '').strip()
        vehicle_no       = (request.POST.get('vehicle_no') or '').strip()
        sell_weight      = sell_decimal(request.POST.get('weight'))
        sell_rate        = sell_decimal(request.POST.get('rate'))
        date_input       = (request.POST.get('date') or '').strip()
        purchase_id_post = request.POST.get('purchase_id')

        if not customer_name:
            messages.error(request, 'Please select Customer / Party.')
            return redirect('sells')

        if sell_weight <= 0:
            messages.error(request, 'Sell weight must be greater than 0.')
            return redirect('sells')

        if sell_rate <= 0:
            messages.error(request, 'Rate must be greater than 0.')
            return redirect('sells')

        # ----------------------------------------------------
        # EDIT / UPDATE EXISTING SELL
        # ----------------------------------------------------
        if sell_id:
            try:
                with transaction.atomic():
                    sell_obj = (
                        SellsInvoice.objects
                        .select_for_update()
                        .filter(id=sell_id)
                        .first()
                    )
                    if not sell_obj:
                        raise ValueError('Sell record not found.')

                    purchase_number = (sell_obj.purchase_number or '').strip()
                    purchase_obj = (
                        PurchaseReceiving.objects
                        .select_for_update()
                        .filter(purchase_number=purchase_number)
                        .first()
                    )
                    if not purchase_obj:
                        raise ValueError('Associated purchase record not found.')

                    old_sell_weight   = sell_decimal(sell_obj.weight)
                    old_sell_amount   = sell_decimal(sell_obj.amount)
                    old_customer_code = sell_obj.customer_code

                    # Date check: Sell date must match purchase date
                    purchase_date = purchase_obj.date.date() if purchase_obj.date else None
                    pk_now = get_pk_now()

                    if date_input:
                        try:
                            sell_date = datetime.strptime(date_input, '%Y-%m-%d').date()
                        except ValueError:
                            sell_date = purchase_date or pk_now.date()
                    else:
                        sell_date = purchase_date or pk_now.date()

                    if purchase_date and sell_date != purchase_date:
                        raise ValueError(
                            f"Ghalat Date! Jo purchase jis date ko purchase ho wo usi date me hi sell ho sakti hai! "
                            f"Purchase #{purchase_obj.purchase_number} ki purchase date {purchase_date.strftime('%d-%m-%Y')} hai, "
                            f"magar sell date {sell_date.strftime('%d-%m-%Y')} select ki gayi hai."
                        )

                    # Stock restoration + deduction
                    current_remaining = sell_decimal(purchase_obj.remaining_weight)
                    restored_stock    = current_remaining + old_sell_weight
                    new_remaining     = restored_stock - sell_weight
                    calculated_amount = sell_weight * sell_rate

                    # Update purchase remaining stock
                    purchase_obj.remaining_weight = sell_number(new_remaining)
                    purchase_obj.save(update_fields=['remaining_weight'])

                    # Resolve customer party
                    party_obj = Parties.objects.filter(
                        company_name=customer_name
                    ).first()
                    if not party_obj:
                        party_obj = Parties.objects.filter(
                            owner_name=customer_name
                        ).first()
                    party_code = party_obj.code if party_obj else ''

                    final_sell_datetime = datetime.combine(purchase_date or sell_date, pk_now.time())

                    # Update sell record
                    sell_obj.customer_name    = customer_name
                    sell_obj.customer_code    = party_code
                    sell_obj.weight           = sell_number(sell_weight)
                    sell_obj.rate             = sell_number(sell_rate)
                    sell_obj.amount           = sell_number(calculated_amount)
                    sell_obj.remaining_amount = sell_number(calculated_amount)
                    sell_obj.vehicle_no       = (vehicle_no or purchase_obj.vehicle_number or '')
                    sell_obj.entry_date       = final_sell_datetime
                    sell_obj.save()

                    # Re-sync double entry voucher
                    sync_sell_voucher(sell_obj)

                    # Update ReceiptHistory
                    if old_customer_code:
                        ReceiptHistory.objects.filter(
                            part_code=old_customer_code,
                            amount=int(old_sell_amount),
                            received_amount='0'
                        ).delete()

                    last_receipt = (
                        ReceiptHistory.objects
                        .filter(part_code=party_code)
                        .order_by('-id')
                        .first()
                    )
                    prev_due = int(last_receipt.due)     if last_receipt and last_receipt.due     else 0
                    prev_adv = int(last_receipt.advance) if last_receipt and last_receipt.advance else 0

                    net = (prev_due - prev_adv) + int(calculated_amount)
                    if net >= 0:
                        new_due, new_adv = net, 0
                    else:
                        new_due, new_adv = 0, abs(net)

                    ReceiptHistory.objects.create(
                        party_name      = customer_name,
                        part_code       = party_code,
                        amount          = int(calculated_amount),
                        received_amount = '0',
                        payment_method  = None,
                        date            = final_sell_datetime,
                        due             = new_due,
                        advance         = new_adv,
                    )

                messages.success(
                    request,
                    f'✅ Sell #{sell_obj.sells_no} updated! '
                    f'Purchase #{purchase_number} | '
                    f'Previous: {sell_number(old_sell_weight)} kg | '
                    f'New: {sell_number(sell_weight)} kg | '
                    f'New Stock: {sell_number(new_remaining)} kg'
                )

            except Exception as e:
                messages.error(request, f'Update Error: {str(e)}')

            return redirect('sells')

        # ----------------------------------------------------
        # NEW SELL
        # ----------------------------------------------------
        target_purchase_id = purchase_id_post or (active_purchase.id if active_purchase else None)
        if not target_purchase_id:
            messages.error(request, 'Please create a Purchase Receiving record first.')
            return redirect('sells')

        try:
            with transaction.atomic():
                purchase_obj = (
                    PurchaseReceiving.objects
                    .select_for_update()
                    .filter(id=target_purchase_id)
                    .first()
                )

                if not purchase_obj:
                    raise ValueError('Purchase record not found.')

                # 🛑 CRITICAL CONSTRAINT: Purchase date == Sale date
                purchase_date = purchase_obj.date.date() if purchase_obj.date else None
                pk_now = get_pk_now()

                if date_input:
                    try:
                        sell_date = datetime.strptime(date_input, '%Y-%m-%d').date()
                    except ValueError:
                        sell_date = purchase_date or pk_now.date()
                else:
                    sell_date = purchase_date or pk_now.date()

                if purchase_date and sell_date != purchase_date:
                    raise ValueError(
                        f"Ghalat Date! Jo purchase jis date ko purchase ho wo usi date me hi sell ho sakti hai! "
                        f"Purchase #{purchase_obj.purchase_number} ki purchase date {purchase_date.strftime('%d-%m-%Y')} hai, "
                        f"magar sell date {sell_date.strftime('%d-%m-%Y')} select ki gayi hai."
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

                final_sell_datetime = datetime.combine(purchase_date or sell_date, pk_now.time())

                # Resolve party code & object
                party_obj = Parties.objects.filter(
                    company_name=customer_name
                ).first()
                if not party_obj:
                    party_obj = Parties.objects.filter(
                        owner_name=customer_name
                    ).first()
                party_code = party_obj.code if party_obj else ''

                # =================================================
                # INSERT SELL RECORD
                # =================================================
                new_sell = SellsInvoice.objects.create(
                    sells_no         = sells_no,
                    purchase_number  = purchase_number,
                    customer_name    = customer_name,
                    customer_code    = party_code,
                    weight           = sell_number(sell_weight),
                    rate             = sell_number(sell_rate),
                    amount           = sell_number(calculated_amount),
                    received_amount  = '0',
                    remaining_amount = sell_number(calculated_amount),
                    vehicle_no       = (vehicle_no or purchase_obj.vehicle_number or ''),
                    entry_date       = final_sell_datetime
                )
                sync_sell_voucher(new_sell)

                # =================================================
                # UPDATE PURCHASE REMAINING
                # =================================================
                purchase_obj.remaining_weight = sell_number(new_remaining)
                purchase_obj.save(update_fields=['remaining_weight'])

                # =================================================
                # 💰 INSERT INTO receipt_history
                # =================================================
                last_receipt = (
                    ReceiptHistory.objects
                    .filter(part_code=party_code)
                    .order_by('-id')
                    .first()
                )

                prev_due = int(last_receipt.due)     if last_receipt and last_receipt.due     else 0
                prev_adv = int(last_receipt.advance) if last_receipt and last_receipt.advance else 0

                net = (prev_due - prev_adv) + int(calculated_amount)

                if net >= 0:
                    new_due, new_adv = net, 0
                else:
                    new_due, new_adv = 0, abs(net)

                ReceiptHistory.objects.create(
                    party_name      = customer_name,
                    part_code       = party_code,
                    amount          = int(calculated_amount),
                    received_amount = '0',
                    payment_method  = None,
                    date            = final_sell_datetime,
                    due             = new_due,
                    advance         = new_adv,
                )

            messages.success(
                request,
                f'Sell #{sells_no} saved | '
                f'Purchase #{purchase_number} | '
                f'Date: {purchase_date.strftime("%d-%m-%Y") if purchase_date else ""} | '
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
    customer_list = Parties.objects.all().order_by('company_name')

    history = SellsInvoice.objects.all().order_by('-id')

    for item in history:
        amount = sell_decimal(item.amount)
        if not item.amount:
            amount = sell_decimal(item.weight) * sell_decimal(item.rate)
        item.total_display = sell_number(amount)

    all_active = PurchaseReceiving.objects.filter(Q(status='Active') | Q(status__isnull=True)).order_by('-date', '-id')[:25]
    active_purchases_list = [p for p in all_active if sell_decimal(p.remaining_weight) > 0]
    if not active_purchases_list:
        active_purchases_list = list(PurchaseReceiving.objects.order_by('-date', '-id')[:10])

    if active_purchase:
        current_remaining = sell_decimal(active_purchase.remaining_weight)
        # If currently editing a sell belonging to this purchase, the sell's current weight is also available to edit
        if edit_sell and edit_sell.purchase_number == active_purchase.purchase_number:
            effective_stock = current_remaining + sell_decimal(edit_sell.weight)
            available_stock = sell_number(effective_stock)
        else:
            available_stock = sell_number(current_remaining)

        auto_vehicle          = active_purchase.vehicle_number or ''
        stock_negative        = (current_remaining < 0)
        stock_zero            = (current_remaining <= 0)
        purchase_date_str     = active_purchase.date.strftime('%Y-%m-%d') if active_purchase.date else ''
        purchase_date_display = active_purchase.date.strftime('%d-%m-%Y') if active_purchase.date else ''
    else:
        available_stock       = '0'
        auto_vehicle          = ''
        stock_negative        = False
        stock_zero            = True
        purchase_date_str     = ''
        purchase_date_display = ''

    pk_now = get_pk_now()

    context = {
        'edit_sell':             edit_sell,
        'active_purchase':       active_purchase,
        'active_purchases_list': active_purchases_list,
        'customer_list':         customer_list,
        'history':               history,
        'available_stock':       available_stock,
        'auto_vehicle':          auto_vehicle,
        'stock_negative':        stock_negative,
        'stock_zero':            stock_zero,
        'current_date':          pk_now.strftime('%Y-%m-%d'),
        'current_date_display':  pk_now.strftime('%d-%m-%Y'),
        'purchase_date_str':     purchase_date_str,
        'purchase_date_display': purchase_date_display,
    }

    return render(
        request,
        'Inventory_managment/sells.html',
        context
    )








