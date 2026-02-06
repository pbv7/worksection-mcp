# Worksection API Reference

This document provides comprehensive API reference for the Worksection API.

## Authentication

The Worksection API supports two authentication methods:

1. **OAuth2 Access Token** - For user-specific access with scoped permissions
2. **Admin API Token** - For administrative access to account data

## OAuth2 Authentication

OAuth2 endpoints for authorization and token management.

### oauth2_authorize

**Path:** `/oauth2/authorize`

**Method:** `GET`

**Description:** Allows to get authorization code needed for token creation

_\*after login to your Worksection account and approval page confirmation, you will be forwarded to specified Redirect URI with authorization code parameter_
_(code is valid for 10 minutes)_

**Parameters:**

- `client_id` (Required) - Client ID Your Worksection application unique ID

- `redirect_uri` (Required) - Redirect URI Must meet the requirements of the OAuth2 standard and use the HTTPS protocol

- `state` (Required) - Random text string. It will be included in the response to your application at the end of the OAuth stream.
  The main purpose is to prevent CSRF requests from being spoofed.

- `scope` (Required) - OAuth permissions. Defines which data in the Worksection your application will have access to.
  Available values (can be specified with commas):
  `projects_read|projects_write|tasks_read|tasks_write|costs_read|costs_write|tags_read|tags_write|comments_read|comments_write|files_read|files_write|users_read|users_write|contacts_read|contacts_write|administrative`

- `response_type` (Required) - Response type, possible value: code _code_ - returns the authorization code

---

### oauth2_token

**Path:** `/oauth2/token`

**Method:** `POST`

**Description:** Returns access and refresh tokens

_\*access_token is valid for 24 hours, refresh_token – 1 month_

**Parameters:**

- `client_id` (Required) - Client ID Your Worksection application unique ID

- `client_secret` (Required) - Client Secret Your Worksection application secret string

- `redirect_uri` (Required) - Redirect URI Must meet the requirements of the OAuth2 standard and use the HTTPS protocol

- `grant_type` (Required) - OAuth grant type, possible value: authorization_code

- `code` (Required) - Authorization code Can be obrained through _oauth2_authorize_ method

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "token_type": "Bearer",
    "expires_in": 86400,
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIwYTlkYTZhOTE4YWZhNGVkZjAwYWRkYjBkNDFjNTEyMCIsImp0aSI6ImJmOGVhZDNhYTMwMWUyNTYwZDI1ODA1MmY5MWY5MjRkNGIxMDJjYWE3MTYzYjBhOTIzN2NkODczMjBiN2NjNjFhZDdiNDA0YjNhMjljNTY4IiwiaWF0IjoxNjk5NjI3NDAyLCJuYmYiOjE2OTk2Mjc0MDIsImV4cCI6MTY5OTcxMzgwMiwic3ViIjoiMjQ3NyIsInNjb3BlcyI6WyJwcm9qZWN0c19yZWFkIiwicHJvamVjdHNfd3JpdGUiLCJ0YXNrc19yZWFkIiwidGFza3Nfd3JpdGUiLCJjb3N0c19yZWFkIiwiY29zdHNfd3JpdGUiLCJ0YWdzX3JlYWQiLCJ0YWdzX3dyaXRlIiwiY29tbWVudHNfcmVhZCIsImNvbW1lbnRzX3dyaXRlIiwiZmlsZXNfcmVhZCIsImZpbGVzX3dyaXRlIiwidXNlcnNfcmVhZCIsInVzZXJzX3dyaXRlIiwiY29udGFjdHNfcmVhZCIsImNvbnRhY3RzX3dyaXRlIiwiYWRtaW5pc3RyYXRpdmUiXX0.ki4Caqyg-aO5Hhl0mctERkEzssICAC06QjmKBLDWIFKf_0BLW9znOiap4_cIVXAZYpjzzd5J_WxhsYTEvQkBjFjeFxVvW8sGszilz08KMipVwbw_DtvXPPJGKA513wyE6B87oc9dTXIpKr7Ws7UZETUd1rbdj9NgNAB1ghpw5UIyIKfqWWYbomatdtAsFnB5ZAf-AJma74MDT0HHHPm02kbOtsifsHny9TbKmWvcmqtojHltdJC15E4LHHgnaA6QhxGs0tXf6nFv3nIoK-eT0YjaXe0YqbOYXhHtI6SD1L6LDKyUjDiKi0XCKI1XEtvLPjkE7NftG8bOIzlrMI4zRw",
    "refresh_token": "def502009eeae35083f65b344d980a855f9f9f456580e3676b993a85c7d7027e20f00474301f8b6355d26ac53187b3d58d871af2efbf96625aeac89bdf696366ec1ae05ddcc8efd6b23ef4806e16565b2eb3124fadaf71090bf344c5cf845ab045575a4567cec410ca98d87a8d68b275bfe880b28b56d9cb13965b60696457bf891db53215fcf98d83c66031b8cb2131784df67657fc8f5111ef781bd86dd17ea31dd6406a4474c20fddacd5946e974b0b1e4c8f5e181334bda96ba8903d15ea5c2be912a1b2187fe6954ca00a33edb9e255acf5a8fae152920d6ff06a23a6ac4c4e8ac176e9965c9db14df41b30519ae1fd0b84047e60e253e14326ca97269ef268e418897d7737c059cb9bdeb60361b8809ddc4eb5b470859bb96d7fed5919044162a111f9c4d12b4e30bf2b734e87635033ccd20a2d3725cb1e2d7e52b13b438251ed5d45dbbeda23a0bd7d6a7a363bb252ca3a3178d71f5dfa728669984b3ad0edd599c211cf7392d4dca3f30a7b1de11c0906b7a6ec44860eb91dc4e4b94f351a2c769a98fdc50c8d124cedf864fb831fd0eea215e05540d5c56325cfc97a76aa3c45c523b0c94149285c9c605983a3e9667b9ac700690a78f5e9510c11b9f18da65b8d989aab4050fc996355dc349d5989002738834edb211f180177a6169da75d90f17f0b0b74549e87c7cf0ccb8a5a2c28cd4e0ec75350645bad15a48e753a18397de3ecbff6ab24dcbf20982df2d823a9bfc70414f8bc3dba7cbdcec6d4e00eb9b92b02282a0dee2e3ecfd1ade93ea1a4454668130548d5ff4d1b4c631449df993da7d928ba03b40022182488d52523088743a35848b1436af8595f9f3db6c34f9f3390a9ab2feab33fe3eff29b9946df0dd96132a2af",
    "account_url": "https://acc1234.worksection.com"
  }
  ```

- **invalid_request** (OK - 200)

  ```json
  {
    "error": "invalid_request",
    "errorDescription": "Authorization code has been revoked"
  }
  ```

- **invalid_client** (OK - 200)

  ```json
  {
    "error": "invalid_client",
    "errorDescription": "Client authentication failed"
  }
  ```

---

### oauth2_refresh

**Path:** `/oauth2/refresh`

**Method:** `POST`

**Description:** Returns new access and refresh tokens

\*used when access token is about to expire or already expired  
_\*access_token is valid for 24 hours, refresh_token – 1 month_

**Parameters:**

- `client_id` (Required) - Client ID Your Worksection application unique ID

- `client_secret` (Required) - Client Secret Your Worksection application secret string

- `refresh_token` (Required) - Refresh token Can be obtained through _oauth2_token_ method

- `grant_type` (Required) - OAuth grant type, possible value: refresh_token

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "token_type": "Bearer",
    "expires_in": 86400,
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIwYTlkYTZhOTE4YWZhNGVkZjAwYWRkYjBkNDFjNTEyMCIsImp0aSI6IjM3MjMxZTYyMzM0N2I1NGJkOTc2NWIwNzE4YjU2ZDIyOWM5YTViMWZhOTVhNDc0ODVjYzM0NTNkYmViYmFmYmE2NjU1NDgxNWFkMDc5YzcxIiwiaWF0IjoxNjk5NjI3OTI5LCJuYmYiOjE2OTk2Mjc5MjksImV4cCI6MTY5OTcxNDMyOSwic3ViIjoiMjQ3NyIsInNjb3BlcyI6WyJwcm9qZWN0c19yZWFkIiwicHJvamVjdHNfd3JpdGUiLCJ0YXNrc19yZWFkIiwidGFza3Nfd3JpdGUiLCJjb3N0c19yZWFkIiwiY29zdHNfd3JpdGUiLCJ0YWdzX3JlYWQiLCJ0YWdzX3dyaXRlIiwiY29tbWVudHNfcmVhZCIsImNvbW1lbnRzX3dyaXRlIiwiZmlsZXNfcmVhZCIsImZpbGVzX3dyaXRlIiwidXNlcnNfcmVhZCIsInVzZXJzX3dyaXRlIiwiY29udGFjdHNfcmVhZCIsImNvbnRhY3RzX3dyaXRlIiwiYWRtaW5pc3RyYXRpdmUiXX0.E7e0Kx1vFzTjTkHDsrJRyjkjcZoWkJAoUnI2wCoF64BGCwWEVzSGhCNqpplEapH-s9c-6pokt18QDbkIieUZv9tpHgErwclg_R4ty3bif75zPd0GbzTTfhSaZRHN74uEP5VkrHiAMlMRy7p_SKvHNX9NBw03_q38OfsOLOdAnTaAriD28z8thZww0NImpkb_0r-bJrjr2c_bol-8s6YsG6sU-P4XRVIQj6hoHQ8GjtiT3KqC9dLD3jua8VFPpGblQ0YQsd14oPyzuBRjtQjiTIZcRkQLVVD2_3tRA8Mvkn1bvcnzJuBZB7YLGCvmHG1bXUt_nY72i1UOz7nBZWvs-g",
    "refresh_token": "def50200ad37fbada26e58119bbd880f7ff776a8ce06fe74502ed172e7fb02fd42fefb6ad6373883e6d51017234fcc6cbf7cd5b86b3e32f13e11360866baa1ebf57aad99bf9238c9316f946232362fc02966aa9d4d112c628ee0c8b82747bdaf36ad6228c8c07d54b41c447456b0ba2c96f8ad5f530183d14dfc379e21f129fc14601af30840232a3c6a1dc1e819ad6447f8c24cacd00f8ddd22dcfaf63ae13481c1cd5d3192aafa3b24710cd4591b8fe1c4c8e8d7cebf9426b0108a3087b3626d1dd517af31e21e8d4f2eee75bcbe682715d96fa83fde3ec87ed3ff531dc63081ab97e1b160237b5b08e51ffbd60b05700c57aa92e542d438d996829ef973ca8549803ba022a142cb47744896716d0d34ec35e2c2a1967673b1d99750b41fdc8cda57b18feba81dc2b37ce75bcd755afdc97e3e1d722046c6dfc7f71d711a69d964efcee6df6a6232cb001c27d44262b3e6de427f854f578905cef94149d990d4b1c45b288a8fd12483d1e619972f4079769596937a95e9823a34861cbe7be478c6da000608bd12400a0f4abdfb30c638d5adb5fba19a6843488dbd79d6eaf4a84c4f4f0299f2b0b8f277f9a3d55d4851bb97e3a8e05082e32bace4adf7690c0b95d36a479c0f3b2e0fe0fdcb51dab8680cea52f69659b7271c1ac0acb93fcb6fc68f20662cb20f4b3fd505638423262d48994f2ef8b8bb245795f2f86a3c5b732702f5fba5ff47f4217adbc6994361d9fdff9ff142b891286bd0a43c605cebbdb596c8a8213a5f5e73b3a9328274587a8f1e9c33bde3c07f5ef16daa15a7a30d82801e8925515fb8679372e8b7d5dfc2b02ccb5a5ff58170280cc5f1c0c6df6dbb7f48d4c5d456f3d07a73573fa443e5408002f3eefc9ef3c1e7"
  }
  ```

