import io
from django.shortcuts import render, redirect
from django.http import JsonResponse, FileResponse
from datetime import datetime, time
from .models import Parties, SellsInvoice, Sellspayment, PurchaseReceiving, PurchasePayments
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

        # 1. OPENING BALANCE LOGIC
        old_sales = SellsInvoice.objects.filter(customer_name__iexact=target_name, entry_date__lt=from_dt)
        old_receipts = Sellspayment.objects.filter(customer_name__iexact=target_name, entry_date__lt=from_dt)
        old_purchases = PurchaseReceiving.objects.filter(vendor_name__iexact=target_name, date__lt=from_dt)
        old_vendor_pays = PurchasePayments.objects.filter(part_name__iexact=target_name, date__lt=from_dt)

        op_dr = sum(safe_decimal(s.amount) for s in old_sales) + sum(safe_decimal(vp.amount) for vp in old_vendor_pays)
        op_cr = sum(safe_decimal(r.received_amount) or safe_decimal(r.amount) for r in old_receipts) + sum(safe_decimal(p.amount) for p in old_purchases)
        opening_balance = op_dr - op_cr

        # 2. TRANSACTIONS
        combined = []
        for inv in SellsInvoice.objects.filter(customer_name__iexact=target_name, entry_date__range=[from_dt, to_dt]):
            combined.append({'dt': inv.entry_date, 'priority': 1, 'desc': f"Sale Invoice #{inv.sells_no}", 'w': inv.weight, 'mr': '-', 'vr': inv.rate, 'dr': safe_decimal(inv.amount), 'cr': 0.0})
        for rec in Sellspayment.objects.filter(customer_name__iexact=target_name, entry_date__range=[from_dt, to_dt]):
            combined.append({'dt': rec.entry_date, 'priority': 2, 'desc': rec.description or "Customer Receipt", 'w': rec.weight, 'mr': '-', 'vr': rec.rate, 'dr': 0.0, 'cr': safe_decimal(rec.received_amount) or safe_decimal(rec.amount)})
        for pur in PurchaseReceiving.objects.filter(vendor_name__iexact=target_name, date__range=[from_dt, to_dt]):
            combined.append({'dt': pur.date, 'priority': 1, 'desc': f"Purchase Invoice #{pur.purchase_number}", 'w': pur.weight, 'mr': pur.market_rate, 'vr': pur.vendor_rate, 'dr': 0.0, 'cr': safe_decimal(pur.amount)})
        for vp in PurchasePayments.objects.filter(part_name__iexact=target_name, date__range=[from_dt, to_dt]):
            combined.append({'dt': vp.date, 'priority': 2, 'desc': vp.remarks or "Vendor Payment", 'w': '-', 'mr': '-', 'vr': '-', 'dr': safe_decimal(vp.amount), 'cr': 0.0})

        combined.sort(key=lambda x: (x['dt'] or from_dt, x['priority']))

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
            # Column headers matches your request: M-Rate, Weight, Rate
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
            # Column widths adjusted for A4 Portrait (Total wide ~535 points)
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
            
            buffer.seek(0)
            return FileResponse(buffer, as_attachment=False, filename=f"Ledger_{target_name}.pdf")

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

    op_dr = sum(safe_decimal(s.amount) for s in old_sales) + sum(safe_decimal(vp.amount) for vp in old_vendor_pays)
    op_cr = sum(safe_decimal(r.received_amount) or safe_decimal(r.amount) for r in old_receipts) + sum(safe_decimal(p.amount) for p in old_purchases)
    opening_balance = op_dr - op_cr

    combined = []
    for inv in SellsInvoice.objects.filter(customer_name__iexact=target_name, entry_date__range=[from_dt, to_dt]):
        combined.append({'date': inv.entry_date.date(), 'sort_dt': inv.entry_date, 'priority': 1, 'code': inv.sells_no or f"SI-{inv.id}", 'desc': f"Sale Invoice #{inv.sells_no}", 'dr': safe_decimal(inv.amount), 'cr': 0.0})
    for rec in Sellspayment.objects.filter(customer_name__iexact=target_name, entry_date__range=[from_dt, to_dt]):
        combined.append({'date': rec.entry_date.date(), 'sort_dt': rec.entry_date, 'priority': 2, 'code': rec.sell_no or f"REC-{rec.id}", 'desc': rec.description or "Customer Receipt", 'dr': 0.0, 'cr': safe_decimal(rec.received_amount) or safe_decimal(rec.amount)})
    for pur in PurchaseReceiving.objects.filter(vendor_name__iexact=target_name, date__range=[from_dt, to_dt]):
        combined.append({'date': pur.date.date(), 'sort_dt': pur.date, 'priority': 1, 'code': pur.purchase_number or f"PI-{pur.id}", 'desc': f"Purchase Invoice #{pur.purchase_number}", 'dr': 0.0, 'cr': safe_decimal(pur.amount)})
    for vp in PurchasePayments.objects.filter(part_name__iexact=target_name, date__range=[from_dt, to_dt]):
        combined.append({'date': vp.date.date(), 'sort_dt': vp.date, 'priority': 2, 'code': vp.purchase_number or f"PAY-{vp.id}", 'desc': vp.remarks or "Vendor Payment", 'dr': safe_decimal(vp.amount), 'cr': 0.0})

    combined.sort(key=lambda x: (x['sort_dt'], x['priority']))
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

    today = timezone.localdate().strftime('%Y-%m-%d')

    party_name = request.GET.get('party_name', '').strip()
    from_date = request.GET.get('from_date') or today
    to_date = request.GET.get('to_date') or today

    parties = (
        Parties.objects
        .filter(Q(party_type__iexact='vendor') | Q(party_type__iexact='trader'))
        .exclude(company_name__isnull=True)
        .exclude(company_name='')
        .order_by('company_name')
    )

    records = PurchaseReceivingView.objects.all()

    if party_name:
        records = records.filter(vendor_name=party_name)

    if from_date:
        records = records.filter(date__date__gte=from_date)

    if to_date:
        records = records.filter(date__date__lte=to_date)

    records = records.order_by('-date', '-id')

    # Totals
    total_weight = sum((r.weight or 0) for r in records)
    total_amount = sum((r.amount or 0) for r in records)
    total_paid = sum((r.payed_amount or 0) for r in records)
    total_remaining = sum((r.remaining_amount or 0) for r in records)

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

    today = timezone.localdate().strftime('%Y-%m-%d')

    party_name = request.GET.get('party_name', '').strip()
    from_date = request.GET.get('from_date') or today
    to_date = request.GET.get('to_date') or today

    records = PurchaseReceivingView.objects.all()

    if party_name:
        records = records.filter(vendor_name=party_name)

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

    elements.append(
        Paragraph(
            f'Party: {party_text} &nbsp;&nbsp; | &nbsp;&nbsp; '
            f'From: {from_date} &nbsp;&nbsp; | &nbsp;&nbsp; To: {to_date}',
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

    today = timezone.localdate().strftime('%Y-%m-%d')
    party = (request.GET.get('party_name') or '').strip()
    from_date = request.GET.get('from_date') or today
    to_date = request.GET.get('to_date') or today

    parties = Parties.objects.filter(
        Q(party_type__iexact='customer') | Q(party_type__iexact='trader')
    ).exclude(company_name__isnull=True).exclude(company_name='').order_by('company_name')

    records = SellsInvoice.objects.all()
    if party:
        records = records.filter(customer_name=party)
    records = records.filter(
        entry_date__date__gte=from_date,
        entry_date__date__lte=to_date
    ).order_by('-entry_date', '-id')

    def num(value):
        try:
            return Decimal(str(value or '0').replace(',', '').strip())
        except (InvalidOperation, ValueError, TypeError):
            return Decimal('0')

    total_weight = total_amount = total_received = total_remaining = Decimal('0')
    for row in records:
        total_weight += num(row.weight)
        total_amount += num(row.amount)
        total_received += num(row.received_amount)
        total_remaining += num(row.remaining_amount)

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

    today = timezone.localdate().strftime('%Y-%m-%d')
    party = (request.GET.get('party_name') or '').strip()
    from_date = request.GET.get('from_date') or today
    to_date = request.GET.get('to_date') or today

    records = SellsInvoice.objects.all()
    if party:
        records = records.filter(customer_name=party)
    records = records.filter(
        entry_date__date__gte=from_date,
        entry_date__date__lte=to_date
    ).order_by('entry_date', 'id')

    def num(value):
        try:
            return Decimal(str(value or '0').replace(',', '').strip())
        except:
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
        received, remaining = num(row.received_amount), num(row.remaining_amount)
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
        topMargin=10*mm, bottomMargin=10*mm
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        'title', parent=styles['Heading1'],
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
    ]))

    party_text = party or 'All Customers / Traders'
    doc.build([
        Paragraph('SELLS REPORT', title),
        Spacer(1, 2*mm),
        Paragraph(f'Party: {party_text} | From: {from_date} | To: {to_date}', info),
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











