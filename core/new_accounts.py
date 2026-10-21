from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
import json
from .models import Parties
from .accounts_views import sync_single_party_to_coa, sync_all_parties_to_coa


def generate_party_code():
    """Generate next party code like 0001, 0002, 0003..."""
    last_party = Parties.objects.exclude(code__isnull=True).exclude(code='').order_by('-id').first()
    if last_party and last_party.code:
        try:
            last_num = int(last_party.code)
            next_num = last_num + 1
        except (ValueError, TypeError):
            next_num = Parties.objects.count() + 1
    else:
        next_num = 1
    return str(next_num).zfill(4)  # 0001, 0002...


def parties(request):
    # Session check
    if not request.session.get('user_id'):
        if request.method == 'POST' or request.GET.get('action'):
            return JsonResponse({'success': False, 'message': 'Session expired'}, status=401)
        return redirect('login')

    # Ensure parties exist in Chart of Accounts Level 4
    sync_all_parties_to_coa()

    action = request.GET.get('action') or request.POST.get('action')

    # ============ SAVE / UPDATE ============
    if request.method == 'POST' and action == 'save':
        try:
            data = json.loads(request.body)
            party_id = data.get('id')
            company_name = (data.get('company_name') or '').strip()
            owner_name = (data.get('owner_name') or '').strip()
            number = (data.get('number') or '').strip()
            party_type = (data.get('party_type') or 'All-in-One').strip()
            address = (data.get('address') or '').strip()

            if not company_name:
                return JsonResponse({'success': False, 'message': 'Company name is required'})
            if not party_type or party_type.lower() == 'party':
                party_type = 'All-in-One'

            if party_id:
                # UPDATE (code remains same)
                party = Parties.objects.get(id=party_id)
                party.company_name = company_name
                party.owner_name = owner_name
                party.number = number
                party.party_type = party_type
                party.address = address
                party.save()
                sync_single_party_to_coa(party)
                return JsonResponse({'success': True, 'message': 'Party updated successfully and synced to Level 4 COA', 'code': party.code})
            else:
                # CREATE (auto-generate code)
                new_code = generate_party_code()
                new_party = Parties.objects.create(
                    code=new_code,
                    company_name=company_name,
                    owner_name=owner_name,
                    number=number,
                    party_type=party_type,
                    address=address,
                    entry_date=timezone.now()
                )
                sync_single_party_to_coa(new_party)
                return JsonResponse({
                    'success': True,
                    'message': f'Party saved successfully (Code: {new_code}) and created in Level 4 COA',
                    'code': new_code
                })
        except Parties.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Party not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    # ============ GET NEXT CODE (for preview in form) ============
    if request.method == 'GET' and action == 'next_code':
        return JsonResponse({'success': True, 'code': generate_party_code()})

    # ============ LIST / SEARCH ============
    if request.method == 'GET' and action == 'list':
        search = request.GET.get('search', '').strip()
        qs = Parties.objects.all().order_by('-id')

        if search:
            qs = qs.filter(
                Q(code__icontains=search) |
                Q(company_name__icontains=search) |
                Q(owner_name__icontains=search) |
                Q(number__icontains=search)
            )

        data = []
        for p in qs:
            data.append({
                'id': p.id,
                'code': p.code or '',
                'company_name': p.company_name or '',
                'owner_name': p.owner_name or '',
                'number': p.number or '',
                'party_type': p.party_type or '',
                'address': p.address or '',
                'entry_date': p.entry_date.strftime('%d-%b-%Y %I:%M %p') if p.entry_date else ''
            })
        return JsonResponse({'success': True, 'data': data})

    # ============ GET SINGLE (for View/Edit) ============
    if request.method == 'GET' and action == 'get':
        try:
            party_id = request.GET.get('id')
            p = Parties.objects.get(id=party_id)
            return JsonResponse({
                'success': True,
                'data': {
                    'id': p.id,
                    'code': p.code or '',
                    'company_name': p.company_name or '',
                    'owner_name': p.owner_name or '',
                    'number': p.number or '',
                    'party_type': p.party_type or '',
                    'address': p.address or '',
                }
            })
        except Parties.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Party not found'})

    # ============ DELETE ============
    if request.method == 'POST' and action == 'delete':
        try:
            data = json.loads(request.body)
            party_id = data.get('id')
            Parties.objects.get(id=party_id).delete()
            return JsonResponse({'success': True, 'message': 'Party deleted successfully'})
        except Parties.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Party not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    # ============ RENDER PAGE ============
    return render(request, 'New_Accounts/parties.html')

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
import json
from .models import ExpenseHead


