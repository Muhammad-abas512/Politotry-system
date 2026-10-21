import json
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Q, Max
import pytz

from .models import (
    ChartOfAccount,
    Voucher,
    VoucherDetail,
    Parties,
    CashRecord,
    CoreUsers,
)


def _get_pk_now():
    pk_tz = pytz.timezone('Asia/Karachi')
    return timezone.now().astimezone(pk_tz).replace(tzinfo=None)


def _to_decimal(val):
    if val is None or str(val).strip() == '':
        return Decimal('0')
    try:
        cleaned = str(val).replace(',', '').strip()
        return Decimal(cleaned)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0')


# ===================================================================
# SEED DEFAULT 4-LEVEL CHART OF ACCOUNTS & PARTY SYNC
# ===================================================================
def seed_default_chart_of_accounts():
    """Populates standard 4-level Chart of Accounts if not already created (idempotent)."""
    # Level 1: Main Classes (2 digits: 01, 02, 03, 04, 05)
    l1_data = [
        ('01', 'Assets', 'Asset'),
        ('02', 'Liabilities', 'Liability'),
        ('03', 'Equity & Capital', 'Equity'),
        ('04', 'Revenue & Sales', 'Revenue'),
        ('05', 'Expenses', 'Expense'),
    ]
    l1_map = {}
    for code, name, ac_type in l1_data:
        acc, _ = ChartOfAccount.objects.get_or_create(
            code=code,
            defaults={'name': name, 'level': 1, 'parent': None, 'account_type': ac_type, 'is_active': True}
        )
        l1_map[code] = acc

    # Level 2: Control Heads (4 digits: 0101, 0102, 0201...)
    l2_data = [
        ('0101', 'Current Assets', l1_map['01']),
        ('0102', 'Fixed & Non-Current Assets', l1_map['01']),
        ('0201', 'Current Liabilities', l1_map['02']),
        ('0202', 'Long-term Liabilities', l1_map['02']),
        ('0301', "Owner's Equity & Capital", l1_map['03']),
        ('0401', 'Operating Revenue & Sales', l1_map['04']),
        ('0501', 'Direct Cost of Sales', l1_map['05']),
        ('0502', 'Operating & Administrative Expenses', l1_map['05']),
    ]
    l2_map = {}
    for code, name, parent in l2_data:
        acc, _ = ChartOfAccount.objects.get_or_create(
            code=code,
            defaults={'name': name, 'level': 2, 'parent': parent, 'account_type': parent.account_type, 'is_active': True}
        )
        l2_map[code] = acc

    # Level 3: Sub Control Heads (6 digits: 010101, 010102...)
    l3_data = [
        ('010101', 'Cash & Bank Balances', l2_map['0101']),
        ('010102', 'Trade Accounts (Parties)', l2_map['0101']),
        ('010103', 'Inventory & Stock', l2_map['0101']),
        ('010201', 'Vehicles & Transport Assets', l2_map['0102']),
        ('010202', 'Plant & Equipment', l2_map['0102']),
        ('020101', 'Trade Payables (Parties)', l2_map['0201']),
        ('020102', 'Short Term Borrowings', l2_map['0201']),
        ('030101', 'Capital Account', l2_map['0301']),
        ('040101', 'Poultry & Broiler Sales', l2_map['0401']),
        ('040102', 'By-Product Sales', l2_map['0401']),
        ('050101', 'Broiler Purchase Cost', l2_map['0501']),
        ('050102', 'Mortality Loss', l2_map['0501']),
        ('050201', 'Vehicle & Transport Expenses', l2_map['0502']),
        ('050202', 'Utilities & Bills', l2_map['0502']),
        ('050203', 'Salaries & Wages', l2_map['0502']),
        ('050204', 'Office & General Expenses', l2_map['0502']),
    ]
    l3_map = {}
    for code, name, parent in l3_data:
        acc, _ = ChartOfAccount.objects.get_or_create(
            code=code,
            defaults={'name': name, 'level': 3, 'parent': parent, 'account_type': parent.account_type, 'is_active': True}
        )
        l3_map[code] = acc

    # Level 4: Transactional Accounts (9 digits: 010101001, 010101002...)
    l4_data = [
        ('010101001', 'Cash in Hand', l3_map['010101']),
        ('010101002', 'Bank Al-Habib Main', l3_map['010101']),
        ('010101003', 'Meezan Bank Account', l3_map['010101']),
        ('010101004', 'MCB Bank Account', l3_map['010101']),
        ('010103001', 'Live Broiler Stock', l3_map['010103']),
        ('010201001', 'Delivery Vehicles', l3_map['010201']),
        ('010202001', 'Cages & Weighing Scales', l3_map['010202']),
        ('020101001', 'General Party Payables', l3_map['020101']),
        ('020102001', 'Temporary Loans', l3_map['020102']),
        ('030101001', 'Owner Capital', l3_map['030101']),
        ('030101002', 'Owner Drawings', l3_map['030101']),
        ('040101001', 'Broiler Sales', l3_map['040101']),
        ('040102001', 'Fat Sales', l3_map['040102']),
        ('040102002', 'Waste Sales', l3_map['040102']),
        ('050101001', 'Broiler Purchases', l3_map['050101']),
        ('050102001', 'Mortality Loss', l3_map['050102']),
        ('050201001', 'Diesel & Fuel Expense', l3_map['050201']),
        ('050201002', 'Vehicle Maintenance & Repair', l3_map['050201']),
        ('050202001', 'Electricity Bill', l3_map['050202']),
        ('050202002', 'Mobile & Internet Expense', l3_map['050202']),
        ('050203001', 'Staff Monthly Salaries', l3_map['050203']),
        ('050203002', 'Daily Labour Wages', l3_map['050203']),
        ('050204001', 'Office Tea & Entertainment', l3_map['050204']),
        ('050204002', 'Office Rent', l3_map['050204']),
        ('050204003', 'Stationery & Printing', l3_map['050204']),
        ('050204004', 'Miscellaneous Expense', l3_map['050204']),
    ]
    for code, name, parent in l4_data:
        ChartOfAccount.objects.get_or_create(
            code=code,
            defaults={'name': name, 'level': 4, 'parent': parent, 'account_type': parent.account_type, 'is_active': True}
        )


