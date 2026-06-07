## ADDED Requirements

### Requirement: Users page component

The frontend SHALL include a `UsersView.vue` component in `frontend/src/views/` that displays the full list of users fetched from `GET /api/users`, renders each user's `username` and `email`, and provides inline Create, Edit, and Delete affordances.

#### Scenario: Users list renders on mount

- **WHEN** the Users view is mounted and `GET /api/users` returns a non-empty array
- **THEN** the component displays one row per user showing at minimum `username` and `email`

#### Scenario: Empty state

- **WHEN** the Users view is mounted and `GET /api/users` returns an empty array
- **THEN** the component displays a visible "No users yet" (or equivalent) message rather than a blank area

### Requirement: Create user form

The `UsersView.vue` component SHALL include an inline form with `username` and `email` input fields and a Submit button. Submitting the form SHALL call `POST /api/users`, clear the form on success, and re-fetch the user list. On `409` conflict, the component SHALL display the conflict error message to the user.

#### Scenario: Successful create updates list

- **WHEN** a user submits the create form with a unique username and email
- **THEN** `POST /api/users` is called, the form clears, and the new user appears in the list without a full page reload

#### Scenario: Conflict on create shows error

- **WHEN** a user submits the create form with a username or email already in use
- **THEN** the component displays an error message (e.g., "Username or email already exists") and does not clear the form

### Requirement: Edit user inline

The `UsersView.vue` component SHALL allow editing an existing user's `username` and `email` in place. Clicking "Edit" on a row SHALL make that row's fields editable; confirming SHALL call `PUT /api/users/{id}` and re-fetch the list; cancelling SHALL restore the original values.

#### Scenario: Edit saves changes

- **WHEN** the user clicks "Edit" on a row, modifies the email, and confirms
- **THEN** `PUT /api/users/{id}` is called with the updated email, the row exits edit mode, and the displayed email reflects the new value

#### Scenario: Cancel edit restores values

- **WHEN** the user clicks "Edit" then "Cancel" without saving
- **THEN** the row values are unchanged and no API call is made

### Requirement: Delete user with confirmation

The `UsersView.vue` component SHALL provide a Delete button per user row. Clicking Delete SHALL call `DELETE /api/users/{id}` and remove the row from the list on `204`. No additional confirmation dialog is required.

#### Scenario: Delete removes row from list

- **WHEN** the user clicks "Delete" on a row
- **THEN** `DELETE /api/users/{id}` is called and the row disappears from the list without a full page reload

### Requirement: API client module

The frontend SHALL expose a typed API client at `frontend/src/api/users.ts` exporting five functions: `listUsers(skip, limit)`, `getUser(id)`, `createUser(data)`, `updateUser(id, data)`, `deleteUser(id)`. Each function SHALL throw an `ApiError` with `status` and `message` fields on non-2xx responses. No third-party HTTP library SHALL be introduced.

#### Scenario: ApiError thrown on non-2xx

- **WHEN** `createUser` is called and the server returns `409`
- **THEN** the function throws an `ApiError` with `status === 409` and `message` equal to the error detail from the response body

### Requirement: Tab navigation in App.vue

`App.vue` SHALL render a two-tab navigation ("Health" and "Users") and conditionally render either `HealthCheck.vue` or `UsersView.vue` based on the active tab. The default active tab SHALL be "Health".

#### Scenario: Switching to Users tab shows UsersView

- **WHEN** the user clicks the "Users" tab
- **THEN** `UsersView.vue` is rendered and the user list is fetched

#### Scenario: Switching back to Health tab shows HealthCheck

- **WHEN** the user is on the "Users" tab and clicks "Health"
- **THEN** `HealthCheck.vue` is rendered and `UsersView.vue` is unmounted