- **invalid_request** (OK - 200)

  ```json
  {
    "error": "invalid_request",
    "errorDescription": "Cannot decrypt the refresh token"
  }
  ```

---

### oauth2_resource

**Path:** `/oauth2/resource`

**Method:** `POST`

**Description:** Returns authorized user's (oauth2) info

**Parameters:**

- `client_id` (Required) - Client ID Your Worksection application unique ID

- `client_secret` (Required) - Client Secret Your Worksection application secret string

- `access_token` (Required) - Access token Can be obtained through _oauth2_token_ method

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "id": "3993",
    "first_name": "Henry",
    "last_name": "Gardner",
    "email": "henry.gardner@ws.com",
    "account_url": "https://acc1234.worksection.com"
  }
  ```

- **not_authorized** (OK - 200)

  ```json
  {
    "error": "not_authorized",
    "errorDescription": "Malformed UTF-8 characters"
  }
  ```

---

## Client API Endpoints

All Client API endpoints use the base URL: `{{account_url}}/api/`

Include your authentication token (admin token or OAuth2 access token) with each request.

## Comments

### get_comments

**Action:** `get_comments`

**Method:** `POST`

**Description:** Returns comments of selected task

**Parameters:**

- `id_task` (Required) - Task ID

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "id": "19086",
        "page": "/project/6622/330090/#com19086",
        "text": "Added one more file needed",
        "date_added": "2021-01-02 11:21",
        "user_from": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "files": [
          {
            "id": "17362",
            "size": "512596",
            "name": "Image file.png",
            "page": "/download/17362/"
          }
        ]
      },
      {
        "id": "19078",
        "page": "/project/6622/330090/#com19078",
        "text": "",
        "date_added": "2021-01-01 10:00",
        "user_from": {
          "id": "5514",
          "email": "frank.harper@ws.com",
          "name": "Frank Harper"
        },
        "files": [
          {
            "id": "17350",
            "size": "111303",
            "name": "Text file.docx",
            "page": "/download/17350/"
          },
          {
            "id": "17354",
            "size": "42669",
            "name": "Spreadsheet file.xlsx",
            "page": "/download/17354/"
          }
        ]
      }
    ]
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 5,
    "message": "Task is invalid"
  }
  ```

---

### post_comment

**Action:** `post_comment`

**Method:** `POST`

**Description:** Creates comment in selected task

_\*allows files attaching (see_ [details](https://worksection.com/en/faq/api-files.html#q1691)_)_

**Parameters:**

- `id_task` (Required) - Task ID

- `text` (Optional) - (Conditional) Comment text At least one of parameters required: _text, todo_

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "20478",
      "page": "/project/6622/330090/#com20478",
      "text": "Need info on the topic about your department\r\n\u2022 survey results\r\n\u2022 questions and suggestions\r\n\u2022 gamification and motivation Frank Harper",
      "date_added": "2021-01-03 09:17",
      "user_from": {
        "id": "3993",
        "email": "henry.gardner@ws.com",
        "name": "Henry Gardner"
      }
    }
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 5,
    "message": "Task is invalid"
  }
  ```

---

## Costs

### get_costs

**Action:** `get_costs`

**Method:** `POST`

**Description:** Returns individual costs added for selected or all tasks

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "raw": "{\n    \"status\": \"ok\",\n    \"data\": [\n        {\n            \"id\": \"3610\",\n            \"comment\": \"Developed new workflow scheme for dev team\",\n            \"time\": \"6:50\",\n            \"money\": \"75.17\",\n            \"date\": \"2021-01-01\",\n            \"is_timer\": true,\n            \"user_from\": {\n                \"id\": \"5514\",\n                \"email\": \"frank.harper@ws.com\",\n                \"name\": \"Frank Harper\"\n            },\n            \"task\": {\n                \"id\": \"330142\",\n                \"name\": \"Workflow revision\",\n                \"page\": \"/project/6622/330142/\",\n                \"status\": \"done\",\n                \"priority\": \"1\",\n                \"user_from\": {\n                    \"id\": \"3993\",\n                    \"email\": \"henry.gardner@ws.com\",\n                    \"name\": \"Henry Gardner\"\n                },\n                \"user_to\": {\n                    \"id\": \"5514\",\n                    \"email\": \"frank.harper@ws.com\",\n                    \"name\": \"Frank Harper\"\n                },\n                \"project\": {\n                    \"id\": \"6622\",\n                    \"name\": \"Performance improvement\",\n                    \"page\": \"/project/6622/\"\n                },\n                \"date_added\": \"2021-01-01 11:00\",\n                \"date_closed\": \"2021-01-02 12:43\"\n            }\n        },\n        {\n            \"id\": \"3686\",\n            \"comment\": \"\",\n            \"time\": \"3:22\",\n            \"money\": \"0.00\",\n            \"date\": \"2021-01-03\",\n            \"is_timer\": false,\n            \"user_from\": {\n                \"id\": \"3993\",\n                \"email\": \"henry.gardner@ws.com\",\n                \"name\": \"Henry Gardner\"\n            },\n            \"task\": {\n                \"id\": \"330090\",\n                \"name\": \"Worksection implementation\",\n                \"page\": \"/project/6622/330090/\",\n                \"status\": \"active\",\n                \"priority\": \"1\",\n                \"user_from\": {\n                    \"id\": \"3993\",\n                    \"email\": \"henry.gardner@ws.com\",\n                    \"name\": \"Henry Gardner\"\n                },\n                \"user_to\": {\n                    \"id\": \"2\",\n                    \"email\": \"ANY\",\n                    \"name\": \"Anyone\"\n                },\n                \"project\": {\n                    \"id\": \"6622\",\n                    \"name\": \"Performance improvement\",\n                    \"page\": \"/project/6622/\"\n                },\n                \"date_added\": \"2021-01-01 12:00\"\n            }\n        },\n\n    ],\n    \"total\": {\n        \"time\": \"10:12\",\n        \"money\": \"75.17\"\n    }\n}"
  }
  ```

---

### get_costs_total

**Action:** `get_costs_total`

**Method:** `POST`

**Description:** Returns total costs added for selected or all tasks

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "total": {
      "time": "103:39",
      "money": "5436.00"
    }
  }
  ```

---

### add_costs

**Action:** `add_costs`

**Method:** `POST`

**Description:** Creates individual costs for selected task

**Parameters:**

- `id_task` (Required) - Task ID

- `time` (Optional) - (Conditional) Time costs in one of the following formats: 0.15 / 0,15 / 0:09 At least one of parameters required: _time, money_

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "id": 3706
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 10,
    "message": "Field is required",
    "message_details": "time or money"
  }
  ```

---

### update_costs

**Action:** `update_costs`

**Method:** `POST`

**Description:** Updates selected individual costs of task

**Parameters:**

- `id_costs` (Required) - Cost ID Can be obtained through _get_costs_ method

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok"
  }
  ```

---

### delete_costs

**Action:** `delete_costs`

**Method:** `POST`

**Description:** Deletes selected individual costs of task

**Parameters:**

- `id_costs` (Required) - Cost ID Can be obtained through _get_costs_ method

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok"
  }
  ```

---

## Files

### get_files