def sync_single_party_to_coa(party):
    """Sync single party to Level 4 Chart of Account under 010102"""
    if not party:
        return None
    parent_l3 = ChartOfAccount.objects.filter(code='010102', level=3).first()
    if not parent_l3:
        parent_l3 = ChartOfAccount.objects.filter(code='1120', level=3).first()
    if not parent_l3:
        seed_default_chart_of_accounts()
        parent_l3 = ChartOfAccount.objects.filter(code='010102', level=3).first()

    p_name = (party.company_name or party.owner_name or f"Party {party.id}").strip()
    acc = ChartOfAccount.objects.filter(party=party).first()

    if acc:
        if acc.name != p_name:
            acc.name = p_name
            acc.save(update_fields=['name'])
        return acc

    # Calculate unique code
    raw_num = ''.join(c for c in str(party.code or party.id) if c.isdigit())
    base_suffix = raw_num[-3:].zfill(3) if raw_num else str(party.id).zfill(3)
    acc_code = f"010102{base_suffix}"

    # Guard against code collision with another party
    if ChartOfAccount.objects.filter(code=acc_code).exists():
        last_acc = ChartOfAccount.objects.filter(parent=parent_l3, level=4).order_by('-code').first()
        if last_acc and last_acc.code.startswith('010102'):
            try:
                sfx = int(last_acc.code.replace('010102', ''))
                acc_code = f"010102{sfx + 1:03d}"
            except ValueError:
                acc_code = f"010102{party.id:03d}"
        else:
            acc_code = f"010102{party.id:03d}"

    acc = ChartOfAccount.objects.create(
        code=acc_code,
        name=p_name,
        level=4,
        parent=parent_l3,
        account_type='Asset',
        party=party,
        opening_balance=Decimal('0'),
        current_balance=Decimal('0'),
        is_active=True,
        description=f"Level 4 Party Account: {p_name} ({party.party_type or 'General'})"
    )
    return acc


def sync_all_parties_to_coa():
    """Sync all parties to Level 4 Chart of Account"""
    seed_default_chart_of_accounts()
    for party in Parties.objects.all():
        sync_single_party_to_coa(party)


