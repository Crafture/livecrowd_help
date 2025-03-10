from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry
from .models import FAQItem

faq_index = Index('faqitems')  # This defines the index name

faq_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)

@registry.register_document
class FAQItemDocument(Document):
    
    event_id = fields.IntegerField(attr="event.pk")
    
    # Override the question field to add a keyword sub-field
    question = fields.TextField(
        attr='question',
        fields={
            'keyword': fields.KeywordField()
        }
    )

    class Index:
        name = 'faqitems'
        settings = {'number_of_shards': 1, 'number_of_replicas': 0}

    class Django:
        model = FAQItem
        # Remove 'question' from here since we're defining it above
        fields = [
            'answer',
        ]