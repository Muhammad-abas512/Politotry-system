import io
from django.shortcuts import render, redirect
from django.http import JsonResponse, FileResponse, HttpResponse
from datetime import datetime, time
from django.db.models import Q, Sum
from .models import (
    Parties, SellsInvoice, Sellspayment, PurchaseReceiving,
    PurchasePayments, Expensedetail, CashRecord, Mortality,
    Voucher, VoucherDetail, ChartOfAccount
)
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def safe_decimal(val):
    if val is None or str(val).strip() == "":
        return 0.0
    try:
        return float(str(val).replace(',', '').strip())
    except (ValueError, TypeError):
        return 0.0

import io
from datetime import datetime, date, time
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse, HttpResponse # HttpResponse add kiya gaya hai
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def get_party_ledger(request):
    if not request.session.get('user_id'):
        return JsonResponse({'success': False, 'message': 'Unauthorized'}, status=401)

    party_id = request.GET.get('party')
    from_date_str = request.GET.get('from')
    to_date_str = request.GET.get('to')
    output_format = request.GET.get('format') 

    if not all([party_id, from_date_str, to_date_str]):
        return JsonResponse({'success': False, 'message': 'Missing parameters'})

    try:
        party = Parties.objects.get(id=party_id)
        target_name = (party.company_name if party.company_name else party.owner_name).strip()

        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        from_dt = datetime.combine(from_date, time.min)
        to_dt = datetime.combine(to_date, time.max)

        # Build comprehensive Party Matching Filters (by Name, Code, and Owner)
        sales_q = Q(customer_name__iexact=target_name)
        pur_q = Q(vendor_name__iexact=target_name)
        if party.code:
            sales_q |= Q(customer_code=party.code)
            pur_q |= Q(vendor_code=party.code)
        if party.company_name:
            sales_q |= Q(customer_name__iexact=party.company_name.strip())
            pur_q |= Q(vendor_name__iexact=party.company_name.strip())
        if party.owner_name:
            sales_q |= Q(customer_name__iexact=party.owner_name.strip())
            pur_q |= Q(vendor_name__iexact=party.owner_name.strip())

        receipt_q = sales_q | (Q(customer_code=party.code) if party.code else Q())
        vp_q = Q(part_name__iexact=target_name)
        if party.code:
            vp_q |= Q(party_code=party.code)
        if party.company_name:
            vp_q |= Q(part_name__iexact=party.company_name.strip())
        if party.owner_name:
            vp_q |= Q(part_name__iexact=party.owner_name.strip())

        # 1. OPENING BALANCE LOGIC
        old_sales = SellsInvoice.objects.filter(sales_q, entry_date__date__lt=from_date)
        old_receipts = Sellspayment.objects.filter(receipt_q, entry_date__date__lt=from_date)
        old_purchases = PurchaseReceiving.objects.filter(pur_q, date__date__lt=from_date)
        old_vendor_pays = PurchasePayments.objects.filter(vp_q, date__date__lt=from_date)

        # Voucher lines before from_date for this party
        party_q = Q(party=party) | Q(account__party=party)
        if target_name:
            party_q |= Q(account__name__iexact=target_name)

        voucher_filter = party_q & ~Q(voucher__voucher_no__startswith='PUR-') & ~Q(voucher__voucher_no__startswith='SLS-')

        past_vouchers = VoucherDetail.objects.filter(voucher_filter, voucher__date__lt=from_date)
        past_v_dr = sum(safe_decimal(v.debit) for v in past_vouchers)
        past_v_cr = sum(safe_decimal(v.credit) for v in past_vouchers)

        # Base opening balance from Level 4 Chart of Account for this party
        party_acc = ChartOfAccount.objects.filter(party=party, level=4).first()
        if not party_acc and party.code:
            party_acc = ChartOfAccount.objects.filter(code=party.code, level=4).first()
        base_opening = safe_decimal(party_acc.opening_balance) if party_acc else 0.0

        op_dr = sum(safe_decimal(s.amount) for s in old_sales) + sum(safe_decimal(vp.amount) for vp in old_vendor_pays) + past_v_dr
        op_cr = sum(safe_decimal(r.received_amount) or safe_decimal(r.amount) for r in old_receipts) + sum(safe_decimal(p.amount) for p in old_purchases) + past_v_cr
        opening_balance = base_opening + op_dr - op_cr

        # 2. TRANSACTIONS
        combined = []
        for inv in SellsInvoice.objects.filter(sales_q, entry_date__date__gte=from_date, entry_date__date__lte=to_date).order_by('entry_date', 'id'):
            combined.append({
                'dt': inv.entry_date,
                'id': inv.id or 0,
                'priority': 1,
                'desc': f"Sale Invoice #{inv.sells_no}",
                'w': inv.weight,
                'mr': '-',
                'vr': inv.rate,
                'dr': safe_decimal(inv.amount),
                'cr': 0.0
            })
        for rec in Sellspayment.objects.filter(receipt_q, entry_date__date__gte=from_date, entry_date__date__lte=to_date).order_by('entry_date', 'id'):
            combined.append({
                'dt': rec.entry_date,
                'id': rec.id or 0,
                'priority': 2,
                'desc': rec.description or "Customer Receipt",
                'w': rec.weight,
                'mr': '-',
                'vr': rec.rate,
                'dr': 0.0,
                'cr': safe_decimal(rec.received_amount) or safe_decimal(rec.amount)
            })
        for pur in PurchaseReceiving.objects.filter(pur_q, date__date__gte=from_date, date__date__lte=to_date).order_by('date', 'id'):
            combined.append({
                'dt': pur.date,
                'id': pur.id or 0,
                'priority': 1,
                'desc': f"Purchase Invoice #{pur.purchase_number}",
                'w': pur.weight,
                'mr': pur.market_rate,
                'vr': pur.vendor_rate,
                'dr': 0.0,
                'cr': safe_decimal(pur.amount)
            })
        for vp in PurchasePayments.objects.filter(vp_q, date__date__gte=from_date, date__date__lte=to_date).order_by('date', 'id'):
            combined.append({
                'dt': vp.date,
                'id': vp.id or 0,
                'priority': 2,
                'desc': vp.remarks or "Vendor Payment",
                'w': '-',
                'mr': '-',
                'vr': '-',
                'dr': safe_decimal(vp.amount),
                'cr': 0.0
            })

        period_vouchers = VoucherDetail.objects.filter(
            voucher_filter, voucher__date__gte=from_date, voucher__date__lte=to_date
        ).select_related('voucher').order_by('voucher__date', 'voucher__id', 'id')
        for v in period_vouchers:
            if v.voucher.created_at:
                v_created = timezone.localtime(v.voucher.created_at) if hasattr(v.voucher.created_at, 'tzinfo') and v.voucher.created_at.tzinfo else v.voucher.created_at
                v_dt = datetime.combine(v.voucher.date, v_created.time())
            else:
                v_dt = datetime.combine(v.voucher.date, time.min)

            v_remarks = (v.narration or v.voucher.remarks or '').strip()
            desc = f"{v.voucher.voucher_no} ({v.voucher.voucher_type})"
            if v_remarks:
                desc += f" - {v_remarks}"
            combined.append({
                'dt': v_dt,
                'id': v.voucher.id or 0,
                'line_id': v.id or 0,
                'priority': 2,
                'desc': desc,
                'w': '-',
                'mr': '-',
                'vr': '-',
                'dr': safe_decimal(v.debit),
                'cr': safe_decimal(v.credit)
            })

        def _get_sort_key(item):
            d = item.get('dt')
            if not d:
                d_date = from_date
                d_time = time.min
            elif hasattr(d, 'hour'):
                if hasattr(d, 'tzinfo') and d.tzinfo is not None:
                    try:
                        d = timezone.localtime(d).replace(tzinfo=None)
                    except Exception:
                        d = d.replace(tzinfo=None)
                d_date = d.date()
                d_time = d.time()
            elif isinstance(d, date):
                d_date = d
                d_time = time.min
            else:
                d_date = from_date
                d_time = time.min

            return (d_date, d_time, item.get('id', 0), item.get('line_id', 0), item.get('priority', 1))

        combined.sort(key=_get_sort_key)

        # 3. PDF GENERATION (ReportLab)
        if output_format == 'pdf':
            buffer = io.BytesIO()
            # A4 Portrait Page
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=50)
            elements = []
            styles = getSampleStyleSheet()

            # --- Custom Styles ---
            title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontSize=22, textColor=colors.navy, spaceAfter=5)
            subtitle_style = ParagraphStyle('SubTitle', fontSize=12, alignment=1, spaceAfter=20)
            footer_style = ParagraphStyle('FooterStyle', fontSize=9, textColor=colors.grey, alignment=1)

            # --- Header Content ---
            elements.append(Paragraph("<b>MJ POULTRIES AND GROUP</b>", title_style))
            elements.append(Paragraph(f"Party Ledger: <b>{target_name}</b>", styles['Normal']))
            elements.append(Paragraph(f"Period: {from_date.strftime('%d-%b-%Y')} to {to_date.strftime('%d-%b-%Y')}", styles['Normal']))
            elements.append(Spacer(1, 15))

            # --- Table Data ---
            data = [["Sr#", "Date", "Description", "M-Rate", "Weight", "Rate", "Debit", "Credit", "Balance"]]
            
            # Opening Balance Row
            data.append(["-", from_date.strftime('%d-%b-%Y'), "Opening Balance", "-", "-", "-", "-", "-", f"{abs(opening_balance):,.2f} {'Dr' if opening_balance >=0 else 'Cr'}"])

            r_bal = opening_balance
            for i, item in enumerate(combined, 1):
                r_bal += (item['dr'] - item['cr'])
                data.append([
                    i, 
                    item['dt'].strftime('%d-%b-%Y') if item['dt'] else '',
                    item['desc'],
                    item['mr'],
                    item['w'],
                    item['vr'],
                    f"{item['dr']:,.2f}" if item['dr'] > 0 else "-",
                    f"{item['cr']:,.2f}" if item['cr'] > 0 else "-",
                    f"{abs(r_bal):,.2f} {'Dr' if r_bal >= 0 else 'Cr'}"
                ])

            # --- Table Styling ---
            table = Table(data, colWidths=[25, 65, 140, 45, 45, 45, 55, 55, 60])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke])
            ]))
            
            elements.append(table)

            # --- Footer Static Text ---
            def add_footer(canvas, doc):
                canvas.saveState()
                canvas.setStrokeColor(colors.navy)
                canvas.line(30, 40, A4[0]-30, 40)
                footer_text = "Developed by Programing zone | Contact: 03157821373"
                canvas.setFont("Helvetica-Oblique", 8)
                canvas.setFillColor(colors.grey)
                canvas.drawCentredString(A4[0]/2.0, 25, footer_text)
                canvas.restoreState()

            # Build PDF
            doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
            
            # --- YAHAN MAIN FIX KIYA GAYA HAI ---
            pdf_bytes = buffer.getvalue()  # Bytes nikal liye
            buffer.close()                 # Buffer close kar diya (Memory free)

            # FileResponse ki jagah HttpResponse use karein
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="Ledger_{target_name}.pdf"'
            return response

        # 4. JSON RESPONSE (For Table View)
        final_list = []
        running_bal = opening_balance
        total_debit, total_credit = 0.0, 0.0
        for idx, item in enumerate(combined, 1):
            running_bal += (item['dr'] - item['cr'])
            total_debit += item['dr']
            total_credit += item['cr']
            final_list.append({
                'sr': idx, 
                'party_name': target_name, 
                'date': item['dt'].strftime('%d-%b-%Y') if item['dt'] else '',
                'description': item['desc'], 
                'weight': item['w'], 
                'm_rate': item['mr'], 
                'v_rate': item['vr'],
                'debit': round(item['dr'], 2), 
                'credit': round(item['cr'], 2),
                'balance': round(abs(running_bal), 2), 
                'balance_type': "Dr" if running_bal >= 0 else "Cr"
            })

        return JsonResponse({
            'success': True, 
            'party_name': target_name,
            'opening_balance': round(abs(opening_balance), 2), 
            'opening_type': "Dr" if opening_balance >= 0 else "Cr",
            'total_debit': round(total_debit, 2), 
            'total_credit': round(total_credit, 2),
            'closing_balance': round(abs(running_bal), 2), 
            'closing_type': "Dr" if running_bal >= 0 else "Cr",
            'transactions': final_list
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def party_ledger(request):
    if not request.session.get('user_id'):
        return redirect('login')
    return render(request, 'Reports/party_ledger.html', {
        'parties': Parties.objects.all().order_by('company_name')
    })



from django.http import HttpResponse
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Frame, KeepInFrame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO

def export_ledger_pdf(request):
    # 1. Get Parameters (Same as your JSON view)
    party_id = request.GET.get('party')
    from_date_str = request.GET.get('from')
    to_date_str = request.GET.get('to')
    
    party = Parties.objects.get(id=party_id)
    target_name = (party.company_name if party.company_name else party.owner_name).strip()
    from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
    to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
    from_dt = datetime.combine(from_date, time.min)
    to_dt = datetime.combine(to_date, time.max)

    # --- Yahan wahi logic paste karein jo aapne get_party_ledger mein likha hai (Data Fetching) ---
    # (Main shortcut le raha hoon calculations ka logic wahi hai jo aapne upar diya tha)
    
    # [Start of calculation logic]
    old_sales = SellsInvoice.objects.filter(customer_name__iexact=target_name, entry_date__lt=from_dt)
    old_receipts = Sellspayment.objects.filter(customer_name__iexact=target_name, entry_date__lt=from_dt)
    old_purchases = PurchaseReceiving.objects.filter(vendor_name__iexact=target_name, date__lt=from_dt)
    old_vendor_pays = PurchasePayments.objects.filter(part_name__iexact=target_name, date__lt=from_dt)

    party_q = Q(party=party) | Q(account__party=party)
    if target_name:
        party_q |= Q(account__name__iexact=target_name)

    past_vouchers = VoucherDetail.objects.filter(party_q, voucher__date__lt=from_date).exclude(voucher__voucher_no__startswith='PUR-').exclude(voucher__voucher_no__startswith='SLS-')
    past_v_dr = sum(safe_decimal(v.debit) for v in past_vouchers)
    past_v_cr = sum(safe_decimal(v.credit) for v in past_vouchers)

    party_acc = ChartOfAccount.objects.filter(party=party, level=4).first()
    if not party_acc and party.code:
        party_acc = ChartOfAccount.objects.filter(code=party.code, level=4).first()
    base_opening = safe_decimal(party_acc.opening_balance) if party_acc else 0.0

    op_dr = sum(safe_decimal(s.amount) for s in old_sales) + sum(safe_decimal(vp.amount) for vp in old_vendor_pays) + past_v_dr
    op_cr = sum(safe_decimal(r.received_amount) or safe_decimal(r.amount) for r in old_receipts) + sum(safe_decimal(p.amount) for p in old_purchases) + past_v_cr
    opening_balance = base_opening + op_dr - op_cr

    combined = []
    for inv in SellsInvoice.objects.filter(customer_name__iexact=target_name, entry_date__range=[from_dt, to_dt]).order_by('entry_date', 'id'):
        combined.append({
            'date': inv.entry_date.date(),
            'sort_dt': inv.entry_date,
            'id': inv.id or 0,
            'priority': 1,
            'code': inv.sells_no or f"SI-{inv.id}",
            'desc': f"Sale Invoice #{inv.sells_no}",
            'dr': safe_decimal(inv.amount),
            'cr': 0.0
        })
    for rec in Sellspayment.objects.filter(customer_name__iexact=target_name, entry_date__range=[from_dt, to_dt]).order_by('entry_date', 'id'):
        combined.append({
            'date': rec.entry_date.date(),
            'sort_dt': rec.entry_date,
            'id': rec.id or 0,
            'priority': 2,
            'code': rec.sell_no or f"REC-{rec.id}",
            'desc': rec.description or "Customer Receipt",
            'dr': 0.0,
            'cr': safe_decimal(rec.received_amount) or safe_decimal(rec.amount)
        })
    for pur in PurchaseReceiving.objects.filter(vendor_name__iexact=target_name, date__range=[from_dt, to_dt]).order_by('date', 'id'):
        combined.append({
            'date': pur.date.date(),
            'sort_dt': pur.date,
            'id': pur.id or 0,
            'priority': 1,
            'code': pur.purchase_number or f"PI-{pur.id}",
            'desc': f"Purchase Invoice #{pur.purchase_number}",
            'dr': 0.0,
            'cr': safe_decimal(pur.amount)
        })
    for vp in PurchasePayments.objects.filter(part_name__iexact=target_name, date__range=[from_dt, to_dt]).order_by('date', 'id'):
        combined.append({
            'date': vp.date.date(),
            'sort_dt': vp.date,
            'id': vp.id or 0,
            'priority': 2,
            'code': vp.purchase_number or f"PAY-{vp.id}",
            'desc': vp.remarks or "Vendor Payment",
            'dr': safe_decimal(vp.amount),
            'cr': 0.0
        })

    period_vouchers = VoucherDetail.objects.filter(
        party_q, voucher__date__range=[from_date, to_date]
    ).exclude(voucher__voucher_no__startswith='PUR-').exclude(voucher__voucher_no__startswith='SLS-').select_related('voucher').order_by('voucher__date', 'voucher__id', 'id')
    for v in period_vouchers:
        if v.voucher.created_at:
            v_created = timezone.localtime(v.voucher.created_at) if hasattr(v.voucher.created_at, 'tzinfo') and v.voucher.created_at.tzinfo else v.voucher.created_at
            v_dt = datetime.combine(v.voucher.date, v_created.time())
        else:
            v_dt = datetime.combine(v.voucher.date, time.min)

        v_remarks = (v.narration or v.voucher.remarks or '').strip()
        v_desc = f"{v.voucher.voucher_no} ({v.voucher.voucher_type})"
        if v_remarks:
            v_desc += f" - {v_remarks}"
        combined.append({
            'date': v.voucher.date,
            'sort_dt': v_dt,
            'id': v.voucher.id or 0,
            'line_id': v.id or 0,
            'priority': 2,
            'code': v.voucher.voucher_no,
            'desc': v_desc,
            'dr': safe_decimal(v.debit),
            'cr': safe_decimal(v.credit)
        })

    def _normalize_pdf_sort_key(x):
        dt = x.get('sort_dt')
        if not dt:
            d_date, d_time = from_date, time.min
        elif hasattr(dt, 'hour'):
            if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
                try:
                    dt = timezone.localtime(dt).replace(tzinfo=None)
                except Exception:
                    dt = dt.replace(tzinfo=None)
            d_date, d_time = dt.date(), dt.time()
        elif isinstance(dt, date):
            d_date, d_time = dt, time.min
        else:
            d_date, d_time = from_date, time.min
        return (d_date, d_time, x.get('id', 0), x.get('line_id', 0), x.get('priority', 1))

    combined.sort(key=_normalize_pdf_sort_key)
    # [End of calculation logic]

    # PDF Setup
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    # 1. Header (Navy Blue)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=20, textColor=colors.white, alignment=1, spaceAfter=10)
    navy_header = Table([[Paragraph("MJ POLUTRIES GROUP", header_style)]], colWidths=[780])
    navy_header.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.navy), ('PADDING', (0, 0), (-1, -1), 15)]))
    elements.append(navy_header)
    elements.append(Spacer(1, 15))

    # 2. Party & Date Info
    info_data = [
        [f"Party Name: {target_name}", f"Report Period: {from_date.strftime('%d-%b-%Y')} to {to_date.strftime('%d-%b-%Y')}"]
    ]
    info_table = Table(info_data, colWidths=[390, 390])
    info_table.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,-1), 10)]))
    elements.append(info_table)
    elements.append(Spacer(1, 15))

    # 3. Summary Cards (Designed as table)
    running_bal = opening_balance
    total_debit = sum(i['dr'] for i in combined)
    total_credit = sum(i['cr'] for i in combined)
    closing_bal = opening_balance + total_debit - total_credit

    def get_bal_str(val):
        t = "Dr" if val >= 0 else "Cr"
        return f"Rs {abs(val):,.2f} {t}"

    summary_data = [
        ["OPENING BALANCE", "TOTAL DEBIT (DR)", "TOTAL CREDIT (CR)", "CLOSING BALANCE"],
        [get_bal_str(opening_balance), f"Rs {total_debit:,.2f}", f"Rs {total_credit:,.2f}", get_bal_str(closing_bal)]
    ]
    summary_table = Table(summary_data, colWidths=[195]*4)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), colors.dodgerblue),
        ('BACKGROUND', (1,0), (1,0), colors.firebrick),
        ('BACKGROUND', (2,0), (2,0), colors.forestgreen),
        ('BACKGROUND', (3,0), (3,0), colors.darkslategray),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 1, colors.whitesmoke),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # 4. Ledger Table
    data = [["Sr#", "Date", "Description", "Debit", "Credit", "Balance"]]
    curr_bal = opening_balance
    for idx, item in enumerate(combined, 1):
        curr_bal += (item['dr'] - item['cr'])
        data.append([
            idx,
            item['code'],
            item['date'].strftime('%d-%b-%y'),
            Paragraph(item['desc'], styles['Normal']),
            f"{item['dr']:,.2f}" if item['dr'] > 0 else "-",
            f"{item['cr']:,.2f}" if item['cr'] > 0 else "-",
            f"{abs(curr_bal):,.2f} {'Dr' if curr_bal >= 0 else 'Cr'}"
        ])

    ledger_table = Table(data, colWidths=[30, 90, 80, 270, 90, 90, 130], repeatRows=1)
    ledger_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white])
    ]))
    elements.append(ledger_table)
    
    # 5. Footer
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=1)
    elements.append(Paragraph("Developed by Programming Zone", footer_style))

    doc.build(elements)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Ledger_{target_name}.pdf"'
    response.write(buffer.getvalue())
    buffer.close()
    return response