**Action:** `get_files`

**Method:** `POST`

**Description:** Returns files list of selected project or task

_\*project files include attached to project description and directly to Files section  
\*task files include attached to task description and comments_

**Parameters:**

- `id_project` (Required) - Project ID Optional if Task ID selected

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "id": "16246",
        "page": "/download/16246/102/",
        "name": "Text file.docx",
        "size": "111303",
        "date_added": "2021-01-01 10:00",
        "user_from": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        }
      },
      {
        "id": "16242",
        "page": "/download/16242/",
        "name": "Image file.jpeg",
        "size": "73444",
        "date_added": "2022-01-01 10:00",
        "user_from": {
          "id": "5514",
          "email": "frank.harper@ws.com",
          "name": "Frank Harper"
        }
      }
    ]
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 4,
    "message": "Project is invalid"
  }
  ```

---

### download

**Action:** `download`

**Method:** `POST`

**Description:** Downloads selected file

_\*attached to project description, task description, comment or directly to Files section_

**Parameters:**

- `id_file` (Required) - File ID Can be obtained through _get_files_ method

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "raw": "Txt file\r\n\r\nLorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse vulputate facilisis pellentesque. Fusce massa magna, tempus id sapien id, maximus dictum neque. Etiam imperdiet felis vitae diam placerat, at feugiat risus pulvinar. Quisque in mi pretium metus tincidunt feugiat a sit amet nibh. Nullam porta quis massa sit amet gravida. Integer ullamcorper, nisl quis dapibus dapibus, mauris orci imperdiet tellus, ac porttitor metus eros scelerisque elit. Pellentesque nec imperdiet lectus.\r\n\r\nSed laoreet sagittis massa, vitae consectetur felis placerat in. Donec elementum tortor et suscipit rhoncus. Nulla facilisi. In pulvinar tincidunt massa, eu mollis ligula. Phasellus eu rhoncus est, id maximus lectus. Aenean finibus ac felis sed eleifend. Nullam quis vestibulum justo, eu ullamcorper justo.\r\n\r\nQuisque a tempus magna, et commodo sapien. Sed sit amet accumsan diam. Etiam blandit velit vel ipsum imperdiet maximus. Integer rhoncus purus pellentesque risus vulputate, in consequat nulla consectetur. Nulla vitae sodales risus. Sed sagittis, urna ut pretium egestas, libero nulla feugiat ex, quis consectetur quam purus id nulla. Nam tincidunt tincidunt finibus. Vestibulum ut pellentesque nisl, maximus gravida eros. Duis vel porta felis, vitae feugiat dolor. Fusce ut pulvinar metus. In hac habitasse platea dictumst. Donec vitae nulla sit amet ante mollis sagittis fringilla non libero. Morbi cursus dapibus velit sit amet malesuada. Aliquam fringilla nisl ut diam iaculis pellentesque cursus ac sapien."
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 4,
    "message": "File not found"
  }
  ```

---

## Members

### me

**Action:** `me`

**Method:** `POST`

**Description:** Returns info about authorized user (oauth2)

**!! User method (only for access token) !!**

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "3993",
      "first_name": "Henry",
      "last_name": "Gardner",
      "name": "Henry Gardner",
      "title": "developer",
      "avatar": "https://acc1234.worksection.com/images/user/246965/3993_2001.jpg",
      "group": "Development",
      "department": "Dev team",
      "role": "Owner",
      "email": "henry.gardner@ws.com",
      "phone": "+15852827023",
      "phone2": "4 4950 234 45 90",
      "phone3": "1 (049) 143-235-08",
      "phone4": "5989 243 88 1",
      "address": "Apt. 902 853 Simona Common, Pollybury, SC 98466-2410",
      "address2": "Suite 329 958 Lashell Branch, Mayertview, SC 07180"
    }
  }
  ```

---

### get_users

**Action:** `get_users`

**Method:** `POST`

**Description:** Returns account users info

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "id": "3993",
        "first_name": "Henry",
        "last_name": "Gardner",
        "name": "Henry Gardner",
        "title": "developer",
        "rate": 25,
        "avatar": "https://acc1234.worksection.com/images/user/246965/3993_2001.jpg",
        "group": "Development",
        "department": "Dev team",
        "role": "Owner",
        "email": "henry.gardner@ws.com",
        "phone": "+15852827023",
        "phone2": "4 4950 234 45 90",
        "phone3": "1 (049) 143 235 08",
        "phone4": "5989 243 88 1",
        "address": "Apt. 902 853 Simona Common, Pollybury, SC 98466-2410",
        "address2": "Suite 329 958 Lashell Branch, Mayertview, SC 07180"
      },
      {
        "id": "5514",
        "first_name": "Frank",
        "last_name": "Harper",
        "name": "Frank Harper",
        "title": "QA specialist",
        "rate": 11,
        "avatar": "https://acc1234.worksection.com/images/user/0m.gif",
        "group": "Development",
        "department": "Test team",
        "role": "Account admin",
        "email": "frank.harper@ws.com"
      },
      {
        "id": "5674",
        "first_name": "John Doe",
        "last_name": "John Doe",
        "name": "John Doe",
        "title": "PM",
        "rate": 11,
        "avatar": "https://acc1234.worksection.com/images/avatar/mail/av_9_40.gif",
        "group": "Singing bird",
        "department": "",
        "role": "User",
        "email": "5674@5674.worksection.com"
      }
    ]
  }
  ```

---

### add_user

**Action:** `add_user`

**Method:** `POST`

**Description:** Invites new account user

_\*into your team if 'group' parameter is not specified_

**Parameters:**

- `email` (Required) - User email

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "5686",
      "first_name": "kate",
      "last_name": "greenway",
      "name": "kate greenway",
      "title": "",
      "rate": 11,
      "avatar": "https://acc1234.worksection.com/images/user/0f.gif",
      "group": "Development",
      "department": "",
      "role": "User",
      "email": "kate.greenway@ws.com"
    }
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 10,
    "message": "Field is required",
    "message_details": "email"
  }
  ```

---

### get_user_groups

**Action:** `get_user_groups`

**Method:** `POST`

**Description:** Returns account user teams list

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "id": "2977",
        "title": "Development",
        "type": "company",
        "client": 0
      },
      {
        "id": "4186",
        "title": "Singing bird",
        "type": "company",
        "client": 1
      }
    ]
  }
  ```

---

### add_user_group

**Action:** `add_user_group`

**Method:** `POST`

**Description:** Creates account user team

_\*if there are no teams with same name_

**Parameters:**

- `title` (Required) - Team name

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "4190",
      "title": "Marketing",
      "type": "company",
      "client": 0
    }
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 10,
    "message": "Field is required",
    "message_details": "title"
  }
  ```

---

### get_contacts

**Action:** `get_contacts`

**Method:** `POST`

**Description:** Returns account contacts info

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "id": "5606",
        "first_name": "Brian",
        "last_name": "Dragonfly",
        "name": "Brian Dragonfly",
        "title": "manager",
        "group": "Clients",
        "email": "brian.dragonfly@gmail.com",
        "phone": "1 345 234 23 67",
        "phone2": "486 09 77",
        "phone3": "(8984) 345 65 02",
        "phone4": "389 87 35",
        "address": "Apt. 406 855 Renner Trail, Rowemouth, IN 42165",
        "address2": "59064 Robby Prairie, North Abel, NE 93368"
      },
      {
        "id": "5614",
        "first_name": "Steve",
        "last_name": "Powerhold",
        "name": "Steve Powerhold",
        "title": "",
        "group": "Contractors",
        "phone": "1265 458 32 12"
      },
      {
        "id": "5658",
        "first_name": "Mike",
        "last_name": "Shaw",
        "name": "Mike Shaw",
        "title": "",
        "group": "DEFAULT",
        "email": "mike.shaw@gmail.com"
      }
    ]
  }
  ```

---

### add_contact

**Action:** `add_contact`

**Method:** `POST`

**Description:** Creates new account contact

_\*no invitation sent_

**Parameters:**

- `email` (Required) - Contact email

- `name` (Required) - Contact name

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "5614",
      "first_name": "Brian",
      "last_name": "Dragonfly",
      "name": "Brian Dragonfly",
      "title": "manager",
      "group": "Clients",
      "email": "brian.dragonfly@gmail.com",
      "phone": "1 345 234 23 67",
      "phone2": "486 09 77",
      "phone3": "(8984) 345 65 02",
      "phone4": "389 87 35",
      "address": "Apt. 406 855 Renner Trail, Rowemouth, IN 42165",
      "address2": "59064 Robby Prairie, North Abel, NE 93368"
    }
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 11,
    "message": "Invalid email",
    "message_details": "brian.dragonfly@gmail.com,mike.showcase@gmail.com"
  }
  ```

---

### get_contact_groups

**Action:** `get_contact_groups`

**Method:** `POST`

**Description:** Returns account contact folders list

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "id": 1,
        "title": "USERS",
        "type": "preset"
      },
      {
        "id": 2,
        "title": "DEFAULT",
        "type": "preset"
      },
      {
        "id": 3,
        "title": "TEAM_ONLY",
        "type": "preset"
      },
      {
        "id": 4,
        "title": "HIDDEN",
        "type": "preset"
      },
      {
        "id": "4178",
        "title": "Clients",
        "type": "folder"
      }
    ]
  }
  ```

---

### add_contact_group

**Action:** `add_contact_group`

**Method:** `POST`

**Description:** Creates account contacts folder

_\*if there are no folders with same name_

**Parameters:**

