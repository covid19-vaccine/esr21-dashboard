
from django.apps import apps as django_apps
from django.core.exceptions import ObjectDoesNotExist
from esr21_subject.models import screen_out

from .screen_out_model_wrapper import ScreenOutModelWrapper

class ScreeningOutWrapperMixin:
    
    screen_out_model_wrapper_cls = ScreenOutModelWrapper
    
    
    @property
    def screen_out_model_obj(self):
        """Returns a screen out model instance or None.
        """
        try:
            return self.screen_out_cls.objects.get(
                **self.screen_out_options)
        except ObjectDoesNotExist:
            return None    
        
        
    @property
    def screen_out(self):
        """Returns a wrapped saved or unsaved screen out.
        """
        model_obj = self.screen_out_model_obj or self.screen_out_cls(
            **self.create_screen_out_options)
        return self.screen_out_model_wrapper_cls(model_obj=model_obj)
            
        
    @property
    def screen_out_cls(self):
        return django_apps.get_model('esr21_subject.screenout')
    

    @property
    def create_screen_out_options(self):
        """ Returns a dictionary of options to create a new
            unpersisted screen out model instance.
        """
        options = dict(
            subject_identifier=self.subject_identifier)
        return options
    
    
    @property
    def screen_out_options(self):
        """ Returns a dictionary of options to get an existing
            screen_out instance.
        """
            
        options = dict(
            subject_identifier=self.subject_identifier,
            )
        return options