from datetime import datetime
from io import BytesIO
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from .models import Parties, PurchaseReceivingView


# =========================================================
# PURCHASE REPORT
# =========================================================
def purchase_report(request):
    if not request.session.get('user_id'):
        return redirect('login')

    party_name = request.GET.get('party_name', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    parties = (
        Parties.objects
        .exclude(company_name__isnull=True)
        .exclude(company_name='')
        .order_by('company_name')
    )

    records = PurchaseReceivingView.objects.all()

    if party_name:
        party_obj = Parties.objects.filter(company_name=party_name).first() or Parties.objects.filter(owner_name=party_name).first()
        if party_obj:
            p_filter = Q(vendor_name__iexact=party_name)
            if party_obj.company_name:
                p_filter |= Q(vendor_name__iexact=party_obj.company_name.strip())
            if party_obj.owner_name:
                p_filter |= Q(vendor_name__iexact=party_obj.owner_name.strip())
            records = records.filter(p_filter)
        else:
            records = records.filter(vendor_name__iexact=party_name)

    if from_date:
        records = records.filter(date__date__gte=from_date)

    if to_date:
        records = records.filter(date__date__lte=to_date)

    records = records.order_by('date', 'id')

    def num(value):
        try:
            return Decimal(str(value or '0').replace(',', '').strip())
        except (InvalidOperation, ValueError, TypeError):
            return Decimal('0')

    # Totals
    total_weight = Decimal('0')
    total_amount = Decimal('0')
    total_paid = Decimal('0')
    total_remaining = Decimal('0')
    for r in records:
        w = num(r.weight)
        amt = num(r.amount)
        paid = num(r.payed_amount)
        rem = num(r.remaining_amount) if r.remaining_amount is not None else (amt - paid)
        total_weight += w
        total_amount += amt
        total_paid += paid
        total_remaining += rem

    return render(request, 'Reports/purchase_report.html', {
        'parties': parties,
        'records': records,
        'selected_party': party_name,
        'from_date': from_date,
        'to_date': to_date,
        'total_weight': total_weight,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_remaining': total_remaining,
    })


# =========================================================
# PURCHASE REPORT PDF
# =========================================================
def purchase_report_print(request):
    if not request.session.get('user_id'):
        return redirect('login')

    party_name = request.GET.get('party_name', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    records = PurchaseReceivingView.objects.all()

    if party_name:
        party_obj = Parties.objects.filter(company_name=party_name).first() or Parties.objects.filter(owner_name=party_name).first()
        if party_obj:
            p_filter = Q(vendor_name__iexact=party_name)
            if party_obj.company_name:
                p_filter |= Q(vendor_name__iexact=party_obj.company_name.strip())
            if party_obj.owner_name:
                p_filter |= Q(vendor_name__iexact=party_obj.owner_name.strip())
            records = records.filter(p_filter)
        else:
            records = records.filter(vendor_name__iexact=party_name)

    if from_date:
        records = records.filter(date__date__gte=from_date)

    if to_date:
        records = records.filter(date__date__lte=to_date)

    records = records.order_by('date', 'id')

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=8 * mm,
        rightMargin=8 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title='Purchase Report'
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'title',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        alignment=1,
        textColor=colors.HexColor('#1e293b')
    )

    info_style = ParagraphStyle(
        'info',
        parent=styles['Normal'],
        fontSize=9,
        alignment=1,
        textColor=colors.HexColor('#64748b')
    )

    elements = [
        Paragraph('PURCHASE REPORT', title_style),
        Spacer(1, 2 * mm),
    ]

    party_text = party_name if party_name else 'All Vendors / Traders'
    if from_date and to_date:
        date_text = f'From: {from_date} &nbsp;&nbsp; | &nbsp;&nbsp; To: {to_date}'
    elif from_date:
        date_text = f'From: {from_date}'
    elif to_date:
        date_text = f'To: {to_date}'
    else:
        date_text = 'All Purchases'

    elements.append(
        Paragraph(
            f'Party: {party_text} &nbsp;&nbsp; | &nbsp;&nbsp; {date_text}',
            info_style
        )
    )

    elements.append(Spacer(1, 5 * mm))

    # No Status column
    data = [[
        '#', 'Purchase #', 'Date', 'Vendor / Trader',
        'Vehicle', 'Weight', 'Vendor Rate', 'Market Rate',
        'Amount', 'Paid', 'Remaining'
    ]]

    total_weight = 0
    total_amount = 0
    total_paid = 0
    total_remaining = 0

    for i, row in enumerate(records, 1):
        weight = row.weight or 0
        amount = row.amount or 0
        paid = row.payed_amount or 0
        remaining = row.remaining_amount or 0

        total_weight += weight
        total_amount += amount
        total_paid += paid
        total_remaining += remaining

        data.append([
            i,
            row.purchase_number or '-',
            row.date.strftime('%d-%m-%Y') if row.date else '-',
            row.vendor_name or '-',
            row.vehicle_number or '-',
            f'{weight:,.0f}',
            f'{(row.vendor_rate or 0):,.0f}',
            f'{(row.market_rate or 0):,.0f}',
            f'{amount:,.0f}',
            f'{paid:,.0f}',
            f'{remaining:,.0f}',
        ])

    # Grand total
    data.append([
        '', '', '', 'GRAND TOTAL', '',
        f'{total_weight:,.0f}',
        '', '',
        f'{total_amount:,.0f}',
        f'{total_paid:,.0f}',
        f'{total_remaining:,.0f}',
    ])

    table = Table(
        data,
        repeatRows=1,
        colWidths=[
            9*mm, 21*mm, 20*mm, 39*mm, 25*mm,
            20*mm, 23*mm, 23*mm, 27*mm, 27*mm, 27*mm
        ]
    )

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [
            colors.white,
            colors.HexColor('#f8fafc')
        ]),
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#cbd5e1')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#334155')),
    ]))

    elements.append(table)
    doc.build(elements)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="purchase_report.pdf"'

    buffer.close()
    return response





from decimal import Decimal, InvalidOperation
from io import BytesIO

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from .models import Parties, SellsInvoice


def sells_report(request):
    if not request.session.get('user_id'):
        return redirect('login')

    party = (request.GET.get('party_name') or '').strip()
    from_date = (request.GET.get('from_date') or '').strip()
    to_date = (request.GET.get('to_date') or '').strip()

    parties = (
        Parties.objects
        .exclude(company_name__isnull=True)
        .exclude(company_name='')
        .order_by('company_name')
    )

    records = SellsInvoice.objects.all()

    if party:
        party_obj = Parties.objects.filter(company_name=party).first() or Parties.objects.filter(owner_name=party).first()
        if party_obj:
            p_filter = Q(customer_name__iexact=party) | Q(customer_code=party)
            if party_obj.company_name:
                p_filter |= Q(customer_name__iexact=party_obj.company_name.strip())
            if party_obj.owner_name:
                p_filter |= Q(customer_name__iexact=party_obj.owner_name.strip())
            if party_obj.code:
                p_filter |= Q(customer_code=party_obj.code.strip())
            records = records.filter(p_filter)
        else:
            records = records.filter(Q(customer_name__iexact=party) | Q(customer_code=party))

    if from_date:
        records = records.filter(entry_date__date__gte=from_date)

    if to_date:
        records = records.filter(entry_date__date__lte=to_date)

    records = records.order_by('entry_date', 'id')

    def num(value):
        try:
            return Decimal(str(value or '0').replace(',', '').strip())
        except (InvalidOperation, ValueError, TypeError):
            return Decimal('0')

    total_weight = Decimal('0')
    total_amount = Decimal('0')
    total_received = Decimal('0')
    total_remaining = Decimal('0')

    for row in records:
        w = num(row.weight)
        amt = num(row.amount)
        rec = num(row.received_amount)
        rem = num(row.remaining_amount) if (row.remaining_amount is not None and str(row.remaining_amount).strip() != '') else (amt - rec)
        row.calc_remaining = rem
        total_weight += w
        total_amount += amt
        total_received += rec
        total_remaining += rem

    return render(request, 'Reports/sells_report.html', {
        'parties': parties,
        'records': records,
        'selected_party': party,
        'from_date': from_date,
        'to_date': to_date,
        'total_weight': total_weight,
        'total_amount': total_amount,
        'total_received': total_received,
        'total_remaining': total_remaining,
    })


