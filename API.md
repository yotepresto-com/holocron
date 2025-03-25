# ** Ozark REST API Interface**

Bellow is the API interface for the project.

---
## **Pagination**

All endpoints returning lists/arrays support pagination parameters (optional) in their query string:

- **page** (integer, default=1): The current page number.
- **page_size** (integer, default=20): How many items to display per page.

Example usage:
```
GET /users?page=2&page_size=10
```

The server should return:
- A list of items for that page
- Additional metadata (e.g., total_items, total_pages, etc.)

---
## **1. Users**

### 1.1. Create User
- **Endpoint:** `POST /users`
- **Description:** Create a new user with a unique username and email.
- **Request Body** (JSON):
  ```json
  {
    "username": "johndoe",
    "email": "test@ytp.com",
    "first_name": "Juan",
    "last_name": "Perez"
  }
  ```
- **Response:**
  - **201 Created** if successful, returns the newly created user object.

### 1.2. Get All Users
- **Endpoint:** `GET /users`
- **Description:** Retrieve a **paginated** list of all users.
- **Query Params (optional):** `page`, `page_size`
- **Response:**
  - **200 OK** returns an array (paginated) of user objects, plus pagination metadata.

### 1.3. Get User by ID
- **Endpoint:** `GET /users/{id}`
- **Description:** Retrieve a user by its unique ID.
- **Response:**
  - **200 OK** returns the user object.
  - **404 Not Found** if the user does not exist.

### 1.4. Update User
- **Endpoint:** `PUT /users/{id}` or `PATCH /users/{id}`
- **Description:** Update user details (e.g., email, name). **Note:** The `is_active` flag cannot be updated here because it is reserved for soft deletion.
- **Request Body (PUT)**:
  ```json
  {
    "email": "newemail@example.com",
    "name": "New Name"
  }
  ```
- **Response:**
  - **200 OK** returns the updated user object.
  - **404 Not Found** if user does not exist.

### 1.5. Delete User
- **Endpoint:** `DELETE /users/{id}`
- **Description:** Soft deletes a user by setting `is_active` to false. Physical deletion may be restricted.
- **Response:**
  - **204 No Content** if successful.
  - **404 Not Found** if user does not exist.

---
## **2. Roles**

### 2.1. Create Role
- **Endpoint:** `POST /roles`
- **Description:** Create a new role with a unique name.
- **Request Body** (JSON):
  ```json
  {
    "name": "Administrator"
  }
  ```
- **Response:**
  - **201 Created** returns newly created role.

### 2.2. Get All Roles
- **Endpoint:** `GET /roles`
- **Description:** Retrieve a **paginated** list of all roles.
- **Query Params (optional):** `page`, `page_size`
- **Response:**
  - **200 OK** returns an array (paginated) of roles.

### 2.3. Get Role by ID
- **Endpoint:** `GET /roles/{id}`
- **Response:**
  - **200 OK** returns the role object.
  - **404 Not Found** if role does not exist.

### 2.4. Update Role
- **Endpoint:** `PUT /roles/{id}` or `PATCH /roles/{id}`
- **Description:** Update role details.
- **Request Body** (JSON):
  ```json
  {
    "name": "New name"
  }
  ```
- **Response:**
  - **200 OK** returns updated role.

### 2.5. Delete Role
- **Endpoint:** `DELETE /roles/{id}`
- **Description:** Deletes a role.
- **Response:**
  - **204 No Content** if successful.
  - **404 Not Found** if role does not exist.

---
## **3. Permissions and Assignments**

### 3.1. Bulk Assign Permissions to Role
- **Endpoint:** `POST /roles/{role_id}/permissions`
- **Description:** Assign multiple permissions to a specific role **atomically**.
- **Request Body** (JSON):
  ```json
  {
    "permissions": [
      "create_user",
      "read_user",
      "update_user"
    ]
  }
  ```
- **Behavior:**
  - If **any** of the specified permissions are already assigned, the request should fail and do nothing.
  - Otherwise, assign **all** listed permissions.
- **Response:**
  - **201 Created** if all permissions were successfully assigned.
  - **409 Conflict** if **any** permission in the list is already assigned (no changes made).

### 3.2. Bulk Remove Permissions from Role
- **Endpoint:** `DELETE /roles/{role_id}/permissions`
- **Description:** Remove multiple permissions from a specific role **atomically**.
- **Request Body** (JSON):
  ```json
  {
    "permissions": [
      "read_user",
      "update_user"
    ]
  }
  ```