# ===================================================================
# 1. CHART OF ACCOUNTS VIEW
# ===================================================================
def chart_of_accounts(request):
    if not request.session.get('user_id'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('action'):
            return JsonResponse({'success': False, 'message': 'Session expired'}, status=401)
        return redirect('login')

    seed_default_chart_of_accounts()
    action = request.GET.get('action') or request.POST.get('action')

    # ------------ AJAX: NEXT ACCOUNT CODE ------------
    if request.method == 'GET' and action == 'next_code':
        level = int(request.GET.get('level', 1))
        parent_id = request.GET.get('parent_id')

        if level == 1:
            last = ChartOfAccount.objects.filter(level=1).order_by('-code').first()
            if last and last.code.isdigit():
                next_code = f"{int(last.code) + 1:02d}"
            else:
                next_code = '01'
        else:
            if not parent_id:
                return JsonResponse({'success': False, 'message': 'Parent is required'})
            parent = get_object_or_404(ChartOfAccount, id=parent_id)
            children = ChartOfAccount.objects.filter(parent=parent).order_by('-code')
            last_child = children.first()

            if last_child and last_child.code.startswith(parent.code):
                prefix = parent.code
                suffix_str = last_child.code[len(prefix):]
                suffix_num = int(suffix_str) if suffix_str.isdigit() else 0
                if level in [2, 3]:
                    next_code = f"{prefix}{suffix_num + 1:02d}"
                else:  # level 4
                    next_code = f"{prefix}{suffix_num + 1:03d}"
            else:
                if level in [2, 3]:
                    next_code = f"{parent.code}01"
                else:  # level 4
                    next_code = f"{parent.code}001"

        return JsonResponse({'success': True, 'code': next_code})

    # ------------ AJAX: GET PARENTS FOR LEVEL ------------
    if request.method == 'GET' and action == 'get_parents':
        level = int(request.GET.get('level', 2))
        parent_level = level - 1
        parents = ChartOfAccount.objects.filter(level=parent_level, is_active=True).order_by('code')
        data = [{'id': p.id, 'code': p.code, 'name': p.name, 'type': p.account_type} for p in parents]
        return JsonResponse({'success': True, 'data': data})

    # ------------ AJAX: GET SINGLE ACCOUNT ------------
    if request.method == 'GET' and action == 'get':
        acc_id = request.GET.get('id')
        acc = get_object_or_404(ChartOfAccount, id=acc_id)
        return JsonResponse({
            'success': True,
            'data': {
                'id': acc.id,
                'code': acc.code,
                'name': acc.name,
                'level': acc.level,
                'parent_id': acc.parent_id,
                'account_type': acc.account_type,
                'opening_balance': str(acc.opening_balance),
                'current_balance': str(acc.current_balance),
                'description': acc.description or '',
                'is_active': acc.is_active,
            }
        })

    # ------------ AJAX: SAVE / UPDATE ACCOUNT ------------
    if request.method == 'POST' and action == 'save':
        try:
            data = json.loads(request.body)
            acc_id = data.get('id')
            code = (data.get('code') or '').strip()
            name = (data.get('name') or '').strip()
            level = int(data.get('level', 1))
            parent_id = data.get('parent_id')
            account_type = (data.get('account_type') or '').strip()
            opening_balance = _to_decimal(data.get('opening_balance', 0))
            description = (data.get('description') or '').strip()
            is_active = bool(data.get('is_active', True))

            if not code or not name:
                return JsonResponse({'success': False, 'message': 'Account Code and Name are required'})

            parent = None
            if level > 1:
                if not parent_id:
                    return JsonResponse({'success': False, 'message': f'Parent account required for Level {level}'})
                parent = get_object_or_404(ChartOfAccount, id=parent_id)
                account_type = parent.account_type

            if acc_id:
                # Update
                acc = get_object_or_404(ChartOfAccount, id=acc_id)
                if ChartOfAccount.objects.filter(code=code).exclude(id=acc_id).exists():
                    return JsonResponse({'success': False, 'message': f'Code {code} is already in use'})
                acc.code = code
                acc.name = name
                acc.description = description
                acc.is_active = is_active
                if level == 4 and acc.level == 4:
                    bal_diff = opening_balance - acc.opening_balance
                    acc.opening_balance = opening_balance
                    acc.current_balance += bal_diff
                acc.save()
                return JsonResponse({'success': True, 'message': 'Account updated successfully'})
            else:
                # Create
                if ChartOfAccount.objects.filter(code=code).exists():
                    return JsonResponse({'success': False, 'message': f'Code {code} already exists'})

                ChartOfAccount.objects.create(
                    code=code,
                    name=name,
                    level=level,
                    parent=parent,
                    account_type=account_type,
                    opening_balance=opening_balance if level == 4 else Decimal('0'),
                    current_balance=opening_balance if level == 4 else Decimal('0'),
                    description=description,
                    is_active=is_active,
                )
                return JsonResponse({'success': True, 'message': f'Level {level} Account created successfully'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    # ------------ AJAX: DELETE ACCOUNT ------------
    if request.method == 'POST' and action == 'delete':
        try:
            data = json.loads(request.body)
            acc_id = data.get('id')
            acc = get_object_or_404(ChartOfAccount, id=acc_id)

            if acc.children.exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot delete account "{acc.name}". It has {acc.children.count()} child accounts under it.'
                })

            if acc.voucher_lines.exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot delete account "{acc.name}". Vouchers have already been posted to it.'
                })

            acc.delete()
            return JsonResponse({'success': True, 'message': 'Account deleted successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    # ------------ FULL HIERARCHICAL TREE DATA FOR PAGE ------------
    l1_accounts = ChartOfAccount.objects.filter(level=1).prefetch_related(
        'children__children__children'
    ).order_by('code')

    total_l1 = ChartOfAccount.objects.filter(level=1).count()
    total_l2 = ChartOfAccount.objects.filter(level=2).count()
    total_l3 = ChartOfAccount.objects.filter(level=3).count()
    total_l4 = ChartOfAccount.objects.filter(level=4).count()

    context = {
        'l1_accounts': l1_accounts,
        'total_l1': total_l1,
        'total_l2': total_l2,
        'total_l3': total_l3,
        'total_l4': total_l4,
        'total_accounts': total_l1 + total_l2 + total_l3 + total_l4,
    }
    return render(request, 'accounts/chart_of_accounts.html', context)


# ===================================================================
# 2. VOUCHER ENTRY VIEW
# ===================================================================
# ===================================================================
# 2. VOUCHER ENTRY VIEW (CPV, CRV, BPV, BRV, JV)
# ===================================================================
def generate_voucher_no(voucher_type):
    prefix_map = {
        'CPV': 'CPV',
        'CRV': 'CRV',
        'BPV': 'BPV',
        'BRV': 'BRV',
        'JV': 'JV',
        'Payment Voucher': 'CPV',
        'Receipt Voucher': 'CRV',
        'Transfer Voucher': 'JV',
    }
    prefix = prefix_map.get(voucher_type, 'CPV')
    year = date.today().year

    last_v = Voucher.objects.filter(voucher_no__startswith=f"{prefix}-{year}").order_by('-id').first()
    if last_v and last_v.voucher_no:
        try:
            num = int(last_v.voucher_no.split('-')[-1])
            return f"{prefix}-{year}-{num + 1:05d}"
        except (ValueError, IndexError):
            pass
    return f"{prefix}-{year}-00001"


def _update_account_balance(account, debit_amt, credit_amt):
    """
    Standard accounting rule:
    Asset / Expense: Normal balance is Debit (Debit increases, Credit decreases)
    Liability / Equity / Revenue: Normal balance is Credit (Credit increases, Debit decreases)
    """
    if account.account_type in ['Asset', 'Expense']:
        net_change = debit_amt - credit_amt
    else:
        net_change = credit_amt - debit_amt

    account.current_balance += net_change
    account.save(update_fields=['current_balance'])


def voucher_entry(request):
    if not request.session.get('user_id'):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('action'):
            return JsonResponse({'success': False, 'message': 'Session expired'}, status=401)
        return redirect('login')

    seed_default_chart_of_accounts()
    sync_all_parties_to_coa()
    action = request.GET.get('action') or request.POST.get('action')

    # ------------ AJAX: GET NEXT VOUCHER NUMBER ------------
    if request.method == 'GET' and action == 'next_voucher_no':
        v_type = request.GET.get('voucher_type', 'CPV')
        return JsonResponse({'success': True, 'voucher_no': generate_voucher_no(v_type)})

    # ------------ AJAX: GET LEVEL 4 ACCOUNTS ------------
    if request.method == 'GET' and action == 'get_level4_accounts':
        accounts = ChartOfAccount.objects.filter(level=4, is_active=True).order_by('code')
        data = [{
            'id': a.id,
            'code': a.code,
            'name': a.name,
            'type': a.account_type,
            'balance': str(a.current_balance),
            'party_id': a.party_id,
        } for a in accounts]
        return JsonResponse({'success': True, 'accounts': data})

    # ------------ AJAX: SAVE VOUCHER ------------
    if request.method == 'POST' and action == 'save_voucher':
        try:
            data = json.loads(request.body)
            raw_type = (data.get('voucher_type') or 'CPV').strip()
            type_map = {
                'Payment Voucher': 'CPV',
                'Receipt Voucher': 'CRV',
                'Transfer Voucher': 'JV',
            }
            v_type = type_map.get(raw_type, raw_type)
            if v_type not in ['CPV', 'CRV', 'BPV', 'BRV', 'JV']:
                v_type = 'CPV'

            date_str = (data.get('date') or '').strip()
            reference_no = (data.get('reference_no') or '').strip()
            remarks = (data.get('remarks') or '').strip()
            mode = data.get('mode', 'quick')  # 'quick' or 'multiline'

            if date_str:
                try:
                    voucher_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    voucher_date = date.today()
            else:
                voucher_date = date.today()

            entries = []

            # Cash in hand account
            cash_acc = ChartOfAccount.objects.filter(code='010101001', level=4).first() or ChartOfAccount.objects.filter(code='1110001', level=4).first()
            if not cash_acc:
                seed_default_chart_of_accounts()
                cash_acc = ChartOfAccount.objects.filter(code='010101001', level=4).first()

            # QUICK MODE: CPV, CRV, BPV, BRV, JV
            if mode == 'quick':
                amount = _to_decimal(data.get('amount'))
                if amount <= 0:
                    return JsonResponse({'success': False, 'message': 'Amount must be greater than 0'})

                dr_acc_id = data.get('debit_account_id')
                cr_acc_id = data.get('credit_account_id')
                party_id = data.get('party_id') or None

                # AUTO-CONFIGURE BASED ON VOUCHER TYPE:
                if v_type == 'CPV':
                    # Cash Payment: Cash in Hand is CREDIT
                    if not cr_acc_id and cash_acc:
                        cr_acc_id = cash_acc.id
                elif v_type == 'CRV':
                    # Cash Receipt: Cash in Hand is DEBIT
                    if not dr_acc_id and cash_acc:
                        dr_acc_id = cash_acc.id

                if not dr_acc_id or not cr_acc_id:
                    return JsonResponse({'success': False, 'message': 'Both Debit and Credit accounts must be specified'})
                if str(dr_acc_id) == str(cr_acc_id):
                    return JsonResponse({'success': False, 'message': 'Debit and Credit accounts cannot be the same'})

                dr_acc = get_object_or_404(ChartOfAccount, id=dr_acc_id, level=4)
                cr_acc = get_object_or_404(ChartOfAccount, id=cr_acc_id, level=4)

                # =============================================================
                # 🛑 INSUFFICIENT BALANCE CHECK FOR CASH & BANK PAYMENTS
                # =============================================================
                cr_code = str(cr_acc.code)
                cr_name_lower = cr_acc.name.lower()
                is_cash_hand_cr = (cr_code in ['010101001', '1110001'] or 'cash in hand' in cr_name_lower)
                is_bank_cr = ((cr_code.startswith('010101') or cr_code.startswith('1110')) and not is_cash_hand_cr) or ('bank' in cr_name_lower and not is_cash_hand_cr)

                if is_cash_hand_cr:
                    available = cr_acc.current_balance
                    if available < amount:
                        return JsonResponse({
                            'success': False,
                            'message': (
                                f"❌ Payment Rejection: Cash in Hand mein kafi raqam mojood nahi hai! "
                                f"Mojooda Cash Balance: Rs. {available:,.2f}, jabkay Payment Amount: Rs. {amount:,.2f}. "
                                f"Pehle Cash Receive karein (CRV) ya Opening Balance darj karein."
                            )
                        })

                elif is_bank_cr:
                    available = cr_acc.current_balance
                    if available < amount:
                        return JsonResponse({
                            'success': False,
                            'message': (
                                f"❌ Payment Rejection: Bank Account '{cr_acc.name}' mein kafi raqam mojood nahi hai! "
                                f"Mojooda Bank Balance: Rs. {available:,.2f}, jabkay Payment Amount: Rs. {amount:,.2f}. "
                                f"Pehle Bank mein raqam transfer/receive karein."
                            )
                        })

                dr_code = str(dr_acc.code)
                dr_name_lower = dr_acc.name.lower()
                is_cash_hand_dr = (dr_code in ['010101001', '1110001'] or 'cash in hand' in dr_name_lower)
                is_bank_dr = ((dr_code.startswith('010101') or dr_code.startswith('1110')) and not is_cash_hand_dr) or ('bank' in dr_name_lower and not is_cash_hand_dr)

                # Auto link party from selected account if not explicitly passed
                # Assign party_id only to the party side, never to cash/bank
                if v_type in ['CPV', 'BPV']:
                    dr_party_id = dr_acc.party_id or party_id
                    cr_party_id = None
                elif v_type in ['CRV', 'BRV']:
                    cr_party_id = cr_acc.party_id or party_id
                    dr_party_id = None
                else:
                    dr_party_id = dr_acc.party_id or (party_id if not is_cash_hand_dr and not is_bank_dr else None)
                    cr_party_id = cr_acc.party_id or (party_id if not is_cash_hand_cr and not is_bank_cr else None)

                entries.append({
                    'account': dr_acc,
                    'debit': amount,
                    'credit': Decimal('0'),
                    'narration': remarks or f"{v_type}: Debit to {dr_acc.name}",
                    'party_id': dr_party_id,
                })
                entries.append({
                    'account': cr_acc,
                    'debit': Decimal('0'),
                    'credit': amount,
                    'narration': remarks or f"{v_type}: Credit from {cr_acc.name}",
                    'party_id': cr_party_id,
                })
                total_voucher_amt = amount

            # MULTI-LINE GRID MODE
            else:
                raw_entries = data.get('entries', [])
                if len(raw_entries) < 2:
                    return JsonResponse({'success': False, 'message': 'At least 2 line items are required in a voucher'})

                total_dr = Decimal('0')
                total_cr = Decimal('0')
                from collections import defaultdict
                credits_per_acc = defaultdict(Decimal)

                for line in raw_entries:
                    acc_id = line.get('account_id')
                    dr = _to_decimal(line.get('debit', 0))
                    cr = _to_decimal(line.get('credit', 0))
                    line_narration = (line.get('narration') or remarks or '').strip()
                    p_id = line.get('party_id') or None

                    if not acc_id:
                        return JsonResponse({'success': False, 'message': 'Account must be selected for all lines'})
                    if dr == 0 and cr == 0:
                        continue

                    acc = get_object_or_404(ChartOfAccount, id=acc_id, level=4)
                    if not p_id and acc.party_id:
                        p_id = acc.party_id

                    entries.append({
                        'account': acc,
                        'debit': dr,
                        'credit': cr,
                        'narration': line_narration,
                        'party_id': p_id,
                    })
                    total_dr += dr
                    total_cr += cr
                    if cr > 0:
                        credits_per_acc[acc] += cr

                if total_dr <= 0 or total_cr <= 0:
                    return JsonResponse({'success': False, 'message': 'Voucher amounts must be greater than 0'})
                if total_dr != total_cr:
                    return JsonResponse({
                        'success': False,
                        'message': f'Voucher is unbalanced! Total Debit (Rs. {total_dr:,}) != Total Credit (Rs. {total_cr:,})'
                    })

                # Check credit balances for cash and bank in grid mode
                for acc, cr_sum in credits_per_acc.items():
                    a_code = str(acc.code)
                    a_name_lower = acc.name.lower()
                    is_cash_hand = (a_code in ['010101001', '1110001'] or 'cash in hand' in a_name_lower)
                    is_bank = ((a_code.startswith('010101') or a_code.startswith('1110')) and not is_cash_hand) or ('bank' in a_name_lower and not is_cash_hand)
                    if is_cash_hand or is_bank:
                        if acc.current_balance < cr_sum:
                            return JsonResponse({
                                'success': False,
                                'message': (
                                    f"❌ Payment Rejection: '{acc.name}' mein kafi raqam mojood nahi hai! "
                                    f"Mojooda Balance: Rs. {acc.current_balance:,.2f}, jabkay Draw/Credit Amount: Rs. {cr_sum:,.2f}."
                                )
                            })

                total_voucher_amt = total_dr

            user_name = request.session.get('user_name', 'Admin')
            voucher_no = generate_voucher_no(v_type)

            with transaction.atomic():
                voucher = Voucher.objects.create(
                    voucher_no=voucher_no,
                    voucher_type=v_type,
                    date=voucher_date,
                    reference_no=reference_no or voucher_no,
                    total_amount=total_voucher_amt,
                    remarks=remarks,
                    created_by=user_name,
                )

                # CASH RECORD SYNC
                net_cash_hand_change = Decimal('0')
                net_cash_bank_change = Decimal('0')

                for item in entries:
                    VoucherDetail.objects.create(
                        voucher=voucher,
                        account=item['account'],
                        debit=item['debit'],
                        credit=item['credit'],
                        narration=item['narration'],
                        party_id=item['party_id'],
                    )
                    # Update account balance in Chart of Accounts
                    _update_account_balance(item['account'], item['debit'], item['credit'])

                    # Check for Cash in Hand / Bank
                    acc_code = str(item['account'].code)
                    acc_name_lower = item['account'].name.lower()
                    if acc_code in ['010101001', '1110001'] or 'cash in hand' in acc_name_lower:
                        net_cash_hand_change += (item['debit'] - item['credit'])
                    elif acc_code.startswith('010101') or acc_code.startswith('1110') or 'bank' in acc_name_lower:
                        net_cash_bank_change += (item['debit'] - item['credit'])

                # If Cash Record is affected, update CashRecord table
                if net_cash_hand_change != 0 or net_cash_bank_change != 0:
                    last_cash = CashRecord.objects.order_by('-id').first()
                    if last_cash and last_cash.cash_in_hand is not None:
                        prev_hand = int(last_cash.cash_in_hand)
                    else:
                        prev_hand = int((cash_acc.current_balance if cash_acc else Decimal('0')) - net_cash_hand_change)

                    if last_cash and last_cash.cash_in_bank is not None:
                        prev_bank = int(last_cash.cash_in_bank)
                    else:
                        prev_bank = 0

                    new_hand = prev_hand + int(net_cash_hand_change)
                    new_bank = prev_bank + int(net_cash_bank_change)

                    max_cash_id = CashRecord.objects.aggregate(Max('id'))['id__max']
                    next_cash_id = 1 if max_cash_id is None else max_cash_id + 1

                    CashRecord.objects.create(
                        id=next_cash_id,
                        cash_in_hand=new_hand,
                        cash_in_bank=new_bank,
                        date=datetime.combine(voucher_date, _get_pk_now().time()),
                        discription=f"[{v_type}] #{voucher_no}: {remarks[:380]}" if remarks else f"[{v_type}] #{voucher_no}",
                    )

            return JsonResponse({
                'success': True,
                'message': f'{v_type} Voucher #{voucher_no} posted successfully! Total: Rs. {total_voucher_amt:,.2f}',
                'voucher_no': voucher_no,
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    # ------------ AJAX: GET VOUCHER DETAILS FOR PRINT / VIEW ------------
    if request.method == 'GET' and action == 'get_voucher':
        v_id = request.GET.get('id')
        voucher = get_object_or_404(Voucher, id=v_id)
        details = []
        for line in voucher.details.all().select_related('account', 'party'):
            details.append({
                'account_code': line.account.code,
                'account_name': line.account.name,
                'account_type': line.account.account_type,
                'party_name': line.party.company_name if line.party else (line.account.party.company_name if line.account.party else ''),
                'debit': str(line.debit),
                'credit': str(line.credit),
                'narration': line.narration or '',
            })
        return JsonResponse({
            'success': True,
            'voucher': {
                'id': voucher.id,
                'voucher_no': voucher.voucher_no,
                'voucher_type': voucher.voucher_type,
                'date': voucher.date.strftime('%d-%b-%Y'),
                'reference_no': voucher.reference_no or '',
                'total_amount': f"{voucher.total_amount:,.2f}",
                'remarks': voucher.remarks or '',
                'created_by': voucher.created_by or '',
                'created_at': voucher.created_at.strftime('%d-%b-%Y %I:%M %p') if voucher.created_at else '',
                'details': details,
            }
        })

    # ------------ AJAX: DELETE VOUCHER ------------
    if request.method == 'POST' and action == 'delete_voucher':
        try:
            data = json.loads(request.body)
            v_id = data.get('id')
            voucher = get_object_or_404(Voucher, id=v_id)

            with transaction.atomic():
                # Reverse account balances
                net_cash_hand_rev = Decimal('0')
                net_cash_bank_rev = Decimal('0')

                for line in voucher.details.all():
                    # Reverse: debit becomes credit, credit becomes debit
                    _update_account_balance(line.account, line.credit, line.debit)

                    acc_code = str(line.account.code)
                    acc_name_lower = line.account.name.lower()
                    # Reversal of (debit - credit) is (credit - debit)
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
                        date=_get_pk_now(),
                        discription=f"Reversal of Voucher #{voucher.voucher_no}",
                    )

                voucher_no = voucher.voucher_no
                voucher.delete()

            return JsonResponse({'success': True, 'message': f'Voucher {voucher_no} reversed and deleted.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    # ------------ DEFAULT PAGE DATA ------------
    level4_accounts = ChartOfAccount.objects.filter(level=4, is_active=True).order_by('code')

    # Cash in Hand account
    cash_account = ChartOfAccount.objects.filter(level=4, code='010101001').first() or ChartOfAccount.objects.filter(level=4, code='1110001').first() or ChartOfAccount.objects.filter(level=4, name__icontains='Cash in Hand').first()

    # Bank Accounts (Level 4 under 010101 or 1110 excluding cash in hand)
    bank_accounts = ChartOfAccount.objects.filter(
        level=4, is_active=True
    ).filter(Q(parent__code__in=['010101', '1110']) | Q(name__icontains='bank')).exclude(code__in=['010101001', '1110001']).order_by('code')

    # Party Accounts (Level 4 under 010102 or 1120 or with party linked)
    party_accounts = ChartOfAccount.objects.filter(
        level=4, is_active=True
    ).filter(Q(parent__code__in=['010102', '1120']) | Q(party__isnull=False)).order_by('name')

    # Expense heads
    expense_accounts = ChartOfAccount.objects.filter(
        level=4, is_active=True, account_type='Expense'
    ).order_by('code')

    # All parties (unified: customer, vendor, trader)
    parties = Parties.objects.all().order_by('company_name')

    # Recent Vouchers
    recent_vouchers = Voucher.objects.all().prefetch_related('details__account', 'details__party').order_by('-id')[:30]

    pk_now = _get_pk_now()

    context = {
        'level4_accounts': level4_accounts,
        'cash_account': cash_account,
        'bank_accounts': bank_accounts,
        'party_accounts': party_accounts,
        'expense_accounts': expense_accounts,
        'parties': parties,
        'recent_vouchers': recent_vouchers,
        'today_date': pk_now.strftime('%Y-%m-%d'),
        'next_cpv': generate_voucher_no('CPV'),
        'next_crv': generate_voucher_no('CRV'),
        'next_bpv': generate_voucher_no('BPV'),
        'next_brv': generate_voucher_no('BRV'),
        'next_jv': generate_voucher_no('JV'),
    }
    return render(request, 'accounts/voucher_entry.html', context)


# ===================================================================
# 3. GENERAL ACCOUNT LEDGER VIEW
# ===================================================================
def account_ledger(request):
    if not request.session.get('user_id'):
        return redirect('login')

    seed_default_chart_of_accounts()

    acc_id = request.GET.get('account')
    from_date_str = request.GET.get('from')
    to_date_str = request.GET.get('to')
    pk_now = _get_pk_now()

    level4_accounts = ChartOfAccount.objects.filter(level=4).order_by('code')

    if not from_date_str:
        from_date = pk_now.date().replace(day=1)
        from_date_str = from_date.strftime('%Y-%m-%d')
    else:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        except ValueError:
            from_date = pk_now.date().replace(day=1)

    if not to_date_str:
        to_date = pk_now.date()
        to_date_str = to_date.strftime('%Y-%m-%d')
    else:
        try:
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except ValueError:
            to_date = pk_now.date()

    selected_account = None
    ledger_entries = []
    opening_balance = Decimal('0')
    total_debit = Decimal('0')
    total_credit = Decimal('0')
    closing_balance = Decimal('0')

    if acc_id:
        selected_account = ChartOfAccount.objects.filter(id=acc_id).first()

    if not selected_account and level4_accounts.exists():
        selected_account = level4_accounts.first()
        acc_id = selected_account.id

    if selected_account:
        is_asset_exp = selected_account.account_type in ['Asset', 'Expense']

        # Calculate Opening Balance before from_date
        # 1. Base opening balance configured on account
        op_bal = selected_account.opening_balance

        # 2. Sum of all voucher lines before from_date
        past_lines = VoucherDetail.objects.filter(
            account=selected_account,
            voucher__date__lt=from_date
        )
        past_dr = past_lines.aggregate(s=Sum('debit'))['s'] or Decimal('0')
        past_cr = past_lines.aggregate(s=Sum('credit'))['s'] or Decimal('0')

        if is_asset_exp:
            opening_balance = op_bal + (past_dr - past_cr)
        else:
            opening_balance = op_bal + (past_cr - past_dr)

        # Transactions within [from_date, to_date]
        lines = VoucherDetail.objects.filter(
            account=selected_account,
            voucher__date__gte=from_date,
            voucher__date__lte=to_date
        ).select_related('voucher', 'party').order_by('voucher__date', 'voucher__id', 'id')

        running_balance = opening_balance
        for line in lines:
            dr = line.debit
            cr = line.credit
            total_debit += dr
            total_credit += cr

            if is_asset_exp:
                running_balance += (dr - cr)
            else:
                running_balance += (cr - dr)

            bal_type = ('Dr' if running_balance >= 0 else 'Cr') if is_asset_exp else ('Cr' if running_balance >= 0 else 'Dr')

            ledger_entries.append({
                'date': line.voucher.date,
                'voucher_no': line.voucher.voucher_no,
                'voucher_type': line.voucher.voucher_type,
                'reference_no': line.voucher.reference_no or '-',
                'narration': line.narration or line.voucher.remarks or '-',
                'party': line.party.company_name if line.party else '-',
                'debit': dr,
                'credit': cr,
                'balance': running_balance,
                'balance_abs': abs(running_balance),
                'balance_type': bal_type,
            })

        closing_balance = running_balance

        opening_balance_type = ('Dr' if opening_balance >= 0 else 'Cr') if is_asset_exp else ('Cr' if opening_balance >= 0 else 'Dr')
        closing_balance_type = ('Dr' if closing_balance >= 0 else 'Cr') if is_asset_exp else ('Cr' if closing_balance >= 0 else 'Dr')
    else:
        opening_balance_type = 'Dr'
        closing_balance_type = 'Dr'

    context = {
        'level4_accounts': level4_accounts,
        'selected_account': selected_account,
        'from_date': from_date_str,
        'to_date': to_date_str,
        'opening_balance': opening_balance,
        'opening_balance_abs': abs(opening_balance),
        'opening_balance_type': opening_balance_type,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'closing_balance': closing_balance,
        'closing_balance_abs': abs(closing_balance),
        'closing_balance_type': closing_balance_type,
        'ledger_entries': ledger_entries,
    }
    return render(request, 'accounts/account_ledger.html', context)
