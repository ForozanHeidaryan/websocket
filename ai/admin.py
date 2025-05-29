from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.shortcuts import render, get_object_or_404

from ai.models import Customers, CustomerData


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
    list_display = ('name', 'host', 'user', 'database_name', 'customer_data_link')
    search_fields = ('name', 'host', 'user', 'database_name')


    def customer_data_link(self, obj):
        url = reverse('admin:customer_data_list', args=[obj.pk])
        return format_html('<a href="{}">View Customer Data</a>', url)

    customer_data_link.short_description = 'Customer Data'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'customer-data/<int:customer_id>/',
                self.admin_site.admin_view(self.customer_data_view),
                name='customer_data_list',
            ),
        ]
        return custom_urls + urls

    def customer_data_view(self, request, customer_id):
        customer = get_object_or_404(Customers, pk=customer_id)
        data = CustomerData.objects.filter(customer=customer)

        if request.method == 'POST':
            form = CustomerDataForm(request.POST)
            if form.is_valid():
                new_data = form.save(commit=False)
                new_data.customer = customer
                new_data.save()
                self.message_user(request, "Customer data added successfully.")
                return HttpResponseRedirect(request.path_info)
        else:
            form = CustomerDataForm()

        context = dict(
            self.admin_site.each_context(request),
            title=f"Customer Data for {customer.name}",
            customer=customer,
            data=data,
            form=form,
        )
        return render(request, 'admin/customer_data_list.html', context)


class CustomerDataForm(forms.ModelForm):
    class Meta:
        model = CustomerData
        fields = ['name']


admin.site.register(Customers, CustomersAdmin)
