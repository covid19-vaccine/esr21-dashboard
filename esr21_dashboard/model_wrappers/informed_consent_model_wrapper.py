from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from edc_model_wrapper import ModelWrapper

from .contact_information_model_wrapper_mixin import ContactInformationWrapperMixin
from .subject_consent_wrapper_mixin import SubjectConsentWrapperMixin
from .vaccination_history_model_wrapper_mixin import VaccinationHistoryModelWrapperMixin
from .screen_out_wrapper_mixin import ScreeningOutWrapperMixin

class InformedConsentModelWrapper(ContactInformationWrapperMixin,
                                  SubjectConsentWrapperMixin,
                                  VaccinationHistoryModelWrapperMixin,
                                  ScreeningOutWrapperMixin,
                                  ModelWrapper):

    model = 'esr21_subject.informedconsent'
    next_url_name = settings.DASHBOARD_URL_NAMES.get(
        'screening_listboard_url')
    next_url_attrs = ['screening_identifier']

    @property
    def querystring_attrs(self):
        options = ['subject_identifier']
        options.extend(self.create_consent_v1_options.keys())
        return options

    @property
    def subject_identifier(self):
        consent_model = self.consent_model_obj
        if consent_model:
            return consent_model.subject_identifier
        return None

    @property
    def screening_cls(self):
        return django_apps.get_model('esr21_subject.screeningeligibility')

    @property
    def subject_consent_cls(self):
        return django_apps.get_model('esr21_subject.informedconsent')

    @property
    def screening_model_obj(self):
        """Returns a caregiver locator model instance or None.
        """
        try:
            return self.screening_cls.objects.get(
                **self.screening_options)
        except ObjectDoesNotExist:
            return None

    @property
    def screening_options(self):
        """Returns a dictionary of options to get an existing
        caregiver locator model instance.
        """
        options = dict(
            subject_identifier=self.subject_identifier)
        return options

    @property
    def is_eligible(self):
        if self.screening_model_obj:
            return self.screening_model_obj.is_eligible
        return False

    @property
    def reasons_ineligible(self):
        if self.screening_model_obj:
            return self.screening_model_obj.ineligibility
        return False

    @property
    def consent_model_obj(self):
        """Returns a consent model instance or None.
        """
        consent_model_cls = django_apps.get_model(self.model)
        try:
            return consent_model_cls.objects.get(**self.consent_options)
        except ObjectDoesNotExist:
            return None
