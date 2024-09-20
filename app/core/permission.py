# permission.py
from enum import Enum


class Permission(str, Enum):
    CREATE_USER = "create_user"
    READ_USER = "read_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"

    CREATE_ROLE = "create_role"
    READ_ROLE = "read_role"
    UPDATE_ROLE = "update_role"
    DELETE_ROLE = "delete_role"

    READ_PERMISSION = "read_permission"
    ASSIGN_PERMISSION = "assign_permission"
    REMOVE_PERMISSION = "remove_permission"

    ASSIGN_ROLE = "assign_role"
    REMOVE_ROLE = "remove_role"

    CREATE_PROFILE = "create_profile"
    READ_PROFILE = "read_profile"
    UPDATE_PROFILE = "update_profile"
    DELETE_PROFILE = "delete_profile"

    CREATE_PRODUCT = "create_product"
    READ_PRODUCT = "read_product"
    UPDATE_PRODUCT = "update_product"
    DELETE_PRODUCT = "delete_product"

    CREATE_RISK_MATRIX = "create_risk_matrix"
    READ_RISK_MATRIX = "read_risk_matrix"
    UPDATE_RISK_MATRIX = "update_risk_matrix"
    DELETE_RISK_MATRIX = "delete_risk_matrix"

    @property
    def description(self) -> str:
        descriptions = {
            "create_user": "Allows creating new users in the system.",
            "read_user": "Allows reading user information.",
            "update_user": "Allows updating existing user information.",
            "delete_user": "Allows deleting users from the system.",
            "create_profile": "Allows creating user profiles.",
            "read_profile": "Allows viewing user profiles.",
            "update_profile": "Allows modifying user profiles.",
            "delete_profile": "Allows removing user profiles.",
            "create_product": "Allows adding new products to the catalog.",
            "read_product": "Allows viewing product details.",
            "update_product": "Allows modifying product information.",
            "delete_product": "Allows removing products from the catalog.",
            "create_risk_matrix": "Allows creating new risk matrices.",
            "read_risk_matrix": "Allows viewing risk matrices.",
            "update_risk_matrix": "Allows updating existing risk matrices.",
            "delete_risk_matrix": "Allows deleting risk matrices.",
            "create_role": "Allows creating new roles in the system.",
            "read_role": "Allows viewing role details.",
            "update_role": "Allows modifying existing roles.",
            "delete_role": "Allows deleting roles from the system.",
            "read_permission": "Allows viewing permissions.",
            "assign_permission": "Allows assigning permissions to roles/users.",
            "remove_permission": "Allows removing permissions from roles/users.",
            "assign_role": "Allows assigning roles to users.",
            "remove_role": "Allows removing roles from users.",
        }
        return descriptions.get(self.value, "No description available.")