- `title` (Required) - Contacts folder name

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "4182",
      "title": "Contractors",
      "type": "folder"
    }
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 10,
    "message": "Field is required",
    "message_details": "title"
  }
  ```

---

### subscribe

**Action:** `subscribe`

**Method:** `POST`

**Description:** Subscribes user to selected task

_\*task subscribers list can be obtained through 'get_task' method with 'extra=subscribers' parameter_

**Parameters:**

- `id_task` (Required) - Task ID

- `email_user` (Required) - User email

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok"
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 11,
    "message": "Invalid email",
    "message_details": "henry.gardner@ws.com,frank.harper@ws.com"
  }
  ```

---

### unsubscribe

**Action:** `unsubscribe`

**Method:** `POST`

**Description:** Unsubscribes user from selected task

_\*task subscribers list can be obtained through 'get_task' method with 'extra=subscribers' parameter_

**Parameters:**

- `id_task` (Required) - Task ID

- `email_user` (Required) - User email

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok"
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 11,
    "message": "Invalid email",
    "message_details": "henry.gardner@ws.com,frank.harper@ws.com"
  }
  ```

---

## Projects

### get_projects

**Action:** `get_projects`

**Method:** `POST`

**Description:** Returns all projects info

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "raw": "{\n    \"status\": \"ok\",\n    \"data\": [\n        {\n            \"id\": \"6622\",\n            \"name\": \"Performance improvement\",\n            \"page\": \"/project/6622/\",\n            \"status\": \"active\",\n            \"company\": \"Development\",\n            \"user_from\": {\n                \"id\": \"3993\",\n                \"email\": \"henry.gardner@ws.com\",\n                \"name\": \"Henry Gardner\"\n            },\n            \"user_to\": {\n                \"id\": \"3993\",\n                \"email\": \"henry.gardner@ws.com\",\n                \"name\": \"Henry Gardner\"\n            },\n            \"text\": \"Inner project for company KPI improvement\",\n            \"date_added\": \"2021-01-01 10:18\",\n            \"date_start\": \"2021-01-01\",\n            \"date_end\": \"2021-07-01\",\n            \"options\": {\n                \"allow_close\": 1,\n                \"allow_give\": 1,\n                \"allow_term\": 0,\n                \"allow_limit\": 0,\n                \"require_term\": 1,\n                \"require_tag\": 1,\n                \"require_limit\": 1,\n                \"require_hidden\": 0,\n                \"deny_comments_edit\": 0,\n                \"deny_task_edit\": 0,\n                \"deny_task_delete\": 1,\n                \"time_require\": 0,\n                \"time_today\": 0,\n                \"timer_only\": 1\n            },\n            \"max_time\": 1200,\n            \"max_money\": 20400,\n            \"tags\": {\n                \"105554\": \"inner\",\n                \"105570\": \"wiki\"\n            },\n            \"users\": [\n                {\n                    \"id\": \"3993\",\n                    \"email\": \"henry.gardner@ws.com\",\n                    \"name\": \"Henry Gardner\"\n                },\n                {\n                    \"id\": \"5514\",\n                    \"email\": \"frank.harper@ws.com\",\n                    \"name\": \"Frank Harper\"\n                },\n                {\n                    \"id\": \"5686\",\n                    \"email\": \"kate.greenway@ws.com\",\n                    \"name\": \"Kate Greenway\"\n                }\n            ]\n        },\n        {\n            \"id\": \"8506\",\n            \"name\": \"Prototyping\",\n            \"page\": \"/project/8506/\",\n            \"status\": \"pending\",\n            \"company\": \"Development\",\n            \"user_from\": {\n                \"id\": \"5686\",\n                \"email\": \"kate.greenway@ws.com\",\n                \"name\": \"Kate Greenway\"\n            },\n            \"user_to\": {\n                \"id\": \"0\",\n                \"email\": \"NOONE\",\n                \"name\": \"Manager isn't assigned\"\n            },\n            \"text\": \"\",\n            \"date_added\": \"2021-01-05 16:21\",\n            \"options\": {\n                \"allow_close\": 1,\n                \"allow_give\": 0,\n                \"allow_term\": 0,\n                \"allow_limit\": 0,\n                \"require_term\": 0,\n                \"require_tag\": 0,\n                \"require_limit\": 0,\n                \"require_hidden\": 0,\n                \"deny_comments_edit\": 0,\n                \"deny_task_edit\": 0,\n                \"deny_task_delete\": 0,\n                \"time_require\": 0,\n                \"time_today\": 0,\n                \"timer_only\": 0\n            },\n            \"users\": [\n                {\n                    \"id\": \"5686\",\n                    \"email\": \"kate.greenway@ws.com\",\n                    \"name\": \"Kate Greenway\"\n                }\n            ]\n        },\n    ]\n}"
  }
  ```

---

### get_project

**Action:** `get_project`

**Method:** `POST`

**Description:** Returns selected project info

**Parameters:**

- `id_project` (Required) - Project ID

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "6622",
      "name": "Performance improvement",
      "page": "/project/6622/",
      "status": "active",
      "company": "Development",
      "user_from": {
        "id": "3993",
        "email": "henry.gardner@ws.com",
        "name": "Henry Gardner"
      },
      "user_to": {
        "id": "5686",
        "email": "kate.greenway@ws.com",
        "name": "Kate Greenway"
      },
      "text": "Inner project for company KPI improvement",
      "date_added": "2021-01-01 10:18",
      "date_start": "2021-01-01",
      "date_end": "2021-07-01",
      "options": {
        "allow_close": 1,
        "allow_give": 1,
        "allow_term": 0,
        "allow_limit": 0,
        "require_term": 1,
        "require_tag": 1,
        "require_limit": 1,
        "require_hidden": 0,
        "deny_comments_edit": 0,
        "deny_task_edit": 0,
        "deny_task_delete": 1,
        "time_require": 0,
        "time_today": 0,
        "timer_only": 1
      },
      "max_time": 1200,
      "max_money": 20400,
      "tags": {
        "105554": "inner",
        "105570": "wiki"
      },
      "users": [
        {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        {
          "id": "5514",
          "email": "frank.harper@ws.com",
          "name": "Frank Harper"
        },
        {
          "id": "5686",
          "email": "kate.greenway@ws.com",
          "name": "Kate Greenway"
        }
      ]
    }
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 4,
    "message": "Project is invalid"
  }
  ```

---

### post_project

**Action:** `post_project`

**Method:** `POST`

**Description:** Creates project

_\*allows files attaching to project description (see_ [details](https://worksection.com/en/faq/api-files.html#q1691)_)_

**Parameters:**

- `title` (Required) - Project name

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "8838",
      "name": "New brand launch",
      "page": "/project/8838/",
      "status": "active",
      "company": "Marketing",
      "user_from": {
        "id": "3993",
        "email": "henry.gardner@ws.com",
        "name": "Henry Gardner"
      },
      "user_to": {
        "id": "5514",
        "email": "frank.harper@ws.com",
        "name": "Frank Harper"
      },
      "date_added": "2021-01-23 10:51",
      "date_start": "2021-02-01",
      "date_end": "2021-03-01",
      "options": {
        "allow_close": 1,
        "allow_give": 1,
        "allow_term": 0,
        "allow_limit": 0,
        "require_term": 1,
        "require_tag": 1,
        "require_limit": 1,
        "require_hidden": 0,
        "deny_comments_edit": 0,
        "deny_task_edit": 0,
        "deny_task_delete": 0,
        "time_require": 0,
        "time_today": 0,
        "timer_only": 1
      },
      "max_time": 352,
      "max_money": 4224,
      "tags": {
        "105118": "paid",
        "105126": "contract"
      }
    }
  }
  ```

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "8530",
      "name": "New brand launch",
      "page": "/project/8530/",
      "status": "active",
      "company": "Development",
      "user_from": {
        "id": "3993",
        "email": "henry.gardner@ws.com",
        "name": "Henry Gardner"
      },
      "user_to": {
        "id": "0",
        "email": "NOONE",
        "name": "Manager isn't assigned"
      },
      "date_added": "2021-02-15 14:25",
      "options": {
        "allow_close": 0,
        "allow_give": 0,
        "allow_term": 0,
        "allow_limit": 0,
        "require_term": 0,
        "require_tag": 0,
        "require_limit": 0,
        "require_hidden": 0,
        "deny_comments_edit": 0,
        "deny_task_edit": 0,
        "deny_task_delete": 0,
        "time_require": 0,
        "time_today": 0,
        "timer_only": 0
      }
    }
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 11,
    "message": "Only one parameter (options.time_require or options.time_today or options.timer_only) can be set as 1."
  }
  ```

---

### update_project

**Action:** `update_project`

**Method:** `POST`

**Description:** Updates selected project parameters

**Parameters:**

- `id_project` (Required) - Project ID

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "8530",
      "name": "Owl brand launch",
      "page": "/project/8530/",
      "status": "active",
      "company": "Development",
      "user_from": {
        "id": "3993",
        "email": "henry.gardner@ws.com",
        "name": "Henry Gardner"
      },
      "user_to": {
        "id": "0",
        "email": "NOONE",
        "name": "Manager isn't assigned"
      },
      "date_added": "2021-02-15 14:25"
    }
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 11,
    "message": "Only one parameter (options.time_require or options.time_today or options.timer_only) can be set as 1."
  }
  ```

---

### close_project

**Action:** `close_project`

**Method:** `POST`

**Description:** Archives selected project

**Parameters:**

