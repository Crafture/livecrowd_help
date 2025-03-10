import re
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .models import FAQItem, Venue
from elasticsearch_dsl.query import Q as elQ
from .documents import FAQItemDocument
import logging

logger = logging.getLogger(__name__)

def extract_quoted_term(query):
    """
    If the entire query is enclosed in quotes, return the inner text and True;
    otherwise return the original query and False.
    """
    pattern = r'^(["\'])(.*?)\1$'
    match = re.match(pattern, query.strip())
    if match:
        return match.group(2).strip(), True
    return query, False

def build_dashboard_queryset(search_query, advanced, event_id, venue_id, all_param):
    """
    Build and return a Django ORM queryset for FAQItem based on the search parameters.
    
    When the query is fully quoted, it treats the quoted word as a standalone token.
    The token must be preceded and followed by either:
      a. The start or end of the string, or 
      b. A whitespace, or 
      c. Any character that is not alphanumeric and not a dash.
    
    If the query is not fully quoted, it falls back to the usual word-splitting logic.
    """
    clean_query, is_exact = extract_quoted_term(search_query)
    clean_query = clean_query.strip()
    
    if clean_query:
        if is_exact:
            pattern = r'(?<![\w-])' + re.escape(clean_query) + r'(?![\w-])'
            qs = FAQItem.objects.filter(question__iregex=pattern)
        else:
            words = clean_query.split()
            if advanced:
                search_vector = SearchVector('question', weight='A') + SearchVector('answer', weight='B')
                search_query_obj = None
                for word in words:
                    word_query = SearchQuery(word, search_type='plain')
                    search_query_obj = word_query if search_query_obj is None else search_query_obj & word_query
                qs = (FAQItem.objects
                      .annotate(rank=SearchRank(search_vector, search_query_obj))
                      .filter(rank__gte=0.1)
                      .order_by('-rank'))
            else:
                q_objects = Q()
                for word in words:
                    q_objects &= Q(question__icontains=word)
                qs = FAQItem.objects.filter(q_objects)
        if event_id:
            qs = qs.filter(event_id=event_id)
        return qs
    else:
        if all_param:
            return FAQItem.objects.all()
        elif event_id:
            return FAQItem.objects.filter(event_id=event_id)
        elif venue_id:
            venue = get_object_or_404(Venue, id=venue_id)
            event_ids = venue.event_set.values_list('id', flat=True)
            return FAQItem.objects.filter(event_id__in=event_ids)
        else:
            return FAQItem.objects.all()

def build_autocomplete_query(search_query, event_id):
    """
    Build and return an Elasticsearch query for FAQItem autocomplete.
    If the query contains quoted text, use a match query with operator 'and'
    so that every word in the quoted text is required.
    Otherwise, build a bool query with match_phrase_prefix and fuzzy matching.
    """
    pattern = r'["\'](.*?)["\']'
    match = re.search(pattern, search_query)
    if match:
        quoted_term = match.group(1).strip("'\"")
        s = FAQItemDocument.search().query(
            "match", 
            question={"query": quoted_term, "operator": "and"}
        )
    else:
        words = search_query.split()
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
        if event_id:
            try:
                event_id = int(event_id)
                event_filter = elQ("term", event_id=event_id)
                final_query = elQ("bool", must=[combined_query, event_filter])
            except ValueError:
                final_query = combined_query
        else:
            final_query = combined_query
        s = FAQItemDocument.search().query(final_query)
    return s