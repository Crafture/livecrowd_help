from django.shortcuts import render, get_object_or_404, redirect
from .models import Event, Venue, FAQItem
from .forms import FAQItemForm, FAQSearchForm
from .helpers import update_query_param
from django.http import JsonResponse
from django.urls import reverse
import re
from django.contrib.auth.decorators import login_required

from .search_helpers import build_dashboard_queryset, build_autocomplete_query


@login_required
def dashboard_view(request):
    search_form = FAQSearchForm(request.GET)
    event_id = request.GET.get('event_id')
    archived_param = request.GET.get('archived', 'false').lower() == 'true'
    
    if search_form.is_valid():
        data = search_form.cleaned_data
        search_query = data.get('q', '').strip()
        advanced = data.get('advanced')
        event_id = data.get('event_id') or event_id
        venue_id = data.get('venue_id')
        all_param = data.get('all')
    else:
        search_query = ''
        advanced = False
        venue_id = None
        all_param = False

    all_events = Event.objects.all().order_by('display_name')
    favorite_events = Event.objects.filter(favorite=True).order_by('display_name')
    all_venues = Venue.objects.all().order_by('display_name')

    if search_query:
        faqitems_qs = build_dashboard_queryset(search_query, advanced, event_id, venue_id, all_param)
        if archived_param:
            faqitems_qs = faqitems_qs.filter(archived=True)
        elif not advanced:
            faqitems_qs = faqitems_qs.filter(archived=False)
    elif event_id:
        faqitems_qs = FAQItem.objects.filter(event__id=event_id)
        if archived_param:
            faqitems_qs = faqitems_qs.filter(archived=True)
        elif not advanced:
            faqitems_qs = faqitems_qs.filter(archived=False)
    else:
        if archived_param:
            faqitems_qs = FAQItem.objects.filter(archived=True)[:200]
        else:
            faqitems_qs = FAQItem.objects.filter(archived=False)[:200] if not advanced else FAQItem.objects.all()[:200]

    edited_faq_id = request.GET.get('edited_id')
    selected_event_id = event_id or ''

    context = {
        'all_events': all_events,
        'favorite_events': favorite_events,
        'all_venues': all_venues,
        'faqitems': faqitems_qs,
        'search_query': search_query,
        'advanced': advanced,
        'edited_faq_id': edited_faq_id,
        'search_form': search_form,
        'selected_event_id': selected_event_id,
    }
    return render(request, 'faqitems/dashboard.html', context)

@login_required
def autocomplete(request):
    search_query = request.GET.get('q', '')
    event_id = request.GET.get('event_id')
    advanced = request.GET.get('advanced', 'false').lower() == 'true'
    suggestions = []

    if search_query:
        s = build_autocomplete_query(search_query, event_id)
        if not advanced:
            s = s.filter(archived=False)
        raw_suggestions = [hit.question for hit in s]
        suggestions = list(dict.fromkeys(raw_suggestions))

    return JsonResponse(suggestions, safe=False)

@login_required
def load_remaining_faqitems(request):
    try:
        offset = int(request.GET.get('offset', 200))
        limit = int(request.GET.get('limit', 200))
    except ValueError:
        offset = 200
        limit = 200

    advanced = request.GET.get('advanced', 'false').lower() == 'true'
    
    faqitems_qs = FAQItem.objects.all() if advanced else FAQItem.objects.filter(archived=False)
    
    faqitems = faqitems_qs[offset: offset + limit]
    data = [
        {
            'id': faq.id,
            'question': faq.question,
            'answer': faq.answer,
            'event_display_name': faq.event.display_name,
            'event_id': faq.event.id
        }
        for faq in faqitems
    ]

    total_count = faqitems_qs.count()
    has_more = offset + limit < total_count

    return JsonResponse({'faqitems': data, 'has_more': has_more}, safe=False)

@login_required
def faq_delete_view(request, pk):
    faq_item = get_object_or_404(FAQItem, pk=pk)
    next_url = request.GET.get('next') or reverse('dashboard')
    
    if request.method == 'POST':
        faq_item.delete()
        return redirect(next_url)
    
    return render(request, 'faqitems/faq_confirm_delete.html', {
        'faq_item': faq_item,
        'next': next_url,
    })

@login_required
def faq_edit_or_create_view(request, pk=None):
    faq_item = None
    
    if pk:
        faq_item = get_object_or_404(FAQItem, pk=pk)
    
    next_url = request.GET.get('next') or request.POST.get('next') or reverse('dashboard')
    
    if request.method == "POST":
        if faq_item:
            form = FAQItemForm(request.POST, instance=faq_item)
        else:
            form = FAQItemForm(request.POST)
        
        if form.is_valid():
            faq = form.save(commit=False)
            if not faq.pk:
                faq.user_created = request.user
            faq.user_last_modified = request.user
            faq.save()
            return redirect(next_url)
    else:
        if faq_item:
            form = FAQItemForm(instance=faq_item)
        else:
            form = FAQItemForm()

    return render(request, "faqitems/faq_edit_or_create.html", {
        "form": form,
        "faq_item": faq_item,
        "next": next_url,
    })

@login_required
def toggle_archive_faq_item(request, pk=None):

    faq_item = None

    if request.method == "POST":
        if pk:
            faq_item = get_object_or_404(FAQItem, pk=pk)

        if faq_item:
            faq_item.archived = not faq_item.archived
            faq_item.save()
            return JsonResponse({"archived": faq_item.archived})
        
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def toggle_favorite_event(request, event_id=None):

    event = None

    if request.method == "POST":
        if event_id:
            event = get_object_or_404(Event, id=event_id)

        if event:
            event.favorite = not event.favorite
            event.save()
            return JsonResponse({"favorite": event.favorite})
        
    return JsonResponse({"error": "Invalid request"}, status=400)
