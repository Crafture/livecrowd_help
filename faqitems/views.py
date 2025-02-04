from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from elasticsearch_dsl import Q as elQ
from .models import Event, Venue, FAQItem
from .forms import FAQItemForm
from .helpers import update_query_param
from django.http import JsonResponse
from django.urls import reverse
from faqitems.documents import FAQItemDocument
from django.contrib.auth.decorators import login_required

# Imports for advanced search (PostgreSQL)
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

@login_required
def dashboard_view(request):
    all_events = Event.objects.all().order_by('display_name')
    all_venues = Venue.objects.all().order_by('display_name')

    events_filtered = all_events

    search_query = request.GET.get('q', '').strip()
    if search_query:
        words = search_query.split()
        if request.GET.get('advanced') == 'true':
            search_vector = SearchVector('question', weight='A') + SearchVector('answer', weight='B')
            search_query_obj = None
            for word in words:
                word_query = SearchQuery(word, search_type='plain')
                search_query_obj = word_query if search_query_obj is None else search_query_obj & word_query
            faqitems = (
                FAQItem.objects
                .annotate(rank=SearchRank(search_vector, search_query_obj))
                .filter(rank__gte=0.1)
                .order_by('-rank')
            )
        else:
            q_objects = Q()
            for word in words:
                q_objects &= Q(question__icontains=word)
            faqitems = FAQItem.objects.filter(q_objects)
    else:
        selected_event_id = request.GET.get('event_id')
        selected_venue_id = request.GET.get('venue_id')
        selected_all = request.GET.get('all')

        if selected_all == 'true':
            faqitems = FAQItem.objects.all()
        elif selected_event_id:
            faqitems = FAQItem.objects.filter(event_id=selected_event_id)
        elif selected_venue_id:
            venue = get_object_or_404(Venue, id=selected_venue_id)
            event_ids = venue.event_set.values_list('id', flat=True)
            faqitems = FAQItem.objects.filter(event_id__in=event_ids)
        else:
            faqitems = FAQItem.objects.all()

    initial_faqitems = faqitems[:200]

    edited_faq_id = request.GET.get('edited_id')

    context = {
        'all_events': all_events,
        'all_venues': all_venues,
        'events_filtered': events_filtered,
        'faqitems': initial_faqitems,
        'search_query': search_query,
        'advanced': request.GET.get('advanced') == 'true',
        'edited_faq_id': edited_faq_id,
    }
    return render(request, 'dashboard.html', context)

@login_required
def load_remaining_faqitems(request):
    try:
        offset = int(request.GET.get('offset', 200))
        limit = int(request.GET.get('limit', 200))
    except ValueError:
        offset = 200
        limit = 200

    faqitems = FAQItem.objects.all()[offset: offset + limit]

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

    total_count = FAQItem.objects.count()
    has_more = offset + limit < total_count

    return JsonResponse({'faqitems': data, 'has_more': has_more}, safe=False)

@login_required
def faq_edit_view(request, pk):
    faq_item = get_object_or_404(FAQItem, pk=pk)
    next_url = request.GET.get('next') or request.POST.get('next') or reverse('dashboard')
    
    next_url = update_query_param(next_url, 'edited_id', faq_item.pk)
    
    if request.method == "POST":
        form = FAQItemForm(request.POST, instance=faq_item)
        if form.is_valid():
            form.save()
            return redirect(next_url)
    else:
        form = FAQItemForm(instance=faq_item)

    return render(request, "faq_edit.html", {
        "form": form,
        "faq_item": faq_item,
        "next": next_url,
    })

@login_required
def faq_delete_view(request, pk):
    faq_item = get_object_or_404(FAQItem, pk=pk)
    next_url = request.GET.get('next') or reverse('dashboard')
    
    if request.method == 'POST':
        faq_item.delete()
        return redirect(next_url)
    
    return render(request, 'faq_confirm_delete.html', {
        'faq_item': faq_item,
        'next': next_url,
    })

@login_required
def autocomplete(request):
    query = request.GET.get('q', '')
    suggestions = []
    
    if query:
        words = query.split()
        
        must_clauses = []
        for word in words:
            word_query = elQ(
                "bool", 
                should=[
                    elQ("match_phrase_prefix", question=word),
                    elQ("match", question={"query": word, "fuzziness": "AUTO"})
                ],
                minimum_should_match=1
            )
            must_clauses.append(word_query)
        
        combined_query = elQ("bool", must=must_clauses)
        
        event_id = request.GET.get('event_id')
        if event_id:
            try:
                event_id = int(event_id)
            except ValueError:
                event_id = None
            
            if event_id is not None:
                event_filter = elQ("term", event_id=event_id)
                final_query = elQ("bool", must=[combined_query, event_filter])
            else:
                final_query = combined_query
        else:
            final_query = combined_query

        search = FAQItemDocument.search().query(final_query)

        raw_suggestions = [hit.question for hit in search]
        unique_suggestions = []
        for suggestion in raw_suggestions:
            if suggestion not in unique_suggestions:
                unique_suggestions.append(suggestion)
        suggestions = unique_suggestions

    return JsonResponse(suggestions, safe=False)