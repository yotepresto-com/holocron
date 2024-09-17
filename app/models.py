from sqlalchemy import MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.automap import automap_base
from .database import engine

# Create a MetaData instance
metadata = MetaData()
metadata.reflect(bind=engine)
Base = declarative_base()
AutomapBase = automap_base()
AutomapBase.prepare(engine, reflect=True)

# Authorization
SystemUser = AutomapBase.classes.system_user
Role = AutomapBase.classes.role
RolePermission = AutomapBase.classes.role_permission
UserRole = AutomapBase.classes.user_role

# Blacklist
BlacklistPerson = AutomapBase.classes.blacklist_person
BlacklistPersonDetails = AutomapBase.classes.blacklist_person_details
BlacklistNaturalPersonDetails = AutomapBase.classes.blacklist_natural_person_details
BlacklistJuridicalPersonDetails = AutomapBase.classes.blacklist_juridical_person_details
BlacklistPublication = AutomapBase.classes.blacklist_publication
SearchNaturalPerson = AutomapBase.classes.search_natural_person
SearchJuridicalPerson = AutomapBase.classes.search_juridical_person

# Person
Person = AutomapBase.classes.person
PersonDetails = AutomapBase.classes.person_details
NaturalPersonDetails = AutomapBase.classes.natural_person_details
JuridicalPersonDetails = AutomapBase.classes.juridical_person_details

# Product
ProductType = AutomapBase.classes.product_type
Product = AutomapBase.classes.product

# Risk
RiskMatrix = AutomapBase.classes.risk_matrix
RiskAttributeValue = AutomapBase.classes.risk_attribute_value
CategoricalValueRisk = AutomapBase.classes.categorical_value_risk
RiskLevel = AutomapBase.classes.risk_level
Risk = AutomapBase.classes.risk

# Transaction
TransactionType = AutomapBase.classes.transaction_type
Transaction = AutomapBase.classes.transaction