- **Behavior:**
  - If **any** of the specified permissions are not currently assigned to the role, the request should fail and do nothing.
  - Otherwise, remove **all** listed permissions.
- **Response:**
  - **204 No Content** if permissions were successfully removed.
  - **409 Conflict** if **any** permission is not currently assigned (no changes made).

### 3.3. Assign Role to User
- **Endpoint:** `POST /users/{user_id}/roles`
- **Description:** Assign a role to a user.
- **Request Body** (JSON):
  ```json
  {
    "role_id": 2
  }
  ```
- **Response:**
  - **201 Created** indicates success.

### 3.4. Remove Role from User
- **Endpoint:** `DELETE /users/{user_id}/roles/{role_id}`
- **Description:** Remove a specific role assignment from a user.
- **Response:**
  - **204 No Content** if successful.

### 3.5. List All Permissions
- **Endpoint:** `GET /permissions`
- **Description:** Returns the list of all available permissions (from the `permission_type` enum).
- **Response:**
  - **200 OK** returns an array of permission objects, for example:
  ```json
  [
    {
      "permission": "create_user"
    },
    {
      "permission": "read_user"
    }
  ]
  ```

---
## **4. Configuration**

### 4.1. Create Config Entry
### 4.2. Get Config by Name
- **Endpoint:** `GET /config/{name}`
- **Response:**
  - **200 OK** returns the config object.
  - **404 Not Found** if config does not exist.

### 4.3. Update Config
- **Endpoint:** `PATCH /config/{name}`
- **Description:** Update the value of an existing config entry.
- **Request Body** (JSON):
  ```json
  {
    "value": "5"
  }
  ```
- **Response:**
  - **200 OK** returns updated config.

---
## **5. Profile Management**

A **profile** is a definition that may apply to either a **natural person** or a **legal person** (or both). Each profile captures:
- **name** (string, required)
- **accept_natural_person** (boolean, required)
- **accept_legal_person** (boolean, required)

A single person may hold multiple profiles in the system, each describing different sets of attributes.

### **Profile Attributes**
Each profile can include one or more **attributes**, each of which must define:
- **name** (string, required)
- **description** (string, optional)
- **type** (string, required) — valid values: `numerical`, `date`, or `categorical`
- **is_transactional** (boolean, optional)
- **accepted_values** (array of strings, **required only if** `type` = `categorical`)

The following endpoints manage the **profile** itself (base data) and its attributes.

---
### 5.1. Create Profile
- **Endpoint:** `POST /profiles`
- **Description:** Create a new profile definition (which may apply to natural and/or legal persons).
- **Request Body (JSON example):**
  ```json
  {
    "name": "High-Value Customer",
    "accept_natural_person": true,
    "accept_legal_person": false
  }
  ```
  (Attributes can be added separately after the profile is created using the attribute endpoints.)
- **Response:**
  - **201 Created** returns the newly created profile object.

### 5.2. Get All Profiles
- **Endpoint:** `GET /profiles`
- **Description:** Retrieve a **paginated** list of profiles.
- **Query Params (optional):** `page`, `page_size`
- **Response:**
  - **200 OK** returns an array (paginated) of profile objects.

### 5.3. Get Profile by ID
- **Endpoint:** `GET /profiles/{id}`
- **Description:** Returns the profile’s base data plus any existing attributes.
- **Response:**
  - **200 OK** returns the profile object (including all attributes).
  - **404 Not Found** if the profile does not exist.

### 5.4. Update Profile Base Info
- **Endpoint:** `PATCH /profiles/{id}`
- **Description:** Updates only the **name**, **accept_natural_person**, or **accept_legal_person** fields of an existing profile.
- **Request Body (JSON example):**
  ```json
  {
    "name": "High-Value Clients",
    "accept_natural_person": true,
    "accept_legal_person": true
  }
  ```
- **Response:**
  - **200 OK** returns the updated profile object (including base data only).

### 5.5. Create an Attribute in a Profile
- **Endpoint:** `POST /profiles/{id}/attribute`
- **Description:** Adds a new attribute definition to an existing profile.
- **Request Body (JSON example):**
  ```json
  {
    "name": "Customer Rating",
    "description": "A rating from 1 to 5",
    "type": "numerical",
    "is_transactional": false
  }
  ```
  If `type` = `categorical`, then:
  ```json
  {
    "name": "Risk Tier",
    "type": "categorical",
    "accepted_values": ["Low", "Medium", "High"]
  }
  ```
