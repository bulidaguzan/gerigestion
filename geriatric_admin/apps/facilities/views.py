from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Room
from .forms import RoomForm


@login_required
def room_list(request):
    """Vista para listar todas las habitaciones"""
    # Parámetros de búsqueda y filtrado
    search = request.GET.get('search', '')
    floor_filter = request.GET.get('floor', '')
    status_filter = request.GET.get('status', '')
    
    # Query base
    rooms = Room.objects.all()
    
    # Aplicar filtros
    if search:
        rooms = rooms.filter(
            Q(room_number__icontains=search) |
            Q(description__icontains=search)
        )
    
    if floor_filter:
        rooms = rooms.filter(floor=floor_filter)
    
    if status_filter:
        rooms = rooms.filter(status=status_filter)
    
    # Paginación
    paginator = Paginator(rooms, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_rooms = rooms.count()
    available_rooms = rooms.filter(status='available').count()
    total_beds = sum(room.total_beds for room in rooms)
    occupied_beds = sum(room.occupied_beds for room in rooms)
    available_beds = total_beds - occupied_beds
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'floor_filter': floor_filter,
        'status_filter': status_filter,
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
        'occupancy_rate': round((occupied_beds / total_beds * 100) if total_beds > 0 else 0, 1),
        'status_choices': Room.ROOM_STATUS_CHOICES,
    }
    
    return render(request, 'facilities/rooms/list.html', context)


@login_required
def room_detail(request, room_id):
    """Vista para mostrar detalles de una habitación"""
    room = get_object_or_404(Room, id=room_id)
    
    # Obtener residentes asignados a esta habitación
    residents = room.residents.all()
    
    context = {
        'room': room,
        'residents': residents,
    }
    
    return render(request, 'facilities/rooms/detail.html', context)


@login_required
def room_create(request):
    """Vista para crear una nueva habitación"""
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save()
            messages.success(request, _('Habitación creada exitosamente.'))
            return redirect('facilities_web:room_detail', room_id=room.id)
        else:
            messages.error(request, _('Por favor corrige los errores en el formulario.'))
    else:
        form = RoomForm()
    
    context = {
        'form': form,
        'action': 'create',
    }
    
    return render(request, 'facilities/rooms/form.html', context)


@login_required
def room_update(request, room_id):
    """Vista para actualizar una habitación existente"""
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, _('Habitación actualizada exitosamente.'))
            return redirect('facilities_web:room_detail', room_id=room.id)
        else:
            messages.error(request, _('Por favor corrige los errores en el formulario.'))
    else:
        form = RoomForm(instance=room)
    
    context = {
        'form': form,
        'room': room,
        'action': 'update',
    }
    
    return render(request, 'facilities/rooms/form.html', context)


@login_required
def room_delete(request, room_id):
    """Vista para eliminar una habitación"""
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        room_number = room.room_number
        room.delete()
        messages.success(request, _('Habitación {} eliminada exitosamente.').format(room_number))
        return redirect('facilities_web:room_list')
    
    context = {
        'room': room,
    }
    
    return render(request, 'facilities/rooms/delete.html', context)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def room_update_occupancy(request, room_id):
    """Vista AJAX para actualizar ocupación de camas"""
    try:
        room = get_object_or_404(Room, id=room_id)
        occupied_beds = int(request.POST.get('occupied_beds', 0))
        
        if occupied_beds < 0:
            return JsonResponse({
                'success': False,
                'error': _('El número de camas ocupadas no puede ser negativo.')
            })
        
        if occupied_beds > room.total_beds:
            return JsonResponse({
                'success': False,
                'error': _('El número de camas ocupadas no puede ser mayor al total de camas.')
            })
        
        room.occupied_beds = occupied_beds
        room.save()
        
        return JsonResponse({
            'success': True,
            'available_beds': room.available_beds,
            'occupancy_rate': room.occupancy_rate,
            'is_full': room.is_full,
            'is_available': room.is_available,
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': _('Valor inválido para el número de camas ocupadas.')
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def room_manage_residents(request, room_id):
    """Vista para gestionar residentes de una habitación"""
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        # Lógica para asignar/desasignar residentes
        action = request.POST.get('action')
        resident_id = request.POST.get('resident_id')
        
        if action == 'assign' and resident_id:
            from apps.residents.models import Resident
            try:
                resident = Resident.objects.get(id=resident_id)
                if resident.room is None:
                    resident.room = room
                    resident.save()
                    messages.success(request, _('Residente {} asignado a la habitación {}.').format(
                        resident.full_name, room.room_number
                    ))
                else:
                    messages.warning(request, _('El residente {} ya está asignado a otra habitación.').format(
                        resident.full_name
                    ))
            except Resident.DoesNotExist:
                messages.error(request, _('Residente no encontrado.'))
        
        elif action == 'unassign' and resident_id:
            from apps.residents.models import Resident
            try:
                resident = Resident.objects.get(id=resident_id, room=room)
                resident.room = None
                resident.save()
                messages.success(request, _('Residente {} desasignado de la habitación {}.').format(
                    resident.full_name, room.room_number
                ))
            except Resident.DoesNotExist:
                messages.error(request, _('Residente no encontrado en esta habitación.'))
        
        return redirect('facilities_web:room_manage_residents', room_id=room.id)
    
    # Obtener residentes asignados y disponibles
    from apps.residents.models import Resident
    assigned_residents = room.residents.all()
    available_residents = Resident.objects.filter(room__isnull=True)
    
    context = {
        'room': room,
        'assigned_residents': assigned_residents,
        'available_residents': available_residents,
    }
    
    return render(request, 'facilities/rooms/manage_residents.html', context)


@login_required
def room_dashboard(request):
    """Vista del dashboard de habitaciones con estadísticas"""
    rooms = Room.objects.all()
    
    # Estadísticas generales
    total_rooms = rooms.count()
    available_rooms = rooms.filter(status='available').count()
    maintenance_rooms = rooms.filter(status='maintenance').count()
    quarantine_rooms = rooms.filter(status='quarantine').count()
    
    total_beds = sum(room.total_beds for room in rooms)
    occupied_beds = sum(room.occupied_beds for room in rooms)
    available_beds = total_beds - occupied_beds
    
    # Habitaciones por piso
    floors = rooms.values_list('floor', flat=True).distinct().order_by('floor')
    floor_stats = []
    for floor in floors:
        floor_rooms = rooms.filter(floor=floor)
        floor_total_beds = sum(room.total_beds for room in floor_rooms)
        floor_occupied_beds = sum(room.occupied_beds for room in floor_rooms)
        floor_available_beds = floor_total_beds - floor_occupied_beds
        
        floor_stats.append({
            'floor': floor,
            'total_rooms': floor_rooms.count(),
            'total_beds': floor_total_beds,
            'occupied_beds': floor_occupied_beds,
            'available_beds': floor_available_beds,
            'occupancy_rate': round((floor_occupied_beds / floor_total_beds * 100) if floor_total_beds > 0 else 0, 1),
        })
    
    # Habitaciones con baja disponibilidad
    low_availability_rooms = [
        room for room in rooms.filter(status='available')
        if room.available_beds <= 2
    ]
    low_availability_rooms.sort(key=lambda x: x.available_beds)
    
    context = {
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'maintenance_rooms': maintenance_rooms,
        'quarantine_rooms': quarantine_rooms,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
        'occupancy_rate': round((occupied_beds / total_beds * 100) if total_beds > 0 else 0, 1),
        'floor_stats': floor_stats,
        'low_availability_rooms': low_availability_rooms,
    }
    
    return render(request, 'facilities/rooms/dashboard.html', context) 