from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from datetime import date, timedelta
from .models import Resident
from .forms import ResidentForm


@login_required
def resident_list(request):
    """Vista para listar todos los residentes"""
    # Parámetros de búsqueda y filtrado
    search = request.GET.get('search', '')
    gender_filter = request.GET.get('gender', '')
    marital_status_filter = request.GET.get('marital_status', '')
    
    # Query base
    residents = Resident.objects.all()
    
    # Aplicar filtros
    if search:
        residents = residents.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )
    
    if gender_filter:
        residents = residents.filter(gender=gender_filter)
    
    if marital_status_filter:
        residents = residents.filter(marital_status=marital_status_filter)
    
    # Paginación
    paginator = Paginator(residents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_residents = residents.count()
    male_residents = residents.filter(gender='M').count()
    female_residents = residents.filter(gender='F').count()
    other_residents = residents.filter(gender='O').count()
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'gender_filter': gender_filter,
        'marital_status_filter': marital_status_filter,
        'total_residents': total_residents,
        'male_residents': male_residents,
        'female_residents': female_residents,
        'other_residents': other_residents,
        'gender_choices': Resident.GENDER_CHOICES,
        'marital_status_choices': Resident.MARITAL_STATUS_CHOICES,
    }
    
    return render(request, 'residents/list.html', context)


@login_required
def resident_detail(request, resident_id):
    """Vista para mostrar detalles de un residente"""
    resident = get_object_or_404(Resident, id=resident_id)
    
    context = {
        'resident': resident,
    }
    
    return render(request, 'residents/detail.html', context)


@login_required
def resident_create(request):
    """Vista para crear un nuevo residente"""
    if request.method == 'POST':
        form = ResidentForm(request.POST)
        if form.is_valid():
            resident = form.save()
            messages.success(request, _('Residente creado exitosamente.'))
            return redirect('residents_web:resident_detail', resident_id=resident.id)
        else:
            messages.error(request, _('Por favor corrige los errores en el formulario.'))
    else:
        form = ResidentForm()
    
    context = {
        'form': form,
        'action': 'create',
    }
    
    return render(request, 'residents/form.html', context)


@login_required
def resident_update(request, resident_id):
    """Vista para actualizar un residente existente"""
    resident = get_object_or_404(Resident, id=resident_id)
    
    if request.method == 'POST':
        form = ResidentForm(request.POST, instance=resident)
        if form.is_valid():
            form.save()
            messages.success(request, _('Residente actualizado exitosamente.'))
            return redirect('residents_web:resident_detail', resident_id=resident.id)
        else:
            messages.error(request, _('Por favor corrige los errores en el formulario.'))
    else:
        form = ResidentForm(instance=resident)
    
    context = {
        'form': form,
        'resident': resident,
        'action': 'update',
    }
    
    return render(request, 'residents/form.html', context)


@login_required
def resident_delete(request, resident_id):
    """Vista para eliminar un residente"""
    resident = get_object_or_404(Resident, id=resident_id)
    
    if request.method == 'POST':
        full_name = resident.full_name
        resident.delete()
        messages.success(request, _('Residente {} eliminado exitosamente.').format(full_name))
        return redirect('residents_web:resident_list')
    
    context = {
        'resident': resident,
    }
    
    return render(request, 'residents/delete.html', context)


@login_required
def resident_dashboard(request):
    """Vista del dashboard de residentes con estadísticas"""
    residents = Resident.objects.all()
    
    # Estadísticas generales
    total_residents = residents.count()
    male_residents = residents.filter(gender='M').count()
    female_residents = residents.filter(gender='F').count()
    other_residents = residents.filter(gender='O').count()
    
    # Estadísticas por edad
    young_residents = residents.filter(date_of_birth__year__gte=date.today().year - 65).count()
    elderly_residents = residents.filter(
        date_of_birth__year__lt=date.today().year - 65,
        date_of_birth__year__gte=date.today().year - 80
    ).count()
    very_elderly_residents = residents.filter(date_of_birth__year__lt=date.today().year - 80).count()
    
    # Estadísticas por estado civil
    single_residents = residents.filter(marital_status='single').count()
    married_residents = residents.filter(marital_status='married').count()
    widowed_residents = residents.filter(marital_status='widowed').count()
    divorced_residents = residents.filter(marital_status='divorced').count()
    
    # Residentes por tiempo de estancia
    recent_admissions = residents.filter(
        admission_date__gte=date.today() - timedelta(days=30)
    ).count()
    long_term_residents = residents.filter(
        admission_date__lt=date.today() - timedelta(days=365)
    ).count()
    
    # Residentes sin habitación asignada
    unassigned_residents = residents.filter(room__isnull=True).count()
    
    context = {
        'total_residents': total_residents,
        'male_residents': male_residents,
        'female_residents': female_residents,
        'other_residents': other_residents,
        'young_residents': young_residents,
        'elderly_residents': elderly_residents,
        'very_elderly_residents': very_elderly_residents,
        'single_residents': single_residents,
        'married_residents': married_residents,
        'widowed_residents': widowed_residents,
        'divorced_residents': divorced_residents,
        'recent_admissions': recent_admissions,
        'long_term_residents': long_term_residents,
        'unassigned_residents': unassigned_residents,
    }
    
    return render(request, 'residents/dashboard.html', context)


@login_required
def resident_search(request):
    """Vista AJAX para búsqueda rápida de residentes"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    residents = Resident.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(phone__icontains=query)
    )[:10]
    
    results = []
    for resident in residents:
        results.append({
            'id': resident.id,
            'name': resident.full_name,
            'age': resident.age,
            'room': resident.room.room_number if resident.room else _('Sin asignar'),
            'phone': resident.phone or _('No disponible'),
        })
    
    return JsonResponse({'results': results}) 