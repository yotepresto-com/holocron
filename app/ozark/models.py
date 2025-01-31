from django.db import models




class AuditLog(models.Model):
    table_name = models.CharField(max_length=100)
    operation_type = models.TextField()  # This field type is a guess.
    record_id = models.IntegerField()
    changed_data = models.JSONField(blank=True, null=True)
    changed_at = models.DateTimeField()
    changed_by = models.ForeignKey('User', models.DO_NOTHING, db_column='changed_by')

    class Meta:
        managed = False
        db_table = 'audit_log'


class Blacklist(models.Model):
    short_name = models.CharField(unique=True, max_length=10)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'blacklist'


class BlacklistAlert(models.Model):
    blacklist_search = models.ForeignKey('BlacklistSearch', models.DO_NOTHING)
    state = models.TextField()  # This field type is a guess.
    date = models.DateField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'blacklist_alert'


class BlacklistJuridicalPersonDetails(models.Model):
    blacklist_person = models.OneToOneField('BlacklistPerson', models.DO_NOTHING, primary_key=True)
    rfc = models.CharField(max_length=13, blank=True, null=True)
    legal_name = models.TextField()
    incorporation_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'blacklist_juridical_person_details'


class BlacklistNaturalPersonDetails(models.Model):
    id = models.OneToOneField('BlacklistPerson', models.DO_NOTHING, db_column='id', primary_key=True)
    curp = models.CharField(max_length=18, blank=True, null=True)
    rfc = models.CharField(max_length=13, blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    first_last_name = models.TextField(blank=True, null=True)
    second_last_name = models.TextField(blank=True, null=True)
    full_name = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'blacklist_natural_person_details'


class BlacklistPerson(models.Model):
    blacklist = models.ForeignKey(Blacklist, models.DO_NOTHING)
    type = models.CharField(max_length=100)
    official_registration_number = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    official_deletion_number = models.CharField(blank=True, null=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'blacklist_person'


class BlacklistPersonAttribute(models.Model):
    attribute_name = models.CharField(unique=True, max_length=50)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'blacklist_person_attribute'


class BlacklistPersonAttributeValue(models.Model):
    blacklist_person = models.ForeignKey(BlacklistPerson, models.DO_NOTHING)
    attribute = models.ForeignKey(BlacklistPersonAttribute, models.DO_NOTHING)
    value = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'blacklist_person_attribute_value'
        unique_together = (('blacklist_person', 'attribute'),)


class BlacklistSearch(models.Model):
    person = models.ForeignKey('Person', models.DO_NOTHING, blank=True, null=True)
    blacklist_person = models.ForeignKey(BlacklistPerson, models.DO_NOTHING, blank=True, null=True)
    match = models.BooleanField(blank=True, null=True)
    match_score = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)
    search_date = models.DateField()
    created_at = models.DateTimeField()
    match_details = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'blacklist_search'


class Config(models.Model):
    name = models.CharField(unique=True, max_length=100)
    value = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'config'


class JuridicalPersonDetails(models.Model):
    person = models.OneToOneField('Person', models.DO_NOTHING, primary_key=True, related_name='juridical_person_details')
    rfc = models.CharField(max_length=13, blank=True, null=True)
    legal_name = models.TextField()
    incorporation_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'juridical_person_details'


class NaturalPersonDetails(models.Model):
    person = models.OneToOneField('Person', models.DO_NOTHING, primary_key=True, related_name='natural_person_details')
    curp = models.CharField(max_length=18, blank=True, null=True)
    rfc = models.CharField(max_length=13, blank=True, null=True)
    name = models.TextField()
    first_last_name = models.TextField()
    second_last_name = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    full_name = models.GeneratedField(expression=None, output_field=models.TextField(), db_persist=True)

    class Meta:
        managed = False
        db_table = 'natural_person_details'


class Person(models.Model):
    type = models.TextField()  # This field type is a guess.
    active = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'person'


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    person = models.ForeignKey(Person, models.DO_NOTHING, blank=True, null=True)
    product_type = models.ForeignKey('ProductType', models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'product'


class ProductAttribute(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    data_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'product_attribute'


class ProductAttributeValue(models.Model):
    product = models.ForeignKey(Product, models.DO_NOTHING)
    attribute = models.ForeignKey(ProductAttribute, models.DO_NOTHING)
    value = models.TextField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'product_attribute_value'


class ProductType(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'product_type'


class Profile(models.Model):
    person = models.ForeignKey(Person, models.DO_NOTHING)
    profile_type = models.ForeignKey('ProfileType', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'profile'


class ProfileAttribute(models.Model):
    profile_type = models.ForeignKey('ProfileType', models.DO_NOTHING)
    attribute = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=50)
    is_transactional = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'profile_attribute'


class ProfileAttributeCategoricalValues(models.Model):
    attribute = models.ForeignKey(ProfileAttribute, models.DO_NOTHING)
    accepted_value = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'profile_attribute_categorical_values'
        unique_together = (('attribute', 'accepted_value'),)


class ProfileData(models.Model):
    profile = models.ForeignKey(Profile, models.DO_NOTHING)
    attribute = models.ForeignKey(ProfileAttribute, models.DO_NOTHING)
    value = models.TextField()
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'profile_data'


class ProfileType(models.Model):
    name = models.CharField(max_length=255)
    accept_natural_person = models.BooleanField(blank=True, null=True)
    accept_legal_person = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'profile_type'


class RelevantOperations(models.Model):
    operation_date = models.DateField()
    customer = models.ForeignKey(Profile, models.DO_NOTHING)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    operation_type = models.CharField(max_length=50, blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    reported_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'relevant_operations'


class Risk(models.Model):
    profile = models.ForeignKey(Profile, models.DO_NOTHING)
    risk_matrix = models.ForeignKey('RiskMatrix', models.DO_NOTHING)
    evaluation_date = models.DateField()
    score = models.DecimalField(max_digits=5, decimal_places=2)
    risk_level = models.ForeignKey('RiskLevel', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'risk'


class RiskAttributeCategoricalValue(models.Model):
    profile_attr_categorical_value = models.OneToOneField(ProfileAttributeCategoricalValues, models.DO_NOTHING, db_column='profile_attr_categorical_value')
    risk_value = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'risk_attribute_categorical_value'


class RiskAttributeValue(models.Model):
    risk_matrix = models.ForeignKey('RiskMatrix', models.DO_NOTHING)
    attribute = models.ForeignKey(ProfileAttribute, models.DO_NOTHING)
    risk_value = models.TextField(blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'risk_attribute_value'
        unique_together = (('risk_matrix', 'attribute'),)


class RiskLevel(models.Model):
    level = models.CharField(max_length=50)
    score_cut = models.DecimalField(max_digits=5, decimal_places=2)
    is_lowest_level = models.BooleanField()
    is_highest_level = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'risk_level'


class RiskMatrix(models.Model):
    profile_type = models.ForeignKey(ProfileType, models.DO_NOTHING)
    name = models.CharField(max_length=255)
    status = models.TextField()  # This field type is a guess.
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'risk_matrix'


class Role(models.Model):
    name = models.CharField(unique=True, max_length=50)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'role'


class RolePermission(models.Model):
    role = models.ForeignKey(Role, models.DO_NOTHING)
    permission = models.TextField()  # This field type is a guess.
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'role_permission'
        unique_together = (('role', 'permission'),)


class Transaction(models.Model):
    product = models.ForeignKey(Product, models.DO_NOTHING)
    transaction_type = models.ForeignKey('TransactionType', models.DO_NOTHING)
    counterpart = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    effective_date = models.DateField()
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transaction'


class TransactionType(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    product_type = models.ForeignKey(ProductType, models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transaction_type'


class UnusualOperations(models.Model):
    operation_date = models.DateField()
    customer = models.ForeignKey(Profile, models.DO_NOTHING)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    alert_level = models.CharField(max_length=20, blank=True, null=True)
    reported_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'unusual_operations'


# TODO: remove, use the django user model
class User(models.Model):
    username = models.CharField(unique=True, max_length=50)
    email = models.CharField(unique=True, max_length=255)
    name = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'user'


class UserRole(models.Model):
    user = models.ForeignKey(User, models.DO_NOTHING)
    role = models.ForeignKey(Role, models.DO_NOTHING)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'user_role'
        unique_together = (('user', 'role'),)
