from django.http import JsonResponse
from django.db.models import Q
from django.db.models.query import QuerySet
from django.views.generic import View

from dashboard.mixins import DateRangeMixin
from core.models import Service

from .mixins import ApiTokenRequiredMixin


class DashboardApiView(ApiTokenRequiredMixin, DateRangeMixin, View):
    def get(self, request, *args, **kwargs):
        services = Service.objects.filter(
            Q(owner=request.user) | Q(collaborators__in=[request.user])
        ).distinct()

        uuid = request.GET.get('uuid')
        if uuid:
            services = services.filter(uuid=uuid)

        basic = request.GET.get('basic', '0').lower() in ('1', 'true')
        start = self.get_start_date()
        end = self.get_end_date()
        services_data = [
            {
                'name': s.name,
                'uuid': s.uuid,
                'link': s.link,
                'stats': s.get_core_stats(start, end, basic),
            }
            for s in services
        ]

        if not basic:
            services_data = self._convert_querysets_to_lists(services_data)

        return JsonResponse(data={'services': services_data})

    def _convert_querysets_to_lists(self, services_data):
        for service_data in services_data:
            for key, value in service_data['stats'].items():
                if isinstance(value, QuerySet):
                    service_data['stats'][key] = list(value)
            for key, value in service_data['stats']['compare'].items():
                if isinstance(value, QuerySet):
                    service_data['stats']['compare'][key] = list(value)

        return service_data
