from sqlalchemy import MetaData
from sqlalchemy.ext.automap import automap_base
from .database import engine

# Create a MetaData instance
metadata = MetaData()
metadata.reflect(bind=engine)
AutomapBase = automap_base()
AutomapBase.prepare(engine, reflect=True)

# Authorization
User = AutomapBase.classes.user
Role = AutomapBase.classes.role
RolePermission = AutomapBase.classes.role_permission
UserRole = AutomapBase.classes.user_role

# Blacklist
Blacklist = AutomapBase.classes.blacklist
BlacklistPerson = AutomapBase.classes.blacklist_person
BlacklistPersonAttribute = AutomapBase.classes.blacklist_person_attribute
BlacklistPersonAttributeValue = AutomapBase.classes.blacklist_person_attribute_value
BlacklistNaturalPersonDetails = AutomapBase.classes.blacklist_natural_person_details
BlacklistJuridicalPersonDetails = AutomapBase.classes.blacklist_juridical_person_details
BlacklistAlert = AutomapBase.classes.blacklist_alert
BlacklistSearch = AutomapBase.classes.blacklist_search

# Person
Person = AutomapBase.classes.person
NaturalPersonDetails = AutomapBase.classes.natural_person_details
JuridicalPersonDetails = AutomapBase.classes.juridical_person_details

# Product
ProductType = AutomapBase.classes.product_type
Product = AutomapBase.classes.product
ProductAttribute = AutomapBase.classes.product_attribute
ProductAttributeValue = AutomapBase.classes.product_attribute_value

# Risk
RiskMatrix = AutomapBase.classes.risk_matrix
RiskAttributeValue = AutomapBase.classes.risk_attribute_value
RiskCategoryValue = AutomapBase.classes.risk_attribute_categorical_value
RiskLevel = AutomapBase.classes.risk_level
Risk = AutomapBase.classes.risk

# Transaction
TransactionType = AutomapBase.classes.transaction_type
Transaction = AutomapBase.classes.transaction

# Transaction alerts
UnusualOperations = AutomapBase.classes.unusual_operations
RelevantOperations = AutomapBase.classes.relevant_operations

