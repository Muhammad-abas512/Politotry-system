from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Q, Max
from django.db import transaction
from django.utils import timezone
from datetime import datetime, date, time
from decimal import Decimal, InvalidOperation
import pytz

from .models import (
    PurchaseReceiving,
    PurchasePayments,
    PurchasePaymentHistory,
    Parties,
    ReceiptHistory,
    SellsInvoice,
    Sellspayment,
    CashRecord,
    ChartOfAccount,
    Voucher,
    VoucherDetail,
)
from .accounts_views import (
    sync_single_party_to_coa,
    generate_voucher_no,
    _update_account_balance,
    _get_pk_now,
)
from .inventory_managment import (
    sync_purchase_voucher,
    sync_sell_voucher,
)


def _to_decimal(val, default='0'):
    try:
        if val is None or str(val).strip() == '':
            return Decimal(default)
        return Decimal(str(val).strip().replace(',', ''))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def _next_op_pur_no():
    last = PurchaseReceiving.objects.filter(purchase_number__startswith='OP-PUR-').order_by('-id').first()
    if last and last.purchase_number:
        try:
            num = int(last.purchase_number.replace('OP-PUR-', ''))
            return f"OP-PUR-{num + 1:04d}"
        except (ValueError, TypeError):
            pass
    return "OP-PUR-0001"


def _next_op_sls_no():
    last = SellsInvoice.objects.filter(sells_no__startswith='OP-SLS-').order_by('-id').first()
    if last and last.sells_no:
        try:
            num = int(last.sells_no.replace('OP-SLS-', ''))
            return f"OP-SLS-{num + 1:04d}"
        except (ValueError, TypeError):
            pass
    return "OP-SLS-0001"


def _sync_opening_cash_record(net_hand, net_bank, description, entry_datetime):
    if net_hand == 0 and net_bank == 0:
        return None
    latest = CashRecord.objects.order_by('-date', '-id').first()
    prev_hand = int(latest.cash_in_hand or 0) if latest else 0
    prev_bank = int(latest.cash_in_bank or 0) if latest else 0
    new_hand = prev_hand + int(net_hand)
    new_bank = prev_bank + int(net_bank)
    max_id = CashRecord.objects.aggregate(Max('id'))['id__max']
    next_id = 1 if max_id is None else max_id + 1
    return CashRecord.objects.create(
        id=next_id,
        cash_in_hand=new_hand,
        cash_in_bank=new_bank,
        date=entry_datetime,
        discription=description[:450],
    )


