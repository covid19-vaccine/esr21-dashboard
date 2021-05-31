from django.core.exceptions import ObjectDoesNotExist

from edc_base.view_mixins import EdcBaseViewMixin

from edc_dashboard.views import DashboardView as BaseDashboardView
from edc_navbar import NavbarViewMixin
from edc_subject_dashboard.view_mixins import SubjectDashboardViewMixin
from edc_subject_dashboard import AppointmentModelWrapper

from .dashboard_view_mixin import DashboardViewMixin
from ....model_wrappers import InformedConsentModelWrapper



class DashboardView(DashboardViewMixin, EdcBaseViewMixin, SubjectDashboardViewMixin,
                    NavbarViewMixin, BaseDashboardView):

    dashboard_url = 'subject_dashboard_url'
    dashboard_template = 'subject_dashboard_template'
    appointment_model = 'edc_appointment.appointment'
    appointment_model_wrapper_cls = AppointmentModelWrapper
    consent_model = 'esr21_subject.subjectconsent'
    consent_model_wrapper_cls = InformedConsentModelWrapper
    navbar_name = 'esr21_dashboard'
    navbar_selected_item = 'consented_subject'
    subject_locator_model = 'esr21_subject.subjectlocator'

    @property
    def appointments(self):
        """Returns a Queryset of all appointments for this subject.
        """
        if not self._appointments:
            self._appointments = self.appointment_model_cls.objects.filter(
                subject_identifier=self.subject_identifier).order_by(
                    'visit_code')
        return self._appointments

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        locator_obj = self.get_locator_info()
        context.update(
            locator_obj=locator_obj,
            schedule_names=[model.schedule_name for model in self.onschedule_models],
            cohorts=self.get_cohorts,
            subject_consent=self.consent_wrapped,
            hiv_status=self.hiv_status,)
        return context

    def get_locator_info(self):

        subject_identifier = self.kwargs.get('subject_identifier')
        try:
            obj = self.subject_locator_model_cls.objects.get(
                subject_identifier=subject_identifier)
        except ObjectDoesNotExist:
            return None
        return obj