- `id_project` (Required) - Project ID

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok"
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 12,
    "message": "Project is already closed"
  }
  ```

---

### activate_project

**Action:** `activate_project`

**Method:** `POST`

**Description:** Activates selected archived project

**Parameters:**

- `id_project` (Required) - Project ID

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok"
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 12,
    "message": "Project is already active"
  }
  ```

---

### add_project_members

**Action:** `add_project_members`

**Method:** `POST`

**Description:** Adds account users to selected project team

**Parameters:**

- `id_project` (Required) - Project ID

- `members` (Required) - User emails separated by commas

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok"
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 11,
    "message": "Invalid email",
    "message_details": "brian.dragonfly@gmail.com"
  }
  ```

---

### delete_project_members

**Action:** `delete_project_members`

**Method:** `POST`

**Description:** Removes account users from selected project team

**Parameters:**

- `id_project` (Required) - Project ID

- `members` (Required) - User emails separated by commas

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok"
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 11,
    "message": "Invalid email",
    "message_details": "brian.dragonfly@gmail.com"
  }
  ```

---

### get_project_groups

**Action:** `get_project_groups`

**Method:** `POST`

**Description:** Returns all project folders info

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "id": "4302",
        "title": "Design",
        "type": "folder"
      },
      {
        "id": "2977",
        "title": "Development",
        "type": "company",
        "client": 0
      },
      {
        "id": "4190",
        "title": "Marketing",
        "type": "company",
        "client": 0
      },
      {
        "id": "4186",
        "title": "Singing bird",
        "type": "company",
        "client": 1
      }
    ]
  }
  ```

---

### add_project_group

**Action:** `add_project_groups`

**Method:** `POST`

**Description:** Creates projects folder

_\*if there are no folders with same name_

**Parameters:**

- `title` (Required) - Project folder name

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "4314",
      "title": "Outsource",
      "type": "folder"
    }
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 10,
    "message": "Field is required",
    "message_details": "title"
  }
  ```

---

### get_events

**Action:** `get_events`

**Method:** `POST`

**Description:** Returns performed actions info in all or selected projects within selected time period

_\*info on who made changes, what changed and when_

**Better use webhooks instead** (see [details](https://worksection.com/en/faq/webhooks.html)).

**Parameters:**

- `period` (Required) - Time period, possible values: 1m..360m|1h..72h|1d..30d _1m..360m_ - in minutes _1h..72h_ - in hours _1d..30d_ - in days
  - Possible values: `1m..360m, 1h..72h, 1d..30d`

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "action": "post",
        "object": {
          "type": "project",
          "id": "8506",
          "page": "/project/8506/"
        },
        "date_added": "2021-01-02 10:16",
        "user_from": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "new": {
          "title": "Prototyping",
          "user_to": {
            "id": "3993",
            "email": "henry.gardner@ws.com",
            "name": "Henry Gardner"
          }
        }
      },
      {
        "action": "post",
        "object": {
          "type": "comment",
          "id": "19870",
          "page": "/project/6622/330090/"
        },
        "date_added": "2021-01-02 11:07",
        "user_from": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "new": {
          "text": "Today we have a meetup. Please, prepare your department results."
        }
      },
      {
        "action": "update",
        "object": {
          "type": "task",
          "id": "331786",
          "page": "/project/6622/331786/"
        },
        "date_added": "2021-01-02 14:37",
        "user_from": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "new": {
          "priority": "7",
          "user_to": {
            "id": "5514",
            "email": "frank.harper@ws.com",
            "name": "Frank Harper"
          },
          "date_end": "2024-01-11",
          "time_end": "16:00"
        },
        "old": {
          "priority": "1",
          "user_to": {
            "id": "2",
            "email": "ANY",
            "name": "Anyone"
          },
          "date_end": "",
          "time_end": ""
        }
      },
      {
        "action": "close",
        "object": {
          "type": "task",
          "id": "330142",
          "page": "/project/6622/330142/"
        },
        "date_added": "2021-01-02 15:54",
        "user_from": {
          "id": "5514",
          "email": "frank.harper@ws.com",
          "name": "Frank Harper"
        }
      }
    ]
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 10,
    "message": "Field is required",
    "message_details": "period"
  }
  ```

---

## Tags

### get_task_tags

**Action:** `get_task_tags`

**Method:** `POST`

**Description:** Returns task tags of all or selected group

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "title": "To-do",
        "id": 72565,
        "group": {
          "title": "Basic workflow",
          "id": 100,
          "id_group": "1",
          "type": "status",
          "access": "public"
        }
      },
      {
        "title": "In progress",
        "id": 72569,
        "group": {
          "title": "Basic workflow",
          "id": 100,
          "id_group": "1",
          "type": "status",
          "access": "public"
        }
      },
      {
        "title": "Need approval",
        "id": 72573,
        "group": {
          "title": "Basic workflow",
          "id": 100,
          "id_group": "1",
          "type": "status",
          "access": "public"
        }
      },
      {
        "title": "Done",
        "id": 72577,
        "group": {
          "title": "Basic workflow",
          "id": 100,
          "id_group": "1",
          "type": "status",
          "access": "public"
        }
      }
    ]
  }
  ```

---

### add_task_tags

**Action:** `add_task_tags`

**Method:** `POST`

**Description:** Creates task tags in selected group

_\*if there are no tags with the same name_

**Parameters:**

- `group` (Required) - Group where task tags will be created.
  You can specify the group name or its ID (can be obtained through _get_task_tag_groups_ method).

- `title` (Required) - Task tag names separated by commas

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "title": "bug",
        "id": 104978
      },
      {
        "title": "feature",
        "id": 104982
      },
      {
        "title": "design",
        "id": 104986
      }
    ]
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 10,
    "message": "Field is required",
    "message_details": "group (id or title)"
  }
  ```

---

### update_task_tags

**Action:** `update_task_tags`

**Method:** `POST`

**Description:** Sets new and removes previously set tags for selected task

**Parameters:**

- `id_task` (Required) - Task ID

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok"
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 16,
    "message": "Tag is invalid",
    "message_details": "docs"
  }
  ```

---

### get_task_tag_groups

**Action:** `get_task_tag_groups`

**Method:** `POST`

**Description:** Returns task tag groups

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "title": "Basic workflow",
        "id": 100,
        "type": "status",
        "access": "public"
      },
      {
        "title": "Sales",
        "id": 104,
        "type": "status",
        "access": "public"
      },
      {
        "title": "Finance",
        "id": 105,
        "type": "label",
        "access": "public"
      },
      {
        "title": "General labels",
        "id": 101,
        "type": "label",
        "access": "public"
      },
      {
        "title": "Time tracking types",
        "id": 106,
        "type": "label",
        "access": "public"
      },
      {
        "title": "Task results",
        "id": 102,
        "type": "label",
        "access": "private"
      }
    ]
  }
  ```

---

### add_task_tag_groups

**Action:** `add_task_tag_groups`

**Method:** `POST`

**Description:** Creates task tag groups

_\*if there are no tag groups with same name_

**Parameters:**

- `type` (Required) - Group type, possible values: status|label
  - Possible values: `status, label`

- `access` (Required) - Tag group visibility (statuses are always visible and have public value), possible values: `public|private`.
  _public_ - available to all teams (including external client teams). _private_ - available only for your company teams.
  - Possible values: `public, private`

- `title` (Required) - Group names separated by commas

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "title": "Development",
        "id": 110,
        "type": "label",
        "access": "public"
      },
      {
        "title": "Marketing",
        "id": 111,
        "type": "label",
        "access": "public"
      }
    ]
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 10,
    "message": "Field is required",
    "message_details": "title"
  }
  ```

---

### get_project_tags

**Action:** `get_project_tags`

**Method:** `POST`

**Description:** Returns project tags of all or selected group

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "title": "Backlog",
        "id": 105114,
        "group": {
          "title": "Project status",
          "id": 97,
          "id_group": "-4",
          "type": "status",
          "access": "public"
        }
      },
      {
        "title": "In progress",
        "id": 105098,
        "group": {
          "title": "Project status",
          "id": 97,
          "id_group": "-4",
          "type": "status",
          "access": "public"
        }
      },
      {
        "title": "Paused",
        "id": 105106,
        "group": {
          "title": "Project status",
          "id": 97,
          "id_group": "-4",
          "type": "status",
          "access": "public"
        }
      },
      {
        "title": "Canceled",
        "id": 105110,
        "group": {
          "title": "Project status",
          "id": 97,
          "id_group": "-4",
          "type": "status",
          "access": "public"
        }
      },
      {
        "title": "Completed",
        "id": 105102,
        "group": {
          "title": "Project status",
          "id": 97,
          "id_group": "-4",
          "type": "status",
          "access": "public"
        }
      }
    ]
  }
  ```

---

### add_project_tags

**Action:** `add_project_tags`

**Method:** `POST`

**Description:** Creates project tags in selected group

_\*if there are no tags with the same name_

**Parameters:**

- `group` (Required) - Group where project tags will be created.
  You can specify the group name or its ID (can be obtained through _get_project_tag_groups_ method).

- `title` (Required) - Project tag names separated by commas

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "title": "paid",
        "id": 105118
      },
      {
        "title": "bill",
        "id": 105122
      },
      {
        "title": "contract",
        "id": 105126
      }
    ]
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 10,
    "message": "Field is required",
    "message_details": "group (id or title)"
  }
  ```

---

### update_project_tags

**Action:** `update_project_tags`

**Method:** `POST`

**Description:** Sets new and removes previously set tags for selected project

**Parameters:**