def sells_report_print(request):
    if not request.session.get('user_id'):
        return redirect('login')

    party = (request.GET.get('party_name') or '').strip()
    from_date = (request.GET.get('from_date') or '').strip()
    to_date = (request.GET.get('to_date') or '').strip()

    records = SellsInvoice.objects.all()

    if party:
        party_obj = Parties.objects.filter(company_name=party).first() or Parties.objects.filter(owner_name=party).first()
        if party_obj:
            p_filter = Q(customer_name__iexact=party) | Q(customer_code=party)
            if party_obj.company_name:
                p_filter |= Q(customer_name__iexact=party_obj.company_name.strip())
            if party_obj.owner_name:
                p_filter |= Q(customer_name__iexact=party_obj.owner_name.strip())
            if party_obj.code:
                p_filter |= Q(customer_code=party_obj.code.strip())
            records = records.filter(p_filter)
        else:
            records = records.filter(Q(customer_name__iexact=party) | Q(customer_code=party))

    if from_date:
        records = records.filter(entry_date__date__gte=from_date)

    if to_date:
        records = records.filter(entry_date__date__lte=to_date)

    records = records.order_by('entry_date', 'id')

    def num(value):
        try:
            return Decimal(str(value or '0').replace(',', '').strip())
        except (InvalidOperation, ValueError, TypeError):
            return Decimal('0')

    def fmt(value):
        return f'{num(value):,.2f}'.rstrip('0').rstrip('.')

    data = [[
        '#', 'Sell #', 'Purchase #', 'Date', 'Customer / Trader',
        'Vehicle', 'Weight', 'Rate', 'Amount', 'Received', 'Remaining'
    ]]

    tw = ta = tr = trem = Decimal('0')

    for i, row in enumerate(records, 1):
        weight, amount = num(row.weight), num(row.amount)
        received = num(row.received_amount)
        remaining = num(row.remaining_amount) if (row.remaining_amount is not None and str(row.remaining_amount).strip() != '') else (amount - received)
        tw += weight
        ta += amount
        tr += received
        trem += remaining

        data.append([
            i,
            row.sells_no or '-',
            row.purchase_number or '-',
            row.entry_date.strftime('%d-%m-%Y') if row.entry_date else '-',
            row.customer_name or '-',
            row.vehicle_no or '-',
            fmt(weight),
            fmt(row.rate),
            fmt(amount),
            fmt(received),
            fmt(remaining),
        ])

    data.append([
        '', '', '', '', 'GRAND TOTAL', '',
        fmt(tw), '', fmt(ta), fmt(tr), fmt(trem)
    ])

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=8*mm, rightMargin=8*mm,
        topMargin=10*mm, bottomMargin=10*mm,
        title='Sells Report'
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        'title', parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18, alignment=1, textColor=colors.HexColor('#1e293b')
    )
    info = ParagraphStyle(
        'info', parent=styles['Normal'],
        fontSize=9, alignment=1, textColor=colors.HexColor('#64748b')
    )

    table = Table(data, repeatRows=1, colWidths=[
        8*mm, 18*mm, 21*mm, 20*mm, 39*mm, 24*mm,
        19*mm, 20*mm, 27*mm, 27*mm, 27*mm
    ])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), .35, colors.HexColor('#cbd5e1')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (4, 1), (4, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#334155')),
    ]))

    party_text = party if party else 'All Customers / Traders'
    if from_date and to_date:
        date_text = f'From: {from_date} &nbsp;&nbsp; | &nbsp;&nbsp; To: {to_date}'
    elif from_date:
        date_text = f'From: {from_date}'
    elif to_date:
        date_text = f'To: {to_date}'
    else:
        date_text = 'All Sales Records'

    doc.build([
        Paragraph('SELLS REPORT', title),
        Spacer(1, 2*mm),
        Paragraph(f'Party: {party_text} &nbsp;&nbsp; | &nbsp;&nbsp; {date_text}', info),
        Spacer(1, 5*mm),
        table
    ])

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="sells_report.pdf"'
    buffer.close()
    return response




from decimal import Decimal, InvalidOperation
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from .models import SellsInvoice, PurchaseReceivingView, Expensedetail, Mortality


def profit_loss_report(request):
    if not request.session.get('user_id'):
        return redirect('login')

    today = timezone.localdate().strftime('%Y-%m-%d')
    from_date = request.GET.get('from_date') or today
    to_date = request.GET.get('to_date') or today

    def dec(value):
        try:
            return Decimal(str(value or '0').replace(',', '').strip())
        except (InvalidOperation, ValueError, TypeError):
            return Decimal('0')

    sales = SellsInvoice.objects.filter(
        entry_date__date__gte=from_date,
        entry_date__date__lte=to_date
    )

    purchases = PurchaseReceivingView.objects.filter(
        date__date__gte=from_date,
        date__date__lte=to_date
    )

    expenses = Expensedetail.objects.filter(
        date__date__gte=from_date,
        date__date__lte=to_date
    ).order_by('head_name')

    mortality = Mortality.objects.filter(
        entry_date__gte=from_date,
        entry_date__lte=to_date
    ).order_by('entry_date', 'id')

    total_sales = sum((dec(x.amount) for x in sales), Decimal('0'))
    total_cogs = sum((dec(x.amount) for x in purchases), Decimal('0'))

    # Expenses group by Head
    expense_groups = {}
    for row in expenses:
        name = (row.head_name or 'Other Expense').strip()
        expense_groups[name] = expense_groups.get(name, Decimal('0')) + dec(row.amount)

    expense_rows = [
        {'name': name, 'amount': amount}
        for name, amount in expense_groups.items()
    ]

    total_expenses = sum(expense_groups.values(), Decimal('0'))
    gross_profit = total_sales - total_cogs
    net_profit = gross_profit - total_expenses

    total_mortality_weight = sum(
        (dec(x.weight) for x in mortality), Decimal('0')
    )
    total_mortality_amount = sum(
        (dec(x.amount) for x in mortality), Decimal('0')
    )

    return render(request, 'Reports/profit_loss_report.html', {
        'from_date': from_date,
        'to_date': to_date,
        'total_sales': total_sales,
        'total_cogs': total_cogs,
        'gross_profit': gross_profit,
        'expense_rows': expense_rows,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'mortality': mortality,
        'total_mortality_weight': total_mortality_weight,
        'total_mortality_amount': total_mortality_amount,
    })



from decimal import Decimal, InvalidOperation
from io import BytesIO
import os
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from .models import SellsInvoice, PurchaseReceivingView, Expensedetail, Mortality


def profit_loss_report_print(request):
    if not request.session.get('user_id'):
        return redirect('login')

    today = timezone.localdate().strftime('%Y-%m-%d')
    from_date = request.GET.get('from_date') or today
    to_date = request.GET.get('to_date') or today

    def dec(value):
        try:
            return Decimal(str(value or '0').replace(',', '').strip())
        except (InvalidOperation, ValueError, TypeError):
            return Decimal('0')

    def money(value):
        return f'{dec(value):,.2f}'

    # Data
    sales = SellsInvoice.objects.filter(entry_date__date__range=[from_date, to_date])
    purchases = PurchaseReceivingView.objects.filter(date__date__range=[from_date, to_date])
    expenses = Expensedetail.objects.filter(date__date__range=[from_date, to_date])
    mortality = Mortality.objects.filter(entry_date__range=[from_date, to_date]).order_by('entry_date', 'id')

    total_sales = sum((dec(x.amount) for x in sales), Decimal('0'))
    total_cogs = sum((dec(x.amount) for x in purchases), Decimal('0'))

    expense_groups = {}
    for row in expenses:
        name = (row.head_name or 'Other Expense').strip()
        expense_groups[name] = expense_groups.get(name, Decimal('0')) + dec(row.amount)

    total_expenses = sum(expense_groups.values(), Decimal('0'))
    gross_profit = total_sales - total_cogs
    net_profit = gross_profit - total_expenses
    mortality_weight = sum((dec(x.weight) for x in mortality), Decimal('0'))
    mortality_amount = sum((dec(x.amount) for x in mortality), Decimal('0'))

    # PDF
    buffer = BytesIO()
    logo = finders.find('mylogo.png')
    page_width, page_height = A4

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=43*mm, bottomMargin=27*mm,
        title='MJ Poultries - Profit & Loss Report'
    )

    # Header / Footer on every page
    def header_footer(canvas, doc):
        canvas.saveState()

        # ================= HEADER =================
        canvas.setFillColor(colors.HexColor('#f0fdf4'))
        canvas.roundRect(15*mm, page_height-39*mm, page_width-30*mm, 31*mm, 3*mm, fill=1, stroke=0)

        canvas.setFillColor(colors.HexColor('#059669'))
        canvas.roundRect(15*mm, page_height-10*mm, page_width-30*mm, 2*mm, 1*mm, fill=1, stroke=0)

        canvas.setFillColor(colors.HexColor('#065f46'))
        canvas.setFont('Helvetica-Bold', 21)
        canvas.drawCentredString(page_width/2, page_height-19*mm, 'MJ POULTRIES')

        canvas.setFillColor(colors.HexColor('#334155'))
        canvas.setFont('Helvetica-Bold', 9)
        canvas.drawCentredString(page_width/2, page_height-25*mm, 'mjpsofficial@gmail.com')

        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.setFont('Helvetica', 8.5)
        canvas.drawCentredString(
            page_width/2,
            page_height-30*mm,
            'Gujranwala Pasrur Road, Opposite Qamar Medical Store, Satrah'
        )

        canvas.setStrokeColor(colors.HexColor('#86efac'))
        canvas.setLineWidth(1)
        canvas.line(35*mm, page_height-35*mm, page_width-35*mm, page_height-35*mm)


        # ================= FOOTER =================
        canvas.setStrokeColor(colors.HexColor('#cbd5e1'))
        canvas.setLineWidth(.8)
        canvas.line(25*mm, 18*mm, page_width-25*mm, 18*mm)

        # Powered by + Logo same line, centered
        text = 'Powered by'
        canvas.setFont('Helvetica-Bold', 10)
        text_width = canvas.stringWidth(text, 'Helvetica-Bold', 10)

        logo_width = 30*mm
        logo_height = 10*mm
        gap = 2*mm

        total_width = text_width + gap + logo_width
        start_x = (page_width - total_width) / 2
        center_y = 10.5*mm

        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawString(start_x, center_y, text)

        if logo and os.path.exists(logo):
            try:
                canvas.drawImage(
                    logo,
                    start_x + text_width + gap,
                    center_y - 2.4*mm,
                    width=logo_width,
                    height=logo_height,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except Exception:
                pass

        # Page Number
        canvas.setFillColor(colors.HexColor('#94a3b8'))
        canvas.setFont('Helvetica', 7)
        canvas.drawRightString(
            page_width - 15*mm,
            center_y,
            f'Page {canvas.getPageNumber()}'
        )
        canvas.restoreState()


    # Styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ReportTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=17, leading=21,
        alignment=1, textColor=colors.HexColor('#0f172a'), spaceAfter=4
    )

    date_style = ParagraphStyle(
        'DateStyle', parent=styles['Normal'],
        fontSize=9, alignment=1, leading=12,
        textColor=colors.HexColor('#64748b')
    )

    section_style = ParagraphStyle(
        'SectionStyle', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=11, leading=14,
        textColor=colors.HexColor('#334155'), spaceAfter=6
    )

    elements = [
        Paragraph('PROFIT & LOSS REPORT', title_style),
        Paragraph(f'Report Period: <b>{from_date}</b> &nbsp;&nbsp; to &nbsp;&nbsp; <b>{to_date}</b>', date_style),
        Spacer(1, 6*mm)
    ]

    # ================= P&L TABLE =================
    pl_data = [
        ['PARTICULARS', 'AMOUNT (Rs.)'],
        ['Total Sales (Dr)', money(total_sales)],
        ['Total Purchase (Cr)', money(total_cogs)],
        ['GROSS PROFIT', money(gross_profit)],
        ['OPERATING EXPENSES', '']
    ]

    for name, amount in expense_groups.items():
        pl_data.append([name, money(amount)])

    pl_data += [
        ['TOTAL OPERATING EXPENSES', money(total_expenses)],
        ['NET PROFIT / LOSS', money(net_profit)]
    ]

    pl_table = Table(pl_data, colWidths=[115*mm, 55*mm], repeatRows=1)

    pl_style = [
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#059669')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9.5),

        ('FONTNAME', (0,3), (-1,4), 'Helvetica-Bold'),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#dcfce7')),
        ('TEXTCOLOR', (0,3), (-1,3), colors.HexColor('#166534')),

        ('BACKGROUND', (0,4), (-1,4), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0,4), (-1,4), colors.HexColor('#334155')),

        ('FONTNAME', (0,-2), (-1,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,-2), (-1,-2), colors.HexColor('#f1f5f9')),

        ('ROWBACKGROUNDS', (0,1), (-1,-3), [colors.white, colors.HexColor('#fafafa')]),
        ('GRID', (0,0), (-1,-1), .4, colors.HexColor('#cbd5e1')),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('LEFTPADDING', (0,0), (-1,-1), 9),
        ('RIGHTPADDING', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7)
    ]

    if net_profit >= 0:
        pl_style += [
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#bbf7d0')),
            ('TEXTCOLOR', (0,-1), (-1,-1), colors.HexColor('#14532d'))
        ]
    else:
        pl_style += [
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#fecaca')),
            ('TEXTCOLOR', (0,-1), (-1,-1), colors.HexColor('#991b1b'))
        ]

    pl_table.setStyle(TableStyle(pl_style))
    elements += [pl_table, Spacer(1, 10*mm)]


    # ================= MORTALITY =================
    elements.append(Paragraph('MORTALITY REPORT', section_style))

    m_data = [['#', 'DATE', 'PURCHASE #', 'VEHICLE', 'WEIGHT', 'RATE', 'AMOUNT']]

    for i, row in enumerate(mortality, 1):
        m_data.append([
            i,
            row.entry_date.strftime('%d-%m-%Y') if row.entry_date else '-',
            row.purchase_no or '-',
            row.vehicle_number or '-',
            money(row.weight),
            money(row.rate),
            money(row.amount)
        ])

    if not mortality.exists():
        m_data.append(['', '', '', 'No mortality records found', '', '', ''])

    m_data.append(['', '', '', 'TOTAL', money(mortality_weight), '', money(mortality_amount)])

    m_table = Table(
        m_data, repeatRows=1,
        colWidths=[10*mm, 25*mm, 28*mm, 30*mm, 25*mm, 25*mm, 30*mm]
    )

    m_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),

        ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#f8fafc')]),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#e2e8f0')),

        ('GRID', (0,0), (-1,-1), .4, colors.HexColor('#cbd5e1')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6)
    ]))

    elements.append(m_table)

    doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="MJ_Poultries_Profit_Loss.pdf"'
    buffer.close()
    return response


def _is_expense_voucher_line(voucher, opposing_line=None):
    """
    Checks if a voucher or its opposing line represents an operating expense.
    """
    if not voucher:
        return False
    if voucher.reference_no and str(voucher.reference_no).upper().startswith('EXP-'):
        return True
    if voucher.remarks and str(voucher.remarks).upper().startswith('EXPENSE #'):
        return True
    if opposing_line and opposing_line.account:
        acc = opposing_line.account
        acc_type = (getattr(acc, 'account_type', '') or '').strip().lower()
        acc_code = str(getattr(acc, 'code', '') or '').strip()
        acc_name = (getattr(acc, 'name', '') or '').strip().lower()
        if acc_type == 'expense' or acc_code.startswith('05') or 'expense' in acc_name or 'expenc' in acc_name:
            return True
    return False


