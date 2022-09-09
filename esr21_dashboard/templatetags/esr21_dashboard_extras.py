from urllib.parse import urlencode, unquote

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from edc_visit_schedule.models import SubjectScheduleHistory
from django.apps import apps as django_apps


register = template.Library()


# screen_out
@register.inclusion_tag('esr21_dashboard/buttons/screening_out_button.html')
def screening_out_button(model_wrapper):
    title = ['Edit screen out form.']
    return dict(
        add_screenout_href=model_wrapper.screen_out.href,
        screen_out=model_wrapper.screen_out,
        screen_out_model_obj=model_wrapper.screen_out_model_obj)

# ntf
@register.inclusion_tag('esr21_dashboard/buttons/edit_ntf_button.html')
def edit_ntf_button(model_wrapper):
    title = ['Edit note to file.']
    return dict(
        href=model_wrapper.href,
        notetofile=model_wrapper.object,
        title=' '.join(title)
    )

@register.inclusion_tag('esr21_dashboard/buttons/edit_protocol_deviation.html')
def edit_protocol_button(model_wrapper):
    title = ['Edit protocol devitaion form.']
    return dict(
        href=model_wrapper.href,
        protocoldeviation=model_wrapper.object,
        title=' '.join(title)
    )

@register.inclusion_tag('esr21_dashboard/buttons/eligibility_confirmation_button.html')
def eligibility_confirmation_button(model_wrapper):
    title = ['Edit eligibility confirmation form.']
    return dict(
        screening_identifier=model_wrapper.object.screening_identifier,
        href=model_wrapper.href,
        title=' '.join(title))


@register.inclusion_tag('esr21_dashboard/buttons/vaccination_history_button.html')
def vaccination_history_button(model_wrapper):
    return dict(
        add_vaccination_history_href=model_wrapper.vaccination_history.href,
        vaccination_history=model_wrapper.vaccination_history,
        vaccination_history_model_obj=model_wrapper.vaccination_history_model_obj)


@register.inclusion_tag('esr21_dashboard/buttons/screening_eligibility_button.html')
def screening_eligibility_button(model_wrapper):
    return dict(
        add_screening_href=model_wrapper.screening.href,
        screening=model_wrapper.screening,
        screening_model_obj=model_wrapper.screening_model_obj)


@register.inclusion_tag('esr21_dashboard/buttons/edit_screening_button.html')
def edit_screening_button(model_wrapper):
    title = ['Edit screening eligibility form.']
    return dict(
        href=model_wrapper.screening.href,
        screening=model_wrapper.screening,
        title=' '.join(title)
    )


@register.inclusion_tag('esr21_dashboard/buttons/eligibility_button.html')
def screening_ineligibility_button(model_wrapper):
    comment = []
    obj = model_wrapper.screening.object
    tooltip = None
    if not obj.is_eligible:
        comment = obj.ineligibility.split(',') if obj.ineligibility else []
    comment = list(set(comment))
    comment.sort()
    return dict(eligible=obj.is_eligible, comment=comment,
                tooltip=tooltip, obj=obj)


@register.inclusion_tag('esr21_dashboard/buttons/eligibility_button.html')
def eligibility_button(model_wrapper):
    comment = []
    obj = model_wrapper.object
    tooltip = None
    if not obj.is_eligible:
        comment = obj.ineligibility.split(',')
    comment = list(set(comment))
    comment.sort()
    return dict(eligible=obj.is_eligible, comment=comment,
                tooltip=tooltip, obj=obj)


@register.inclusion_tag('esr21_dashboard/buttons/consent_button.html')
def consent_button(model_wrapper):
    title = ['Consent subject to participate.']
    consent_version = model_wrapper.consent_version
    return dict(
        screening_identifier=model_wrapper.object.screening_identifier,
        subject_identifier=model_wrapper.object.subject_identifier,
        add_consent_href=model_wrapper.consent.href,
        consent_version=consent_version,
        title=' '.join(title))


@register.inclusion_tag('esr21_dashboard/buttons/dashboard_button.html')
def dashboard_button(model_wrapper):
    subject_dashboard_url = settings.DASHBOARD_URL_NAMES.get(
        'subject_dashboard_url')
    return dict(
        subject_dashboard_url=subject_dashboard_url,
        subject_identifier=model_wrapper.subject_identifier)