- `id_project` (Required) - Project ID

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok"
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 16,
    "message": "Tag is invalid",
    "message_details": "declined"
  }
  ```

---

### get_project_tag_groups

**Action:** `get_project_tag_groups`

**Method:** `POST`

**Description:** Returns project tag groups

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "title": "Project status",
        "id": 97,
        "type": "status",
        "access": "public"
      },
      {
        "title": "Common labels",
        "id": 98,
        "type": "label",
        "access": "public"
      },
      {
        "title": "Internal labels",
        "id": 99,
        "type": "label",
        "access": "private"
      }
    ]
  }
  ```

---

### add_project_tag_groups

**Action:** `add_project_tag_groups`

**Method:** `POST`

**Description:** Creates project tag groups

_\*if there are no tags with the same name_

**Parameters:**

- `title` (Required) - Group names separated by commas

- `access` (Required) - Tag group visibility, possible values: `public|private`.
  _public_ - available to all teams (including external client teams). _private_ - available only for your company teams.
  - Possible values: `public, private`

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "title": "Budget level",
        "id": 113,
        "type": "",
        "access": "public"
      },
      {
        "title": "Devs number",
        "id": 114,
        "type": "",
        "access": "public"
      }
    ]
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 10,
    "message": "Field is required",
    "message_details": "title"
  }
  ```

---

## Tasks

### get_all_tasks

**Action:** `get_all_tasks`

**Method:** `POST`

**Description:** Returns all incomplete and completed tasks of all projects

_\*except tasks with delayed publication  
\*subtasks can be returned with extra=subtasks parameter_

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "id": "331894",
        "name": "Development",
        "page": "/project/8562/331894/",
        "status": "active",
        "priority": "7",
        "user_from": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "user_to": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "project": {
          "id": "8562",
          "name": "Owl brand launch",
          "page": "/project/8562/"
        },
        "text": "Business logic programming",
        "date_added": "2021-01-07 10:01",
        "date_start": "2021-01-16",
        "date_end": "2021-02-16",
        "time_start": "08:00",
        "time_end": "18:00",
        "max_time": 352,
        "max_money": 5280,
        "files": [
          {
            "id": "17694",
            "page": "/download/17694/",
            "name": "Development requirements.doc",
            "size": "27136"
          },
          {
            "id": "17698",
            "page": "/download/17698/",
            "name": "Development progress.xlsx",
            "size": "10698"
          }
        ],
        "has_comments": 1,
        "comments": [
          {
            "id": "19978",
            "page": "/project/8562/331894/#com19978",
            "text": "Thanks, first section done",
            "date_added": "2021-01-07 16:38",
            "user_from": {
              "id": "5514",
              "email": "frank.harper@ws.com",
              "name": "Frank Harper"
            }
          },
          {
            "id": "19974",
            "page": "/project/8562/331894/#com19974",
            "text": "As usual",
            "date_added": "2021-01-07 11:15",
            "user_from": {
              "id": "3993",
              "email": "henry.gardner@ws.com",
              "name": "Henry Gardner"
            }
          },
          {
            "id": "19962",
            "page": "/project/8562/331894/#com19962",
            "text": "And what about development\u00a0environment?",
            "date_added": "2021-01-07 11:10",
            "user_from": {
              "id": "5514",
              "email": "frank.harper@ws.com",
              "name": "Frank Harper"
            }
          },
          {
            "id": "19954",
            "page": "/project/8562/331894/#com19954",
            "text": "Need your help with first section",
            "date_added": "2021-01-07 11:04",
            "user_from": {
              "id": "5514",
              "email": "frank.harper@ws.com",
              "name": "Frank Harper"
            }
          },
          {
            "id": "19950",
            "page": "/project/8562/331894/#com19950",
            "text": "Updated development requirements",
            "date_added": "2021-01-07 10:33",
            "user_from": {
              "id": "3993",
              "email": "henry.gardner@ws.com",
              "name": "Henry Gardner"
            }
          }
        ],
        "relations": {
          "from": [
            {
              "type": "finish-to-start",
              "task": {
                "id": "331902",
                "name": "Prototyping",
                "page": "/project/8562/331902/",
                "status": "active",
                "priority": "1"
              }
            }
          ],
          "to": [
            {
              "type": "finish-to-start",
              "task": {
                "id": "331906",
                "name": "Testing",
                "page": "/project/8562/331906/",
                "status": "active",
                "priority": "1"
              }
            }
          ]
        },
        "child": [
          {
            "id": "331910",
            "name": "Sprint 1",
            "page": "/project/8562/331894/331910/",
            "status": "active",
            "priority": "1",
            "user_from": {
              "id": "3993",
              "email": "henry.gardner@ws.com",
              "name": "Henry Gardner"
            },
            "user_to": {
              "id": "3993",
              "email": "henry.gardner@ws.com",
              "name": "Henry Gardner"
            },
            "project": {
              "id": "8562",
              "name": "Owl brand launch",
              "page": "/project/8562/"
            },
            "text": "",
            "date_added": "2021-01-07 10:05",
            "has_comments": 0,
            "child": [
              {
                "id": "331914",
                "name": "Subsprint 1.1",
                "page": "/project/8562/331894/331914/",
                "status": "active",
                "priority": "1",
                "user_from": {
                  "id": "3993",
                  "email": "henry.gardner@ws.com",
                  "name": "Henry Gardner"
                },
                "user_to": {
                  "id": "3993",
                  "email": "henry.gardner@ws.com",
                  "name": "Henry Gardner"
                },
                "project": {
                  "id": "8562",
                  "name": "Owl brand launch",
                  "page": "/project/8562/"
                },
                "text": "",
                "date_added": "2021-01-07 10:07",
                "has_comments": 0
              }
            ]
          }
        ]
      },
      {
        "id": "331902",
        "name": "Prototyping",
        "page": "/project/8562/331902/",
        "status": "active",
        "priority": "1",
        "user_from": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "user_to": {
          "id": "5686",
          "email": "kate.greenway@ws.com",
          "name": "Kate Greenway"
        },
        "project": {
          "id": "8562",
          "name": "Owl brand launch",
          "page": "/project/8562/"
        },
        "text": "",
        "date_added": "2021-01-07 11:41",
        "date_start": "2021-01-10",
        "date_end": "2021-01-15",
        "has_comments": 0,
        "relations": {
          "to": [
            {
              "type": "finish-to-start",
              "task": {
                "id": "331894",
                "name": "Development",
                "page": "/project/8562/331894/",
                "status": "active",
                "priority": "7"
              }
            }
          ]
        }
      },
      {
        "id": "331906",
        "name": "Testing",
        "page": "/project/8562/331906/",
        "status": "active",
        "priority": "1",
        "user_from": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "user_to": {
          "id": "5514",
          "email": "frank.harper@ws.com",
          "name": "Frank Harper"
        },
        "project": {
          "id": "8562",
          "name": "Owl brand launch",
          "page": "/project/8562/"
        },
        "text": "",
        "date_added": "2021-01-07 12:00",
        "date_start": "2021-02-17",
        "date_end": "2021-02-24",
        "has_comments": 0,
        "relations": {
          "from": [
            {
              "type": "finish-to-start",
              "task": {
                "id": "331894",
                "name": "Development",
                "page": "/project/8562/331894/",
                "status": "active",
                "priority": "7"
              }
            }
          ]
        }
      }
    ]
  }
  ```

---

### get_tasks

**Action:** `get_tasks`

**Method:** `POST`

**Description:** Returns all incomplete and completed tasks of selected project

_\*except tasks with delayed publication  
\*subtasks can be returned with extra=subtasks parameter_

**Parameters:**

