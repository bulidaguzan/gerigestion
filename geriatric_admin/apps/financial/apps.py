from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FinancialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.financial'
    verbose_name = _('Gestión Financiera')
    
    def ready(self):
        import apps.financial.signals 