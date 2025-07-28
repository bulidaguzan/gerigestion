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
    male_count = residents.filter(gender='M').count()
    female_count = residents.filter(gender='F').count()
    
    # Residentes activos (todos los residentes están activos por defecto)
    active_residents = total_residents
    
    # Residentes en tratamiento (aquellos con alergias o condiciones médicas)
    in_treatment = residents.filter(
        Q(allergies__isnull=False) & ~Q(allergies='') |
        Q(medical_conditions__isnull=False) & ~Q(medical_conditions='')
    ).count()
    
    # Altas recientes (residentes admitidos en los últimos 30 días)
    recent_discharges = residents.filter(
        admission_date__gte=date.today() - timedelta(days=30)
    ).count()
    
    # Promedio de edad
    if total_residents > 0:
        # Calcular edad para cada residente
        total_age = 0
        for resident in residents:
            total_age += resident.age
        avg_age = round(total_age / total_residents, 1)
    else:
        avg_age = 0
    
    # Tasa de ocupación (residentes con habitación asignada)
    residents_with_room = residents.filter(room__isnull=False).count()
    if total_residents > 0:
        occupancy_rate = round((residents_with_room / total_residents) * 100, 1)
    else:
        occupancy_rate = 0
    
    # Residentes recientes (últimos 5 residentes)
    recent_residents = residents.order_by('-admission_date')[:5]
    
    # Estadísticas de salud (simuladas basadas en edad)
    # Calcular edad basada en date_of_birth
    today = date.today()
    
    # Residentes menores de 70 años
    excellent_health = residents.filter(
        date_of_birth__year__gt=today.year - 70
    ).count()
    
    # Residentes entre 70 y 79 años
    good_health = residents.filter(
        date_of_birth__year__lte=today.year - 70,
        date_of_birth__year__gt=today.year - 80
    ).count()
    
    # Residentes entre 80 y 89 años
    fair_health = residents.filter(
        date_of_birth__year__lte=today.year - 80,
        date_of_birth__year__gt=today.year - 90
    ).count()
    
    # Residentes de 90 años o más
    poor_health = residents.filter(
        date_of_birth__year__lte=today.year - 90
    ).count()
    
    context = {
        'total_residents': total_residents,
        'active_residents': active_residents,
        'in_treatment': in_treatment,
        'recent_discharges': recent_discharges,
        'avg_age': avg_age,
        'female_count': female_count,
        'male_count': male_count,
        'occupancy_rate': occupancy_rate,
        'recent_residents': recent_residents,
        'excellent_health': excellent_health,
        'good_health': good_health,
        'fair_health': fair_health,
        'poor_health': poor_health,
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