- `id_project` (Required) - Project ID

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "id": "331894",
        "name": "Development",
        "page": "/project/8562/331894/",
        "status": "active",
        "priority": "7",
        "user_from": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "user_to": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "project": {
          "id": "8562",
          "name": "Owl brand launch",
          "page": "/project/8562/"
        },
        "text": "Business logic programming",
        "date_added": "2021-01-07 10:01",
        "date_start": "2021-01-16",
        "date_end": "2021-02-16",
        "time_start": "08:00",
        "time_end": "18:00",
        "max_time": 352,
        "max_money": 5280,
        "subscribers": [
          {
            "id": "3993",
            "email": "henry.gardner@ws.com",
            "name": "Henry Gardner"
          },
          {
            "id": "5514",
            "email": "frank.harper@ws.com",
            "name": "Frank Harper"
          }
        ],
        "files": [
          {
            "id": "17694",
            "page": "/download/17694/",
            "name": "Development requirements.doc",
            "size": "27136"
          },
          {
            "id": "17698",
            "page": "/download/17698/",
            "name": "Development progress.xlsx",
            "size": "10698"
          }
        ],
        "has_comments": 1,
        "comments": [
          {
            "id": "19978",
            "page": "/project/8562/331894/#com19978",
            "text": "Thanks, first section done",
            "date_added": "2021-01-07 16:38",
            "user_from": {
              "id": "5514",
              "email": "frank.harper@ws.com",
              "name": "Frank Harper"
            }
          },
          {
            "id": "19974",
            "page": "/project/8562/331894/#com19974",
            "text": "As usual",
            "date_added": "2021-01-07 11:15",
            "user_from": {
              "id": "3993",
              "email": "henry.gardner@ws.com",
              "name": "Henry Gardner"
            }
          },
          {
            "id": "19962",
            "page": "/project/8562/331894/#com19962",
            "text": "And what about development\u00a0environment?",
            "date_added": "2021-01-07 11:10",
            "user_from": {
              "id": "5514",
              "email": "frank.harper@ws.com",
              "name": "Frank Harper"
            }
          },
          {
            "id": "19954",
            "page": "/project/8562/331894/#com19954",
            "text": "Need your help with first section",
            "date_added": "2021-01-07 11:04",
            "user_from": {
              "id": "5514",
              "email": "frank.harper@ws.com",
              "name": "Frank Harper"
            }
          },
          {
            "id": "19950",
            "page": "/project/8562/331894/#com19950",
            "text": "Updated development requirements",
            "date_added": "2021-01-07 10:33",
            "user_from": {
              "id": "3993",
              "email": "henry.gardner@ws.com",
              "name": "Henry Gardner"
            }
          }
        ],
        "relations": {
          "from": [
            {
              "type": "finish-to-start",
              "task": {
                "id": "331902",
                "name": "Prototyping",
                "page": "/project/8562/331902/",
                "status": "active",
                "priority": "1"
              }
            }
          ],
          "to": [
            {
              "type": "finish-to-start",
              "task": {
                "id": "331906",
                "name": "Testing",
                "page": "/project/8562/331906/",
                "status": "active",
                "priority": "1"
              }
            }
          ]
        },
        "child": [
          {
            "id": "331910",
            "name": "Sprint 1",
            "page": "/project/8562/331894/331910/",
            "status": "active",
            "priority": "1",
            "user_from": {
              "id": "3993",
              "email": "henry.gardner@ws.com",
              "name": "Henry Gardner"
            },
            "user_to": {
              "id": "3993",
              "email": "henry.gardner@ws.com",
              "name": "Henry Gardner"
            },
            "project": {
              "id": "8562",
              "name": "Owl brand launch",
              "page": "/project/8562/"
            },
            "text": "",
            "date_added": "2021-01-07 10:05",
            "subscribers": [
              {
                "id": "3993",
                "email": "henry.gardner@ws.com",
                "name": "Henry Gardner"
              }
            ],
            "has_comments": 0,
            "child": [
              {
                "id": "331914",
                "name": "Subsprint 1.1",
                "page": "/project/8562/331894/331914/",
                "status": "active",
                "priority": "1",
                "user_from": {
                  "id": "3993",
                  "email": "henry.gardner@ws.com",
                  "name": "Henry Gardner"
                },
                "user_to": {
                  "id": "3993",
                  "email": "henry.gardner@ws.com",
                  "name": "Henry Gardner"
                },
                "project": {
                  "id": "8562",
                  "name": "Owl brand launch",
                  "page": "/project/8562/"
                },
                "text": "",
                "date_added": "2021-01-07 10:07",
                "subscribers": [
                  {
                    "id": "3993",
                    "email": "henry.gardner@ws.com",
                    "name": "Henry Gardner"
                  }
                ],
                "has_comments": 0
              }
            ]
          }
        ]
      },
      {
        "id": "331902",
        "name": "Prototyping",
        "page": "/project/8562/331902/",
        "status": "active",
        "priority": "1",
        "user_from": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "user_to": {
          "id": "5686",
          "email": "kate.greenway@ws.com",
          "name": "Kate Greenway"
        },
        "project": {
          "id": "8562",
          "name": "Owl brand launch",
          "page": "/project/8562/"
        },
        "text": "",
        "date_added": "2021-01-07 11:41",
        "date_start": "2021-01-10",
        "date_end": "2021-01-15",
        "subscribers": [
          {
            "id": "3993",
            "email": "henry.gardner@ws.com",
            "name": "Henry Gardner"
          },
          {
            "id": "5686",
            "email": "kate.greenway@ws.com",
            "name": "Kate Greenway"
          }
        ],
        "has_comments": 0,
        "relations": {
          "to": [
            {
              "type": "finish-to-start",
              "task": {
                "id": "331894",
                "name": "Development",
                "page": "/project/8562/331894/",
                "status": "active",
                "priority": "7"
              }
            }
          ]
        }
      },
      {
        "id": "331906",
        "name": "Testing",
        "page": "/project/8562/331906/",
        "status": "active",
        "priority": "1",
        "user_from": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "user_to": {
          "id": "5514",
          "email": "frank.harper@ws.com",
          "name": "Frank Harper"
        },
        "project": {
          "id": "8562",
          "name": "Owl brand launch",
          "page": "/project/8562/"
        },
        "text": "",
        "date_added": "2021-01-07 12:00",
        "date_start": "2021-02-17",
        "date_end": "2021-02-24",
        "subscribers": [
          {
            "id": "3993",
            "email": "henry.gardner@ws.com",
            "name": "Henry Gardner"
          },
          {
            "id": "5514",
            "email": "frank.harper@ws.com",
            "name": "Frank Harper"
          }
        ],
        "has_comments": 0,
        "relations": {
          "from": [
            {
              "type": "finish-to-start",
              "task": {
                "id": "331894",
                "name": "Development",
                "page": "/project/8562/331894/",
                "status": "active",
                "priority": "7"
              }
            }
          ]
        }
      }
    ]
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 4,
    "message": "Project is invalid"
  }
  ```

---

### get_task

**Action:** `get_task`

**Method:** `POST`

**Description:** Returns selected incomplete or completed (sub)task

_\*except (sub)tasks with delayed publication  
\*task along with its subtasks can be returned with extra=subtasks parameter_

**Parameters:**

- `id_task` (Required) - Task ID

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "331894",
      "name": "Development",
      "page": "/project/8562/331894/",
      "status": "active",
      "priority": "7",
      "user_from": {
        "id": "3993",
        "email": "henry.gardner@ws.com",
        "name": "Henry Gardner"
      },
      "user_to": {
        "id": "3993",
        "email": "henry.gardner@ws.com",
        "name": "Henry Gardner"
      },
      "project": {
        "id": "8562",
        "name": "Owl brand launch",
        "page": "/project/8562/"
      },
      "text": "Business logic programming",
      "date_added": "2021-01-07 10:01",
      "date_start": "2021-01-16",
      "date_end": "2021-02-16",
      "time_start": "08:00",
      "time_end": "18:00",
      "max_time": 352,
      "max_money": 5280,
      "files": [
        {
          "id": "17694",
          "page": "/download/17694/",
          "name": "Development requirements.doc",
          "size": "27136"
        },
        {
          "id": "17698",
          "page": "/download/17698/",
          "name": "Development progress.xlsx",
          "size": "10698"
        }
      ],
      "has_comments": 1,
      "comments": [
        {
          "id": "19978",
          "page": "/project/8562/331894/#com19978",
          "text": "Thanks, first section done",
          "date_added": "2021-01-07 16:38",
          "user_from": {
            "id": "5514",
            "email": "frank.harper@ws.com",
            "name": "Frank Harper"
          }
        },
        {
          "id": "19974",
          "page": "/project/8562/331894/#com19974",
          "text": "As usual",
          "date_added": "2021-01-07 11:15",
          "user_from": {
            "id": "3993",
            "email": "henry.gardner@ws.com",
            "name": "Henry Gardner"
          }
        },
        {
          "id": "19962",
          "page": "/project/8562/331894/#com19962",
          "text": "And what about development\u00a0environment?",
          "date_added": "2021-01-07 11:10",
          "user_from": {
            "id": "5514",
            "email": "frank.harper@ws.com",
            "name": "Frank Harper"
          }
        },
        {
          "id": "19954",
          "page": "/project/8562/331894/#com19954",
          "text": "Need your help with first section",
          "date_added": "2021-01-07 11:04",
          "user_from": {
            "id": "5514",
            "email": "frank.harper@ws.com",
            "name": "Frank Harper"
          }
        },
        {
          "id": "19950",
          "page": "/project/8562/331894/#com19950",
          "text": "Updated development requirements",
          "date_added": "2021-01-07 10:33",
          "user_from": {
            "id": "3993",
            "email": "henry.gardner@ws.com",
            "name": "Henry Gardner"
          }
        }
      ],
      "subscribers": [
        {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        {
          "id": "5514",
          "email": "frank.harper@ws.com",
          "name": "Frank Harper"
        }
      ],
      "relations": {
        "from": [
          {
            "type": "finish-to-start",
            "task": {
              "id": "331902",
              "name": "Prototyping",
              "page": "/project/8562/331902/",
              "status": "active",
              "priority": "1"
            }
          }
        ],
        "to": [
          {
            "type": "finish-to-start",
            "task": {
              "id": "331906",
              "name": "Testing",
              "page": "/project/8562/331906/",
              "status": "active",
              "priority": "1"
            }
          }
        ]
      },
      "child": [
        {
          "id": "331910",
          "name": "Sprint 1",
          "page": "/project/8562/331894/331910/",
          "status": "active",
          "priority": "1",
          "child": [
            {
              "id": "331914",
              "name": "Subsprint 1.1",
              "page": "/project/8562/331894/331914/",
              "status": "active",
              "priority": "1"
            }
          ]
        }
      ]
    }
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 5,
    "message": "Task is invalid"
  }
  ```

---

### post_task

**Action:** `post_task`

**Method:** `POST`

**Description:** Creates (sub)task in selected project