# =========================================================
# CASH LEDGER REPORT
# =========================================================
def cash_ledger(request):
    if not request.session.get('user_id'):
        return redirect('login')

    today = timezone.localdate().strftime('%Y-%m-%d')
    from_date = request.GET.get('from_date') or today
    to_date = request.GET.get('to_date') or today

    try:
        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
    except ValueError:
        from_date_obj = timezone.localdate()
        from_date = from_date_obj.strftime('%Y-%m-%d')

    try:
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
    except ValueError:
        to_date_obj = timezone.localdate()
        to_date = to_date_obj.strftime('%Y-%m-%d')

    # 1. Opening Balance (from CashRecord table: cash_in_hand + cash_in_bank)
    # Strictly fetch the latest CashRecord entry before from_date
    prior_cash = CashRecord.objects.filter(
        date__date__lt=from_date_obj
    ).order_by('-date', '-id').first()

    # Fallback: if no record exists before from_date, check if an opening balance was created on from_date itself
    if not prior_cash:
        prior_cash = CashRecord.objects.filter(
            date__date=from_date_obj,
            discription__icontains='opening'
        ).order_by('date', 'id').first()

    # Fallback: check any opening balance record
    if not prior_cash:
        prior_cash = CashRecord.objects.filter(discription__icontains='opening').order_by('date', 'id').first()
    if not prior_cash:
        prior_cash = CashRecord.objects.order_by('date', 'id').first()

    if prior_cash:
        op_cash_in_hand = safe_decimal(prior_cash.cash_in_hand or 0)
        op_cash_in_bank = safe_decimal(prior_cash.cash_in_bank or 0)
    else:
        op_cash_in_hand = 0.0
        op_cash_in_bank = 0.0

    opening_balance = op_cash_in_hand + op_cash_in_bank

    # 2. Period Transactions
    transactions = []

    # A) Purchase Payments -> Cash Out (Cr)
    purchases = PurchasePayments.objects.filter(
        date__date__gte=from_date_obj, date__date__lte=to_date_obj
    ).exclude(purchase_number__startswith='OPEN').exclude(payment_mood__icontains='opening').order_by('date', 'id')

    for p in purchases:
        p_name = (p.part_name or "").strip()
        p_code = (p.party_code or "").strip()
        if p_name and p_code:
            account_name = f"{p_name} ({p_code})"
        elif p_name:
            account_name = p_name
        elif p_code:
            account_name = f"Party ({p_code})"
        else:
            account_name = "Purchase Payment"

        transactions.append({
            'date': p.date or datetime.combine(from_date_obj, time.min),
            'tx_id': p.id or 0,
            'line_id': 0,
            'account': account_name,
            'description': (p.remarks or "").strip() or "-",
            'dr': 0.0,
            'cr': safe_decimal(p.amount),
            'type': 'purchase',
        })

    # B) Sales Payments -> Cash In (Dr)
    sells = Sellspayment.objects.filter(
        entry_date__date__gte=from_date_obj, entry_date__date__lte=to_date_obj
    ).exclude(sell_no__startswith='OPEN').exclude(vehicle_no='OPENING').exclude(payment_method__icontains='opening').order_by('entry_date', 'id')

    for s in sells:
        c_name = (s.customer_name or "").strip()
        c_code = (s.customer_code or "").strip()
        if c_name and c_code:
            account_name = f"{c_name} ({c_code})"
        elif c_name:
            account_name = c_name
        elif c_code:
            account_name = f"Customer ({c_code})"
        else:
            account_name = "Sales Receipt"

        amt = safe_decimal(s.received_amount)
        if amt == 0.0:
            amt = safe_decimal(s.amount)

        transactions.append({
            'date': s.entry_date or datetime.combine(from_date_obj, time.min),
            'tx_id': s.id or 0,
            'line_id': 0,
            'account': account_name,
            'description': (s.description or "").strip() or "-",
            'dr': amt,
            'cr': 0.0,
            'type': 'sales',
        })

    # C) Vouchers (CPV, CRV, BPV, BRV, JV) - All transactions including Expenses shown one by one
    expenses_qs = Expensedetail.objects.filter(date__date__gte=from_date_obj, date__date__lte=to_date_obj)
    exp_voucher_nos = set(
        expenses_qs.exclude(voucher_no__isnull=True).exclude(voucher_no='').values_list('voucher_no', flat=True)
    )

    vouchers_period = Voucher.objects.filter(
        date__gte=from_date_obj, date__lte=to_date_obj
    ).prefetch_related('details__account', 'details__party').order_by('date', 'id')

    for v in vouchers_period:
        if v.created_at:
            v_created = timezone.localtime(v.created_at) if hasattr(v.created_at, 'tzinfo') and v.created_at.tzinfo else v.created_at
            v_dt = datetime.combine(v.date, v_created.time())
        else:
            v_dt = datetime.combine(v.date, time.min)

        for line in v.details.all():
            code = str(line.account.code)
            name_lower = line.account.name.lower()
            is_cash_bank = (code in ['010101001', '1110001'] or code.startswith('010101') or code.startswith('1110') or 'cash in hand' in name_lower or 'bank' in name_lower)
            if is_cash_bank:
                opposing = v.details.exclude(id=line.id).first()
                is_exp = _is_expense_voucher_line(v, opposing) or (v.voucher_no in exp_voucher_nos)

                if opposing:
                    acc_name = opposing.party.company_name if opposing.party else (opposing.account.party.company_name if opposing.account.party else opposing.account.name)
                else:
                    acc_name = line.party.company_name if line.party else line.account.name

                desc = f"[{v.voucher_type}] #{v.voucher_no}"
                if v.remarks:
                    desc += f" - {v.remarks}"
                elif line.narration:
                    desc += f" - {line.narration}"

                if line.debit > 0:
                    transactions.append({
                        'date': v_dt,
                        'tx_id': v.id or 0,
                        'line_id': line.id or 0,
                        'account': acc_name,
                        'description': desc,
                        'dr': float(line.debit),
                        'cr': 0.0,
                        'type': 'voucher_in',
                        'is_expense': False,
                    })
                elif line.credit > 0:
                    transactions.append({
                        'date': v_dt,
                        'tx_id': v.id or 0,
                        'line_id': line.id or 0,
                        'account': acc_name,
                        'description': desc,
                        'dr': 0.0,
                        'cr': float(line.credit),
                        'type': 'voucher_out',
                        'is_expense': is_exp,
                    })

    # Include any Expensedetail records without an associated voucher so nothing is missed
    voucher_nos_in_period = set(vouchers_period.values_list('voucher_no', flat=True))
    orphan_expenses = expenses_qs.exclude(voucher_no__in=voucher_nos_in_period)
    for exp in orphan_expenses:
        exp_dt = exp.date or datetime.combine(from_date_obj, time.min)
        transactions.append({
            'date': exp_dt,
            'tx_id': exp.id or 0,
            'line_id': 0,
            'account': exp.head_name or "Expense",
            'description': exp.remarks or "-",
            'dr': 0.0,
            'cr': safe_decimal(exp.amount),
            'type': 'expense',
            'is_expense': True,
        })

    def _normalize_dt(tx):
        dt_val = tx.get('date')
        if not dt_val:
            d_date, d_time = from_date_obj, time.min
        elif hasattr(dt_val, 'tzinfo') and dt_val.tzinfo is not None:
            try:
                dt_obj = timezone.localtime(dt_val).replace(tzinfo=None)
            except Exception:
                dt_obj = dt_val.replace(tzinfo=None)
            d_date, d_time = dt_obj.date(), dt_obj.time()
        elif isinstance(dt_val, datetime):
            d_date, d_time = dt_val.date(), dt_val.time()
        elif isinstance(dt_val, date):
            d_date, d_time = dt_val, time.min
        else:
            d_date, d_time = from_date_obj, time.min
        return (d_date, d_time, tx.get('tx_id', 0) or 0, tx.get('line_id', 0) or 0)

    # Sort transactions chronologically
    transactions.sort(key=_normalize_dt)

    # 3. Build Ledger Rows starting with Opening Balance
    ledger_rows = []
    ledger_rows.append({
        'date_str': from_date_obj.strftime('%d-%m-%Y'),
        'account': 'Opening Balance',
        'description': 'Cash in hand & bank (opening balance)',
        'dr': 0.0,
        'cr': 0.0,
        'balance': opening_balance,
        'is_opening': True,
        'is_expense': False,
    })

    running_bal = opening_balance
    period_in = 0.0
    period_out = 0.0
    for tx in transactions:
        running_bal = running_bal + tx['dr'] - tx['cr']
        period_in += tx['dr']
        period_out += tx['cr']
        d = tx['date']
        date_str = d.strftime('%d-%m-%Y') if hasattr(d, 'strftime') else str(d)[:10]
        ledger_rows.append({
            'date_str': date_str,
            'account': tx['account'],
            'description': tx['description'],
            'dr': tx['dr'],
            'cr': tx['cr'],
            'balance': running_bal,
            'is_opening': False,
            'is_expense': tx.get('is_expense', False),
        })

    total_dr = period_in
    total_cr = period_out
    closing_balance = running_bal

    context = {
        'from_date': from_date,
        'to_date': to_date,
        'from_date_display': from_date_obj.strftime('%d-%m-%Y'),
        'to_date_display': to_date_obj.strftime('%d-%m-%Y'),
        'op_cash_in_hand': op_cash_in_hand,
        'op_cash_in_bank': op_cash_in_bank,
        'op_dr': op_cash_in_hand,
        'op_cr': op_cash_in_bank,
        'opening_balance': opening_balance,
        'period_in': period_in,
        'period_out': period_out,
        'total_dr': total_dr,
        'total_cr': total_cr,
        'closing_balance': closing_balance,
        'ledger_rows': ledger_rows,
    }
    return render(request, 'Reports/cash_ledger.html', context)


