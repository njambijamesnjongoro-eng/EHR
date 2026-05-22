import django_filters
from core.models import Patient


class PatientFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(lookup_expr="icontains")
    last_name = django_filters.CharFilter(lookup_expr="icontains")
    gender = django_filters.ChoiceFilter(choices=Patient.Gender.choices)
    blood_group = django_filters.ChoiceFilter(choices=Patient.BloodGroup.choices)
    date_of_birth = django_filters.DateFromToRangeFilter()
    created_at = django_filters.DateFromToRangeFilter()
    search = django_filters.CharFilter(method="search_filter")

    class Meta:
        model = Patient
        fields = [
            "first_name",
            "last_name",
            "gender",
            "blood_group",
            "date_of_birth",
            "created_at",
        ]

    def search_filter(self, queryset, name, value):
        from django.db.models import Q

        return queryset.filter(
            Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
            | Q(health_id__icontains=value)
            | Q(national_id__icontains=value)
            | Q(phone_number__icontains=value)
            | Q(email__icontains=value)
        )