_\*allows files attaching to (sub)task description (see_ [details](https://worksection.com/en/faq/api-files.html#q1691)_)_

**Parameters:**

- `id_project` (Required) - Project ID

- `title` (Required) - Task name

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "333118",
      "name": "Template prototype",
      "page": "/project/6622/332150/333118/",
      "status": "active",
      "priority": "2",
      "user_from": {
        "id": "3993",
        "email": "henry.gardner@ws.com",
        "name": "Henry Gardner"
      },
      "user_to": {
        "id": "5514",
        "email": "frank.harper@ws.com",
        "name": "Frank Harper"
      },
      "project": {
        "id": "6622",
        "name": "Performance improvement",
        "page": "/project/6622/"
      },
      "parent": {
        "id": "332150",
        "name": "Template creation",
        "page": "/project/6622/332150/",
        "status": "active",
        "priority": "10"
      },
      "text": "Take previous prototype as an example\r\n\u2022 draft\r\n\u2022 first version\r\n\u2022 final result",
      "date_added": "2021-01-11 11:37",
      "date_start": "2021-01-15",
      "date_end": "2021-01-17",
      "max_time": 15,
      "max_money": 165
    }
  }
  ```

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "332150",
      "name": "Template creation",
      "page": "/project/6622/332150/",
      "status": "active",
      "priority": "1",
      "user_from": {
        "id": "3993",
        "email": "henry.gardner@ws.com",
        "name": "Henry Gardner"
      },
      "user_to": {
        "id": "1",
        "email": "NOONE",
        "name": "Executive isn't assigned"
      },
      "project": {
        "id": "6622",
        "name": "Performance improvement",
        "page": "/project/6622/"
      },
      "date_added": "2021-01-10 15:17"
    }
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 8,
    "message": "Task is closed"
  }
  ```

---

### update_task

**Action:** `update_task`

**Method:** `POST`

**Description:** Updates selected incomplete or completed (sub)task parameters

**Parameters:**

- `id_task` (Required) - Task ID

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "332150",
      "name": "Template creation",
      "page": "/project/6622/332150/",
      "status": "active",
      "priority": "10",
      "user_from": {
        "id": "3993",
        "email": "henry.gardner@ws.com",
        "name": "Henry Gardner"
      },
      "user_to": {
        "id": "1",
        "email": "NOONE",
        "name": "Executive isn't assigned"
      },
      "project": {
        "id": "6622",
        "name": "Performance improvement",
        "page": "/project/6622/"
      },
      "date_added": "2021-01-20 15:17"
    }
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 5,
    "message": "Task is invalid"
  }
  ```

---

### complete_task

**Action:** `complete_task`

**Method:** `POST`

**Description:** Completes selected (sub)task

**Parameters:**

- `id_task` (Required) - Task ID

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "id": "331430",
      "name": "Team meetup",
      "page": "/project/6622/331430/",
      "status": "active",
      "priority": "1",
      "user_from": {
        "id": "3993",
        "email": "henry.gardner@ws.com",
        "name": "Henry Gardner"
      },
      "user_to": {
        "id": "3993",
        "email": "henry.gardner@ws.com",
        "name": "Henry Gardner"
      },
      "project": {
        "id": "6622",
        "name": "Performance improvement",
        "page": "/project/6622/"
      },
      "date_added": "2021-01-05 11:24"
    }
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 12,
    "message": "Task is already closed"
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 13,
    "message": "Task has children"
  }
  ```

---

### reopen_task

**Action:** `reopen_task`

**Method:** `POST`

**Description:** Reopens selected completed (sub)task

**Parameters:**

- `id_task` (Required) - Task ID

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok"
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 12,
    "message": "Task is already active"
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 14,
    "message": "Parent task is done"
  }
  ```

---

### search_tasks

**Action:** `search_tasks`

**Method:** `POST`

**Description:** Returns tasks that meet search query

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "id": "330090",
        "name": "Worksection implementation",
        "page": "/project/6622/330090/",
        "status": "active",
        "priority": "1",
        "user_from": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "user_to": {
          "id": "2",
          "email": "ANY",
          "name": "Anyone"
        },
        "project": {
          "id": "6622",
          "name": "Performance improvement",
          "page": "/project/6622/"
        },
        "date_added": "2021-01-01 12:00"
      },
      {
        "id": "331502",
        "name": "Worksection docs",
        "page": "/project/6622/331502/",
        "status": "active",
        "priority": "1",
        "user_from": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "user_to": {
          "id": "1",
          "email": "NOONE",
          "name": "Executive isn't assigned"
        },
        "project": {
          "id": "6622",
          "name": "Performance improvement",
          "page": "/project/6622/"
        },
        "date_added": "2021-01-01 13:04"
      }
    ]
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 10,
    "message": "At least one of fields required",
    "message_details": "filter, id_project, id_task, email_user_from, email_user_to"
  }
  ```

---

## Timers

### get_timers

**Action:** `get_timers`

**Method:** `POST`

**Description:** Returns running timers info

_\*their ID, start time, timer value and who started them_

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "id": "2918",
        "time": "00:11:13",
        "date_started": "2021-01-01 13:23",
        "user_from": {
          "id": "5514",
          "email": "frank.harper@ws.com",
          "name": "Frank Harper"
        },
        "task": {
          "id": "330142",
          "name": "Workflow revision",
          "page": "/project/6622/330142/",
          "status": "active",
          "priority": "1",
          "user_from": {
            "id": "3993",
            "email": "henry.gardner@ws.com",
            "name": "Henry Gardner"
          },
          "user_to": {
            "id": "5514",
            "email": "frank.harper@ws.com",
            "name": "Frank Harper"
          },
          "project": {
            "id": "6622",
            "name": "Performance improvement",
            "page": "/project/6622/"
          },
          "date_added": "2021-01-01 09:11"
        }
      },
      {
        "id": "2914",
        "time": "01:12:45",
        "date_started": "2021-01-01 12:00",
        "user_from": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "task": {
          "id": "330090",
          "name": "Worksection implementation",
          "page": "/project/6622/330090/",
          "status": "active",
          "priority": "1",
          "user_from": {
            "id": "3993",
            "email": "dimitriy.worksection@gmail.com",
            "name": "Henry Gardner"
          },
          "user_to": {
            "id": "2",
            "email": "ANY",
            "name": "Anyone"
          },
          "project": {
            "id": "6622",
            "name": "Performance improvement",
            "page": "/project/6622/"
          },
          "date_added": "2021-01-01 11:00"
        }
      }
    ]
  }
  ```

---

### stop_timer

**Action:** `stop_timer`

**Method:** `POST`

**Description:** Stops and saves selected running timer

**Parameters:**

- `timer` (Required) - Timer ID Can be obtained through _get_timers_ method

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok"
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 7,
    "message": "Timer not found"
  }
  ```

---

### get_my_timer

**Action:** `get_my_timer`

**Method:** `POST`

**Description:** Returns authorized user's (oauth2) active timer

**!! User method (available only for access token) !!**

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": {
      "time": 4360,
      "date_started": "2021-01-01 12:00",
      "task": {
        "id": "330090",
        "name": "Worksection implementation",
        "page": "/project/6622/330090/",
        "status": "active",
        "priority": "8",
        "user_from": {
          "id": "3993",
          "email": "henry.gardner@ws.com",
          "name": "Henry Gardner"
        },
        "user_to": {
          "id": "2",
          "email": "ANY",
          "name": "Anyone"
        },
        "project": {
          "id": "6622",
          "name": "Performance improvement",
          "page": "/project/6622/"
        },
        "date_added": "2021-01-01 11:00"
      }
    }
  }
  ```

---

### start_my_timer

**Action:** `start_my_timer`

**Method:** `POST`

**Description:** Starts authorized user's (oauth2) timer in selected task

**!! User method (available only for access token) !!**

**Parameters:**

- `id_task` (Required) - Task ID

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok"
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 6,
    "message": "Timer is already started"
  }
  ```

---

### stop_my_timer

**Action:** `stop_my_timer`

**Method:** `POST`

**Description:** Stops and saves authorized user's (oauth2) active timer

**!! User method (only for access token) !!**

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok"
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 7,
    "message": "Timer is not started"
  }
  ```

---

## Webhooks

### get_webhooks

**Action:** `get_webhooks`

**Method:** `POST`

**Description:** Returns webhooks list

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "data": [
      {
        "id": "122",
        "url": "https://eoaerhysr9s04hw.m.pipedream.net",
        "events": "post_task,post_comment,post_project",
        "status": "active",
        "projects": "5"
      },
      {
        "id": "123",
        "url": "https://eogt7ju5yih2iks.m.pipedream.net",
        "events": "update_task,update_comment,delete_task,delete_comment,close_task",
        "status": "paused"
      }
    ]
  }
  ```

---

### add_webhook

**Action:** `add_webhook`

**Method:** `POST`

**Description:** Creates webhook

**Parameters:**

- `url` (Required) - Webhook URL

- `events` (Required) - Events separated by commas. Selected events will send notifications to Webhook URL.
  Possible values: `post_task|post_comment|post_project|update_task|update_comment|update_project|delete_task|delete_comment|close_task`.
  - Possible values: `post_task, post_comment, post_project, update_task, update_comment, update_project, delete_task, delete_comment, close_task`

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok",
    "id": 130
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 11,
    "message": "Url should respond 200 HTTP_CODE and JSON {status:OK}",
    "message_details": "https://google.com"
  }
  ```

---

### delete_webhook

**Action:** `delete_webhook`

**Method:** `POST`

**Description:** Deletes selected webhook

**Parameters:**

- `id` (Required) - Webhook ID Can be obtained through _get_webhooks_ method

**Responses:**

- **success** (OK - 200)

  ```json
  {
    "status": "ok"
  }
  ```

- **error** (OK - 200)

  ```json
  {
    "status": "error",
    "status_code": 10,
    "message": "WebHook not found"
  }
  ```

---
