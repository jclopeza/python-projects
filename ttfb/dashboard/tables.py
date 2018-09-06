import django_tables2 as tables
from .models import TTFB


class TTFBTable(tables.Table):
    class Meta:
        model = TTFB
        # add class="paleblue" to <table> tag
        attrs = {'class': 'paleblue'}
