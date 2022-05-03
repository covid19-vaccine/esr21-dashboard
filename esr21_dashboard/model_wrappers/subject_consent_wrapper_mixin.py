from edc_consent import ConsentModelWrapperMixin
from edc_consent.site_consents import site_consents
from datetime import datetime
from django.utils.timezone import make_aware
import pytz
from django.apps import apps as django_apps
from django.core.exceptions import ObjectDoesNotExist


class SubjectConsentWrapperMixin(ConsentModelWrapperMixin):

    consent_model = 'esr21_subject.informedconsent'

    @property
    def consent_version(self):
        consent_datetime = datetime.now()
        tz = pytz.timezone('Africa/Gaborone')
        consent_datetime = make_aware(consent_datetime, tz, True)
        consent = site_consents.get_consent(report_datetime=consent_datetime)
        return consent.version

    @property
    def consent_options(self):
        """Returns a dictionary of options to get an existing
        consent model instance.
        """
        options = dict(
            screening_identifier=self.object.screening_identifier,
            version=self.consent_version)

        return options

    @property
    def create_consent_v1_options(self):
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
            consent_version_1.update({'dob': consent_version_1.get('dob').strftime('%d %B %Y')})
            options.update(**consent_version_1)
        return options

    @property
    def consent_version_1_model_obj(self):
        """Returns a consent version 1 model instance or None.
        """
        options = dict(
            screening_identifier=self.screening_identifier,
            version='1')
        try:
            consent_model_cls = django_apps.get_model(self.consent_model)
            return consent_model_cls.objects.get(**options)
        except ObjectDoesNotExist:
            return None