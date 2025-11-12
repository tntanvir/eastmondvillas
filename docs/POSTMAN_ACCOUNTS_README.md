# Accounts API - Postman Collection Guide

Complete Postman collection for testing and integrating with the Accounts API.

## 📦 Files

- `postman_accounts_collection.json` - Main collection with all endpoints
- `postman_accounts_environment.json` - Environment variables

## 🚀 Quick Start

### 1. Import into Postman

1. Open Postman
2. Click **Import** button (top left)
3. Drag and drop both files:
   - `postman_accounts_collection.json`
   - `postman_accounts_environment.json`
4. Select the **Accounts API Environment** from the environment dropdown (top right)

### 2. Configure Environment

Update these variables in the environment:

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8000/api` | API base URL |
| `admin_email` | `admin@example.com` | Admin account email |
| `admin_password` | `AdminPass123!` | Admin account password |
| `test_user_email` | `testuser@example.com` | Test user email |
| `test_user_password` | `TestPass123!` | Test user password |

### 3. Create Admin Account

Before running the collection, create an admin user:

```bash
cd /path/to/eastmondvilla
source env/bin/activate  # or `env\Scripts\activate` on Windows
python manage.py createsuperuser
```

Update `admin_email` and `admin_password` in the environment with your admin credentials.

## 📚 Collection Structure

### 1. Authentication & Registration
- **Register New User** - Create new user account (role: customer)
- **Login User** - Authenticate and get JWT tokens
- **Login Admin** - Authenticate as admin
- **Get Current User** - Retrieve authenticated user details
- **Logout** - Logout and blacklist refresh token

### 2. Password Management
- **Change Password** - Update password for authenticated user
- **Request Password Reset** - Send password reset email
- **Confirm Password Reset** - Reset password with token

### 3. Email Verification
- **Verify Email** - Confirm email with verification key

### 4. Admin - User Management
- **List All Users** - Get all users (admin only)
- **Create User (Admin)** - Create user with role/permission (admin only)
- **Get User Details** - Retrieve specific user (admin only)
- **Update User** - Update user including role (admin only)
- **Delete User (Admin)** - Delete any user (admin only)

### 5. Account Management
- **Delete Own Account** - Users can delete their own account

### 6. Error Examples
- **401 - Unauthorized** - Missing authentication
- **403 - Forbidden** - Insufficient permissions
- **400 - Bad Request** - Validation errors

## 🔄 Automated Workflows

### Token Management

The collection automatically manages JWT tokens:

1. **Login** requests store `access_token` and `refresh_token` in environment
2. All authenticated requests use `{{access_token}}` automatically
3. User ID is stored as `{{user_id}}` for account operations

### Test Scripts

Each request includes test scripts that:
- ✅ Validate response status codes
- ✅ Check response structure
- ✅ Store tokens and IDs automatically
- ✅ Verify data integrity

## 🎯 Usage Scenarios

### Scenario 1: Register and Login as New User

1. **Register New User**
   - Creates account with role `customer`
   - Stores `user_id` and `user_email`
   
2. **Login User**
   - Authenticates with credentials
   - Stores `access_token` and `refresh_token`
   
3. **Get Current User**
   - Retrieves user profile using token

### Scenario 2: Admin User Management

1. **Login Admin**
   - Authenticate as admin
   - Stores admin `access_token`
   
2. **List All Users**
   - View all registered users
   
3. **Create User (Admin)**
   - Create user with specific role (agent, manager, admin)
   - Stores `created_user_id`
   
4. **Update User**
   - Change role from `agent` to `manager`
   - Update permissions
   
5. **Delete User (Admin)**
   - Remove user by ID

### Scenario 3: Password Management

1. **Login User**
   - Authenticate first
   
2. **Change Password**
   - Update password with old/new password
   
3. **Request Password Reset**
   - Send reset email (no auth required)
   
4. **Confirm Password Reset**
   - Use uid/token from email to reset

## 🔐 Authentication

### JWT Tokens

The API uses JWT Bearer token authentication:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

**Token Lifetimes:**
- Access Token: 60 minutes
- Refresh Token: 7 days

### Roles & Permissions

**Roles:**
- `customer` - Default for registration
- `agent` - Assigned by admin
- `manager` - Assigned by admin
- `admin` - Full system access

**Permissions:**
- `only_view` - Read-only access (default)
- `download` - Can download resources
- `full_access` - Complete system access

## 📊 Running Tests

### Run Entire Collection

1. Click **Collections** in left sidebar
2. Click **...** next to "Accounts API Collection"
3. Select **Run collection**
4. Click **Run Accounts API Collection**

### Run Folder

Right-click any folder (e.g., "1. Authentication & Registration") and select **Run folder**.

### View Test Results

After running, the **Runner** tab shows:
- ✅ Passed tests (green)
- ❌ Failed tests (red)
- Test execution time
- Response details

## 🐛 Troubleshooting

### Issue: 401 Unauthorized

**Solution:** 
- Login first using **Login User** or **Login Admin**
- Verify `access_token` is set in environment
- Check token hasn't expired (60 min lifetime)

### Issue: 403 Forbidden

**Solution:**
- Ensure you're using admin token for admin endpoints
- Run **Login Admin** first
- Check user has required role/permission

### Issue: 400 Bad Request - Email Already Exists

**Solution:**
- Use different email in request body
- Or delete existing user first
- Check `test_user_email` in environment

### Issue: Connection Refused

**Solution:**
- Start Django server: `python manage.py runserver`
- Verify `base_url` in environment matches server
- Check Django server is running on port 8000

### Issue: CSRF Token Error

**Solution:**
- Django REST Framework doesn't require CSRF for JWT auth
- Ensure using `Authorization: Bearer` header
- Not using session authentication

## 🔧 Advanced Configuration

### Custom Base URL

For deployed environments, update `base_url`:

```
Production: https://api.example.com/api
Staging: https://staging-api.example.com/api
Local: http://localhost:8000/api
```

### Multiple Environments

Create separate environments for different stages:

1. Duplicate environment
2. Rename (e.g., "Accounts API - Production")
3. Update `base_url` and credentials
4. Switch between environments in dropdown

### Pre-request Scripts

The collection uses environment variables, but you can add pre-request scripts:

```javascript
// Auto-refresh token if expired
const expiryTime = pm.environment.get('token_expiry');
if (Date.now() > expiryTime) {
    // Add refresh logic here
}
```

## 📝 Environment Variables Reference

### Auto-populated Variables

These are set automatically by test scripts:

| Variable | Set By | Usage |
|----------|--------|-------|
| `access_token` | Login requests | Authentication header |
| `refresh_token` | Login requests | Token refresh |
| `user_id` | Login/Register | Account operations |
| `user_email` | Login/Register | User identification |
| `created_user_id` | Create User | Admin operations |

### Manual Configuration

Set these before running:

| Variable | Purpose |
|----------|---------|
| `base_url` | API endpoint URL |
| `admin_email` | Admin login email |
| `admin_password` | Admin login password |
| `test_user_email` | Test user email |
| `test_user_password` | Test user password |

## 🎓 Examples

### Example 1: Create Agent User

```json
POST {{base_url}}/admin/users/