# ===================================================================
# 1. PARTY OPENING TRANSACTIONS & BALANCES
# ===================================================================
def opening(request):
    """
    Four Distinct Opening Transaction Types:
    1. 'purchase' (خریداری):
       - Creates PurchaseReceiving ('OP-PUR-XXXX')
       - Appears in Purchase Report & Party Ledger
       - Does NOT appear in Cash Ledger or Daily Cash Report
    2. 'sale' (فروخت):
       - Creates SellsInvoice ('OP-SLS-XXXX')
       - Appears in Sells Report & Party Ledger
       - Does NOT appear in Cash Ledger or Daily Cash Report
    3. 'payment' (پیسے دیے / ادا کیے):
       - Creates CPV/BPV Voucher + CashRecord + PurchasePayments
       - Appears in Cash Ledger, Daily Cash Report, and Party Ledger
    4. 'receipt' (پیسے لیے / وصول کیے):
       - Creates CRV/BRV Voucher + CashRecord + Sellspayment
       - Appears in Cash Ledger, Daily Cash Report, and Party Ledger
    5. 'receivable' / 'payable':
       - Pure Chart of Account starting balance without invoice or cash movement.
    """
    # ============================================================
    # 1. DELETE OPENING ENTRY
    # ============================================================
    delete_id = request.GET.get('delete_id')
    delete_type = request.GET.get('delete_type', '').strip().lower()

    if delete_id:
        try:
            with transaction.atomic():
                if delete_type == 'purchase':
                    pur = PurchaseReceiving.objects.filter(id=delete_id).first()
                    if pur:
                        sync_purchase_voucher(pur, is_delete=True)
                        if pur.vendor_code:
                            PurchasePaymentHistory.objects.filter(
                                party_code=pur.vendor_code,
                                date=pur.date,
                                totall_amount=int(pur.amount or 0)
                            ).delete()
                        pur.delete()
                        messages.success(request, f"اوپننگ خریداری (بل #{pur.purchase_number}) ڈیلیٹ کر دی گئی۔")
                elif delete_type == 'sale':
                    sell = SellsInvoice.objects.filter(id=delete_id).first()
                    if sell:
                        sync_sell_voucher(sell, is_delete=True)
                        if sell.customer_code:
                            ReceiptHistory.objects.filter(
                                part_code=sell.customer_code,
                                date=sell.entry_date,
                                amount=int(_to_decimal(sell.amount))
                            ).delete()
                        sell.delete()
                        messages.success(request, f"اوپننگ فروخت (بل #{sell.sells_no}) ڈیلیٹ کر دی گئی۔")
                elif delete_type in ('payment', 'receipt'):
                    voucher = Voucher.objects.filter(id=delete_id).first()
                    if not voucher and delete_id.isdigit():
                        voucher = Voucher.objects.filter(id=int(delete_id)).first()
                    if voucher:
                        v_no = voucher.voucher_no
                        net_hand = Decimal('0')
                        net_bank = Decimal('0')
                        for line in voucher.details.all():
                            _update_account_balance(line.account, line.credit, line.debit)
                            acc_code = str(line.account.code)
                            acc_name = line.account.name.lower()
                            if acc_code in ['010101001', '1110001'] or 'cash in hand' in acc_name:
                                net_hand += (line.credit - line.debit)  # reverse effect
                            elif acc_code.startswith('010101') or acc_code.startswith('1110') or 'bank' in acc_name:
                                net_bank += (line.credit - line.debit)

                        if net_hand != 0 or net_bank != 0:
                            _sync_opening_cash_record(net_hand, net_bank, f"Reversal of Voucher #{v_no}", timezone.now())

                        PurchasePayments.objects.filter(purchase_number=v_no).delete()
                        Sellspayment.objects.filter(sell_no=v_no).delete()
                        voucher.delete()
                        messages.success(request, f"اوپننگ واؤچر #{v_no} ڈیلیٹ کر دیا گیا۔")
                else:
                    # Pure COA opening balance
                    coa_acc = ChartOfAccount.objects.filter(id=delete_id, party__isnull=False).first()
                    if not coa_acc:
                        coa_acc = ChartOfAccount.objects.filter(party_id=delete_id, level=4).first()
                    if coa_acc:
                        coa_acc.opening_balance = Decimal('0.00')
                        coa_acc.description = ''
                        v_dr = sum(d.debit for d in coa_acc.voucher_lines.all())
                        v_cr = sum(d.credit for d in coa_acc.voucher_lines.all())
                        coa_acc.current_balance = v_dr - v_cr
                        coa_acc.save()
                        messages.success(request, f"{coa_acc.name} کا اوپننگ بیلنس ری سیٹ کر دیا گیا۔")

        except Exception as e:
            messages.error(request, f"ڈیلیٹ میں خرابی پیش آئی: {e}")

        return redirect('opening')

    # ============================================================
    # 2. SAVE / UPDATE OPENING ENTRY (POST)
    # ============================================================
    if request.method == 'POST':
        party_name = (request.POST.get('party_name') or '').strip()
        party_code = (request.POST.get('party_code') or '').strip()
        raw_type = (request.POST.get('opening_type') or request.POST.get('entry_type') or 'purchase').strip().lower()
        amount_raw = (request.POST.get('amount') or '0').strip()
        weight_raw = (request.POST.get('weight') or '0').strip()
        rate_raw = (request.POST.get('rate') or '0').strip()
        vehicle_no = (request.POST.get('vehicle_no') or 'OPENING').strip()
        date_str = (request.POST.get('date') or '').strip()
        description = (request.POST.get('description') or '').strip()
        pay_account_id = (request.POST.get('pay_account_id') or '').strip()

        # Resolve party
        party_obj = None
        if party_code:
            party_obj = Parties.objects.filter(code=party_code).first()
        if not party_obj and party_name:
            party_obj = Parties.objects.filter(company_name=party_name).first() or \
                        Parties.objects.filter(owner_name=party_name).first()

        if not party_obj:
            messages.error(request, "براہ کرم درست پارٹی منتخب کریں۔ (Please select a valid party.)")
            return redirect('opening')

        party_code = party_obj.code or party_code
        party_name = party_obj.company_name or party_obj.owner_name or party_name

        # Parse date
        if date_str:
            try:
                entry_date_val = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                entry_date_val = timezone.localdate()
        else:
            entry_date_val = timezone.localdate()

        pk_now = _get_pk_now()
        naive_dt = datetime.combine(entry_date_val, pk_now.time())
        try:
            final_datetime = timezone.make_aware(naive_dt, pytz.timezone('Asia/Karachi'))
        except Exception:
            final_datetime = naive_dt

        weight = _to_decimal(weight_raw)
        rate = _to_decimal(rate_raw)
        amount = _to_decimal(amount_raw)

        # Auto-calculate amount if weight and rate provided
        if amount <= 0 and weight > 0 and rate > 0:
            amount = weight * rate

        if amount <= 0:
            messages.error(request, "براہ کرم 0 سے زیادہ رقم یا وزن اور ریٹ درج کریں۔ (Amount must be > 0.)")
            return redirect('opening')

        with transaction.atomic():
            # 1. 🛒 PURCHASE OPENING (خریداری)
            if raw_type in ('purchase', 'pur', 'kharidari'):
                pur_no = _next_op_pur_no()
                desc = description or f"اوپننگ خریداری: {weight}kg @ {rate}"
                pur = PurchaseReceiving.objects.create(
                    purchase_number=pur_no,
                    vendor_code=party_code,
                    vendor_name=party_name,
                    date=final_datetime,
                    vendor_rate=rate,
                    market_rate=rate,
                    weight=weight,
                    remaining_weight=str(weight),
                    vehicle_number=vehicle_no or 'OPENING',
                    status='Active',
                    amount=amount,
                    payed_amount=0,
                    discription=desc,
                )
                sync_purchase_voucher(pur)

                PurchasePaymentHistory.objects.create(
                    party_code=party_code,
                    party_name=party_name,
                    date=final_datetime,
                    totall_amount=int(amount),
                    payed_amount=0,
                    due=int(amount),
                    advanced=0,
                    remarks=desc,
                )
                messages.success(request, f"اوپننگ خریداری محفوظ ہو گئی! بل نمبر: {pur_no} | پارٹی: {party_name} | رقم: Rs. {amount:,.2f} (پرچیز رپورٹ اور پارٹی لیجر میں شامل)")

            # 2. 📦 SALE OPENING (فروخت)
            elif raw_type in ('sale', 'sell', 'sales', 'farokht'):
                sls_no = _next_op_sls_no()
                desc = description or f"اوپننگ فروخت: {weight}kg @ {rate}"
                sell = SellsInvoice.objects.create(
                    sells_no=sls_no,
                    purchase_number='OPENING',
                    customer_name=party_name,
                    customer_code=party_code,
                    weight=str(weight),
                    rate=str(rate),
                    amount=str(amount),
                    received_amount='0',
                    remaining_amount=str(amount),
                    vehicle_no=vehicle_no or 'OPENING',
                    entry_date=final_datetime,
                )
                sync_sell_voucher(sell)

                ReceiptHistory.objects.create(
                    party_name=party_name,
                    part_code=party_code,
                    date=final_datetime,
                    amount=int(amount),
                    received_amount='0',
                    due=int(amount),
                    advance=0,
                    payment_method='Opening Sale',
                )
                messages.success(request, f"اوپننگ فروخت محفوظ ہو گئی! انوائس: {sls_no} | پارٹی: {party_name} | رقم: Rs. {amount:,.2f} (سیلز رپورٹ اور پارٹی لیجر میں شامل)")

            # 3. 💸 PAYMENT OPENING (پیسے دیے / ادا کیے)
            elif raw_type in ('payment', 'pay', 'dena_cash', 'paise_diye'):
                is_bank = bool(pay_account_id and pay_account_id != 'cash')
                v_type = 'BPV' if is_bank else 'CPV'
                asset_acc = None
                if is_bank:
                    asset_acc = ChartOfAccount.objects.filter(id=pay_account_id, level=4).first()
                if not asset_acc:
                    asset_acc = ChartOfAccount.objects.filter(level=4, code__in=['010101001', '1110001']).first() or ChartOfAccount.objects.filter(level=4, name__icontains='Cash in Hand').first()
                    v_type = 'CPV'

                party_acc = sync_single_party_to_coa(party_obj)
                v_no = generate_voucher_no(v_type)
                desc = description or f"Opening Payment to {party_name}"

                voucher = Voucher.objects.create(
                    voucher_no=v_no,
                    voucher_type=v_type,
                    date=entry_date_val,
                    reference_no=f"OP-PAY-{party_code}",
                    total_amount=amount,
                    remarks=desc[:450],
                    created_by=request.session.get('user_name', 'System / Opening'),
                )
                # Debit Party
                VoucherDetail.objects.create(
                    voucher=voucher,
                    account=party_acc,
                    debit=amount,
                    credit=Decimal('0'),
                    party=party_obj,
                    narration=f"Opening Payment ({v_no})",
                )
                _update_account_balance(party_acc, amount, Decimal('0'))

                # Credit Cash/Bank
                VoucherDetail.objects.create(
                    voucher=voucher,
                    account=asset_acc,
                    debit=Decimal('0'),
                    credit=amount,
                    narration=f"Opening Payment to {party_name}",
                )
                _update_account_balance(asset_acc, Decimal('0'), amount)

                # Sync CashRecord
                net_hand = -amount if v_type == 'CPV' else Decimal('0')
                net_bank = -amount if v_type == 'BPV' else Decimal('0')
                _sync_opening_cash_record(net_hand, net_bank, f"[{v_type}] #{v_no}: Opening Payment to {party_name}", final_datetime)

                messages.success(request, f"اوپننگ نقد/بینک ادائیگی محفوظ ہو گئی! واؤچر #{v_no} | پارٹی: {party_name} | رقم: Rs. {amount:,.2f} (کیش لیجر، کیش رپورٹ، اور پارٹی لیجر میں شامل)")

            # 4. 💰 RECEIPT OPENING (پیسے لیے / وصول کیے)
            elif raw_type in ('receipt', 'receive', 'lena_cash', 'paise_liye'):
                is_bank = bool(pay_account_id and pay_account_id != 'cash')
                v_type = 'BRV' if is_bank else 'CRV'
                asset_acc = None
                if is_bank:
                    asset_acc = ChartOfAccount.objects.filter(id=pay_account_id, level=4).first()
                if not asset_acc:
                    asset_acc = ChartOfAccount.objects.filter(level=4, code__in=['010101001', '1110001']).first() or ChartOfAccount.objects.filter(level=4, name__icontains='Cash in Hand').first()
                    v_type = 'CRV'

                party_acc = sync_single_party_to_coa(party_obj)
                v_no = generate_voucher_no(v_type)
                desc = description or f"Opening Receipt from {party_name}"

                voucher = Voucher.objects.create(
                    voucher_no=v_no,
                    voucher_type=v_type,
                    date=entry_date_val,
                    reference_no=f"OP-REC-{party_code}",
                    total_amount=amount,
                    remarks=desc[:450],
                    created_by=request.session.get('user_name', 'System / Opening'),
                )
                # Debit Cash/Bank
                VoucherDetail.objects.create(
                    voucher=voucher,
                    account=asset_acc,
                    debit=amount,
                    credit=Decimal('0'),
                    narration=f"Opening Receipt from {party_name}",
                )
                _update_account_balance(asset_acc, amount, Decimal('0'))

                # Credit Party
                VoucherDetail.objects.create(
                    voucher=voucher,
                    account=party_acc,
                    debit=Decimal('0'),
                    credit=amount,
                    party=party_obj,
                    narration=f"Opening Receipt ({v_no})",
                )
                _update_account_balance(party_acc, Decimal('0'), amount)

                # Sync CashRecord
                net_hand = amount if v_type == 'CRV' else Decimal('0')
                net_bank = amount if v_type == 'BRV' else Decimal('0')
                _sync_opening_cash_record(net_hand, net_bank, f"[{v_type}] #{v_no}: Opening Receipt from {party_name}", final_datetime)

                messages.success(request, f"اوپننگ نقد/بینک وصولی محفوظ ہو گئی! واؤچر #{v_no} | پارٹی: {party_name} | رقم: Rs. {amount:,.2f} (کیش لیجر، کیش رپورٹ، اور پارٹی لیجر میں شامل)")

            # 5. ⚖️ PURE LEDGER OPENING (لینا ہے / دینا ہے سابقہ بیلنس)
            else:
                party_acc = sync_single_party_to_coa(party_obj)
                is_receivable = raw_type in ('receivable', 'debit', 'dr', 'receive', 'lena', 'sales_due', 'purchase_advance')
                bal_value = amount if is_receivable else -amount

                party_acc.opening_balance = bal_value
                party_acc.description = description or ("Opening Receivable (لینا ہے)" if is_receivable else "Opening Payable (دینا ہے)")
                v_dr = sum(d.debit for d in party_acc.voucher_lines.all())
                v_cr = sum(d.credit for d in party_acc.voucher_lines.all())
                party_acc.current_balance = bal_value + v_dr - v_cr
                party_acc.save()

                type_label = "لینا ہے (Receivable)" if is_receivable else "دینا ہے (Payable)"
                messages.success(request, f"پارٹی اوپننگ لیجر بیلنس محفوظ ہو گیا: {party_name} - Rs. {amount:,.2f} ({type_label})")

        return redirect('opening')

    # ============================================================
    # 3. GET: FETCH UNIFIED OPENING HISTORY & SUMMARY
    # ============================================================
    all_parties = Parties.objects.all().order_by('company_name')

    # Bank Accounts from Level 4 COA (under 010101 or 1110)
    bank_accounts = ChartOfAccount.objects.filter(
        level=4, is_active=True
    ).filter(Q(parent__code__in=['010101', '1110']) | Q(name__icontains='bank')).exclude(code__in=['010101001', '1110001']).order_by('code')

    cash_account = ChartOfAccount.objects.filter(level=4, code__in=['010101001', '1110001']).first() or ChartOfAccount.objects.filter(level=4, name__icontains='Cash in Hand').first()

    opening_history = []
    total_purchases = Decimal('0')
    total_sales = Decimal('0')
    total_payments = Decimal('0')
    total_receipts = Decimal('0')

    # 1. Opening Purchases (OP-PUR-)
    op_purchases = PurchaseReceiving.objects.filter(
        Q(purchase_number__startswith='OP-') | Q(vehicle_number='OPENING')
    ).order_by('-date', '-id')

    for p in op_purchases:
        amt = Decimal(str(p.amount or 0))
        total_purchases += amt
        opening_history.append({
            'id': p.id,
            'source_type': 'purchase',
            'ref_no': p.purchase_number,
            'party_name': p.vendor_name,
            'party_code': p.vendor_code,
            'type_key': 'purchase',
            'type_label': 'خریداری (Purchase)',
            'badge_class': 'badge-purchase',
            'reports_label': 'پرچیز رپورٹ + پارٹی لیجر',
            'reports_badge_class': 'bg-primary-subtle text-primary border border-primary-subtle',
            'weight': p.weight,
            'rate': p.vendor_rate,
            'vehicle_no': p.vehicle_number,
            'amount': amt,
            'date': p.date,
            'description': p.discription or 'Opening Purchase',
        })

    # 2. Opening Sales (OP-SLS-)
    op_sales = SellsInvoice.objects.filter(
        Q(sells_no__startswith='OP-') | Q(vehicle_no='OPENING')
    ).order_by('-entry_date', '-id')

    for s in op_sales:
        amt = _to_decimal(s.amount)
        total_sales += amt
        opening_history.append({
            'id': s.id,
            'source_type': 'sale',
            'ref_no': s.sells_no,
            'party_name': s.customer_name,
            'party_code': s.customer_code,
            'type_key': 'sale',
            'type_label': 'فروخت (Sale)',
            'badge_class': 'badge-sale',
            'reports_label': 'سیلز رپورٹ + پارٹی لیجر',
            'reports_badge_class': 'bg-warning-subtle text-warning-emphasis border border-warning-subtle',
            'weight': s.weight,
            'rate': s.rate,
            'vehicle_no': s.vehicle_no,
            'amount': amt,
            'date': s.entry_date,
            'description': f"Vehicle: {s.vehicle_no}" if s.vehicle_no else 'Opening Sale',
        })

    # 3. Opening Payments (Vouchers with OP-PAY- or remarks)
    op_payments = Voucher.objects.filter(
        Q(reference_no__startswith='OP-PAY-') | Q(remarks__icontains='Opening Payment')
    ).prefetch_related('details__account', 'details__party').order_by('-date', '-id')

    for v in op_payments:
        party_detail = v.details.filter(party__isnull=False).first() or v.details.filter(account__party__isnull=False).first()
        p_name = party_detail.party.company_name if party_detail and party_detail.party else (
            party_detail.account.party.company_name if party_detail and party_detail.account.party else 'Party'
        )
        p_code = party_detail.party.code if party_detail and party_detail.party else ''
        amt = Decimal(str(v.total_amount or 0))
        total_payments += amt
        opening_history.append({
            'id': v.id,
            'source_type': 'payment',
            'ref_no': v.voucher_no,
            'party_name': p_name,
            'party_code': p_code,
            'type_key': 'payment',
            'type_label': 'ادائیگی / پیسے دیے (Payment)',
            'badge_class': 'badge-payment',
            'reports_label': 'کیش لیجر + کیش رپورٹ + لیجر',
            'reports_badge_class': 'bg-danger-subtle text-danger border border-danger-subtle',
            'weight': '-',
            'rate': '-',
            'vehicle_no': '-',
            'amount': amt,
            'date': datetime.combine(v.date, time.min),
            'description': v.remarks or 'Opening Payment',
        })

    # 4. Opening Receipts (Vouchers with OP-REC- or remarks)
    op_receipts = Voucher.objects.filter(
        Q(reference_no__startswith='OP-REC-') | Q(remarks__icontains='Opening Receipt')
    ).prefetch_related('details__account', 'details__party').order_by('-date', '-id')

    for v in op_receipts:
        party_detail = v.details.filter(party__isnull=False).first() or v.details.filter(account__party__isnull=False).first()
        p_name = party_detail.party.company_name if party_detail and party_detail.party else (
            party_detail.account.party.company_name if party_detail and party_detail.account.party else 'Party'
        )
        p_code = party_detail.party.code if party_detail and party_detail.party else ''
        amt = Decimal(str(v.total_amount or 0))
        total_receipts += amt
        opening_history.append({
            'id': v.id,
            'source_type': 'receipt',
            'ref_no': v.voucher_no,
            'party_name': p_name,
            'party_code': p_code,
            'type_key': 'receipt',
            'type_label': 'وصولی / پیسے لیے (Receipt)',
            'badge_class': 'badge-receipt',
            'reports_label': 'کیش لیجر + کیش رپورٹ + لیجر',
            'reports_badge_class': 'bg-success-subtle text-success border border-success-subtle',
            'weight': '-',
            'rate': '-',
            'vehicle_no': '-',
            'amount': amt,
            'date': datetime.combine(v.date, time.min),
            'description': v.remarks or 'Opening Receipt',
        })

    # 5. Pure COA Balances
    active_openings = ChartOfAccount.objects.filter(
        party__isnull=False, level=4
    ).exclude(opening_balance=0).select_related('party').order_by('name')

    for acc in active_openings:
        p = acc.party
        is_rec = (acc.opening_balance or Decimal('0')) > 0
        amt = abs(acc.opening_balance or Decimal('0'))
        p_name = p.company_name or p.owner_name or acc.name
        p_code = p.code or acc.code

        opening_history.append({
            'id': acc.id,
            'party_id': p.id,
            'source_type': 'party_opening',
            'ref_no': f"OP-{acc.code}",
            'party_name': p_name,
            'party_code': p_code,
            'type_key': 'receivable' if is_rec else 'payable',
            'type_label': 'سابقہ لینا ہے (Dr)' if is_rec else 'سابقہ دینا ہے (Cr)',
            'badge_class': 'badge-receipt' if is_rec else 'badge-payment',
            'reports_label': 'صرف پارٹی لیجر',
            'reports_badge_class': 'bg-secondary-subtle text-secondary border border-secondary-subtle',
            'weight': '-',
            'rate': '-',
            'vehicle_no': '-',
            'amount': amt,
            'date': acc.created_at,
            'description': acc.description or ('Receivable balance' if is_rec else 'Payable balance'),
        })

    def _sort_key(item):
        d = item.get('date')
        if not d:
            return datetime.min
        if hasattr(d, 'date') and callable(getattr(d, 'date')):
            return d
        if isinstance(d, date) and not isinstance(d, datetime):
            return datetime.combine(d, time.min)
        return d

    opening_history.sort(key=_sort_key, reverse=True)

    context = {
        'all_parties': all_parties,
        'bank_accounts': bank_accounts,
        'cash_account': cash_account,
        'opening_history': opening_history,
        'total_purchases': total_purchases,
        'total_sales': total_sales,
        'total_payments': total_payments,
        'total_receipts': total_receipts,
        'total_entries': len(opening_history),
        'current_date': timezone.now().date(),
    }
    return render(request, 'opening/opening.html', context)


