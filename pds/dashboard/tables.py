import django_tables2 as tables
from django_tables2.utils import A
from dashboard import models


class ApplicationTable(tables.Table):
    name = tables.LinkColumn('application-details', args=[A('pk')])

    class Meta:
        model = models.Application
        fields = ['name']
        attrs = {'class': 'table table-hover table-striped'}
