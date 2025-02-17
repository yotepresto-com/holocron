from django.contrib import admin
from django.db import connection


from .models import AuditLog, Blacklist, BlacklistAlert, BlacklistJuridicalPersonDetails, BlacklistNaturalPersonDetails, \
    BlacklistPerson, BlacklistSearch, Config, JuridicalPersonDetails, Product, Person, NaturalPersonDetails


class GenericAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        with connection.cursor() as cursor:
            cursor.execute("select set_current_user_id(%s)", [request.user.id,])
            super().save_model(request, obj, form, change)


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'name', 'is_active', 'created_at', 'updated_at')


class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'table_name', 'operation_type', 'record_id', 'changed_data', 'changed_at', 'changed_by')
    #list_filter = ()
    #search_fields = ()


class BlacklistPersonAdmin(admin.TabularInline):
    list_display = ('id', 'type', 'official_registration_number', 'created_at', 'updated_at', 'deleted_at', 'official_deletion_number')
    model = BlacklistPerson


class BlacklistAdmin(GenericAdmin):
    list_display = ('id', 'name', 'description', 'created_at', 'updated_at')
    inlines = [BlacklistPersonAdmin,]


class BlacklistAlertAdmin(GenericAdmin):
    list_display = ('id', 'blacklist_search', 'state', 'date', 'created_at', 'updated_at')


class BlacklistSearchAdmin(GenericAdmin):
    list_display = ('id', 'person', 'blacklist_person', 'match', 'match_score', 'search_date', 'created_at', 'match_details')


class ConfigAdmin(GenericAdmin):
    list_display = ('id', 'name', 'value', 'created_at', 'updated_at')


class ProductAdmin(GenericAdmin):
    list_display = ('id', 'name', 'description', 'person', 'product_type', 'created_at', 'updated_at')


class PersonAdmin(GenericAdmin):
    list_display = ('id', 'type', 'active', 'created_at', 'updated_at', 'deleted_at')


class NaturalPersonDetailsAdmin(GenericAdmin):
    list_display = ('person', 'curp', 'rfc', 'name', 'first_last_name', 'second_last_name',
                    'date_of_birth', 'created_at', 'full_name')


class BlacklistNaturalPersonDetailsAdmin(GenericAdmin):
    list_display = ('blacklist_person', 'curp', 'rfc', 'name', 'first_last_name', 'second_last_name',
                    'date_of_birth', 'created_at', 'full_name', 'calculated_full_name')

admin.site.register(AuditLog, AuditLogAdmin)
admin.site.register(Blacklist, BlacklistAdmin)
admin.site.register(BlacklistAlert, BlacklistAlertAdmin)
admin.site.register(BlacklistSearch, BlacklistSearchAdmin)
admin.site.register(Config, ConfigAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(NaturalPersonDetails, NaturalPersonDetailsAdmin)
admin.site.register(BlacklistNaturalPersonDetails, BlacklistNaturalPersonDetailsAdmin)