@register.inclusion_tag('esr21_dashboard/buttons/personal_contact_info_button.html')
def personal_contact_info_button(model_wrapper):
    title = ['Edit Personal Contact information.']
    return dict(
        subject_identifier=model_wrapper.contact_information.subject_identifier,
        add_contact_information_href=model_wrapper.contact_information.href,
        contact_information_model_obj=model_wrapper.contact_information_model_obj,
        title=' '.join(title))


@register.inclusion_tag('edc_visit_schedule/subject_schedule_footer_row.html')
def subject_schedule_footer_row(subject_identifier, visit_schedule, schedule,
                                subject_dashboard_url):
    context = {}
    try:
        history_obj = SubjectScheduleHistory.objects.get(
            visit_schedule_name=visit_schedule.name,
            schedule_name=schedule.name,
            subject_identifier=subject_identifier,
            offschedule_datetime__isnull=False)
    except SubjectScheduleHistory.DoesNotExist:
        onschedule_model_obj = schedule.onschedule_model_cls.objects.get(
            subject_identifier=subject_identifier,
            schedule_name=schedule.name, )
        options = dict(subject_identifier=subject_identifier)
        query = unquote(urlencode(options))
        href = (f'{visit_schedule.offstudy_model_cls().get_absolute_url()}?next='
                f'{subject_dashboard_url},subject_identifier')
        href = '&'.join([href, query])
        context = dict(
            offschedule_datetime=None,
            onschedule_datetime=onschedule_model_obj.onschedule_datetime,
            href=mark_safe(href))
    else:
        onschedule_model_obj = schedule.onschedule_model_cls.objects.get(
            subject_identifier=subject_identifier,
            schedule_name=schedule.name)
        options = dict(subject_identifier=subject_identifier)
        query = unquote(urlencode(options))
        offstudy_model_obj = None
        try:
            offstudy_model_obj = visit_schedule.offstudy_model_cls.objects.get(
                subject_identifier=subject_identifier)
        except visit_schedule.offstudy_model_cls.DoesNotExist:
            href = (f'{visit_schedule.offstudy_model_cls().get_absolute_url()}'
                    f'?next={subject_dashboard_url},subject_identifier')
        else:
            href = (f'{offstudy_model_obj.get_absolute_url()}?next='
                    f'{subject_dashboard_url},subject_identifier')

        href = '&'.join([href, query])

        context = dict(
            offschedule_datetime=history_obj.offschedule_datetime,
            onschedule_datetime=onschedule_model_obj.onschedule_datetime,
            href=mark_safe(href))
        if offstudy_model_obj:
            context.update(offstudy_date=offstudy_model_obj.offstudy_date)
    context.update(
        visit_schedule=visit_schedule,
        schedule=schedule,
        verbose_name=visit_schedule.offstudy_model_cls._meta.verbose_name)
    return context


@register.inclusion_tag('esr21_dashboard/buttons/subject_offstudy_button.html')
def subject_offstudy_button(modelwrapper):

    context = {
        'title': 'Subject Offstudy',
        'href': modelwrapper.href,
    }
    return context


@register.inclusion_tag('esr21_dashboard/buttons/consent_button.html')
def consent_v3_button(model_wrapper):
    title = ['Consent subject to participate.']
    return dict(
        screening_identifier=model_wrapper.object.screening_identifier,
        subject_identifier=model_wrapper.object.subject_identifier,
        add_consent_href=model_wrapper.href,
        consent_version='3',
        title=' '.join(title))



@register.filter(name='get_label_lower')
def get_label_lower(info):
    esr21_subject = django_apps.get_app_config('esr21_subject')
    list_x_mdl = []
    dev_list = info.replace('"', '').replace("''", '')
    x = dev_list.replace("'", '')
    x = x.replace('[', '').replace(']', '')
    x = x.split(',')
    for f_n in x:
        f_n = f_n.strip()
        list_x = [x_model._meta.verbose_name for x_model in esr21_subject.get_models() if x_model._meta.label_lower == f_n]
        list_x_mdl += list_x
        
    dev_form_name = ''
    for form_name in list_x_mdl:
        dev_form_name += f'{form_name}, '
    dev_form_name = dev_form_name.strip().removesuffix(',')
    return dev_form_name
    
    
    
    