Headers:
  Authorization: Bearer {{access_token}}
  Content-Type: application/json

Body:
{
  "email": "agent@example.com",
  "name": "Agent User",
  "phone": "+15559998888",
  "role": "agent",
  "permission": "download",
  "password": "AgentPass123!",
  "is_active": true,
  "is_staff": false
}
```

### Example 2: Update User Role

```json
PUT {{base_url}}/admin/users/5/

Headers:
  Authorization: Bearer {{access_token}}
  Content-Type: application/json

Body:
{
  "role": "manager",
  "permission": "full_access",
  "is_staff": true
}
```

### Example 3: Password Change

```json
POST {{base_url}}/auth/password/change/

Headers:
  Authorization: Bearer {{access_token}}
  Content-Type: application/json

Body:
{
  "old_password": "OldPass123!",
  "new_password1": "NewSecurePass456!",
  "new_password2": "NewSecurePass456!"
}
```

## 🔗 Related Documentation

- [Accounts API Specification](./ACCOUNTS_API_COMPLETE.md) - Complete API reference
- [Admin API Documentation](./ACCOUNTS_ADMIN_API.md) - Admin endpoints reference
- [OpenAPI Specification](./openapi_accounts.yaml) - OpenAPI/Swagger docs

## 🆘 Support

For issues or questions:

1. Check the API specification: `docs/ACCOUNTS_API_COMPLETE.md`
2. Review Django logs: Look for errors in terminal running `manage.py runserver`
3. Check Postman Console: View → Show Postman Console (see raw requests/responses)
4. Inspect test results: Look at failed test assertions

## 🎯 Best Practices

1. **Always login first** before testing authenticated endpoints
2. **Use environment variables** instead of hardcoding values
3. **Run tests** to validate API behavior
4. **Check test results** after each request
5. **Create separate environments** for dev/staging/production
6. **Store sensitive data** (passwords) as secret variables
7. **Document custom requests** in the collection

## 📋 Checklist for Integration

- [ ] Import collection and environment
- [ ] Create admin account via Django
- [ ] Update environment variables
- [ ] Run "Login Admin" to verify admin access
- [ ] Run "Register New User" to test user creation
- [ ] Test all endpoints in order
- [ ] Review test results
- [ ] Set up production environment
- [ ] Document any customizations

---

**Collection Version:** 1.0  
**Last Updated:** November 12, 2025  
**API Version:** 1.0
