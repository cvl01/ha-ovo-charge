# OVO Charge (Bonnet) Unofficial API Documentation

**Last Updated:** 2025-06-12

## Disclaimer

This documentation is the result of reverse-engineering the OVO Charge (formerly Bonnet) mobile application's network traffic. It is not official, may be incomplete, and is subject to change without notice. Use of this API should be for personal, non-commercial purposes only. Interacting with this API directly may be against the OVO Charge terms of service.

## Overview

The OVO Charge API allows users to access their account information, including charging history. Authentication is handled through Google's Firebase identity platform, using a "magic link" (email link) sign-in flow. The entire authentication process involves three distinct steps.

## Authentication

### Step 1: Requesting the Magic Link

To initiate the login process, the client application tells Firebase to send a magic link to the user's email address.

-   **Endpoint**: `POST https://www.googleapis.com/identitytoolkit/v3/relyingparty/getOobConfirmationCode`
-   **Query Parameter**: `key` (The public Firebase API key: `AIzaSyBc8a2MgrJ3krmxixlWflgVGg5ZQ_pHF78`)
-   **Request Headers**:
    ```
    x-client-version: iOS/FirebaseSDK/11.13.0/FirebaseCore-iOS
    content-type: application/json
    x-ios-bundle-identifier: com.bonnet.driver
    ```
-   **Request Body**: The body specifies the user's email and configuration for how the link should behave on mobile devices.
    ```json
    {
      "requestType": "EMAIL_SIGNIN",
      "email": "user@example.com",
      "continueUrl": "https://joinbonnet.com?flow=logIn",
      "iOSBundleId": "com.bonnet.driver",
      "androidPackageName": "com.bonnet",
      "canHandleCodeInApp": true
    }
    ```
-   **Success Response**: The server acknowledges the request and sends the email. The response itself does not contain any secrets.
    ```json
    {
      "kind": "identitytoolkit#GetOobConfirmationCodeResponse",
      "email": "user@example.com"
    }
    ```

### Step 2: Verifying the Magic Link

Once the user receives the email and clicks the link, the application extracts the `oobCode` (out-of-band code) from the link's URL. This code is then exchanged for an `idToken` (access token) and a `refreshToken`.

-   **Endpoint**: `POST https://www.googleapis.com/identitytoolkit/v3/relyingparty/emailLinkSignin`
-   **Query Parameter**: `key` (The same public Firebase API key)
-   **Request Body**:
    ```json
    {
      "email": "user@example.com",
      "oobCode": "ONE_TIME_CODE_FROM_MAGIC_LINK"
    }
    ```
-   **Success Response**: The server returns a JSON object containing the tokens.
    -   `idToken`: A short-lived JWT (1 hour) used for API requests.
    -   `refreshToken`: A long-lived token used to get a new `idToken`. **This should be stored securely.**

### Step 3: Refreshing the Session

Once the `idToken` expires, you can use the `refreshToken` to get a new one without user interaction. This allows for persistent sessions.

-   **Endpoint**: `POST https://securetoken.googleapis.com/v1/token`
-   **Query Parameter**: `key` (The same public Firebase API key)
-   **Request Body**:
    ```json
    {
      "grantType": "refresh_token",
      "refreshToken": "YOUR_STORED_REFRESH_TOKEN"
    }
    ```
-   **Success Response**: The server returns a new `idToken` (named `id_token` in this response).
    -   `idToken`: A short-lived JWT (1 hour) used for API requests.
    -   `refreshToken`: A long-lived token used to get a new `idToken`. **This should be stored securely as it may be rotated.**
    -   `user_id`: The unique identifier for the user.

    ```json
    {
      "access_token": "eyJhbGciOi...",
      "expires_in": "3600",
      "token_type": "Bearer",
      "refresh_token": "AMf-vBxE4p...",
      "id_token": "eyJhbGciOi...",
      "user_id": "2ugKwj9ym...",
      "project_id": "1003470..."
    }
    ```

## API Reference

### Base URL

-   **Production API**: `https://bonnetapps.com/driver/api/1.1`

### Common Headers

All requests to the Bonnet API (`bonnetapps.com`) should include the `Authorization` header, as well as headers that mimic the mobile application to ensure compatibility.

```
Authorization: <Your_idToken>
Content-Type: application/json
User-Agent: OVOCharge/1 CFNetwork/3826.500.131 Darwin/24.5.0
app-version: 3.14.3
app-platform: ios
```

---

### Endpoints

#### Get User Charge Logs

Retrieves a paginated list of the user's past and active charging sessions.
**Authentication required.**

