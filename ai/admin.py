from django import forms
from django.contrib import admin

from ai.models import Customers


class CustomersAdminForm(forms.ModelForm):
    raw_password = forms.CharField(
        label="Database Password",
        widget=forms.PasswordInput(),
        required=False  # Allow empty if not changing password
    )

    class Meta:
        model = Customers
        fields = ('name', 'host', 'user', 'raw_password', 'database_name', 'level_number', 'project_id')

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data['raw_password']:
            instance.set_password(self.cleaned_data['raw_password'])  # Encrypt password
        if commit:
            instance.save()
        return instance

class CustomersAdmin(admin.ModelAdmin):
    form = CustomersAdminForm
    list_display = ('name', 'host', 'user', 'database_name')
    search_fields = ('name', 'host', 'user', 'database_name')

admin.site.register(Customers, CustomersAdmin)
