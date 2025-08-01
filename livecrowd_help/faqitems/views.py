from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse

from .forms import FAQBulkUploadForm
from .forms import FAQItemForm
from .forms import FAQSearchForm
from .forms import TagBulkUploadForm
from .models import Event
from .models import FAQItem
from .models import Tag
from .models import Venue
from .search_helpers import build_autocomplete_query
from .search_helpers import build_dashboard_queryset
from .utils import CSVValidationError
from .utils import bulk_create_faqs
from .utils import create_tags_bulk
from .utils import parse_csv
from .utils import resolve_relations
from .utils import validate_rows
from .utils import validate_tag_rows


@login_required
def dashboard_view(request):
    form = FAQSearchForm(request.GET)
    params = form.cleaned_data if form.is_valid() else {}
    q = params.get("q", "").strip()
    advanced = params.get("advanced", False)
    event_id = params.get("event_id") or request.GET.get("event_id") or ""
    venue_id = params.get("venue_id")
    all_items = params.get("all", False)
    archived = request.GET.get("archived", "false").lower() == "true"
    edited_id = request.GET.get("edited_id", "")

    # NEW: pull a list of tagslugs from the querystring
    tag_ids = request.GET.getlist("tags")  # e.g. ?tags=rock&tags=pop

    # 1) base qs
    if q:
        qs = build_dashboard_queryset(q, advanced, event_id, venue_id, all_items)
    elif event_id:
        qs = FAQItem.objects.filter(event_id=event_id)
    else:
        qs = FAQItem.objects.all()

    # 2) filtering
    qs = qs.order_by("-updated_at")
    if archived:
        qs = qs.filter(archived=True)
    elif not advanced:
        qs = qs.filter(archived=False)

    # NEW: tags filter
    if tag_ids:
        qs = qs.filter(tags__id__in=tag_ids).distinct()

    # 3) limit when no search & no event
    if not q and not event_id:
        qs = qs[:200]

    # sidebar data
    all_events = Event.objects.all().order_by("name")
    favorite_events = all_events.filter(favorite=True)
    all_venues = Venue.objects.all().order_by("name")
    all_tags = Tag.objects.all().order_by("name")

    return render(
        request,
        "faqitems/dashboard.html",
        {
            "search_form": form,
            "faqitems": qs,
            "search_query": q,
            "advanced": advanced,
            "edited_faq_id": edited_id,
            "selected_event_id": event_id,
            "all_events": all_events,
            "favorite_events": favorite_events,
            "all_venues": all_venues,
            "all_tags": all_tags,
            "selected_tags": tag_ids,
        },
    )


@login_required
def autocomplete(request):
    search_query = request.GET.get("q", "")
    event_id = request.GET.get("event_id")
    advanced = request.GET.get("advanced", "false").lower() == "true"
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
        offset = int(request.GET.get("offset", 200))
        limit = int(request.GET.get("limit", 200))
    except ValueError:
        offset = 200
        limit = 200

    advanced = request.GET.get("advanced", "false").lower() == "true"

    faqitems_qs = FAQItem.objects.all() if advanced else FAQItem.objects.filter(archived=False)

    faqitems = faqitems_qs[offset : offset + limit]
    data = [
        {
            "id": faq.id,
            "question": faq.question,
            "answer": faq.answer,
            "event_name": faq.event.name,
            "event_id": faq.event.id,
        }
        for faq in faqitems
    ]

    total_count = faqitems_qs.count()
    has_more = offset + limit < total_count

    return JsonResponse({"faqitems": data, "has_more": has_more}, safe=False)


@login_required
def faq_delete_view(request, pk):
    faq_item = get_object_or_404(FAQItem, pk=pk)
    next_url = request.GET.get("next") or reverse("dashboard")

    if request.method == "POST":
        faq_item.delete()
        return redirect(next_url)

    return render(
        request,
        "faqitems/faq_confirm_delete.html",
        {
            "faq_item": faq_item,
            "next": next_url,
        },
    )


@login_required
def faq_edit_or_create_view(request, pk=None):
    faq_item = get_object_or_404(FAQItem, pk=pk) if pk else None

    next_url = request.GET.get("next") or request.POST.get("next") or reverse("dashboard")
    if request.method == "POST":
        form = FAQItemForm(request.POST, instance=faq_item)
        if form.is_valid():
            faq = form.save(commit=False)
            if faq_item is None:
                faq.user_created = request.user
            faq.user_last_modified = request.user
            faq.save()
            form.save_m2m()
            return redirect(next_url)
    else:
        form = FAQItemForm(instance=faq_item)

    return render(
        request,
        "faqitems/faq_edit_or_create.html",
        {
            "form": form,
            "faq_item": faq_item,
            "next": next_url,
        },
    )


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


@login_required
def faq_bulk_upload_view(request):
    if request.method == "POST":
        form = FAQBulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data["csv_file"]

            # 1) Parse CSV
            expected = ["question", "answer", "event", "tags"]
            try:
                _, raw_rows = parse_csv(csv_file, expected)
            except CSVValidationError as e:
                form.add_error("csv_file", str(e))
            else:
                # 2) Validate rows
                valid_rows, val_errors = validate_rows(raw_rows)

                # 3) Resolve foreign-keys
                resolved, rel_errors = resolve_relations(valid_rows)

                # 4) Aggregate errors
                all_errors = val_errors + rel_errors
                if all_errors:
                    for err in all_errors:
                        form.add_error("csv_file", err)
                else:
                    # 5) Bulk create
                    count = bulk_create_faqs(resolved, request.user)
                    messages.success(request, f"Successfully imported {count} FAQs.")
                    return redirect(reverse("dashboard"))
    else:
        form = FAQBulkUploadForm()

    return render(request, "faqitems/bulk_upload.html", {"form": form})


@login_required
def tag_bulk_upload_view(request):
    form = TagBulkUploadForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        csv_file = form.cleaned_data["csv_file"]

        # 1) Parse & header-check
        try:
            _, raw_rows = parse_csv(csv_file, expected=["tag"])
        except CSVValidationError as e:
            form.add_error("csv_file", str(e))
        else:
            # 2) Validate rows
            valid_names, errors = validate_tag_rows(raw_rows)

            if errors:
                for err in errors:
                    form.add_error("csv_file", err)
            else:
                # 3) Create tags atomically
                created_count = create_tags_bulk(valid_names)
                messages.success(
                    request,
                    f"Bulk upload complete — created {created_count} new tag"
                    + ("s" if created_count != 1 else "")
                    + ".",
                )
                return redirect(reverse("dashboard"))

    return render(request, "faqitems/bulk_upload_tags.html", {"form": form})