# =========================================================
# CASH LEDGER REPORTLAB PDF PRINT
# =========================================================
def cash_ledger_print(request):
    if not request.session.get('user_id'):
        return redirect('login')

    today = timezone.localdate().strftime('%Y-%m-%d')
    from_date = request.GET.get('from_date') or today
    to_date = request.GET.get('to_date') or today

    try:
        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
    except ValueError:
        from_date_obj = timezone.localdate()
        from_date = from_date_obj.strftime('%Y-%m-%d')

    try:
        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
    except ValueError:
        to_date_obj = timezone.localdate()
        to_date = to_date_obj.strftime('%Y-%m-%d')

    # 1. Opening Balance (from CashRecord table: cash_in_hand + cash_in_bank)
    prior_cash = CashRecord.objects.filter(
        date__date__lt=from_date_obj
    ).order_by('-date', '-id').first()

    # Fallback: if no record exists before from_date, check if an opening balance was created on from_date itself
    if not prior_cash:
        prior_cash = CashRecord.objects.filter(
            date__date=from_date_obj,
            discription__icontains='opening'
        ).order_by('date', 'id').first()

    # Fallback: check any opening balance record
    if not prior_cash:
        prior_cash = CashRecord.objects.filter(discription__icontains='opening').order_by('date', 'id').first()
    if not prior_cash:
        prior_cash = CashRecord.objects.order_by('date', 'id').first()

    if prior_cash:
        op_cash_in_hand = safe_decimal(prior_cash.cash_in_hand or 0)
        op_cash_in_bank = safe_decimal(prior_cash.cash_in_bank or 0)
    else:
        op_cash_in_hand = 0.0
        op_cash_in_bank = 0.0

    opening_balance = op_cash_in_hand + op_cash_in_bank

    # 2. Period Transactions
    transactions = []

    purchases = PurchasePayments.objects.filter(
        date__date__gte=from_date_obj, date__date__lte=to_date_obj
    ).exclude(purchase_number__startswith='OPEN').exclude(payment_mood__icontains='opening').order_by('date', 'id')

    for p in purchases:
        p_name = (p.part_name or "").strip()
        p_code = (p.party_code or "").strip()
        if p_name and p_code:
            account_name = f"{p_name} ({p_code})"
        elif p_name:
            account_name = p_name
        elif p_code:
            account_name = f"Party ({p_code})"
        else:
            account_name = "Purchase Payment"

        transactions.append({
            'date': p.date or datetime.combine(from_date_obj, time.min),
            'tx_id': p.id or 0,
            'line_id': 0,
            'account': account_name,
            'description': (p.remarks or "").strip() or "-",
            'dr': 0.0,
            'cr': safe_decimal(p.amount),
        })

    sells = Sellspayment.objects.filter(
        entry_date__date__gte=from_date_obj, entry_date__date__lte=to_date_obj
    ).exclude(sell_no__startswith='OPEN').exclude(vehicle_no='OPENING').exclude(payment_method__icontains='opening').order_by('entry_date', 'id')

    for s in sells:
        c_name = (s.customer_name or "").strip()
        c_code = (s.customer_code or "").strip()
        if c_name and c_code:
            account_name = f"{c_name} ({c_code})"
        elif c_name:
            account_name = c_name
        elif c_code:
            account_name = f"Customer ({c_code})"
        else:
            account_name = "Sales Receipt"

        amt = safe_decimal(s.received_amount) or safe_decimal(s.amount)
        transactions.append({
            'date': s.entry_date or datetime.combine(from_date_obj, time.min),
            'tx_id': s.id or 0,
            'line_id': 0,
            'account': account_name,
            'description': (s.description or "").strip() or "-",
            'dr': amt,
            'cr': 0.0,
        })

    # C) Vouchers (CPV, CRV, BPV, BRV, JV) - All transactions including Expenses shown one by one
    expenses_qs = Expensedetail.objects.filter(date__date__gte=from_date_obj, date__date__lte=to_date_obj)
    exp_voucher_nos = set(
        expenses_qs.exclude(voucher_no__isnull=True).exclude(voucher_no='').values_list('voucher_no', flat=True)
    )

    vouchers_period = Voucher.objects.filter(
        date__gte=from_date_obj, date__lte=to_date_obj
    ).prefetch_related('details__account', 'details__party').order_by('date', 'id')

    for v in vouchers_period:
        if v.created_at:
            v_created = timezone.localtime(v.created_at) if hasattr(v.created_at, 'tzinfo') and v.created_at.tzinfo else v.created_at
            v_dt = datetime.combine(v.date, v_created.time())
        else:
            v_dt = datetime.combine(v.date, time.min)

        for line in v.details.all():
            code = str(line.account.code)
            name_lower = line.account.name.lower()
            is_cash_bank = (code in ['010101001', '1110001'] or code.startswith('010101') or code.startswith('1110') or 'cash in hand' in name_lower or 'bank' in name_lower)
            if is_cash_bank:
                opposing = v.details.exclude(id=line.id).first()
                is_exp = _is_expense_voucher_line(v, opposing) or (v.voucher_no in exp_voucher_nos)

                if opposing:
                    acc_name = opposing.party.company_name if opposing.party else (opposing.account.party.company_name if opposing.account.party else opposing.account.name)
                else:
                    acc_name = line.party.company_name if line.party else line.account.name

                desc = f"[{v.voucher_type}] #{v.voucher_no}"
                if v.remarks:
                    desc += f" - {v.remarks}"
                elif line.narration:
                    desc += f" - {line.narration}"

                if line.debit > 0:
                    transactions.append({
                        'date': v_dt,
                        'tx_id': v.id or 0,
                        'line_id': line.id or 0,
                        'account': acc_name,
                        'description': desc,
                        'dr': float(line.debit),
                        'cr': 0.0,
                    })
                elif line.credit > 0:
                    transactions.append({
                        'date': v_dt,
                        'tx_id': v.id or 0,
                        'line_id': line.id or 0,
                        'account': acc_name,
                        'description': desc,
                        'dr': 0.0,
                        'cr': float(line.credit),
                    })

    # Include any Expensedetail records without an associated voucher so nothing is missed
    voucher_nos_in_period = set(vouchers_period.values_list('voucher_no', flat=True))
    orphan_expenses = expenses_qs.exclude(voucher_no__in=voucher_nos_in_period)
    for exp in orphan_expenses:
        exp_dt = exp.date or datetime.combine(from_date_obj, time.min)
        transactions.append({
            'date': exp_dt,
            'tx_id': exp.id or 0,
            'line_id': 0,
            'account': exp.head_name or "Expense",
            'description': exp.remarks or "-",
            'dr': 0.0,
            'cr': safe_decimal(exp.amount),
        })

    def _normalize_dt(tx):
        dt_val = tx.get('date')
        if not dt_val:
            d_date, d_time = from_date_obj, time.min
        elif hasattr(dt_val, 'tzinfo') and dt_val.tzinfo is not None:
            try:
                dt_obj = timezone.localtime(dt_val).replace(tzinfo=None)
            except Exception:
                dt_obj = dt_val.replace(tzinfo=None)
            d_date, d_time = dt_obj.date(), dt_obj.time()
        elif isinstance(dt_val, datetime):
            d_date, d_time = dt_val.date(), dt_val.time()
        elif isinstance(dt_val, date):
            d_date, d_time = dt_val, time.min
        else:
            d_date, d_time = from_date_obj, time.min
        return (d_date, d_time, tx.get('tx_id', 0) or 0, tx.get('line_id', 0) or 0)

    transactions.sort(key=_normalize_dt)

    ledger_rows = []
    ledger_rows.append({
        'date_str': from_date_obj.strftime('%d-%m-%Y'),
        'account': 'Opening Balance',
        'description': f"Cash in hand & bank (Hand: {op_cash_in_hand:,.2f}, Bank: {op_cash_in_bank:,.2f})",
        'dr': 0.0,
        'cr': 0.0,
        'balance': opening_balance,
        'is_opening': True,
        'is_expense': False,
    })

    running_bal = opening_balance
    period_in = 0.0
    period_out = 0.0
    for tx in transactions:
        running_bal = running_bal + tx['dr'] - tx['cr']
        period_in += tx['dr']
        period_out += tx['cr']
        d = tx['date']
        date_str = d.strftime('%d-%m-%Y') if hasattr(d, 'strftime') else str(d)[:10]
        ledger_rows.append({
            'date_str': date_str,
            'account': tx['account'],
            'description': tx['description'],
            'dr': tx['dr'],
            'cr': tx['cr'],
            'balance': running_bal,
            'is_opening': False,
            'is_expense': False,
        })

    total_dr = period_in
    total_cr = period_out
    closing_balance = running_bal

    # ReportLab Generation
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=8 * mm,
        rightMargin=8 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
        title=f"Cash_Ledger_{from_date}_to_{to_date}"
    )

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontSize = 8
    normal_style.leading = 10

    elements = []

    # Title Banner (Navy Blue matching UI)
    banner_cell = Paragraph(
        "<font color='white'><b>CASH LEDGER</b></font>",
        ParagraphStyle('CLBanner', fontName='Helvetica-Bold', fontSize=15, alignment=1, textColor=colors.white)
    )
    title_banner = Table([[banner_cell]], colWidths=[281 * mm])
    title_banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0B2545')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
    ]))
    elements.append(title_banner)
    elements.append(Spacer(1, 3 * mm))

    # Info & Summary Row
    info_p = Paragraph(f"<b>MJ POULTRIES AND GROUP</b><br/><font color='#64748b' size=7.5>Period: {from_date_obj.strftime('%d-%m-%Y')} to {to_date_obj.strftime('%d-%m-%Y')}</font>", normal_style)
    
    summary_data = [
        [
            info_p,
            Paragraph(f"<font size=7 color='#64748b'>OPENING BALANCE</font><br/><b>PKR {opening_balance:,.2f}</b><br/><font size=6.5 color='#64748b'>Hand: {op_cash_in_hand:,.2f} | Bank: {op_cash_in_bank:,.2f}</font>", normal_style),
            Paragraph(f"<font size=7 color='#15803d'>TOTAL CASH IN (DR)</font><br/><font color='#15803d'><b>PKR {total_dr:,.2f}</b></font>", normal_style),
            Paragraph(f"<font size=7 color='#b91c1c'>TOTAL CASH OUT (CR)</font><br/><font color='#b91c1c'><b>PKR {total_cr:,.2f}</b></font>", normal_style),
            Paragraph(f"<font size=7 color='#0b2545'>CLOSING BALANCE</font><br/><font color='#0b2545'><b>PKR {closing_balance:,.2f}</b></font>", normal_style),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[81*mm, 50*mm, 50*mm, 50*mm, 50*mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 4 * mm))

    # Main Ledger Table
    table_data = [
        ["Date", "Account", "Description", "Cash In (Dr / Receipt)", "Cash Out (Cr / Payment)", "Balance (PKR)"]
    ]

    for r in ledger_rows:
        dr_str = f"PKR {r['dr']:,.2f}" if r['dr'] > 0 else "-"
        cr_str = f"PKR {r['cr']:,.2f}" if r['cr'] > 0 else "-"
        bal_str = f"PKR {r['balance']:,.2f}"
        
        acc_p = Paragraph(f"<font size=8>{r['account']}</font>", normal_style)
        desc_p = Paragraph(f"<font size=8>{r['description']}</font>", normal_style)

        table_data.append([
            r['date_str'],
            acc_p,
            desc_p,
            dr_str,
            cr_str,
            bal_str,
        ])

    # Footer total row (matching design in image)
    table_data.append([
        "Total",
        "",
        "",
        f"PKR {total_dr:,.2f}",
        f"PKR {total_cr:,.2f}",
        f"PKR {closing_balance:,.2f}",
    ])

    col_widths = [26*mm, 70*mm, 75*mm, 36*mm, 36*mm, 38*mm]
    ledger_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    t_style = [
        # Headers matching image
        ('BACKGROUND', (0,0), (2,0), colors.HexColor('#0B2545')),
        ('BACKGROUND', (3,0), (3,0), colors.HexColor('#15803D')),  # Green header for Cash In
        ('BACKGROUND', (4,0), (4,0), colors.HexColor('#B91C1C')),  # Red header for Cash Out
        ('BACKGROUND', (5,0), (5,0), colors.HexColor('#0B2545')),  # Navy header for Balance
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),

        # Body alignment
        ('ALIGN', (0,1), (0,-2), 'CENTER'),
        ('ALIGN', (1,1), (2,-2), 'LEFT'),
        ('ALIGN', (3,1), (5,-2), 'RIGHT'),
        ('FONTSIZE', (0,1), (-1,-2), 8),
        ('TOPPADDING', (0,1), (-1,-2), 3.5),
        ('BOTTOMPADDING', (0,1), (-1,-2), 3.5),
        ('GRID', (0,0), (-1,-2), 0.4, colors.HexColor('#CBD5E1')),

        # Body text colors
        ('TEXTCOLOR', (3,1), (3,-2), colors.HexColor('#15803D')),  # Dr green
        ('TEXTCOLOR', (4,1), (4,-2), colors.HexColor('#B91C1C')),  # Cr red
        ('TEXTCOLOR', (5,1), (5,-2), colors.HexColor('#0B2545')),  # Balance dark
        ('FONTNAME', (3,1), (5,-2), 'Helvetica-Bold'),

        # Total row (at the bottom)
        ('SPAN', (0,-1), (2,-1)),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#0B2545')),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,-1), (-1,-1), 8.5),
        ('ALIGN', (0,-1), (0,-1), 'CENTER'),
        ('TEXTCOLOR', (0,-1), (0,-1), colors.white),
        ('ALIGN', (3,-1), (5,-1), 'RIGHT'),
        ('TEXTCOLOR', (3,-1), (3,-1), colors.HexColor('#4ADE80')),  # Bright Green Total Dr
        ('TEXTCOLOR', (4,-1), (4,-1), colors.HexColor('#F87171')),  # Bright Red Total Cr
        ('TEXTCOLOR', (5,-1), (5,-1), colors.white),                # White Total Balance
        ('TOPPADDING', (0,-1), (-1,-1), 6),
        ('BOTTOMPADDING', (0,-1), (-1,-1), 6),
    ]

    for row_idx in range(1, len(table_data) - 1):
        bg = colors.HexColor('#F8FAFC') if row_idx % 2 == 0 else colors.white
        t_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), bg))

    ledger_table.setStyle(TableStyle(t_style))
    elements.append(ledger_table)

    def print_footer(canvas, d):
        canvas.saveState()
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(colors.HexColor('#64748B'))
        canvas.drawString(8 * mm, 4 * mm, f"Printed: {timezone.now().strftime('%d-%m-%Y %H:%M')} | MJ Poultries System")
        canvas.drawRightString(289 * mm, 4 * mm, f"Page {d.page}")
        canvas.restoreState()

    doc.build(elements, onFirstPage=print_footer, onLaterPages=print_footer)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Cash_Ledger_{from_date}_to_{to_date}.pdf"'
    buffer.close()
    return response


