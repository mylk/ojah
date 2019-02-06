from django.contrib import admin
from django.db.models import Count


class CorpusMetricAdmin(admin.ModelAdmin):
    change_list_template = 'admin/corpus_metric_list.html'
    date_hierarchy = 'added_at'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(
            request,
            extra_context=extra_context,
        )

        try:
            query_set = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        metrics = {
            'total': Count('id')
        }

        response.context_data['corpus_metrics'] = list(
            query_set
                .values('positive')
                .annotate(**metrics)
                .order_by('-total')
        )

        response.context_data['corpus_metrics_total'] = dict(
            query_set.aggregate(**metrics)
        )

        return response