# ===================================================================
# 2. CASH & BANK OPENING BALANCE
# ===================================================================
def cash(request):
    """
    Cash in Hand & Cash in Bank Opening Balance Setup:
    Allows user/admin to enter or update the initial cash & bank opening balances.
    Synchronizes with CashRecord and Chart of Accounts Level 4 (Cash in Hand & Banks).
    """
    # Fetch existing opening record if any
    existing_opening = (
        CashRecord.objects.filter(discription__icontains="opening").order_by("date", "id").first()
        or CashRecord.objects.order_by("date", "id").first()
    )

    # Bank Accounts from Level 4 COA (under 010101 or 1110)
    bank_accounts = ChartOfAccount.objects.filter(
        level=4, is_active=True
    ).filter(Q(parent__code__in=['010101', '1110']) | Q(name__icontains='bank')).exclude(code__in=['010101001', '1110001']).order_by('code')

    cash_account = ChartOfAccount.objects.filter(level=4, code__in=['010101001', '1110001']).first() or ChartOfAccount.objects.filter(level=4, name__icontains='Cash in Hand').first()

    if request.method == "POST":
        cash_in_hand_raw = request.POST.get("cashInHand")
        cash_in_bank_raw = request.POST.get("cashInBank")
        discription      = (request.POST.get("discription") or "").strip()
        date_str         = (request.POST.get("date") or "").strip()
        bank_account_id  = request.POST.get("bankAccountId")

        try:
            hand_val = int(_to_decimal(cash_in_hand_raw))
            bank_val = int(_to_decimal(cash_in_bank_raw))

            if hand_val < 0 or bank_val < 0:
                return JsonResponse({'status': 'error', 'message': 'Opening amounts cannot be negative.'}, status=400)

            if date_str:
                try:
                    entry_date = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    entry_date = timezone.now()
            else:
                entry_date = timezone.now()

            desc = discription if discription else "Opening Cash & Bank Balance"
            if "opening" not in desc.lower():
                desc = f"Opening Balance - {desc}"

            with transaction.atomic():
                # 1. Update or Create CashRecord
                if existing_opening:
                    existing_opening.cash_in_hand = hand_val
                    existing_opening.cash_in_bank = bank_val
                    existing_opening.discription  = desc
                    existing_opening.date         = entry_date
                    existing_opening.save()
                    rec = existing_opening
                else:
                    max_id = CashRecord.objects.aggregate(Max('id'))['id__max']
                    next_id = 1 if max_id is None else max_id + 1
                    rec = CashRecord.objects.create(
                        id=next_id,
                        cash_in_hand=hand_val,
                        cash_in_bank=bank_val,
                        discription=desc,
                        date=entry_date,
                    )

                # 2. Update Chart of Accounts Level 4: Cash in Hand (1110001)
                if cash_account:
                    cash_account.opening_balance = Decimal(str(hand_val))
                    cash_account.current_balance = Decimal(str(hand_val))
                    cash_account.save()

                # 3. Update Chart of Accounts Level 4: Bank Account(s)
                if bank_account_id:
                    target_bank = ChartOfAccount.objects.filter(id=bank_account_id, level=4).first()
                    if target_bank:
                        target_bank.opening_balance = Decimal(str(bank_val))
                        target_bank.current_balance = Decimal(str(bank_val))
                        target_bank.save()
                elif bank_accounts.exists():
                    first_bank = bank_accounts.first()
                    first_bank.opening_balance = Decimal(str(bank_val))
                    first_bank.current_balance = Decimal(str(bank_val))
                    first_bank.save()

            msg = f"Opening cash balances saved successfully! (Cash in Hand: Rs. {hand_val:,} | Cash in Bank: Rs. {bank_val:,})"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('is_ajax'):
                return JsonResponse({
                    "status": "success",
                    "message": msg,
                    "cash_in_hand": hand_val,
                    "cash_in_bank": bank_val,
                    "discription": rec.discription,
                    "date": rec.date.strftime("%d-%m-%Y") if rec.date else "",
                    "total_opening": hand_val + bank_val,
                })
            else:
                messages.success(request, msg)
                return redirect('cash')

        except Exception as e:
            err_msg = f"Error: {str(e)}"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('is_ajax'):
                return JsonResponse({"status": "error", "message": err_msg}, status=400)
            messages.error(request, err_msg)
            return redirect('cash')

    # GET Request
    cur_hand = existing_opening.cash_in_hand if existing_opening and existing_opening.cash_in_hand is not None else (cash_account.current_balance if cash_account else 0)
    cur_bank = existing_opening.cash_in_bank if existing_opening and existing_opening.cash_in_bank is not None else 0
    total_opening = int(cur_hand or 0) + int(cur_bank or 0)

    selected_bank_id = None
    for b in bank_accounts:
        if (b.opening_balance or Decimal('0')) > Decimal('0'):
            selected_bank_id = b.id
            break

    context = {
        "existing_opening": existing_opening,
        "cash_in_hand": cur_hand,
        "cash_in_bank": cur_bank,
        "discription": existing_opening.discription if existing_opening else "Opening Cash & Bank Balance",
        "opening_date": existing_opening.date.strftime('%Y-%m-%d') if (existing_opening and existing_opening.date) else timezone.now().strftime('%Y-%m-%d'),
        "total_opening": total_opening,
        "bank_accounts": bank_accounts,
        "selected_bank_id": selected_bank_id,
        "cash_account": cash_account,
    }
    return render(request, "opening/cash.html", context)
