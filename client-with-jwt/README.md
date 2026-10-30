# JWT Frontend Client

This React application provides a complete **JWT-based authentication flow** (sign up, log in, session persistence). It is designed to connect to your **Flask backend** and assumes the backend exposes JWT-protected routes.

You will not need to modify this frontend. However, your backend must implement and support the routes described below for this client to work correctly.

---

## Getting Started

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Start the application**
   ```bash
   npm start
   ```

3. **Backend requirements**
   - Backend must be running locally on `http://localhost:3000` OR use a proxy.
   - Supports `JWT` via `Bearer <token>` headers.
   - All responses must return JSON.

---

## Auth Flow Overview

This app manages login, signup, and session persistence through `fetch()` calls to the following endpoints:

---

### POST `/login`

**Description**: Authenticates an existing user.  
**Headers**:
```json
{
  "Content-Type": "application/json"
}
```

**Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Response**:
```json
{
  "token": "<JWT string>",
  "user": {
    "id": 1,
    "username": "string"
  }
}
```

---

### POST `/signup`

**Description**: Registers a new user and logs them in.  
**Headers**:
```json
{
  "Content-Type": "application/json"
}
```

**Body**:
```json
{
  "username": "string",
  "password": "string",
  "password_confirmation": "string"
}
```

**Response**:
```json
{
  "token": "<JWT string>",
  "user": {
    "id": 1,
    "username": "string"
  }
}
```

---

### GET `/me`

**Description**: Retrieves the current authenticated user if a valid JWT is present.  
**Headers**:
```json
{
  "Authorization": "Bearer <token>"
}
```

**Response**:
```json
{
  "id": 1,
  "username": "string"
}
```

---

## Token Management

- On login/signup, the `token` is saved to `localStorage`.
- The `/me` endpoint checks this token on page load to persist the session.
- On logout, `localStorage.removeItem("token")` clears the session.

---

## Custom Resource Endpoints

The frontend **does not** include routes or fetches for your custom resource (e.g., `/notes`, `/workouts`, `/entries`). These endpoints will be **integrated by the frontend team** after your backend is complete.

Ensure your resource endpoints:
- Are fully authenticated
- Use the JWT identity to associate data with the current user
- Follow RESTful patterns (`GET`, `POST`, `PATCH`, `DELETE`)
- Support pagination on `GET /<resource>?page=1&per_page=10`

---
