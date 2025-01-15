from django import template
from django.core.serializers.json import DjangoJSONEncoder
import json

register = template.Library()

@register.filter(is_safe=True)
def jsonify(obj):
    return json.dumps(obj, cls=DjangoJSONEncoder)