def generate_expense_code():
    """Generate next expense head code like 001, 002, 003..."""
    last = ExpenseHead.objects.exclude(code__isnull=True).exclude(code='').order_by('-id').first()
    if last and last.code:
        try:
            next_num = int(last.code) + 1
        except (ValueError, TypeError):
            next_num = ExpenseHead.objects.count() + 1
    else:
        next_num = 1
    return str(next_num).zfill(3)  # 001, 002, 003...


def expense_head(request):
    # Session check
    if not request.session.get('user_id'):
        if request.method == 'POST' or request.GET.get('action'):
            return JsonResponse({'success': False, 'message': 'Session expired'}, status=401)
        return redirect('login')

    action = request.GET.get('action') or request.POST.get('action')

    # ============ SAVE / UPDATE ============
    if request.method == 'POST' and action == 'save':
        try:
            data = json.loads(request.body)
            head_id = data.get('id')
            name = (data.get('name') or '').strip()

            if not name:
                return JsonResponse({'success': False, 'message': 'Expense head name is required'})

            if head_id:
                head = ExpenseHead.objects.get(id=head_id)
                head.name = name
                head.save()
                return JsonResponse({'success': True, 'message': 'Expense head updated successfully'})
            else:
                new_code = generate_expense_code()
                ExpenseHead.objects.create(
                    code=new_code,
                    name=name,
                    entry_date=timezone.now()
                )
                return JsonResponse({
                    'success': True,
                    'message': f'Expense head saved successfully (Code: {new_code})',
                    'code': new_code
                })
        except ExpenseHead.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Expense head not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    # ============ GET NEXT CODE (for preview) ============
    if request.method == 'GET' and action == 'next_code':
        return JsonResponse({'success': True, 'code': generate_expense_code()})

    # ============ LIST / SEARCH ============
    if request.method == 'GET' and action == 'list':
        search = request.GET.get('search', '').strip()
        qs = ExpenseHead.objects.all().order_by('-id')

        if search:
            qs = qs.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search)
            )

        data = []
        for e in qs:
            data.append({
                'id': e.id,
                'code': e.code or '',
                'name': e.name or '',
                'entry_date': e.entry_date.strftime('%d-%b-%Y %I:%M %p') if e.entry_date else ''
            })
        return JsonResponse({'success': True, 'data': data})

    # ============ GET SINGLE (for View/Edit) ============
    if request.method == 'GET' and action == 'get':
        try:
            head_id = request.GET.get('id')
            e = ExpenseHead.objects.get(id=head_id)
            return JsonResponse({
                'success': True,
                'data': {
                    'id': e.id,
                    'code': e.code or '',
                    'name': e.name or '',
                }
            })
        except ExpenseHead.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Expense head not found'})

    # ============ DELETE ============
    if request.method == 'POST' and action == 'delete':
        try:
            data = json.loads(request.body)
            head_id = data.get('id')
            ExpenseHead.objects.get(id=head_id).delete()
            return JsonResponse({'success': True, 'message': 'Expense head deleted successfully'})
        except ExpenseHead.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Expense head not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    # ============ RENDER PAGE ============
    return render(request, 'New_Accounts/expense_head.html')