- **Response:**
  - **201 Created** returns the newly created attribute.
  - **404 Not Found** if profile `{id}` does not exist.

### 5.6. Delete an Attribute from a Profile
- **Endpoint:** `DELETE /profiles/{id}/attribute/{attribute_id}`
- **Description:** Permanently removes a specific attribute from a profile.
- **Response:**
  - **204 No Content** if deletion succeeds.
  - **404 Not Found** if either the profile or the attribute is not found.

### 5.7. Delete Profile
- **Endpoint:** `DELETE /profiles/{id}`
- **Description:** Deletes (or soft-deletes) the entire profile definition.
- **Response:**
  - **204 No Content** if successful.
  - **404 Not Found** if profile does not exist.

---
## **6. Person Management**

### 6.1. Create Person
- **Endpoint:** `POST /persons`
- **Description:** Create a new person record. The `type` must be either `natural` or `juridical`. If `type = "natural"`, the `natural_details` object is required; if `type = "juridical"`, the `juridical_details` object is required. The `active` flag defaults to `true` if not specified.

- **Profiles**: Instead of a single `attributes` object, this endpoint now accepts a `profiles` dictionary where **each key** is the **profile name**, and the **value** is a dictionary of attribute key-value pairs relevant to that profile.

- **Request Body** (JSON example for a natural person):
  ```json
  {
    "type": "natural",
    "natural_details": {
      "curp": "XAXX010101HNEXXXA0",
      "rfc": "XAXX010101XX0",
      "name": "Juan",
      "first_last_name": "Pérez",
      "second_last_name": "Gómez",
      "date_of_birth": "1990-05-21"
    },
    "profiles": {
      "customer_profile": {
        "income_level": "high",
        "preferred_language": "es"
      },
      "vip_settings": {
        "loyalty_level": "gold"
      }
    }
  }
  ```
  For a juridical person:
  ```json
  {
    "type": "juridical",
    "juridical_details": {
      "rfc": "ABC123456789",
      "legal_name": "My Company Inc.",
      "incorporation_date": "2020-01-01"
    },
    "profiles": {
      "business_profile": {
        "business_sector": "finance",
        "employee_count": 50
      },
      "compliance_info": {
        "kyc_status": "approved"
      }
    }
  }
  ```
- **Response:**
  - **201 Created** returns the newly created person object. The response may include:
    - The generated `id`
    - The `type`
    - The relevant `*_details`
    - A `profiles` dictionary structure holding each profile’s nested attribute data.

### 6.2. Get Person by ID
- **Endpoint:** `GET /persons/{id}`
- **Description:** Returns both the person’s base info (`type`, plus `natural_details` or `juridical_details`) and a `profiles` dictionary with any stored profile data.
- **Response:**
  - **200 OK** returns the person data (including `profiles`).
  - **404 Not Found** if the person does not exist.

### 6.3. Delete Person
- **Endpoint:** `DELETE /persons/{id}`
- **Description:** A deletion attempt triggers the `prevent_deletion()` function. If business rules do not allow direct deletion, handle accordingly.
- **Response:**
  - **403 Forbidden** if direct deletion is disallowed.
  - **204 No Content** if the person was successfully marked as deleted (soft delete logic).

---
## **7. Product Management**

### 7.1. Create Product
- **Endpoint:** `POST /products`
- **Description:** Create a new product.
- **Request Body** (JSON):
  ```json
  {
    "name": "Example Savings Account",
    "description": "A standard savings account",
    "person_id": 123,
    "product_type_id": 1
  }
  ```
- **Response:**
  - **201 Created** returns the newly created product.

### 7.2. Get Product by ID
- **Endpoint:** `GET /products/{id}`
- **Response:**
  - **200 OK** returns the product details.

### 7.3. Update Product
- **Endpoint:** `PATCH /products/{id}`
- **Description:** Update product details.
- **Request Body** (JSON):
  ```json
  {
    "name": "New Product Name"
  }
  ```
- **Response:**
  - **200 OK** returns updated product.

### 7.4. Delete Product
- **Endpoint:** `DELETE /products/{id}`
- **Response:**
  - **204 No Content** if successful.

---
## **9. Blacklisted Persons**

Manage records of **persons** that are blacklisted in the system, irrespective of a specific blacklist.