-   **Method**: `GET`
-   **Path**: `/me/logs`
-   **Query Parameters**:
    -   `limit` (integer, e.g., `10`): The number of logs to retrieve.
    -   `offset` (integer, e.g., `0`): The starting position for pagination.
    -   `include_unfinished` (boolean, `true`): Whether to include active sessions.
-   **Success Response (200 OK)**:
    ```json
    {
      "position": 0,
      "totalCount": 36,
      "items": [
        {
          "kwh": 11,
          "status": "ACTIVE",
          "date_time": "2025-06-12T10:18:00.000Z",
          "address": "Bloemensingel 1"
        }
      ]
    }
    ```

#### Check if Email is in Use

Checks if a given email address is already registered with the service. This is a public endpoint used in the registration/login flow.
**No authentication required.**

-   **Method**: `GET`
-   **Path**: `/register/email-in-use`
-   **Query Parameters**:
    -   `email` (string, e.g., `christiaan@vanluikmail.nl`): The email to check.
-   **Success Response (200 OK)**:
    ```json
    {
      "in_use": true
    }
    ```

---

## Data Models

### ChargeLog Object

Describes a single charging session.

| Field                | Type      | Description                                                              |
| -------------------- | --------- | ------------------------------------------------------------------------ |
| `status`             | String    | The status of the charge (`"ACTIVE"`, `"COMPLETED"`, etc.).              |
| `date_time`          | String    | ISO 8601 timestamp of when the session started.                          |
| `address`            | String    | The street address of the charging location.                             |
| `operator`           | String    | The name of the charge point operator.                                   |
| `kwh`                | Number    | The total energy delivered in kilowatt-hours.                            |
| `power`              | Number    | The current charging power in kW (only for `ACTIVE` sessions).           |
| `total_cost`         | Number    | The total cost of the session (only for `ACTIVE` sessions).              |
| `currency`           | String    | The currency of the cost (e.g., `"EUR"`).                                |
| `bonnet_location_id` | String    | The internal ID for the location.                                        |
| `command_id`         | String    | The internal ID for the charge command.                                  |
| `coordinates`        | Object    | An object containing `latitude` and `longitude`.                         |

---

## Real-Time Charging Status (WebSocket)

For active charging sessions, the OVO Charge app uses a WebSocket connection to receive real-time updates on power, energy delivered, and cost.

### Protocol: Socket.IO

The connection does not use raw WebSockets. It uses the **Socket.IO** library (Engine.IO protocol v4). Any client wishing to connect must use a compatible Socket.IO v3/v4 client library.

-   **Connection URL**: `wss://bonnetapps.com/stream/`
-   **Transport Options**: `transport=websocket`, `EIO=4`

### Connection Flow

1.  **Authenticate**: First, complete the standard HTTP authentication flow to obtain a valid `idToken` and, most importantly, the `localId` for the user.
2.  **Connect**: Establish a Socket.IO connection to the URL above. You must pass the `Cookie` header obtained from previous HTTP API calls to maintain session affinity with the server load balancer.
3.  **Listen for Events**: Once connected, the server will automatically start pushing events for active charging sessions. No explicit "subscribe" message appears to be needed.

### Socket.IO Events

The server emits a single type of event for charging updates.

-   **Event Name**: `"<USER_ID>-charging-updates"`
    -   This is a dynamic event name. The `<USER_ID>` part must be replaced with the `localId` of the authenticated user (e.g., `"2ugKwj9ymldXl1zsWkdzcV3fbLe2-charging-updates"`).
    -   A client should listen for this specific event or filter all incoming events to match its user ID.
-   **Event Payload**: The event data is a JSON object with the following structure.

| Field                   | Type    | Description                                                              |
| ----------------------- | ------- | ------------------------------------------------------------------------ |
| `session_id`            | String  | The unique ID for this specific charging session.                        |
| `command_id`            | String  | The internal ID for the charge command.                                  |
| `kwh`                   | Number  | The total energy delivered so far in kWh.                                |
| `power`                 | Number  | The current charging power in kW. Can be `0` if the car is full or paused. |
| `total_cost`            | Number  | The running total cost of the session.                                   |
| `total_savings`         | Number  | The running total savings from a boost/membership.                       |
| `currency`              | String  | The currency of the cost (e.g., `"GBP"`, `"EUR"`).                       |
| `last_updated`          | String  | ISO 8601 timestamp of this specific update.                              |
| `has_overstay_fee`      | Boolean | Whether an overstay fee is currently being applied.                      |
| `membership_sufficient` | Boolean | Whether the user's membership covers this session.                       |

