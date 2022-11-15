
from django.core.exceptions import ObjectDoesNotExist

from edc_base.view_mixins import EdcBaseViewMixin

from edc_constants.constants import YES
from edc_dashboard.views import DashboardView as BaseDashboardView
from edc_navbar import NavbarViewMixin
from edc_subject_dashboard.view_mixins import SubjectDashboardViewMixin
from edc_visit_schedule.site_visit_schedules import site_visit_schedules
from esr21_subject.helper_classes import EnrollmentHelper

from .dashboard_view_mixin import DashboardViewMixin
from ....model_wrappers import InformedConsentModelWrapper
from ....model_wrappers import AppointmentModelWrapper, ContactInformationModelWrapper, SubjectOffStudyModelWrapper

from django.shortcuts import redirect
from django.apps import apps as django_apps
from edc_base.utils import get_utcnow
from django.contrib import messages
from django.contrib.messages import get_messages



class DashboardView(DashboardViewMixin, EdcBaseViewMixin, SubjectDashboardViewMixin,
                    NavbarViewMixin, BaseDashboardView):
    dashboard_url = 'subject_dashboard_url'
    dashboard_template = 'subject_dashboard_template'
    appointment_model = 'edc_appointment.appointment'
    appointment_model_wrapper_cls = AppointmentModelWrapper
    consent_model = 'esr21_subject.informedconsent'
    consent_model_wrapper_cls = InformedConsentModelWrapper
    subject_locator_model = 'esr21_subject.personalcontactinfo'
    subject_locator_model_wrapper_cls = ContactInformationModelWrapper
    special_forms_include_value = "esr21_dashboard/subject/dashboard/special_forms.html"
    navbar_name = 'esr21_dashboard'
    navbar_selected_item = 'consented_subject'
    onschedule_model = 'esr21_subject.onschedule'
    schedule_enrollment = EnrollmentHelper
    vaccination_details_model = 'esr21_subject.vaccinationdetails'

    @property
    def vaccination_details_cls(self):
        return django_apps.get_model(self.vaccination_details_model)

    @property
    def consent_model_cls(self):
        return django_apps.get_model(self.consent_model)

    @property
    def vaccination_history_cls(self):
        return django_apps.get_model('esr21_subject.vaccinationhistory')

    @property
    def onschedule_model_cls(self):
        return django_apps.get_model(self.onschedule_model)

    @property
    def subject_offstudy_wrapper(self):
        """
        - Used to create an instance of the subject offstudy if the offstudy form is filled,
        then pass the instance to the context so can be used in the special forms.
        - If not filled, a none object will returned so that the button cannot be rendered by the template
        """

        # getting the class for offstudy
        subject_offstudy_cls = django_apps.get_model('esr21_prn.subjectoffstudy')

        try:
            # get offstudy instance
            subject_offstudy_obj = subject_offstudy_cls.objects.get(subject_identifier=self.subject_identifier)
        except subject_offstudy_cls.DoesNotExist:
            # If the offstudy does not exist
            return None
        else:
            # create instance of the wrapper
            subject_offstudy_wrapper = SubjectOffStudyModelWrapper(model_obj=subject_offstudy_obj)

            reason = subject_offstudy_wrapper.object.get_reason_display()
            messages.add_message(self.request, messages.ERROR,
                                 f'Subject is off study due to {reason}')
            
            return subject_offstudy_wrapper

    @property
    def appointments(self):
        """Returns a Queryset of all appointments for this subject.
        """
        if not self._appointments:
            self._appointments = self.appointment_model_cls.objects.filter(
                subject_identifier=self.subject_identifier).order_by(
                'visit_code')
        return self._appointments

    def get_onschedule_model_obj(self, schedule):
        try:
            return schedule.onschedule_model_cls.objects.get(
                subject_identifier=self.subject_identifier,
                schedule_name=schedule.name)
        except ObjectDoesNotExist:
            return None

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        locator_obj = self.get_locator_info()
        edc_readonly = None
        
        if self.request.GET.get('edc_readonly'):
            edc_readonly = self.request.GET.get('edc_readonly') == '1'
            
        if edc_readonly:
            storage = get_messages(self.request)
            storage.used = True    

        if 'main_schedule_enrollment' in self.request.path:
            self.enrol_subject(cohort='esr21')

        if 'sub_cohort_enrollment' in self.request.path:
            if not self.is_subcohort_full():
                self.enrol_subject(cohort='esr21_sub')
            else:
                messages.add_message(self.request, messages.ERROR,
                                     'The sub cohort is full.')

        if 'booster_enrollment' in self.request.path:
            self.booster_enrollment()
        context.update(
            locator_obj=locator_obj,
            subject_consent=self.consent_wrapped,
            schedule_names=[model.schedule_name for model in self.onschedule_models],
            is_subcohort_full=self.is_subcohort_full(),
            has_schedules=self.has_schedules(),
            subject_offstudy=self.subject_offstudy_wrapper,
            booster_due=self.booster_due,
            show_schedule_buttons=self.show_schedule_buttons,
            wrapped_consent_v3=self.wrapped_consent_v3,
            reconsented=self.reconsented,
            valid_doses=self.check_dose_quantity,
            edc_readonly=edc_readonly,
        )

        return context

    def enrol_subject(self, cohort=None):
        schedule_enrollment = self.schedule_enrollment(
            cohort=cohort, subject_identifier=self.subject_identifier)
        schedule_enrollment.schedule_enrol()

    @property
    def booster_due(self):
        schedules = ['esr21_enrol_schedule', 'esr21_sub_enrol_schedule']
        schedule_names = [model.schedule_name for model in self.onschedule_models]

        if ('esr21_boost_schedule' not in schedule_names and
                'esr21_sub_boost_schedule' not in schedule_names):
            try:
                first_dose = self.vaccination_details_cls.objects.get(
                    subject_visit__subject_identifier=self.kwargs.get('subject_identifier'),
                    subject_visit__schedule_name__in=schedules,
                    received_dose=YES,
                    received_dose_before='first_dose')
            except self.vaccination_details_cls.DoesNotExist:
                return None
            else:
                return (get_utcnow() - first_dose.vaccination_date).days >= 156

    def booster_enrollment(self):
        schedule_names = [model.schedule_name for model in self.onschedule_models]
        cohort = None
        if 'esr21_sub_enrol_schedule' in schedule_names:
            cohort = 'esr21_sub'
            if not self.is_subcohort_full():
                self.enrol_booster(cohort=cohort)
            else:
                messages.add_message(self.request, messages.ERROR,
                                     'The sub cohort is full.')
        else:
            cohort = 'esr21'
            self.enrol_booster(cohort=cohort)

    def enrol_booster(self, cohort=None):
        onschedule_model = 'esr21_subject.onschedule'

        onschedule_dt = get_utcnow()
        try:
            history = self.vaccination_history_cls.objects.get(
                subject_identifier=self.kwargs.get('subject_identifier'))
        except self.vaccination_history_cls.DoesNotExist:
            messages.add_message(self.request, messages.ERROR,
                                 'Missing vaccination history form.')
        else:
            if history.received_vaccine == YES and history.dose_quantity == '2':
                self.put_on_schedule(
                    f'{cohort}_boost_schedule',
                    onschedule_model=onschedule_model,
                    onschedule_datetime=onschedule_dt.replace(second=0, microsecond=0))

    def put_on_schedule(self, schedule_name, onschedule_model,
                        onschedule_datetime=None):
        _, schedule = site_visit_schedules.get_by_onschedule_model_schedule_name(
            onschedule_model=onschedule_model, name=schedule_name)
        schedule.put_on_schedule(
            subject_identifier=self.subject_identifier,
            onschedule_datetime=onschedule_datetime,
            schedule_name=schedule_name)

    def get_locator_info(self):

        subject_identifier = self.kwargs.get('subject_identifier')
        try:
            obj = self.subject_locator_model_cls.objects.get(
                subject_identifier=subject_identifier)
        except ObjectDoesNotExist:
            return None
        return obj

    def set_current_schedule(self, onschedule_model_obj=None,
                             schedule=None, visit_schedule=None,
                             is_onschedule=True):
        if onschedule_model_obj:
            if is_onschedule:
                self.current_schedule = schedule
                self.current_visit_schedule = visit_schedule
                self.current_onschedule_model = onschedule_model_obj
            self.onschedule_models.append(onschedule_model_obj)
            self.visit_schedules.update(
                {visit_schedule.name: visit_schedule})

    def is_subcohort_full(self):
        onschedule_subcohort = self.onschedule_model_cls.objects.filter(
            schedule_name__in=['esr21_sub_enrol_schedule',
                               'esr21_sub_enrol_schedule3',
                               'esr21_sub_fu_schedule3',
                               'esr21_sub_boost_schedule'])
        return onschedule_subcohort.count() == 900

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if 'main_schedule_enrollment' in self.request.path:
            url = self.request.path.split('main_schedule_enrollment')[0]
            return redirect(url)
        elif 'sub_cohort_enrollment' in self.request.path:
            url = self.request.path.split('sub_cohort_enrollment')[0]
            return redirect(url)
        elif 'booster_enrollment' in self.request.path:
            url = self.request.path.split('booster_enrollment')[0]
            return redirect(url)
        else:
            return self.render_to_response(context)

    def has_schedules(self):
        onschedule = self.onschedule_model_cls.objects.filter(
            subject_identifier=self.subject_identifier)
        return onschedule.count() > 0

    @property
    def show_schedule_buttons(self):
        try:
            vaccination_history = self.vaccination_history_cls.objects.get(
                subject_identifier=self.subject_identifier)
        except self.vaccination_history_cls.DoesNotExist:
            pass
        else:
            received_vaccine = vaccination_history.received_vaccine
            if received_vaccine == YES:
                dose_quantity = vaccination_history.dose_quantity
                if dose_quantity == '1':
                    last_dose_received = vaccination_history.dose1_date
                    if (get_utcnow().date() - last_dose_received).days >= 56:
                        return True
                elif dose_quantity == '2':
                    last_dose_received = vaccination_history.dose2_date
                    if (get_utcnow().date() - last_dose_received).days >= 86:
                        return True
                return False
            return True

    @property
    def wrapped_consent_v3(self):
        model_obj = self.consent_model_cls(
            **self.create_consent_v3_options)
        return self.consent_model_wrapper_cls(model_obj=model_obj)

    @property
    def consent_version_1_model_obj(self):
        """Returns a consent version 1 model instance or None.
        """
        options = dict(
            subject_identifier=self.subject_identifier,
            version='1')
        try:
            return self.consent_model_cls.objects.get(**options)
        except ObjectDoesNotExist:
            return None

    @property
    def create_consent_v3_options(self):
        options = {}
        if self.consent_version_1_model_obj:
            consent_version_1 = self.consent_version_1_model_obj.__dict__
            exclude_options = ['_state', 'consent_datetime', 'report_datetime',
                               'consent_identifier', 'version', 'id',
                               'subject_identifier_as_pk', 'created',
                               'subject_identifier_aka', 'modified',
                               'site_id', 'device_created', 'device_modified',
                               'hostname_modified', 'user_modified',
                               'hostname_created', 'user_created',
                               'revision', 'slug', 'subject_identifier',
                               ]
            for option in exclude_options:
                del consent_version_1[option]

            # Update DOB date format
            consent_version_1.update({
                'dob': consent_version_1.get('dob').strftime('%d %B %Y'),
                'version': '3'
                })
            options.update(**consent_version_1)
        return options

    @property
    def reconsented(self):
        options = dict(
            subject_identifier=self.subject_identifier,
            version='3')
        try:
            return self.consent_model_cls.objects.get(**options)
        except ObjectDoesNotExist:
            return False
        else:
            True

    @property
    def check_dose_quantity(self):
        try:
            history = self.vaccination_history_cls.objects.get(
                subject_identifier=self.kwargs.get('subject_identifier'))
        except self.vaccination_history_cls.DoesNotExist:
            messages.add_message(self.request, messages.ERROR,
                                 'Missing vaccination history form.')
        else:
            if history.received_vaccine == YES and history.dose_quantity == '3':
                return True
        return False
    