### 9.1. Create Blacklisted Person
- **Endpoint:** `POST /blacklisted_persons`
- **Description:** Create a new blacklisted person record. The structure is similar to creating a normal person, but flagged as blacklisted.
- **Request Body (JSON):**
  ```json
  {
    "blacklist_id": 2,
    "type": "natural", // or "juridical"
    "official_registration_number": "123456", // optional
    "natural_details": {
      "curp": "ABCD010101HDFLRS09",
      "rfc": "ABCD010101XXX",
      "name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "date_of_birth": "1980-05-15"
    },
    "juridical_details": {
      "rfc": "XYZ987654321",
      "legal_name": "Blacklisted Co.",
      "incorporation_date": "2010-06-30"
    },
    "attributes": [
      {
        "name": "Notes",
        "value": "High-risk individual"
      },
      {
        "name": "AdditionalInfo",
        "value": "Sanctioned by XYZ"
      }
    ]
  }
  ```
  **Fields:**
  - **type**: `natural` or `juridical` (required)
  - **official_registration_number**: optional reference code
  - **natural_details** (required if `type = "natural"`)
    - `curp` (optional, domain-specific)
    - `rfc` (optional or required, domain-specific)
    - `name`, `last_name`, or `full_name`
    - `date_of_birth`
  - **juridical_details** (required if `type = "juridical"`)
    - `rfc`
    - `legal_name`
    - `incorporation_date`
  - **attributes**: array of objects, each with `name` and `value`.

- **Response:**
  - **201 Created** returns the newly created blacklisted person object.

### 9.2. Get Blacklisted Person
- **Endpoint:** `GET /blacklisted_persons/{id}`
- **Description:** Retrieve details of a single blacklisted person.
- **Response:**
  - **200 OK** returns the blacklisted person object (including details and attributes).
  - **404 Not Found** if the blacklisted person does not exist.

### 9.3. Update Blacklisted Person (Attributes Only)
- **Endpoint:** `PATCH /blacklisted_persons/{id}`
- **Description:** Update **only** the attributes of a blacklisted person.
- **Request Body (JSON example):**
  ```json
  {
    "attributes": [
      {
        "name": "Notes",
        "value": "Updated note"
      },
      {
        "name": "RiskScore",
        "value": "7"
      }
    ]
  }
  ```
- **Behavior:**
  - Replace or upsert attributes based on `name`.
  - Other details (like type, official_registration_number, natural/juridical fields) are **not** changed here.
- **Response:**
  - **200 OK** returns the updated blacklisted person record.
  - **404 Not Found** if the blacklisted person does not exist.

### 9.4. Delete Blacklisted Person (Soft Delete)
- **Endpoint:** `DELETE /blacklisted_persons/{id}`
- **Description:** Soft deletes the blacklisted person (e.g., sets a `deleted_at` timestamp instead of removing the record).
- **Response:**
  - **204 No Content** if successful.
  - **404 Not Found** if the blacklisted person does not exist.

### 9.5. Search Blacklisted Persons
- **Endpoint:** `GET /blacklisted_persons`
- **Description:** Returns a paginated list of blacklisted persons, optionally filtered by query params:
  - `type` (natural/juridical)
  - `curp`
  - `rfc`
  - `name`
  - `last_name`
  - `full_name`
  - `date_of_birth`
  - `legal_name`
  - `incorporation_date`
  - plus `page`, `page_size` for pagination.
- **Response:**
  - **200 OK** returns an array (paginated) of blacklisted persons matching the criteria. Attributes and details can also be included or omitted, depending on requirements.

---
## **Considerations**
1. **Authentication** There are two types of autentication, UI authentication that should be made with google sso, and api authentication that it will be made via supertoken.
2. **Authorization** Authorization is managed internally, for example User creation might only be available to roles with the `create_user` permission.
2. **Audit Logging**: All `INSERT`, `UPDATE`, `DELETE` calls can trigger the audit log triggers. Clients typically don’t need to post directly to `audit_log`.
3. **Conflict & Error Handling**: Return appropriate HTTP status codes:
   - `400 Bad Request` for invalid data.
   - `401 Unauthorized` / `403 Forbidden` for permission issues.
   - `409 Conflict` for unique constraint violations.
4. **Soft vs. Hard Deletion**: Some tables have triggers that prevent physical deletion. Decide whether to implement endpoints that do a logical (soft) delete if needed.
5. **Validation**: Each POST/PUT/PATCH endpoint should validate the incoming data. For example, check length constraints for fields like CURP or RFC.