# =========================================================
# BROILER REPORT (DAILY SALES VS PURCHASES + MORTALITY)
# =========================================================
def broiler_report(request):
    if not request.session.get('user_id'):
        return redirect('login')

    today = timezone.localdate().strftime('%Y-%m-%d')
    selected_date_str = request.GET.get('date') or today

    try:
        selected_date_obj = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date_obj = timezone.localdate()
        selected_date_str = selected_date_obj.strftime('%Y-%m-%d')

    selected_date_display = selected_date_obj.strftime('%d-%m-%Y')

    # 1. Left Table: SellsInvoice (Sales)
    # Party Name, Qty (Weight), Rate, Amount
    sales_qs = SellsInvoice.objects.filter(
        entry_date__date=selected_date_obj
    ).order_by('entry_date', 'id')
    sales_list = []
    total_sales_qty = 0.0
    total_sales_amount = 0.0

    for idx, s in enumerate(sales_qs, 1):
        c_name = (s.customer_name or "").strip()
        c_code = (s.customer_code or "").strip()
        if c_name and c_code:
            party_name = f"{c_name} ({c_code})"
        elif c_name:
            party_name = c_name
        elif c_code:
            party_name = f"Customer ({c_code})"
        else:
            party_name = "Customer"

        w = safe_decimal(s.weight)
        r = safe_decimal(s.rate)
        a = safe_decimal(s.amount)
        if a == 0.0 and w > 0 and r > 0:
            a = round(w * r, 2)

        total_sales_qty += w
        total_sales_amount += a

        sales_list.append({
            'sr': idx,
            'party_name': party_name,
            'qty': w,
            'rate': r,
            'amount': a,
            'vehicle_no': s.vehicle_no or "-",
            'sells_no': s.sells_no or "-",
        })

    # 2. Right Table: PurchaseReceiving (Purchases)
    # Party Name, Qty (Weight), Rate, Amount
    purchases_qs = PurchaseReceiving.objects.filter(
        date__date=selected_date_obj
    ).order_by('date', 'id')
    purchases_list = []
    total_purchase_qty = 0.0
    total_purchase_amount = 0.0

    for idx, p in enumerate(purchases_qs, 1):
        v_name = (p.vendor_name or "").strip()
        v_code = (p.vendor_code or "").strip()
        if v_name and v_code:
            party_name = f"{v_name} ({v_code})"
        elif v_name:
            party_name = v_name
        elif v_code:
            party_name = f"Party ({v_code})"
        else:
            party_name = "Vendor"

        w = safe_decimal(p.weight)
        r = safe_decimal(p.vendor_rate)
        a = safe_decimal(p.amount)
        if a == 0.0 and w > 0 and r > 0:
            a = round(w * r, 2)

        total_purchase_qty += w
        total_purchase_amount += a

        purchases_list.append({
            'sr': idx,
            'party_name': party_name,
            'qty': w,
            'rate': r,
            'amount': a,
            'vehicle_number': p.vehicle_number or "-",
            'purchase_number': p.purchase_number or "-",
            'remaining_weight': p.remaining_weight,
        })

    # 3. Totals and Profit / Loss
    # Profit / Loss = Total Sale - Total Purchase
    profit_loss = total_sales_amount - total_purchase_amount
    is_profit = profit_loss >= 0
    profit_loss_type = "Profit" if is_profit else "Loss"
    abs_profit_loss = abs(profit_loss)
    purchase_minus_sale = total_purchase_amount - total_sales_amount

    # 4. Mortality / Wadya Maal (مورٹالٹی / وادیا مال)
    # Check Mortality table for that date
    mortality_qs = Mortality.objects.filter(entry_date=selected_date_obj)
    if mortality_qs.exists():
        mortality_weight = sum(safe_decimal(m.weight) for m in mortality_qs)
        mortality_source = "Mortality Table"
        mortality_from_table = True
    else:
        # If no record in Mortality table for this date -> look at PurchaseReceiving remaining_weight
        # If negative, remove minus sign (abs)
        raw_rem = sum(safe_decimal(p.remaining_weight) for p in purchases_qs)
        mortality_weight = abs(raw_rem)
        mortality_source = "Purchase Receiving (Remaining Weight)"
        mortality_from_table = False

    if mortality_from_table:
        mortality_card_title = "Mortality"
        mortality_badge = "مورٹالٹی"
    else:
        mortality_card_title = "Wadya Maal"
        mortality_badge = "وادیا مال"

    # Check for Print / PDF request
    is_print = (
        request.GET.get('action') == 'print'
        or request.GET.get('print') == '1'
        or request.GET.get('format') == 'pdf'
        or 'print' in request.path
    )

    if is_print:
        # =========================================================
        # REPORTLAB PDF GENERATION FOR BROILER REPORT
        # =========================================================
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=8 * mm,
            rightMargin=8 * mm,
            topMargin=8 * mm,
            bottomMargin=8 * mm,
            title=f"Broiler_Report_{selected_date_str}"
        )

        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontSize = 7.5
        normal_style.leading = 9.5

        elements = []

        # Title Banner with MJ POULTRIES prominently displayed
        banner_cell = Paragraph(
            f"<font color='white' size=16><b>MJ POULTRIES</b></font><br/>"
            f"<font color='#93c5fd' size=10><b>DAILY BROILER REPORT</b></font><br/>"
            f"<font color='#e2e8f0' size=8>Date: {selected_date_display}</font>",
            ParagraphStyle('BRBanner', fontName='Helvetica-Bold', fontSize=14, leading=17, alignment=1, textColor=colors.white)
        )
        title_banner = Table([[banner_cell]], colWidths=[281 * mm])
        title_banner.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0B2545')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(title_banner)
        elements.append(Spacer(1, 3 * mm))

        # KPI Summary Cards Table
        pl_color = '#15803d' if is_profit else '#b91c1c'
        mort_pdf_header = "MORTALITY" if mortality_from_table else "WADYA MAAL"
        summary_data = [
            [
                Paragraph(
                    f"<font size=7 color='#64748b'>TOTAL SALE </font><br/>"
                    f"<font color='#15803d' size=9.5><b>PKR {total_sales_amount:,.2f}</b></font><br/>"
                    f"<font size=6.5 color='#64748b'>Total Qty: {total_sales_qty:,.2f} KG</font>",
                    normal_style
                ),
                Paragraph(
                    f"<font size=7 color='#64748b'>TOTAL PURCHASE </font><br/>"
                    f"<font color='#0b2545' size=9.5><b>PKR {total_purchase_amount:,.2f}</b></font><br/>"
                    f"<font size=6.5 color='#64748b'>Total Qty: {total_purchase_qty:,.2f} KG</font>",
                    normal_style
                ),
                Paragraph(
                    f"<font size=7 color='#64748b'>PROFIT / LOSS </font><br/>"
                    f"<font color='{pl_color}' size=9.5><b>PKR {abs_profit_loss:,.2f}</b></font><br/>"
                    f"<font size=6.5 color='{pl_color}'><b>{profit_loss_type.upper()}</b> (Sale &minus; Purchase)</font>",
                    normal_style
                ),
                Paragraph(
                    f"<font size=7 color='#64748b'>{mort_pdf_header}</font><br/>"
                    f"<font color='#d97706' size=9.5><b>{mortality_weight:,.2f} KG</b></font><br/>"
                    f"<font size=6 color='#64748b'>Source: {mortality_source}</font>",
                    normal_style
                ),
            ]
        ]
        summary_table = Table(summary_data, colWidths=[70.25 * mm, 70.25 * mm, 70.25 * mm, 70.25 * mm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 3 * mm))

        # Build Side-by-Side Tables: Sales (Left) & Purchases (Right)
        # 1. Left Table: Sales
        s_headers = ["#", "Customer Name", "Qty (KG)", "Rate", "Amount (PKR)"]
        sales_table_data = [
            [
                Paragraph("<font color='white'><b>SALES </b></font>", normal_style),
                "", "", "", ""
            ],
            s_headers
        ]

        if sales_list:
            for s in sales_list:
                sales_table_data.append([
                    str(s['sr']),
                    Paragraph(f"<font size=7.5>{s['party_name']}</font>", normal_style),
                    f"{s['qty']:,.2f}",
                    f"{s['rate']:,.2f}",
                    f"{s['amount']:,.2f}",
                ])
        else:
            sales_table_data.append([
                "-",
                Paragraph("<font color='#94a3b8'>No sales records found</font>", normal_style),
                "-", "-", "-"
            ])

        sales_table_data.append([
            "Total",
            "",
            f"{total_sales_qty:,.2f}",
            "",
            f"{total_sales_amount:,.2f}",
        ])

        s_col_widths = [8 * mm, 52 * mm, 24 * mm, 24 * mm, 30 * mm]
        sales_table = Table(sales_table_data, colWidths=s_col_widths)
        s_style = [
            # Title Row
            ('SPAN', (0, 0), (4, 0)),
            ('BACKGROUND', (0, 0), (4, 0), colors.HexColor('#15803D')),
            ('ALIGN', (0, 0), (4, 0), 'CENTER'),
            ('TOPPADDING', (0, 0), (4, 0), 4),
            ('BOTTOMPADDING', (0, 0), (4, 0), 4),
            # Column Header Row
            ('BACKGROUND', (0, 1), (4, 1), colors.HexColor('#166534')),
            ('TEXTCOLOR', (0, 1), (4, 1), colors.white),
            ('FONTNAME', (0, 1), (4, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (4, 1), 7.5),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
            ('TOPPADDING', (0, 1), (4, -1), 3),
            ('BOTTOMPADDING', (0, 1), (4, -1), 3),
            ('GRID', (0, 1), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            # Footer Row
            ('SPAN', (0, -1), (1, -1)),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#DCFCE7')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#14532D')),
        ]
        for r_i in range(2, len(sales_table_data) - 1):
            bg = colors.HexColor('#F8FAFC') if r_i % 2 == 0 else colors.white
            s_style.append(('BACKGROUND', (0, r_i), (-1, r_i), bg))
        sales_table.setStyle(TableStyle(s_style))

        # 2. Right Table: Purchases
        p_headers = ["#", "Vendor Name", "Qty (KG)", "Rate", "Amount (PKR)"]
        purchases_table_data = [
            [
                Paragraph("<font color='white'><b>PURCHASES</b></font>", normal_style),
                "", "", "", ""
            ],
            p_headers
        ]

        if purchases_list:
            for p in purchases_list:
                purchases_table_data.append([
                    str(p['sr']),
                    Paragraph(f"<font size=7.5>{p['party_name']}</font>", normal_style),
                    f"{p['qty']:,.2f}",
                    f"{p['rate']:,.2f}",
                    f"{p['amount']:,.2f}",
                ])
        else:
            purchases_table_data.append([
                "-",
                Paragraph("<font color='#94a3b8'>No purchase records found</font>", normal_style),
                "-", "-", "-"
            ])

        purchases_table_data.append([
            "Total",
            "",
            f"{total_purchase_qty:,.2f}",
            "",
            f"{total_purchase_amount:,.2f}",
        ])

        p_col_widths = [8 * mm, 52 * mm, 24 * mm, 24 * mm, 30 * mm]
        purchases_table = Table(purchases_table_data, colWidths=p_col_widths)
        p_style = [
            # Title Row
            ('SPAN', (0, 0), (4, 0)),
            ('BACKGROUND', (0, 0), (4, 0), colors.HexColor('#0B2545')),
            ('ALIGN', (0, 0), (4, 0), 'CENTER'),
            ('TOPPADDING', (0, 0), (4, 0), 4),
            ('BOTTOMPADDING', (0, 0), (4, 0), 4),
            # Column Header Row
            ('BACKGROUND', (0, 1), (4, 1), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0, 1), (4, 1), colors.white),
            ('FONTNAME', (0, 1), (4, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (4, 1), 7.5),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
            ('TOPPADDING', (0, 1), (4, -1), 3),
            ('BOTTOMPADDING', (0, 1), (4, -1), 3),
            ('GRID', (0, 1), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            # Footer Row
            ('SPAN', (0, -1), (1, -1)),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#DBEAFE')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1E3A8A')),
        ]
        for r_i in range(2, len(purchases_table_data) - 1):
            bg = colors.HexColor('#F8FAFC') if r_i % 2 == 0 else colors.white
            p_style.append(('BACKGROUND', (0, r_i), (-1, r_i), bg))
        purchases_table.setStyle(TableStyle(p_style))

        # Put side-by-side in outer table
        side_by_side = Table(
            [[sales_table, purchases_table]],
            colWidths=[139 * mm, 139 * mm]
        )
        side_by_side.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 1),
            ('RIGHTPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ]))
        elements.append(side_by_side)

        # Bottom Summary Table in PDF (Matching web page bottom card)
        mort_pdf_bottom_title = "MORTALITY (مورٹالٹی)" if mortality_from_table else "WADYA MAAL"
        bottom_summary_data = [
            [
                Paragraph(
                    f"<font size=8 color='#475569'><b>DAILY PROFIT / LOSS </b></font><br/>"
                    f"<font size=12.5 color='{pl_color}'><b>PKR {abs_profit_loss:,.2f}</b></font> "
                    f"<font size=8.5 color='{pl_color}'><b>[{profit_loss_type.upper()}]</b></font><br/>"
                    f"<font size=6.5 color='#64748b'>Total Sale (PKR {total_sales_amount:,.2f}) &minus; Total Purchase (PKR {total_purchase_amount:,.2f})</font>",
                    normal_style
                ),
                Paragraph(
                    f"<font size=8 color='#475569'><b>{mort_pdf_bottom_title}</b></font><br/>"
                    f"<font size=12.5 color='#b45309'><b>{mortality_weight:,.2f} KG</b></font><br/>"
                    f"<font size=6.5 color='#64748b'>Source: {mortality_source}</font>",
                    normal_style
                ),
            ]
        ]
        bottom_summary_table = Table(bottom_summary_data, colWidths=[139 * mm, 139 * mm])
        bottom_summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(Spacer(1, 3.5 * mm))
        elements.append(bottom_summary_table)

        def print_broiler_footer(canvas, d):
            canvas.saveState()
            canvas.setFont('Helvetica', 7.5)
            canvas.setFillColor(colors.HexColor('#64748B'))
            canvas.drawString(8 * mm, 4 * mm, f"Printed: {timezone.now().strftime('%d-%m-%Y %H:%M')} | MJ Poultries System")
            canvas.drawRightString(289 * mm, 4 * mm, f"Page {d.page}")
            canvas.restoreState()

        doc.build(elements, onFirstPage=print_broiler_footer, onLaterPages=print_broiler_footer)

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Broiler_Report_{selected_date_str}.pdf"'
        buffer.close()
        return response

    # HTML Context
    context = {
        'selected_date': selected_date_str,
        'selected_date_display': selected_date_display,
        'sales_list': sales_list,
        'total_sales_qty': total_sales_qty,
        'total_sales_amount': total_sales_amount,
        'purchases_list': purchases_list,
        'total_purchase_qty': total_purchase_qty,
        'total_purchase_amount': total_purchase_amount,
        'profit_loss': profit_loss,
        'is_profit': is_profit,
        'profit_loss_type': profit_loss_type,
        'abs_profit_loss': abs_profit_loss,
        'purchase_minus_sale': purchase_minus_sale,
        'mortality_weight': mortality_weight,
        'mortality_source': mortality_source,
        'mortality_from_table': mortality_from_table,
        'mortality_card_title': mortality_card_title,
        'mortality_badge': mortality_badge,
    }
    return render(request, 'Reports/broiler_report.html', context)


# =========================================================
# CASH REPORT (DAILY RECEIPTS & PREV BALANCE VS PAYMENTS & EXPENSE)
# =========================================================
def _get_cash_report_data(request):
    today = timezone.localdate().strftime('%Y-%m-%d')
    selected_date_str = request.GET.get('date') or today

    try:
        selected_date_obj = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date_obj = timezone.localdate()
        selected_date_str = selected_date_obj.strftime('%Y-%m-%d')

    selected_date_display = selected_date_obj.strftime('%d-%m-%Y')

    # 1. Left Side: Sellspayment & Voucher Receipts (CRV, BRV - Money In)
    sells_qs = Sellspayment.objects.filter(
        entry_date__date=selected_date_obj
    ).exclude(sell_no__startswith='OPEN').exclude(vehicle_no='OPENING').exclude(payment_method__icontains='opening').order_by('entry_date', 'id')
    raw_sells = []
    total_sells_amount = 0.0

    for s in sells_qs:
        c_name = (s.customer_name or "").strip()
        c_code = (s.customer_code or "").strip()
        if c_name and c_code:
            party_name = f"{c_name} ({c_code})"
        elif c_name:
            party_name = c_name
        elif c_code:
            party_name = f"Customer ({c_code})"
        else:
            party_name = "Customer"

        amt = safe_decimal(s.received_amount)
        if amt == 0.0:
            amt = safe_decimal(s.amount)

        total_sells_amount += amt
        s_dt = s.entry_date or datetime.combine(selected_date_obj, time.min)
        raw_sells.append({
            'sort_dt': s_dt,
            'sort_id': s.id or 0,
            'customer_name': party_name,
            'amount': amt,
            'payment_method': s.payment_method or "-",
            'sell_no': s.sell_no or "-",
            'vehicle_no': s.vehicle_no or "-",
        })

    # Add CRV & BRV Vouchers (Cash & Bank Receipts)
    vouchers_in = Voucher.objects.filter(
        date=selected_date_obj,
        voucher_type__in=['CRV', 'BRV', 'Receipt Voucher']
    ).prefetch_related('details__account', 'details__party').order_by('date', 'id')

    for v in vouchers_in:
        amt = float(v.total_amount)
        total_sells_amount += amt
        # Get opposing party or account
        opposing = v.details.exclude(account__code__in=['010101001', '1110001']).exclude(account__code__startswith='010101').exclude(account__code__startswith='1110').first()
        if opposing:
            party_name = opposing.party.company_name if opposing.party else (opposing.account.party.company_name if opposing.account.party else opposing.account.name)
        else:
            party_name = "Cash / Bank Receipt"

        if v.created_at:
            v_created = timezone.localtime(v.created_at) if hasattr(v.created_at, 'tzinfo') and v.created_at.tzinfo else v.created_at
            v_dt = datetime.combine(v.date, v_created.time())
        else:
            v_dt = datetime.combine(v.date, time.min)

        raw_sells.append({
            'sort_dt': v_dt,
            'sort_id': v.id or 0,
            'customer_name': f"[{v.voucher_type}] {party_name}",
            'amount': amt,
            'payment_method': v.voucher_type,
            'sell_no': v.voucher_no,
            'vehicle_no': v.reference_no or "-",
        })

    def _sort_dt_key(item):
        d = item.get('sort_dt')
        if not d:
            d_dt = datetime.combine(selected_date_obj, time.min)
        elif hasattr(d, 'tzinfo') and d.tzinfo is not None:
            try:
                d_dt = timezone.localtime(d).replace(tzinfo=None)
            except Exception:
                d_dt = d.replace(tzinfo=None)
        elif isinstance(d, datetime):
            d_dt = d
        elif isinstance(d, date):
            d_dt = datetime.combine(d, time.min)
        else:
            d_dt = datetime.combine(selected_date_obj, time.min)
        return (d_dt, item.get('sort_id', 0))

    raw_sells.sort(key=_sort_dt_key)

    sells_list = []
    for idx, item in enumerate(raw_sells, 1):
        item['sr'] = idx
        sells_list.append(item)

    # 2. Previous Day Closing Balance from Cash Ledger (CashRecord)
    prior_cash = CashRecord.objects.filter(
        date__date__lt=selected_date_obj
    ).order_by('-date', '-id').first()

    if not prior_cash:
        prior_cash = CashRecord.objects.filter(
            date__date=selected_date_obj,
            discription__icontains='opening'
        ).order_by('date', 'id').first()

    if not prior_cash:
        prior_cash = CashRecord.objects.filter(discription__icontains='opening').order_by('date', 'id').first()
    if not prior_cash:
        prior_cash = CashRecord.objects.order_by('date', 'id').first()

    if prior_cash:
        prev_hand = safe_decimal(prior_cash.cash_in_hand or 0)
        prev_bank = safe_decimal(prior_cash.cash_in_bank or 0)
    else:
        prev_hand = 0.0
        prev_bank = 0.0

    prev_closing_balance = prev_hand + prev_bank
    total_left = total_sells_amount + prev_closing_balance

    # 3. Right Side: PurchasePayments & Voucher Payments (CPV, BPV - Money Out)
    purchases_qs = PurchasePayments.objects.filter(
        date__date=selected_date_obj
    ).exclude(purchase_number__startswith='OPEN').exclude(payment_mood__icontains='opening').order_by('date', 'id')
    raw_purchases = []
    total_purchase_amount = 0.0

    for p in purchases_qs:
        p_name = (p.part_name or "").strip()
        p_code = (p.party_code or "").strip()
        if p_name and p_code:
            party_name = f"{p_name} ({p_code})"
        elif p_name:
            party_name = p_name
        elif p_code:
            party_name = f"Party ({p_code})"
        else:
            party_name = "Vendor"

        amt = safe_decimal(p.amount)
        total_purchase_amount += amt
        p_dt = p.date or datetime.combine(selected_date_obj, time.min)
        raw_purchases.append({
            'sort_dt': p_dt,
            'sort_id': p.id or 0,
            'party_name': party_name,
            'amount': amt,
            'payment_mood': p.payment_mood or "-",
            'purchase_number': p.purchase_number or "-",
            'remarks': p.remarks or "-",
        })

    # Add CPV & BPV Vouchers (Cash & Bank Payments)
    vouchers_out = Voucher.objects.filter(
        date=selected_date_obj,
        voucher_type__in=['CPV', 'BPV', 'Payment Voucher']
    ).prefetch_related('details__account', 'details__party').order_by('date', 'id')

    for v in vouchers_out:
        # Get opposing party or account
        opposing = v.details.exclude(account__code__in=['010101001', '1110001']).exclude(account__code__startswith='010101').exclude(account__code__startswith='1110').first()
        if _is_expense_voucher_line(v, opposing):
            # Exclude operating expense vouchers here; they are accounted for under Expenses
            continue

        amt = float(v.total_amount)
        total_purchase_amount += amt
        if opposing:
            party_name = opposing.party.company_name if opposing.party else (opposing.account.party.company_name if opposing.account.party else opposing.account.name)
        else:
            party_name = "Cash / Bank Payment"

        if v.created_at:
            v_created = timezone.localtime(v.created_at) if hasattr(v.created_at, 'tzinfo') and v.created_at.tzinfo else v.created_at
            v_dt = datetime.combine(v.date, v_created.time())
        else:
            v_dt = datetime.combine(v.date, time.min)

        raw_purchases.append({
            'sort_dt': v_dt,
            'sort_id': v.id or 0,
            'party_name': f"[{v.voucher_type}] {party_name}",
            'amount': amt,
            'payment_mood': v.voucher_type,
            'purchase_number': v.voucher_no,
            'remarks': v.remarks or opposing.narration if opposing else "-",
        })

    raw_purchases.sort(key=_sort_dt_key)

    purchases_list = []
    for idx, item in enumerate(raw_purchases, 1):
        item['sr'] = idx
        purchases_list.append(item)

    # 4. Expenses for that date from Expensedetail
    expenses_qs = Expensedetail.objects.filter(date__date=selected_date_obj)
    total_expense_amount = sum(safe_decimal(e.amount) for e in expenses_qs)

    total_right = total_purchase_amount + total_expense_amount

    # 5. Net Calculation: (Sells + Prev Day Closing) - (Purchase + Expense)
    net_balance = total_left - total_right
    is_positive_balance = net_balance >= 0

    return {
        'selected_date': selected_date_str,
        'selected_date_display': selected_date_display,
        'sells_list': sells_list,
        'total_sells_amount': total_sells_amount,
        'prev_closing_balance': prev_closing_balance,
        'prev_hand': prev_hand,
        'prev_bank': prev_bank,
        'total_left': total_left,
        'purchases_list': purchases_list,
        'total_purchase_amount': total_purchase_amount,
        'total_expense_amount': total_expense_amount,
        'total_right': total_right,
        'net_balance': net_balance,
        'is_positive_balance': is_positive_balance,
        'abs_net_balance': abs(net_balance),
    }


def cash_report(request):
    if not request.session.get('user_id'):
        return redirect('login')

    if request.GET.get('action') == 'print':
        return cash_report_print(request)

    data = _get_cash_report_data(request)
    return render(request, 'Reports/cashreport.html', data)


def cash_report_print(request):
    if not request.session.get('user_id'):
        return redirect('login')

    data = _get_cash_report_data(request)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=8 * mm,
        rightMargin=8 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
        title=f"Cash_Report_{data['selected_date']}"
    )

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontSize = 7.5
    normal_style.leading = 9.5

    elements = []

    # 1. Header Banner with MJ POULTRIES prominently displayed
    banner_cell = Paragraph(
        f"<font color='white' size=16><b>MJ POULTRIES</b></font><br/>"
        f"<font color='#93c5fd' size=10><b>DAILY CASH REPORT (روزانہ کیش رپورٹ)</b></font><br/>"
        f"<font color='#e2e8f0' size=8>Date: {data['selected_date_display']}</font>",
        ParagraphStyle('CRBanner', fontName='Helvetica-Bold', fontSize=14, leading=17, alignment=1, textColor=colors.white)
    )
    title_banner = Table([[banner_cell]], colWidths=[281 * mm])
    title_banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0B2545')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(title_banner)
    elements.append(Spacer(1, 3 * mm))

    # 2. Top KPI Overview Table (4 cards)
    bal_color = '#15803d' if data['is_positive_balance'] else '#b91c1c'
    kpi_data = [
        [
            Paragraph(
                f"<font size=7 color='#64748b'>TOTAL CASH RECEIPTS (کل وصولیاں)</font><br/>"
                f"<font color='#15803d' size=9.5><b>PKR {data['total_sells_amount']:,.2f}</b></font><br/>"
                f"<font size=6.5 color='#64748b'>{len(data['sells_list'])} Cash Receipts</font>",
                normal_style
            ),
            Paragraph(
                f"<font size=7 color='#64748b'>PREV DAY CLOSING (سابقہ کیش)</font><br/>"
                f"<font color='#0284c7' size=9.5><b>PKR {data['prev_closing_balance']:,.2f}</b></font><br/>"
                f"<font size=6.5 color='#64748b'>Hand: {data['prev_hand']:,.2f} | Bank: {data['prev_bank']:,.2f}</font>",
                normal_style
            ),
            Paragraph(
                f"<font size=7 color='#64748b'>PAYMENTS & EXPENSES (ادائیگیاں)</font><br/>"
                f"<font color='#b91c1c' size=9.5><b>PKR {data['total_right']:,.2f}</b></font><br/>"
                f"<font size=6.5 color='#64748b'>Paid: {data['total_purchase_amount']:,.2f} | Exp: {data['total_expense_amount']:,.2f}</font>",
                normal_style
            ),
            Paragraph(
                f"<font size=7 color='#64748b'>NET CLOSING CASH (اختتامی کیش)</font><br/>"
                f"<font color='{bal_color}' size=9.5><b>PKR {data['abs_net_balance']:,.2f}</b></font><br/>"
                f"<font size=6.5 color='{bal_color}'><b>{'POSITIVE' if data['is_positive_balance'] else 'NEGATIVE'}</b></font>",
                normal_style
            ),
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[70.25 * mm, 70.25 * mm, 70.25 * mm, 70.25 * mm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 3 * mm))

    # 3. Side-by-Side Tables: Left (Cash Receipts) & Right (Cash Payments & Expenses)
    # --- Left Table (Receipts & Previous Day Balance) ---
    s_table_data = [
        [
            Paragraph("<font color='white'><b>CASH RECEIPTS / COLLECTIONS (کیش وصولیاں)</b></font>", normal_style),
            "", ""
        ],
        ["#", "Party / Source Name", "Amount (PKR)"]
    ]

    if data['sells_list']:
        for s in data['sells_list']:
            s_table_data.append([
                str(s['sr']),
                Paragraph(f"<font size=7.5>{s['customer_name']}</font>", normal_style),
                f"PKR {s['amount']:,.2f}",
            ])
    else:
        s_table_data.append([
            "-",
            Paragraph("<font color='#94a3b8'>No cash receipt recorded for this date</font>", normal_style),
            "-"
        ])

    # Sells Subtotal Row
    s_table_data.append([
        "Total Cash Receipts (کل وصولیاں)",
        "",
        f"PKR {data['total_sells_amount']:,.2f}"
    ])

    # Previous Day Closing Row
    s_table_data.append([
        "Previous Day Closing Balance (سابقہ کیش)",
        "",
        f"PKR {data['prev_closing_balance']:,.2f}"
    ])

    # Left Grand Total Row: Sells + Previous Day
    s_table_data.append([
        "Total Available Cash (کل دستیاب کیش)",
        "",
        f"PKR {data['total_left']:,.2f}"
    ])

    s_col_widths = [10 * mm, 88 * mm, 41 * mm]
    left_table = Table(s_table_data, colWidths=s_col_widths)
    l_style = [
        # Title Row
        ('SPAN', (0, 0), (2, 0)),
        ('BACKGROUND', (0, 0), (2, 0), colors.HexColor('#15803D')),
        ('ALIGN', (0, 0), (2, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (2, 0), 4),
        ('BOTTOMPADDING', (0, 0), (2, 0), 4),
        # Column Header Row
        ('BACKGROUND', (0, 1), (2, 1), colors.HexColor('#166534')),
        ('TEXTCOLOR', (0, 1), (2, 1), colors.white),
        ('FONTNAME', (0, 1), (2, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (2, 1), 7.5),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('TOPPADDING', (0, 1), (2, -1), 3),
        ('BOTTOMPADDING', (0, 1), (2, -1), 3),
        ('GRID', (0, 1), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        # Sells Subtotal Row
        ('SPAN', (0, -3), (1, -3)),
        ('BACKGROUND', (0, -3), (-1, -3), colors.HexColor('#F0FDF4')),
        ('FONTNAME', (0, -3), (-1, -3), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -3), (-1, -3), colors.HexColor('#166534')),
        # Prev Day Row
        ('SPAN', (0, -2), (1, -2)),
        ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor('#F0F9FF')),
        ('FONTNAME', (0, -2), (-1, -2), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -2), (-1, -2), colors.HexColor('#0369A1')),
        # Grand Total Left Row
        ('SPAN', (0, -1), (1, -1)),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#DCFCE7')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#14532D')),
    ]
    for r_i in range(2, len(s_table_data) - 3):
        bg = colors.HexColor('#F8FAFC') if r_i % 2 == 0 else colors.white
        l_style.append(('BACKGROUND', (0, r_i), (-1, r_i), bg))
    left_table.setStyle(TableStyle(l_style))

    # --- Right Table (Payments, Purchases & Expense) ---
    p_table_data = [
        [
            Paragraph("<font color='white'><b>CASH PAYMENTS & EXPENSES (کیش ادائیگیاں)</b></font>", normal_style),
            "", ""
        ],
        ["#", "Party / Account Name", "Amount (PKR)"]
    ]

    if data['purchases_list']:
        for p in data['purchases_list']:
            p_table_data.append([
                str(p['sr']),
                Paragraph(f"<font size=7.5>{p['party_name']}</font>", normal_style),
                f"PKR {p['amount']:,.2f}",
            ])
    else:
        p_table_data.append([
            "-",
            Paragraph("<font color='#94a3b8'>No cash payment recorded for this date</font>", normal_style),
            "-"
        ])

    # Purchase Subtotal Row
    p_table_data.append([
        "Total Cash Payments (پارٹی ادائیگیاں)",
        "",
        f"PKR {data['total_purchase_amount']:,.2f}"
    ])

    # Expenses Row
    p_table_data.append([
        "Expense (کل اخراجات)",
        "",
        f"PKR {data['total_expense_amount']:,.2f}"
    ])

    # Right Grand Total Row: Purchases + Expenses
    p_table_data.append([
        "Total Cash Outflow (کل ادائیگیاں و اخراجات)",
        "",
        f"PKR {data['total_right']:,.2f}"
    ])

    p_col_widths = [10 * mm, 88 * mm, 41 * mm]
    right_table = Table(p_table_data, colWidths=p_col_widths)
    r_style = [
        # Title Row
        ('SPAN', (0, 0), (2, 0)),
        ('BACKGROUND', (0, 0), (2, 0), colors.HexColor('#0B2545')),
        ('ALIGN', (0, 0), (2, 0), 'CENTER'),
        ('TOPPADDING', (0, 0), (2, 0), 4),
        ('BOTTOMPADDING', (0, 0), (2, 0), 4),
        # Column Header Row
        ('BACKGROUND', (0, 1), (2, 1), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0, 1), (2, 1), colors.white),
        ('FONTNAME', (0, 1), (2, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (2, 1), 7.5),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('TOPPADDING', (0, 1), (2, -1), 3),
        ('BOTTOMPADDING', (0, 1), (2, -1), 3),
        ('GRID', (0, 1), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        # Purchase Subtotal Row
        ('SPAN', (0, -3), (1, -3)),
        ('BACKGROUND', (0, -3), (-1, -3), colors.HexColor('#EFF6FF')),
        ('FONTNAME', (0, -3), (-1, -3), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -3), (-1, -3), colors.HexColor('#1E40AF')),
        # Expense Row
        ('SPAN', (0, -2), (1, -2)),
        ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor('#FEF2F2')),
        ('FONTNAME', (0, -2), (-1, -2), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -2), (-1, -2), colors.HexColor('#B91C1C')),
        # Grand Total Right Row
        ('SPAN', (0, -1), (1, -1)),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#FEE2E2')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#991B1B')),
    ]
    for r_i in range(2, len(p_table_data) - 3):
        bg = colors.HexColor('#F8FAFC') if r_i % 2 == 0 else colors.white
        r_style.append(('BACKGROUND', (0, r_i), (-1, r_i), bg))
    right_table.setStyle(TableStyle(r_style))

    # Put side-by-side in outer table
    side_by_side = Table(
        [[left_table, right_table]],
        colWidths=[139 * mm, 139 * mm]
    )
    side_by_side.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 1),
        ('RIGHTPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(side_by_side)

    # 4. Bottom Net Summary Table: (Sells + Prev Day) - (Purchase + Expense)
    net_badge_color = '#15803d' if data['is_positive_balance'] else '#b91c1c'
    bottom_summary_data = [
        [
            Paragraph(
                f"<font size=8 color='#475569'><b>TOTAL AVAILABLE (آمدنی + سابقہ کیش)</b></font><br/>"
                f"<font size=12 color='#15803d'><b>PKR {data['total_left']:,.2f}</b></font><br/>"
                f"<font size=6.5 color='#64748b'>Sells: PKR {data['total_sells_amount']:,.2f} + Prev Closing: PKR {data['prev_closing_balance']:,.2f}</font>",
                normal_style
            ),
            Paragraph(
                f"<font size=8 color='#475569'><b>TOTAL OUTFLOW (خریداری ادائیگیاں + اخراجات)</b></font><br/>"
                f"<font size=12 color='#b91c1c'><b>PKR {data['total_right']:,.2f}</b></font><br/>"
                f"<font size=6.5 color='#64748b'>Purchases: PKR {data['total_purchase_amount']:,.2f} + Expense: PKR {data['total_expense_amount']:,.2f}</font>",
                normal_style
            ),
            Paragraph(
                f"<font size=8 color='#475569'><b>NET CASH BALANCE (اختتامی بیلنس)</b></font><br/>"
                f"<font size=13 color='{net_badge_color}'><b>PKR {data['abs_net_balance']:,.2f}</b></font><br/>"
                f"<font size=6.5 color='#64748b'>(Sells + Prev Day) &minus; (Purchase + Expense)</font>",
                normal_style
            ),
        ]
    ]
    bottom_summary_table = Table(bottom_summary_data, colWidths=[92 * mm, 92 * mm, 94 * mm])
    bottom_summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(Spacer(1, 3.5 * mm))
    elements.append(bottom_summary_table)

    def print_cash_footer(canvas, d):
        canvas.saveState()
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(colors.HexColor('#64748B'))
        canvas.drawString(8 * mm, 4 * mm, f"Printed: {timezone.now().strftime('%d-%m-%Y %H:%M')} | MJ Poultries System")
        canvas.drawRightString(289 * mm, 4 * mm, f"Page {d.page}")
        canvas.restoreState()

    doc.build(elements, onFirstPage=print_cash_footer, onLaterPages=print_cash_footer)


    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Cash_Report_{data["selected_date"]}.pdf"'
    buffer.close()
    return response


# =========================================================
# BUSINESS NET POSITION CALCULATION & REPORT
# =========================================================

def calculate_single_party_closing(party, to_date=None):
    """
    Calculates the exact closing balance of a single party, 100% identical to Party Ledger (get_party_ledger):
    - Base opening balance from Level 4 Chart of Account for this party
    - Sales Invoices (amount) as Debit (Dr)
    - Customer Receipts (received_amount or amount) as Credit (Cr)
    - Purchase Invoices (amount) as Credit (Cr)
    - Vendor Payments (amount) as Debit (Dr)
    - Voucher lines (debit / credit), excluding PUR- and SLS- vouchers to prevent double counting with invoices
    - Net Balance = base_opening + total_dr - total_cr
    Returns:
        dict with net_bal, closing_amount, closing_type ('Dr' or 'Cr'), dr, cr, base_opening, target_name
    """
    target_name = (party.company_name if party.company_name else party.owner_name or '').strip()

    sales_q = Q(customer_name__iexact=target_name)
    pur_q = Q(vendor_name__iexact=target_name)
    if party.code:
        sales_q |= Q(customer_code=party.code)
        pur_q |= Q(vendor_code=party.code)
    if party.company_name:
        sales_q |= Q(customer_name__iexact=party.company_name.strip())
        pur_q |= Q(vendor_name__iexact=party.company_name.strip())
    if party.owner_name:
        sales_q |= Q(customer_name__iexact=party.owner_name.strip())
        pur_q |= Q(vendor_name__iexact=party.owner_name.strip())

    receipt_q = sales_q | (Q(customer_code=party.code) if party.code else Q())
    vp_q = Q(part_name__iexact=target_name)
    if party.code:
        vp_q |= Q(party_code=party.code)
    if party.company_name:
        vp_q |= Q(part_name__iexact=party.company_name.strip())
    if party.owner_name:
        vp_q |= Q(part_name__iexact=party.owner_name.strip())

    party_q = Q(party=party) | Q(account__party=party)
    if target_name:
        party_q |= Q(account__name__iexact=target_name)

    voucher_filter = party_q & ~Q(voucher__voucher_no__startswith='PUR-') & ~Q(voucher__voucher_no__startswith='SLS-')

    if to_date:
        to_dt = datetime.combine(to_date, time.max)
        sales_qs = SellsInvoice.objects.filter(sales_q, entry_date__lte=to_dt)
        rec_qs = Sellspayment.objects.filter(receipt_q, entry_date__lte=to_dt)
        pur_qs = PurchaseReceiving.objects.filter(pur_q, date__lte=to_dt)
        vp_qs = PurchasePayments.objects.filter(vp_q, date__lte=to_dt)
        vouchers_qs = VoucherDetail.objects.filter(voucher_filter, voucher__date__lte=to_date)
    else:
        sales_qs = SellsInvoice.objects.filter(sales_q)
        rec_qs = Sellspayment.objects.filter(receipt_q)
        pur_qs = PurchaseReceiving.objects.filter(pur_q)
        vp_qs = PurchasePayments.objects.filter(vp_q)
        vouchers_qs = VoucherDetail.objects.filter(voucher_filter)

    party_acc = ChartOfAccount.objects.filter(party=party, level=4).first()
    if not party_acc and party.code:
        party_acc = ChartOfAccount.objects.filter(code=party.code, level=4).first()
    base_opening = safe_decimal(party_acc.opening_balance) if party_acc else 0.0

    dr = (
        sum(safe_decimal(s.amount) for s in sales_qs) +
        sum(safe_decimal(vp.amount) for vp in vp_qs) +
        sum(safe_decimal(v.debit) for v in vouchers_qs)
    )
    cr = (
        sum(safe_decimal(r.received_amount) or safe_decimal(r.amount) for r in rec_qs) +
        sum(safe_decimal(p.amount) for p in pur_qs) +
        sum(safe_decimal(v.credit) for v in vouchers_qs)
    )

    net_bal = base_opening + dr - cr
    closing_amount = round(abs(net_bal), 2)
    closing_type = 'Dr' if net_bal >= 0 else 'Cr'

    return {
        'net_bal': net_bal,
        'closing_amount': closing_amount,
        'closing_type': closing_type,
        'dr': dr,
        'cr': cr,
        'base_opening': base_opening,
        'target_name': target_name,
    }


def get_net_position_data(to_date=None):
    """
    Calculates balance for every party using the exact same logic as party ledger:
    - Each party's closing balance is calculated identically to Party Ledger.
    - If Party Closing is Debit (Dr > 0): Listed in Debit Table (Receivables).
    - If Party Closing is Credit (Cr > 0): Listed in Credit Table (Payables).
    - Total Debit = Sum of all Debit parties' closing balances
    - Total Credit = Sum of all Credit parties' closing balances
    - Cash in Hand & Cash in Bank from latest CashRecord (or COA)
    - Total Cash = Cash in Hand + Cash in Bank
    - Net Position = (Total Debit + Cash in Hand + Cash in Bank) - Total Credit
    """
    parties = Parties.objects.all().order_by('company_name', 'owner_name')

    debit_parties = []
    credit_parties = []
    total_debit = 0.0
    total_credit = 0.0

    for party in parties:
        res = calculate_single_party_closing(party, to_date=to_date)
        closing_amount = res['closing_amount']
        closing_type = res['closing_type']

        if closing_amount <= 0.009:
            continue

        party_type = (party.party_type or '').strip()
        if not party_type:
            party_type = 'Customer' if closing_type == 'Dr' else 'Vendor'

        party_info = {
            'id': party.id,
            'party_code': party.code or '',
            'party_name': res['target_name'],
            'party_type': party_type,
            'dr': res['dr'],
            'cr': res['cr'],
            'amount': closing_amount,
            'formatted_amount': f"{closing_amount:,.2f}"
        }

        if closing_type == 'Dr':
            debit_parties.append(party_info)
            total_debit += closing_amount
        else:
            credit_parties.append(party_info)
            total_credit += closing_amount

    debit_parties.sort(key=lambda x: x['amount'], reverse=True)
    credit_parties.sort(key=lambda x: x['amount'], reverse=True)

    cash_qs = CashRecord.objects.all()
    if to_date:
        to_dt = datetime.combine(to_date, time.max)
        last_cash = cash_qs.filter(date__lte=to_dt).order_by('-date', '-id').first()
    else:
        last_cash = cash_qs.order_by('-id').first()

    cash_in_hand = safe_decimal(last_cash.cash_in_hand) if (last_cash and last_cash.cash_in_hand is not None) else 0.0
    cash_in_bank = safe_decimal(last_cash.cash_in_bank) if (last_cash and last_cash.cash_in_bank is not None) else 0.0

    # Fallback to Level 4 Chart of Accounts if CashRecord is empty
    if not last_cash or (cash_in_hand == 0.0 and cash_in_bank == 0.0):
        cash_acc = ChartOfAccount.objects.filter(level=4, code__in=['010101001', '1110001']).first() or ChartOfAccount.objects.filter(level=4, name__icontains='Cash in Hand').first()
        bank_accs = ChartOfAccount.objects.filter(level=4, is_active=True).filter(Q(parent__code__in=['010101', '1110']) | Q(name__icontains='bank')).exclude(code__in=['010101001', '1110001'])
        if cash_acc and safe_decimal(cash_acc.current_balance) > 0:
            cash_in_hand = safe_decimal(cash_acc.current_balance)
        coa_bank_total = sum(safe_decimal(b.current_balance) for b in bank_accs)
        if coa_bank_total > 0:
            cash_in_bank = coa_bank_total

    total_cash = cash_in_hand + cash_in_bank
    cash_date = last_cash.date if last_cash else None
    cash_desc = (last_cash.discription if last_cash else '') or ''

    total_debit = round(total_debit, 2)
    total_credit = round(total_credit, 2)
    total_cash = round(total_cash, 2)

    net_position = round((total_debit + total_cash) - total_credit, 2)

    return {
        'debit_parties': debit_parties,
        'credit_parties': credit_parties,
        'debit_count': len(debit_parties),
        'credit_count': len(credit_parties),
        'total_debit': total_debit,
        'total_credit': total_credit,
        'cash_in_hand': cash_in_hand,
        'cash_in_bank': cash_in_bank,
        'total_cash': total_cash,
        'cash_date': cash_date,
        'cash_desc': cash_desc,
        'net_position': net_position,
        'is_positive': net_position >= 0,
    }


def net_position_report(request):
    if not request.session.get('user_id'):
        return redirect('login')

    # Agar user format=pdf ya print mang raha ho to print report call karein
    if request.GET.get('format') == 'pdf' or request.GET.get('print') in ['1', 'true', 'yes']:
        return net_position_print(request)

    to_date = None
    to_date_str = request.GET.get('to') or request.GET.get('date')
    if to_date_str:
        try:
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except Exception:
            to_date = None

    # Shuru se le kar specified ya current date tak sara cumulative data
    data = get_net_position_data(to_date=to_date)
    current_date = to_date.strftime('%d-%b-%Y') if to_date else timezone.localdate().strftime('%d-%b-%Y')

    context = {
        **data,
        'current_date': current_date,
    }
    return render(request, 'Reports/net_position.html', context)


def net_position_print(request):
    if not request.session.get('user_id'):
        return redirect('login')

    to_date = None
    to_date_str = request.GET.get('to') or request.GET.get('date')
    if to_date_str:
        try:
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except Exception:
            to_date = None

    # Shuru se le kar specified ya current date tak sara cumulative data
    data = get_net_position_data(to_date=to_date)
    today = to_date if to_date else timezone.localdate()
    today_display = today.strftime('%d-%b-%Y')

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=8 * mm,
        rightMargin=8 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
        title=f"Net_Position_Report_{today.strftime('%Y_%m_%d')}"
    )

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontSize = 7.5
    normal_style.leading = 9.5

    elements = []

    # 1. Header Banner with MJ POULTRIES prominently displayed
    banner_cell = Paragraph(
        f"<font color='white' size=16><b>MJ POULTRIES</b></font><br/>"
        f"<font color='#93c5fd' size=10><b>BUSINESS NET POSITION REPORT (کاروباری خالص پوزیشن رپورٹ)</b></font><br/>"
        f"<font color='#e2e8f0' size=8>Calculated from Inception to Current Date: {today_display} &bull; Formula: Total Debit + Total Cash &minus; Total Credit</font>",
        ParagraphStyle('CRBanner', fontName='Helvetica-Bold', fontSize=14, leading=17, alignment=1, textColor=colors.white)
    )
    title_banner = Table([[banner_cell]], colWidths=[281 * mm])
    title_banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0B2545')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(title_banner)
    elements.append(Spacer(1, 2.5 * mm))

    # 2. Top KPI Overview Table (4 cards)
    bal_color = '#15803d' if data['is_positive'] else '#b91c1c'
    kpi_data = [
        [
            Paragraph(
                f"<font size=7 color='#64748b'>TOTAL DEBIT (DR - واجـب الادا)</font><br/>"
                f"<font color='#1e40af' size=9.5><b>PKR {data['total_debit']:,.2f}</b></font><br/>"
                f"<font size=6.5 color='#64748b'>{data['debit_count']} Parties (Receivables)</font>",
                normal_style
            ),
            Paragraph(
                f"<font size=7 color='#64748b'>TOTAL CASH (ہاتھ اور بینک کیش)</font><br/>"
                f"<font color='#047857' size=9.5><b>PKR {data['total_cash']:,.2f}</b></font><br/>"
                f"<font size=6.5 color='#64748b'>Hand: {data['cash_in_hand']:,.2f} | Bank: {data['cash_in_bank']:,.2f}</font>",
                normal_style
            ),
            Paragraph(
                f"<font size=7 color='#64748b'>TOTAL CREDIT (CR - قابـل ادا)</font><br/>"
                f"<font color='#b91c1c' size=9.5><b>PKR {data['total_credit']:,.2f}</b></font><br/>"
                f"<font size=6.5 color='#64748b'>{data['credit_count']} Parties (Payables)</font>",
                normal_style
            ),
            Paragraph(
                f"<font size=7 color='#64748b'>NET POSITION (خالص کاروباری پوزیشن)</font><br/>"
                f"<font color='{bal_color}' size=9.5><b>PKR {data['net_position']:,.2f}</b></font><br/>"
                f"<font size=6.5 color='{bal_color}'><b>{'SURPLUS (مستحکم)' if data['is_positive'] else 'DEFICIT (خسارہ)'}</b></font>",
                normal_style
            ),
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[70.25 * mm, 70.25 * mm, 70.25 * mm, 70.25 * mm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 2.5 * mm))

    # 3. Side-by-Side Dual Table: Left (Debit Parties) & Right (Credit Parties)
    table_data = [
        [
            Paragraph("<font color='white'><b>DEBIT PARTIES (DR - واجـب الادا / رقم لینی ہے)</b></font>", normal_style),
            "", "", "",
            Paragraph("<font color='white'><b>CREDIT PARTIES (CR - قابـل ادا / رقم دینی ہے)</b></font>", normal_style),
            "", "", ""
        ],
        ["#", "Party Name", "Type", "Amount (PKR)", "#", "Party Name", "Type", "Amount (PKR)"]
    ]

    debits = data['debit_parties']
    credits = data['credit_parties']
    max_rows = max(len(debits), len(credits), 1)

    for i in range(max_rows):
        row = []
        if i < len(debits):
            d = debits[i]
            row.extend([str(i+1), Paragraph(f"<font size=7.5>{d['party_name']}</font>", normal_style), d['party_type'], f"{d['amount']:,.2f}"])
        else:
            row.extend(["-", "-" if i == 0 else "", "", ""])

        if i < len(credits):
            c = credits[i]
            row.extend([str(i+1), Paragraph(f"<font size=7.5>{c['party_name']}</font>", normal_style), c['party_type'], f"{c['amount']:,.2f}"])
        else:
            row.extend(["-", "-" if i == 0 else "", "", ""])
        table_data.append(row)

    # Total row
    table_data.append([
        "TOTAL DEBIT (DR)", "", "", f"PKR {data['total_debit']:,.2f}",
        "TOTAL CREDIT (CR)", "", "", f"PKR {data['total_credit']:,.2f}"
    ])

    col_widths = [10*mm, 68.5*mm, 26*mm, 35*mm, 10*mm, 68.5*mm, 26*mm, 35*mm]
    main_table = Table(table_data, colWidths=col_widths, repeatRows=2)

    t_style = [
        # Header titles
        ('SPAN', (0,0), (3,0)),
        ('BACKGROUND', (0,0), (3,0), colors.HexColor('#1E3A8A')),
        ('ALIGN', (0,0), (3,0), 'CENTER'),
        ('SPAN', (4,0), (7,0)),
        ('BACKGROUND', (4,0), (7,0), colors.HexColor('#991B1B')),
        ('ALIGN', (4,0), (7,0), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,0), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,0), 3.5),

        # Column subheaders
        ('BACKGROUND', (0,1), (3,1), colors.HexColor('#2563EB')),
        ('BACKGROUND', (4,1), (7,1), colors.HexColor('#DC2626')),
        ('TEXTCOLOR', (0,1), (-1,1), colors.white),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,1), (-1,1), 7.5),
        ('ALIGN', (0,1), (0,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-1), 'LEFT'),
        ('ALIGN', (2,1), (2,-1), 'CENTER'),
        ('ALIGN', (3,1), (3,-1), 'RIGHT'),
        ('ALIGN', (4,1), (4,-1), 'CENTER'),
        ('ALIGN', (5,1), (5,-1), 'LEFT'),
        ('ALIGN', (6,1), (6,-1), 'CENTER'),
        ('ALIGN', (7,1), (7,-1), 'RIGHT'),
        ('GRID', (0,1), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,1), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,1), (-1,-1), 2.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),

        # Total row
        ('SPAN', (0,-1), (2,-1)),
        ('BACKGROUND', (0,-1), (3,-1), colors.HexColor('#DBEAFE')),
        ('FONTNAME', (0,-1), (3,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,-1), (3,-1), colors.HexColor('#1E40AF')),

        ('SPAN', (4,-1), (6,-1)),
        ('BACKGROUND', (4,-1), (7,-1), colors.HexColor('#FEE2E2')),
        ('FONTNAME', (4,-1), (7,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (4,-1), (7,-1), colors.HexColor('#991B1B')),
    ]

    for r_i in range(2, len(table_data) - 1):
        bg = colors.HexColor('#F8FAFC') if r_i % 2 == 0 else colors.white
        t_style.append(('BACKGROUND', (0, r_i), (-1, r_i), bg))

    main_table.setStyle(TableStyle(t_style))
    elements.append(main_table)
    elements.append(Spacer(1, 2.5 * mm))

    # 4. Bottom Net Position Equation Summary
    eq_data = [
        [
            Paragraph(
                f"<b>NET POSITION FORMULA:</b> Total Debit (PKR {data['total_debit']:,.2f}) + Total Cash (PKR {data['total_cash']:,.2f}) &minus; Total Credit (PKR {data['total_credit']:,.2f}) = <b><font color='{bal_color}'>NET POSITION: PKR {data['net_position']:,.2f}</font></b>",
                ParagraphStyle('EqStyle', fontName='Helvetica', fontSize=8, leading=10, alignment=1)
            )
        ]
    ]
    eq_table = Table(eq_data, colWidths=[281 * mm])
    eq_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
    ]))
    elements.append(eq_table)

    def print_np_footer(canvas, d):
        canvas.saveState()
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(colors.HexColor('#64748B'))
        canvas.drawString(8 * mm, 4 * mm, f"Printed: {timezone.now().strftime('%d-%m-%Y %H:%M')} | MJ Poultries Management System")
        canvas.drawRightString(289 * mm, 4 * mm, f"Page {d.page}")
        canvas.restoreState()

    doc.build(elements, onFirstPage=print_np_footer, onLaterPages=print_np_footer)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Net_Position_Report_{today_display}.pdf"'
    buffer.close()
    return response
















