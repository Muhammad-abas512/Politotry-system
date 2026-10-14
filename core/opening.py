from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime

from .models import (
    PurchaseReceiving,
    PurchasePayments,
    PurchasePaymentHistory,
    Parties,
    ReceiptHistory,
    SellsInvoice,
    Sellspayment,
)


def opening(request):
    # ============================================================
    # 1. DELETE
    # ============================================================
    delete_id = request.GET.get('delete_id')
    if delete_id:
        try:
            obj = PurchaseReceiving.objects.get(id=delete_id)
            p_code = obj.vendor_code
            obj.delete()

            if p_code:
                records = PurchaseReceiving.objects.filter(vendor_code=p_code)
                total_amount = records.aggregate(t=Sum('amount'))['t'] or 0
                total_payed  = records.aggregate(t=Sum('payed_amount'))['t'] or 0
                latest = records.order_by('-date', '-id').first()
                party_name = latest.vendor_name if latest else ''
                latest_description = (latest.discription or '') if latest else ''

                balance = float(total_amount) - float(total_payed)
                due      = balance if balance > 0 else 0
                advanced = abs(balance) if balance < 0 else 0

                h_qs = PurchasePaymentHistory.objects.filter(party_code=p_code)
                if h_qs.exists():
                    h = h_qs.first()
                    h.party_name    = party_name
                    h.date          = timezone.now()
                    h.totall_amount = int(total_amount)
                    h.payed_amount  = int(total_payed)
                    h.due           = int(due)
                    h.advanced      = int(advanced)
                    h.remarks       = latest_description[:500]
                    h.save()
                else:
                    PurchasePaymentHistory.objects.create(
                        party_code=p_code,
                        party_name=party_name,
                        date=timezone.now(),
                        totall_amount=int(total_amount),
                        payed_amount=int(total_payed),
                        due=int(due),
                        advanced=int(advanced),
                        remarks=latest_description[:500],
                    )

            messages.success(request, "Record deleted successfully")
        except PurchaseReceiving.DoesNotExist:
            messages.error(request, "Record not found")
        except Exception as e:
            print(f"[DELETE ERROR] {e}")
            messages.error(request, f"Delete failed: {e}")

        return redirect('opening')

    # ============================================================
    # 2. POST
    # ============================================================
    if request.method == 'POST':
        record_id   = request.POST.get('record_id', '').strip()
        party_code  = request.POST.get('party_code', '').strip()
        party_name  = request.POST.get('party_name', '').strip()
        date_str    = request.POST.get('date', '').strip()
        description = request.POST.get('description', '').strip()
        amount_str  = request.POST.get('amount', '0').strip()
        entry_type  = request.POST.get('entry_type', 'debit').strip()

        if not party_name or not amount_str:
            messages.error(request, "Party and Amount are required")
            return redirect('opening')

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d') if date_str else timezone.now()
        except ValueError:
            date_obj = timezone.now()

        try:
            final_amount = float(amount_str)
        except ValueError:
            final_amount = 0.0

        # ----------------------------------------------------------
        # Determine party type from Parties model
        # ----------------------------------------------------------
        party_obj = Parties.objects.filter(company_name=party_name).first()
        party_type = (party_obj.party_type or '').strip().lower() if party_obj else ''

        is_vendor_or_trader = party_type in ('vendor', 'trader')

        # ==========================================================
        # BRANCH A: VENDOR / TRADER  →  Purchase tables
        # ==========================================================
        if is_vendor_or_trader:
            try:
                # ---- Auto generate OPEN(PUR)-0001, 0002 ... ----
                last_rec = PurchaseReceiving.objects.filter(
                    purchase_number__startswith='OPEN(PUR)-'
                ).order_by('-id').first()

                if last_rec and last_rec.purchase_number:
                    try:
                        n = int(last_rec.purchase_number.split('-')[-1]) + 1
                    except (ValueError, IndexError, TypeError):
                        n = 1
                else:
                    n = 1
                open_pur_no = f"OPEN(PUR)-{n:04d}"

                if entry_type == 'credit':
                    # -------- CREDIT: PurchaseReceiving + PurchasePaymentHistory --------
                    PurchaseReceiving.objects.create(
                        purchase_number=open_pur_no,
                        vendor_code=party_code,
                        vendor_name=party_name,
                        date=date_obj,
                        status='Active',
                        amount=final_amount,
                        payed_amount=0,
                        remaining_weight='0',
                        discription=description,
                    )

                    PurchasePaymentHistory.objects.create(
                        party_code=party_code,
                        party_name=party_name,
                        date=date_obj,
                        totall_amount=int(final_amount),
                        payed_amount=0,
                        due=int(final_amount),
                        advanced=0,
                        remarks=description[:500],
                    )

                    messages.success(request, f"Credit entry saved (OPEN(PUR)-{n:04d})")
                    # NOTE: PurchasePayments gets NO entry on credit

                elif entry_type == 'debit':
                    # -------- DEBIT: PurchasePayments + PurchasePaymentHistory --------
                    PurchasePayments.objects.create(
                        purchase_number=open_pur_no,
                        party_code=party_code,
                        part_name=party_name,
                        date=date_obj,
                        amount=str(final_amount),
                        payment_mood=None,
                        remarks=description[:50] if description else '',
                    )

                    PurchasePaymentHistory.objects.create(
                        party_code=party_code,
                        party_name=party_name,
                        date=date_obj,
                        totall_amount=0,
                        payed_amount=int(final_amount),
                        due=0,
                        advanced=int(final_amount),
                        remarks=description[:500],
                    )

                    messages.success(request, f"Debit entry saved (OPEN(PUR)-{n:04d})")
                    # NOTE: PurchaseReceiving gets NO entry on debit

                else:
                    messages.error(request, "Invalid entry type")

            except Exception as e:
                print(f"[VENDOR/TRADER ERROR] {type(e).__name__}: {e}")
                messages.error(request, f"Save failed: {e}")

            return redirect('opening')

        # ==========================================================
        # BRANCH B: CUSTOMER (or anything else) → existing behavior
        # ==========================================================
        if entry_type == 'debit':
            try:
                last_sell = SellsInvoice.objects.order_by('-id').first()
                if last_sell and last_sell.sells_no:
                    try:
                        n = int(str(last_sell.sells_no).strip()) + 1
                    except (ValueError, TypeError):
                        n = 1
                else:
                    n = 1
                sells_no = f"{n:04d}"

                SellsInvoice.objects.create(
                    purchase_number='',
                    sells_no=sells_no,
                    customer_code=party_code,  
                    customer_name=party_name,
                    weight='0',
                    rate='0',
                    amount=str(final_amount),
                    received_amount='0',
                    remaining_amount=str(final_amount),
                    vehicle_no='0',
                    entry_date=date_obj,
                )

                ReceiptHistory.objects.create(
                    party_name=party_name,
                    part_code=party_code,
                    amount=int(final_amount),
                    received_amount='',
                    payment_method=None,
                    date=date_obj,
                    due=int(final_amount),
                    advance=0,
                )

                messages.success(request, f"Debit entry saved (Sells No: {sells_no})")
            except Exception as e:
                print(f"[DEBIT ERROR] {type(e).__name__}: {e}")
                messages.error(request, f"Debit save failed: {e}")

            return redirect('opening')

        if entry_type == 'credit':
            try:
                Sellspayment.objects.create(
                    sell_no='',
                    customer_code=party_code,  
                    customer_name=party_name,
                    weight='0',
                    rate='0',
                    vehicle_no='0',
                    amount='0',
                    received_amount=str(final_amount),
                    description=description[:50] if description else '',
                    payment_method=None,
                    entry_date=date_obj,
                )

                ReceiptHistory.objects.create(
                    party_name=party_name,
                    part_code=party_code,
                    amount=0,
                    received_amount=str(final_amount),
                    payment_method=None,
                    date=date_obj,
                    due=0,
                    advance=int(final_amount),
                )

                messages.success(request, "Credit entry saved (advance recorded)")
            except Exception as e:
                print(f"[CREDIT ERROR] {type(e).__name__}: {e}")
                messages.error(request, f"Credit save failed: {e}")

            return redirect('opening')

    # ============================================================
    # 3. GET
    # ============================================================
    edit_id = request.GET.get('edit_id')
    edit_obj = None
    if edit_id:
        try:
            edit_obj = PurchaseReceiving.objects.get(id=edit_id)
        except PurchaseReceiving.DoesNotExist:
            messages.error(request, "Record not found")

    try:
        all_parties = Parties.objects.all().order_by('company_name')
    except Exception as e:
        print(f"[PARTIES ERROR] {e}")
        all_parties = []

    history = PurchaseReceiving.objects.all().order_by('-date', '-id')

    context = {
        'all_parties': all_parties,
        'history': history,
        'edit_obj': edit_obj,
        'current_date': timezone.now().date(),
    }
    return render(request, 'opening/opening.html', context)


