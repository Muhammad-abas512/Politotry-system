from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal, InvalidOperation
from datetime import datetime
import json
import re
from .models import WasteRate


def waste_rate(request):
    # Session check
    if not request.session.get('user_id'):
        if request.method == 'POST' or request.GET.get('action'):
            return JsonResponse({'success': False, 'message': 'Session expired. Please login again.'}, status=401)
        return redirect('login')

    # Month constants for parsing and sorting
    MONTHS = ['January','February','March','April','May','June',
             'July','August','September','October','November','December']
    MONTH_ORDER = {m: i+1 for i, m in enumerate(MONTHS)}

    action = request.GET.get('action') or request.POST.get('action')

    # ============ CHECK DUPLICATE (Live Check) ============
    if request.method == 'GET' and action == 'check_duplicate':
        month_year = request.GET.get('month_year', '').strip()
        exclude_id = request.GET.get('exclude_id')

        # '2025-08' → month='August', year='2025'
        month_name, year = '', ''
        if month_year and re.match(r'^\d{4}-\d{2}$', month_year):
            try:
                dt = datetime.strptime(month_year, '%Y-%m')
                month_name = MONTHS[dt.month - 1]
                year = str(dt.year)
            except ValueError:
                pass

        if not month_name or not year:
            return JsonResponse({'success': True, 'exists': False})

        qs = WasteRate.objects.filter(month=month_name, year=year)
        if exclude_id:
            try:
                qs = qs.exclude(id=int(exclude_id))
            except (ValueError, TypeError):
                pass

        exists = qs.exists()
        existing_rate = 0
        if exists:
            rec = qs.first()
            try:
                existing_rate = float(rec.rate) if rec.rate else 0
            except (ValueError, TypeError):
                existing_rate = 0

        return JsonResponse({
            'success': True,
            'exists': exists,
            'existing_rate': existing_rate,
            'label': f'{month_name} {year}'
        })

    # ============ SAVE / UPDATE ============
    if request.method == 'POST' and action == 'save':
        try:
            data = json.loads(request.body)
            rate_id = data.get('id')
            month_year = (data.get('month_year') or '').strip()
            rate_val = data.get('rate')

            # Basic Validation
            if not month_year:
                return JsonResponse({'success': False, 'message': 'Month & Year select karna zaroori hai.'})

            # Format YYYY-MM to Month Name and Year
            month_name, year = '', ''
            if re.match(r'^\d{4}-\d{2}$', month_year):
                try:
                    dt = datetime.strptime(month_year, '%Y-%m')
                    month_name = MONTHS[dt.month - 1]
                    year = str(dt.year)
                except ValueError:
                    pass

            if not month_name or not year:
                return JsonResponse({'success': False, 'message': 'Invalid month/year format.'})

            if rate_val in (None, ''):
                return JsonResponse({'success': False, 'message': 'Rate enter karna zaroori hai.'})

            try:
                rate_decimal = Decimal(str(rate_val))
                if rate_decimal <= 0:
                    return JsonResponse({'success': False, 'message': 'Rate 0 se zyada hona chahiye.'})
            except (InvalidOperation, ValueError):
                return JsonResponse({'success': False, 'message': 'Invalid rate value.'})

            # ⭐ STRICT DUPLICATE CHECK (One Month/Year = One Rate)
            duplicate_qs = WasteRate.objects.filter(month=month_name, year=year)
            if rate_id:
                try:
                    duplicate_qs = duplicate_qs.exclude(id=int(rate_id))
                except (ValueError, TypeError):
                    pass

            if duplicate_qs.exists():
                existing = duplicate_qs.first()
                try:
                    existing_rate = float(existing.rate) if existing.rate else 0
                except (ValueError, TypeError):
                    existing_rate = 0
                return JsonResponse({
                    'success': False,
                    'message': f'{month_name} {year} ka rate pehle se mojood hai (Rs {existing_rate:.2f}).',
                    'duplicate': True
                })

            # Save Logic
            if rate_id:
                # --- UPDATE CASE ---
                try:
                    obj = WasteRate.objects.get(id=int(rate_id))
                    obj.month = month_name
                    obj.year = year
                    obj.rate = str(rate_decimal)
                    obj.save()
                    return JsonResponse({'success': True, 'message': 'Waste rate kamyabi se update ho gaya!'})
                except WasteRate.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Record nahi mila.'})
            else:
                # --- CREATE CASE ---
                WasteRate.objects.create(
                    month=month_name,
                    year=year,
                    rate=str(rate_decimal)
                )
                return JsonResponse({'success': True, 'message': 'Waste rate kamyabi se save ho gaya!'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid request data.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'System Error: {str(e)}'})

    # ============ LIST / SEARCH ============
    if request.method == 'GET' and action == 'list':
        search = request.GET.get('search', '').strip()
        qs = WasteRate.objects.all()

        if search:
            qs = qs.filter(
                Q(month__icontains=search) |
                Q(year__icontains=search) |
                Q(rate__icontains=search)
            )

        # Sorting: Year descending, Month index descending
        records = list(qs)
        records.sort(
            key=lambda r: (
                int(r.year) if r.year and str(r.year).isdigit() else 0,
                MONTH_ORDER.get(r.month, 0)
            ),
            reverse=True
        )

        data = []
        for r in records:
            try:
                rate_val = float(r.rate) if r.rate else 0
            except (ValueError, TypeError):
                rate_val = 0

            # Convert to HTML month input format ('YYYY-MM')
            month_year_str = ''
            if r.month and r.year:
                m_num = MONTH_ORDER.get(r.month, 0)
                if m_num > 0:
                    month_year_str = f"{r.year}-{str(m_num).zfill(2)}"

            data.append({
                'id': r.id,
                'month': r.month or '',
                'year': r.year or '',
                'month_year': month_year_str,
                'label': f'{r.month} {r.year}' if r.month and r.year else '',
                'rate': rate_val,
            })
        return JsonResponse({'success': True, 'data': data})

    # ============ GET SINGLE (for Edit) ============
    if request.method == 'GET' and action == 'get':
        try:
            rate_id = request.GET.get('id')
            r = WasteRate.objects.get(id=int(rate_id))
            try:
                rate_val = float(r.rate) if r.rate else 0
            except (ValueError, TypeError):
                rate_val = 0

            month_year_str = ''
            if r.month and r.year:
                m_num = MONTH_ORDER.get(r.month, 0)
                if m_num > 0:
                    month_year_str = f"{r.year}-{str(m_num).zfill(2)}"

            return JsonResponse({
                'success': True,
                'data': {
                    'id': r.id,
                    'month': r.month or '',
                    'year': r.year or '',
                    'month_year': month_year_str,
                    'rate': rate_val,
                }
            })
        except (WasteRate.DoesNotExist, ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Record nahi mila.'})

    # ============ DELETE ============
    if request.method == 'POST' and action == 'delete':
        try:
            data = json.loads(request.body)
            rate_id = data.get('id')
            if not rate_id:
                return JsonResponse({'success': False, 'message': 'Record ID missing.'})

            obj = WasteRate.objects.get(id=int(rate_id))
            obj.delete()
            return JsonResponse({'success': True, 'message': 'Waste rate kamyabi se delete ho gaya!'})
        except WasteRate.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Record pehle hi delete ho chuka hai.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Delete error: {str(e)}'})

    # ============ RENDER PAGE ============
    current_month_year = timezone.now().strftime('%Y-%m')
    return render(request, 'market_rate/waste_rate.html', {
        'current_month_year': current_month_year,
    })



from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal, InvalidOperation
from datetime import datetime
import json
import re
from .models import FatRate


def fat_rate(request):
    # Session check
    if not request.session.get('user_id'):
        if request.method == 'POST' or request.GET.get('action'):
            return JsonResponse({'success': False, 'message': 'Session expired. Please login again.'}, status=401)
        return redirect('login')

    # Month constants for parsing and sorting
    MONTHS = ['January','February','March','April','May','June',
             'July','August','September','October','November','December']
    MONTH_ORDER = {m: i+1 for i, m in enumerate(MONTHS)}

    action = request.GET.get('action') or request.POST.get('action')

    # ============ CHECK DUPLICATE (Live Check) ============
    if request.method == 'GET' and action == 'check_duplicate':
        month_year = request.GET.get('month_year', '').strip()
        exclude_id = request.GET.get('exclude_id')

        # '2025-08' → month='August', year='2025'
        month_name, year = '', ''
        if month_year and re.match(r'^\d{4}-\d{2}$', month_year):
            try:
                dt = datetime.strptime(month_year, '%Y-%m')
                month_name = MONTHS[dt.month - 1]
                year = str(dt.year)
            except ValueError:
                pass

        if not month_name or not year:
            return JsonResponse({'success': True, 'exists': False})

        qs = FatRate.objects.filter(month=month_name, year=year)
        if exclude_id:
            try:
                qs = qs.exclude(id=int(exclude_id))
            except (ValueError, TypeError):
                pass

        exists = qs.exists()
        existing_rate = 0
        if exists:
            rec = qs.first()
            try:
                existing_rate = float(rec.rate) if rec.rate else 0
            except (ValueError, TypeError):
                existing_rate = 0

        return JsonResponse({
            'success': True,
            'exists': exists,
            'existing_rate': existing_rate,
            'label': f'{month_name} {year}'
        })

    # ============ SAVE / UPDATE ============
    if request.method == 'POST' and action == 'save':
        try:
            data = json.loads(request.body)
            rate_id = data.get('id')
            month_year = (data.get('month_year') or '').strip()
            rate_val = data.get('rate')

            # Basic Validation
            if not month_year:
                return JsonResponse({'success': False, 'message': 'Month & Year select karna zaroori hai.'})

            # Format YYYY-MM to Month Name and Year
            month_name, year = '', ''
            if re.match(r'^\d{4}-\d{2}$', month_year):
                try:
                    dt = datetime.strptime(month_year, '%Y-%m')
                    month_name = MONTHS[dt.month - 1]
                    year = str(dt.year)
                except ValueError:
                    pass

            if not month_name or not year:
                return JsonResponse({'success': False, 'message': 'Invalid month/year format.'})

            if rate_val in (None, ''):
                return JsonResponse({'success': False, 'message': 'Rate enter karna zaroori hai.'})

            try:
                rate_decimal = Decimal(str(rate_val))
                if rate_decimal <= 0:
                    return JsonResponse({'success': False, 'message': 'Rate 0 se zyada hona chahiye.'})
            except (InvalidOperation, ValueError):
                return JsonResponse({'success': False, 'message': 'Invalid rate value.'})

            # ⭐ STRICT DUPLICATE CHECK (One Month/Year = One Rate)
            duplicate_qs = FatRate.objects.filter(month=month_name, year=year)
            if rate_id:
                try:
                    duplicate_qs = duplicate_qs.exclude(id=int(rate_id))
                except (ValueError, TypeError):
                    pass

            if duplicate_qs.exists():
                existing = duplicate_qs.first()
                try:
                    existing_rate = float(existing.rate) if existing.rate else 0
                except (ValueError, TypeError):
                    existing_rate = 0
                return JsonResponse({
                    'success': False,
                    'message': f'{month_name} {year} ka rate pehle se mojood hai (Rs {existing_rate:.2f}).',
                    'duplicate': True
                })

            # Save Logic
            if rate_id:
                # --- UPDATE CASE ---
                try:
                    obj = FatRate.objects.get(id=int(rate_id))
                    obj.month = month_name
                    obj.year = year
                    obj.rate = str(rate_decimal)
                    obj.save()
                    return JsonResponse({'success': True, 'message': 'Fat rate kamyabi se update ho gaya!'})
                except FatRate.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Record nahi mila.'})
            else:
                # --- CREATE CASE ---
                FatRate.objects.create(
                    month=month_name,
                    year=year,
                    rate=str(rate_decimal)
                )
                return JsonResponse({'success': True, 'message': 'Fat rate kamyabi se save ho gaya!'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid request data.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'System Error: {str(e)}'})

    # ============ LIST / SEARCH ============
    if request.method == 'GET' and action == 'list':
        search = request.GET.get('search', '').strip()
        qs = FatRate.objects.all()

        if search:
            qs = qs.filter(
                Q(month__icontains=search) |
                Q(year__icontains=search) |
                Q(rate__icontains=search)
            )

        # Python sorting: Year descending, Month index descending
        records = list(qs)
        records.sort(
            key=lambda r: (
                int(r.year) if r.year and str(r.year).isdigit() else 0,
                MONTH_ORDER.get(r.month, 0)
            ),
            reverse=True
        )

        data = []
        for r in records:
            try:
                rate_val = float(r.rate) if r.rate else 0
            except (ValueError, TypeError):
                rate_val = 0

            # Convert to HTML month input format ('YYYY-MM')
            month_year_str = ''
            if r.month and r.year:
                m_num = MONTH_ORDER.get(r.month, 0)
                if m_num > 0:
                    month_year_str = f"{r.year}-{str(m_num).zfill(2)}"

            data.append({
                'id': r.id,
                'month': r.month or '',
                'year': r.year or '',
                'month_year': month_year_str,
                'label': f'{r.month} {r.year}' if r.month and r.year else '',
                'rate': rate_val,
            })
        return JsonResponse({'success': True, 'data': data})

    # ============ GET SINGLE (for Edit) ============
    if request.method == 'GET' and action == 'get':
        try:
            rate_id = request.GET.get('id')
            r = FatRate.objects.get(id=int(rate_id))
            try:
                rate_val = float(r.rate) if r.rate else 0
            except (ValueError, TypeError):
                rate_val = 0

            month_year_str = ''
            if r.month and r.year:
                m_num = MONTH_ORDER.get(r.month, 0)
                if m_num > 0:
                    month_year_str = f"{r.year}-{str(m_num).zfill(2)}"

            return JsonResponse({
                'success': True,
                'data': {
                    'id': r.id,
                    'month': r.month or '',
                    'year': r.year or '',
                    'month_year': month_year_str,
                    'rate': rate_val,
                }
            })
        except (FatRate.DoesNotExist, ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Record nahi mila.'})

    # ============ DELETE ============
    if request.method == 'POST' and action == 'delete':
        try:
            data = json.loads(request.body)
            rate_id = data.get('id')
            if not rate_id:
                return JsonResponse({'success': False, 'message': 'Record ID missing.'})

            obj = FatRate.objects.get(id=int(rate_id))
            obj.delete()
            return JsonResponse({'success': True, 'message': 'Fat rate kamyabi se delete ho gaya!'})
        except FatRate.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Record pehle hi delete ho chuka hai.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Delete error: {str(e)}'})

    # ============ RENDER PAGE ============
    current_month_year = timezone.now().strftime('%Y-%m')
    return render(request, 'market_rate/fat_rate.html', {
        'current_month_year': current_month_year,
    })


from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal, InvalidOperation
from datetime import datetime
import json
from .models import BroilerRate


def broiler_rate(request):
    # Session check (Agar user login nahi hai)
    if not request.session.get('user_id'):
        if request.method == 'POST' or request.GET.get('action'):
            return JsonResponse({'success': False, 'message': 'Session expired. Please login again.'}, status=401)
        return redirect('login')

    action = request.GET.get('action') or request.POST.get('action')

    # ============================================================
    # 1. LIVE DATE DUPLICATE CHECK (Frontend k lye)
    # ============================================================
    if request.method == 'GET' and action == 'check_date':
        date_str = request.GET.get('date', '').strip()
        exclude_id = request.GET.get('exclude_id')

        if not date_str:
            return JsonResponse({'success': True, 'exists': False})

        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': True, 'exists': False})

        qs = BroilerRate.objects.filter(date=date_obj)
        if exclude_id:
            try:
                qs = qs.exclude(id=int(exclude_id))
            except (ValueError, TypeError):
                pass

        exists = qs.exists()
        existing_rate = None
        if exists:
            rec = qs.first()
            existing_rate = float(rec.rate) if rec.rate is not None else 0

        return JsonResponse({
            'success': True,
            'exists': exists,
            'existing_rate': existing_rate,
            'date_display': date_obj.strftime('%d %b %Y')
        })

    # ============================================================
    # 2. SAVE YA UPDATE RATE
    # ============================================================
    if request.method == 'POST' and action == 'save':
        try:
            data = json.loads(request.body)
            rate_id = data.get('id')
            date_str = (data.get('date') or '').strip()
            rate_val = data.get('rate')

            # Required field validation
            if not date_str:
                return JsonResponse({'success': False, 'message': 'Date enter karna zaroori hai'})
            if rate_val in (None, ''):
                return JsonResponse({'success': False, 'message': 'Rate enter karna zaroori hai'})

            # Parse Date
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid date format'})

            # Parse Rate
            try:
                rate_decimal = Decimal(str(rate_val))
                if rate_decimal <= 0:
                    return JsonResponse({'success': False, 'message': 'Rate 0 se zyada hona chahiye'})
            except (InvalidOperation, ValueError):
                return JsonResponse({'success': False, 'message': 'Invalid rate value'})

            # ⭐ DUPLICATE CHECK: Ek date par sirf 1 hi rate aa sakta hai
            duplicate_qs = BroilerRate.objects.filter(date=date_obj)
            if rate_id:
                try:
                    duplicate_qs = duplicate_qs.exclude(id=int(rate_id))
                except (ValueError, TypeError):
                    pass

            if duplicate_qs.exists():
                existing = duplicate_qs.first()
                existing_rate = float(existing.rate) if existing.rate is not None else 0
                return JsonResponse({
                    'success': False,
                    'message': f'{date_obj.strftime("%d %b %Y")} ka rate pehle se mojood hai (Rs {existing_rate:.2f}). Ek date pe sirf aik rate save ho sakta hai.',
                    'duplicate': True
                })

            # --- UPDATE CASE ---
            if rate_id:
                try:
                    obj = BroilerRate.objects.get(id=int(rate_id))
                    obj.date = date_obj
                    obj.rate = rate_decimal
                    obj.save()
                    return JsonResponse({
                        'success': True,
                        'message': 'Rate kamyabi se update ho gaya!'
                    })
                except BroilerRate.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Record nahi mila'})

            # --- INSERT CASE ---
            else:
                BroilerRate.objects.create(date=date_obj, rate=rate_decimal)
                return JsonResponse({
                    'success': True,
                    'message': 'Rate kamyabi se save ho gaya!'
                })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid request data'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'System error: {str(e)}'})

    # ============================================================
    # 3. LIST & SEARCH
    # ============================================================
    if request.method == 'GET' and action == 'list':
        search = request.GET.get('search', '').strip()
        qs = BroilerRate.objects.all().order_by('-date', '-id')

        if search:
            qs = qs.filter(
                Q(rate__icontains=search) |
                Q(date__icontains=search)
            )

        data = []
        for r in qs:
            data.append({
                'id': r.id,
                'date': r.date.strftime('%d %b %Y') if r.date else '',
                'date_raw': r.date.strftime('%Y-%m-%d') if r.date else '',
                'rate': float(r.rate) if r.rate is not None else 0,
            })
        return JsonResponse({'success': True, 'data': data})

    # ============================================================
    # 4. SINGLE RECORD (Edit Form k lye)
    # ============================================================
    if request.method == 'GET' and action == 'get':
        try:
            rate_id = request.GET.get('id')
            r = BroilerRate.objects.get(id=int(rate_id))
            return JsonResponse({
                'success': True,
                'data': {
                    'id': r.id,
                    'date': r.date.strftime('%Y-%m-%d') if r.date else '',
                    'rate': float(r.rate) if r.rate is not None else 0,
                }
            })
        except (BroilerRate.DoesNotExist, ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Record nahi mila'})

    # ============================================================
    # 5. DELETE
    # ============================================================
    if request.method == 'POST' and action == 'delete':
        try:
            data = json.loads(request.body)
            rate_id = data.get('id')
            if not rate_id:
                return JsonResponse({'success': False, 'message': 'Record ID missing'})

            obj = BroilerRate.objects.get(id=int(rate_id))
            obj.delete()
            return JsonResponse({
                'success': True,
                'message': 'Rate kamyabi se delete ho gaya!'
            })
        except BroilerRate.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Record pehle hi delete ho chuka hai'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Delete error: {str(e)}'})

    # ============================================================
    # 6. DEFAULT PAGE LOAD
    # ============================================================
    today = timezone.now().date().strftime('%Y-%m-%d')
    return render(request, 'market_rate/broiler_rate.html', {'today': today})










































































