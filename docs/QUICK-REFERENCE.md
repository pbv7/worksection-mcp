# Worksection API Quick Reference

Quick reference guide for all Worksection API endpoints.

## OAuth2 Endpoints

| Name | Method | Path | Description |
|------|--------|------|-------------|
| oauth2_authorize | GET | /oauth2/authorize | Allows to get authorization code needed for token creation |
| oauth2_token | POST | /oauth2/token | Returns access and refresh tokens |
| oauth2_refresh | POST | /oauth2/refresh | Returns new access and refresh tokens |
| oauth2_resource | POST | /oauth2/resource | Returns authorized user's (oauth2) info |

## Client API Endpoints

### Comments

| Name | Action | Required Parameters | Description |
|------|--------|---------------------|-------------|
| get_comments | get_comments | id_task | Returns comments of selected task |
| post_comment | post_comment | id_task | Creates comment in selected task |

### Costs

| Name | Action | Required Parameters | Description |
|------|--------|---------------------|-------------|
| add_costs | add_costs | id_task | Creates individual costs for selected task |
| delete_costs | delete_costs | id_costs | Deletes selected individual costs of task |
| get_costs | get_costs | None | Returns individual costs added for selected or all tasks |
| get_costs_total | get_costs_total | None | Returns total costs added for selected or all tasks |
| update_costs | update_costs | id_costs | Updates selected individual costs of task |

### Files

| Name | Action | Required Parameters | Description |
|------|--------|---------------------|-------------|
| download | download | id_file | Downloads selected file |
| get_files | get_files | id_project | Returns files list of selected project or task |

### Members

| Name | Action | Required Parameters | Description |
|------|--------|---------------------|-------------|
| add_contact | add_contact | email, name | Creates new account contact |
| add_contact_group | add_contact_group | title | Creates account contacts folder |
| add_user | add_user | email | Invites new account user |
| add_user_group | add_user_group | title | Creates account user team |
| get_contact_groups | get_contact_groups | None | Returns account contact folders list |
| get_contacts | get_contacts | None | Returns account contacts info |
| get_user_groups | get_user_groups | None | Returns account user teams list |
| get_users | get_users | None | Returns account users info |
| me | me | None | Returns info about authorized user (oauth2) |
| subscribe | subscribe | id_task, email_user | Subscribes user to selected task |
| unsubscribe | unsubscribe | id_task, email_user | Unsubscribes user from selected task |

### Projects

| Name | Action | Required Parameters | Description |
|------|--------|---------------------|-------------|
| activate_project | activate_project | id_project | Activates selected archived project |
| add_project_group | add_project_groups | title | Creates projects folder |
| add_project_members | add_project_members | id_project, members | Adds account users to selected project team |
| close_project | close_project | id_project | Archives selected project |
| delete_project_members | delete_project_members | id_project, members | Removes account users from selected project team |
| get_events | get_events | period | Returns performed actions info in all or selected projects w |
| get_project | get_project | id_project | Returns selected project info |
| get_project_groups | get_project_groups | None | Returns all project folders info |
| get_projects | get_projects | None | Returns all projects info |
| post_project | post_project | title | Creates project |
| update_project | update_project | id_project | Updates selected project parameters |

### Tags

| Name | Action | Required Parameters | Description |
|------|--------|---------------------|-------------|
| add_project_tag_groups | add_project_tag_groups | title, access | Creates project tag groups |
| add_project_tags | add_project_tags | group, title | Creates project tags in selected group |
| add_task_tag_groups | add_task_tag_groups | type, access, title | Creates task tag groups |
| add_task_tags | add_task_tags | group, title | Creates task tags in selected group |
| get_project_tag_groups | get_project_tag_groups | None | Returns project tag groups |
| get_project_tags | get_project_tags | None | Returns project tags of all or selected group |
| get_task_tag_groups | get_task_tag_groups | None | Returns task tag groups |
| get_task_tags | get_task_tags | None | Returns task tags of all or selected group |
| update_project_tags | update_project_tags | id_project | Sets new and removes previously set tags for selected projec |
| update_task_tags | update_task_tags | id_task | Sets new and removes previously set tags for selected task |

### Tasks

| Name | Action | Required Parameters | Description |
|------|--------|---------------------|-------------|
| complete_task | complete_task | id_task | Completes selected (sub)task |
| get_all_tasks | get_all_tasks | None | Returns all incomplete and completed tasks of all projects |
| get_task | get_task | id_task | Returns selected incomplete or completed (sub)task |
| get_tasks | get_tasks | id_project | Returns all incomplete and completed tasks of selected proje |
| post_task | post_task | id_project, title | Creates (sub)task in selected project |
| reopen_task | reopen_task | id_task | Reopens selected completed (sub)task |
| search_tasks | search_tasks | None | Returns tasks that meet search query |
| update_task | update_task | id_task | Updates selected incomplete or completed (sub)task parameter |

### Timers

| Name | Action | Required Parameters | Description |
|------|--------|---------------------|-------------|
| get_my_timer | get_my_timer | None | Returns authorized user's (oauth2) active timer |
| get_timers | get_timers | None | Returns running timers info |
| start_my_timer | start_my_timer | id_task | Starts authorized user's (oauth2) timer in selected task |
| stop_my_timer | stop_my_timer | None | Stops and saves authorized user's (oauth2) active timer |
| stop_timer | stop_timer | timer | Stops and saves selected running timer |

### Webhooks

| Name | Action | Required Parameters | Description |
|------|--------|---------------------|-------------|
| add_webhook | add_webhook | url, events | Creates webhook |
| delete_webhook | delete_webhook | id | Deletes selected webhook |
| get_webhooks | get_webhooks | None | Returns webhooks list |

## Common Parameters

Frequently used parameters across endpoints:

- `id_project` - Project ID
- `id_task` - Task ID
- `id_tag` - Tag ID
- `email` / `email_user` - User email address
- `title` / `name` - Object title/name
- `text` - Text content (comments, descriptions)
- `date_start` / `date_end` - Date ranges
- `status` - Status identifier
- `priority` - Priority level

## Response Status Codes

| Code | Meaning |
|------|---------|
| 5 | Invalid object (project/task/tag) |
| 10 | Required field missing |
| 11 | Invalid field value (e.g., email) |
| 20 | Access denied |
| 30 | Object not found |