from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from .models import CashRecord


def cash(request):
    # Check if Cash Opening already exists
    existing_opening = (
        CashRecord.objects.filter(discription__icontains="opening").order_by("date", "id").first()
        or CashRecord.objects.order_by("date", "id").first()
    )
    is_locked = existing_opening is not None

    if request.method == "POST":
        if is_locked:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "کیش کی اوپننگ پہلے ہی درج ہو چکی ہے! یہ فارم لاک ہے اور دوبارہ اوپننگ درج نہیں کی جا سکتی۔",
                    "is_locked": True,
                },
                status=400,
            )

        cash_in_hand = request.POST.get("cashInHand")
        cash_in_bank = request.POST.get("cashInBank")
        discription = request.POST.get("discription")

        try:
            # Empty check aur Integer conversion
            hand_val = int(cash_in_hand) if cash_in_hand else 0
            bank_val = int(cash_in_bank) if cash_in_bank else 0

            desc = (discription or "").strip()
            if not desc:
                desc = "opening balance"
            elif "opening" not in desc.lower():
                desc = f"opening balance - {desc}"

            # Aapke existing model me direct save
            new_rec = CashRecord.objects.create(
                cash_in_hand=hand_val,
                cash_in_bank=bank_val,
                discription=desc,
                date=timezone.now(),  # Current date & time automatically save hogi
            )

            return JsonResponse(
                {
                    "status": "success",
                    "message": "کیش کی ابتدائی رقم (Opening Balance) کامیابی سے محفوظ ہو گئی ہے۔ اب یہ فارم لاک ہو چکا ہے۔",
                    "is_locked": True,
                    "cash_in_hand": new_rec.cash_in_hand,
                    "cash_in_bank": new_rec.cash_in_bank,
                    "discription": new_rec.discription,
                    "date": new_rec.date.strftime("%d-%m-%Y %H:%M") if new_rec.date else "",
                }
            )

        except Exception as e:
            return JsonResponse(
                {"status": "error", "message": f"Error: {str(e)}"}, status=400
            )

    total_opening = 0
    if existing_opening:
        total_opening = (existing_opening.cash_in_hand or 0) + (existing_opening.cash_in_bank or 0)

    context = {
        "is_locked": is_locked,
        "opening_record": existing_opening,
        "cash_in_hand": existing_opening.cash_in_hand if existing_opening else "",
        "cash_in_bank": existing_opening.cash_in_bank if existing_opening else "",
        "discription": existing_opening.discription if existing_opening else "",
        "opening_date": existing_opening.date if existing_opening else None,
        "total_opening": total_opening,
    }
    return render(request, "opening/cash.html", context)











