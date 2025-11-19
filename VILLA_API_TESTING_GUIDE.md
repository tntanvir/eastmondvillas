# Villa App API Testing Guide

## Overview
This document provides instructions for testing all villa app API endpoints.

## Server Information
- Base URL: `http://localhost:8888/api/villas/`
- Authentication: JWT Bearer Token

## Test User Credentials
After running `python manage.py populate_villas`, the following users are created:

- **Admin**: 
  - Email: `admin@eastmondvilla.com`
  - Password: `admin123`
  
- **Manager**: 
  - Email: `manager@eastmondvilla.com`
  - Password: `manager123`
  
- **Agent** (3 agents):
  - Email: `agent1@eastmondvilla.com`, `agent2@eastmondvilla.com`, `agent3@eastmondvilla.com`
  - Password: `agent123`
  
- **Customers** (5 customers):
  - Email: `customer1@example.com`, `customer2@example.com`, etc.
  - Password: `customer123`

## Authentication

### 1. Get JWT Token
```bash
curl -X POST http://localhost:8888/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@eastmondvilla.com",
    "password": "admin123"
  }'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "admin@eastmondvilla.com",
    "name": "Admin User",
    "role": "admin"
  }
}
```

## Property Endpoints

### 2. List All Properties (Public)
```bash
curl -X GET http://localhost:8888/api/villas/properties/
```

### 3. List All Properties (Authenticated)
```bash
curl -X GET http://localhost:8888/api/villas/properties/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Get Single Property
```bash
curl -X GET http://localhost:8888/api/villas/properties/1/
```

### 5. Create Property (Admin/Manager Only)
```bash
curl -X POST http://localhost:8888/api/villas/properties/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "title=New Luxury Villa" \
  -F "description=Beautiful beachfront property" \
  -F "price=800.00" \
  -F "listing_type=rent" \
  -F "status=draft" \
  -F "city=Miami" \
  -F "address=123 Ocean Drive" \
  -F "add_guest=10" \
  -F "bedrooms=5" \
  -F "bathrooms=4" \
  -F "has_pool=true" \
  -F 'amenities={"wifi":true,"pool":"private","parking":true}' \
  -F "latitude=25.761681" \
  -F "longitude=-80.191788"
```

### 6. Create Property with Media Files
```bash
curl -X POST http://localhost:8888/api/villas/properties/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "title=Villa with Images" \
  -F "description=Test property with images" \
  -F "price=600.00" \
  -F "listing_type=rent" \
  -F "status=published" \
  -F "city=Miami" \
  -F "add_guest=8" \
  -F "bedrooms=4" \
  -F "bathrooms=3" \
  -F "media_files=@/path/to/image1.jpg" \
  -F "media_files=@/path/to/image2.jpg" \
  -F 'media_metadata=[{"category":"exterior","is_primary":true,"order":0}]' \
  -F 'media_metadata=[{"category":"bedroom","caption":"Master Bedroom","order":1}]'
```

### 7. Update Property (Admin/Manager/Assigned Agent)
```bash
curl -X PATCH http://localhost:8888/api/villas/properties/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "title=Updated Villa Title" \
  -F "price=950.00"
```

### 8. Delete Property (Admin/Manager Only)
```bash
curl -X DELETE http://localhost:8888/api/villas/properties/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Booking Endpoints

### 9. List User's Bookings (Authenticated)
```bash
curl -X GET http://localhost:8888/api/villas/bookings/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 10. List All Bookings (Admin/Manager)
```bash
curl -X GET http://localhost:8888/api/villas/bookings/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

### 11. Get Single Booking (Owner/Admin/Manager)
```bash
curl -X GET http://localhost:8888/api/villas/bookings/1/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 12. Create Booking (Authenticated)
```bash
curl -X POST http://localhost:8888/api/villas/bookings/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "property": 1,
    "email": "customer1@example.com",
    "phone": "+1234567890",
    "check_in": "2025-12-01",
    "check_out": "2025-12-07",
    "total_price": "3500.00"
  }'
```

### 13. Update Booking Status (Admin/Manager Only)
```bash
curl -X PATCH http://localhost:8888/api/villas/bookings/1/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved"
  }'
```

Status options: `pending`, `approved`, `rejected`, `completed`, `cancelled`

### 14. Delete Booking (Admin/Manager Only)
```bash
curl -X DELETE http://localhost:8888/api/villas/bookings/1/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

## Property Availability Endpoint

### 15. Check Property Availability (Public)
```bash
curl -X GET "http://localhost:8888/api/villas/properties/1/availability/?month=12&year=2025"
```

Response:
```json
[
  {
    "start": "2025-12-01",
    "end": "2025-12-07"
  },
  {
    "start": "2025-12-15",
    "end": "2025-12-20"
  }
]
```

## Testing with Python Requests

Create a file `test_api.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8888/api/villas/"
AUTH_URL = "http://localhost:8888/api/auth/login/"

# 1. Login and get token
def get_token(email, password):
    response = requests.post(AUTH_URL, json={
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        return response.json()['access']
    return None

# 2. List properties
def list_properties(token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = requests.get(f"{BASE_URL}properties/", headers=headers)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

# 3. Create booking
def create_booking(token, property_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "property": property_id,
        "email": "test@example.com",
        "phone": "+1234567890",
        "check_in": "2025-12-10",
        "check_out": "2025-12-15",
        "total_price": "2500.00"
    }
    response = requests.post(f"{BASE_URL}bookings/", headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

# Test execution
if __name__ == "__main__":
    # Get admin token
    admin_token = get_token("admin@eastmondvilla.com", "admin123")
    print(f"Admin Token: {admin_token[:50]}...\n")
    
    # List properties as admin
    print("=== Listing Properties as Admin ===")
    properties = list_properties(admin_token)
    print(f"\nTotal Properties: {len(properties)}\n")
    
    # Get customer token
    customer_token = get_token("customer1@example.com", "customer123")
    print(f"Customer Token: {customer_token[:50]}...\n")
    
    # Create a booking
    if properties:
        print("=== Creating Booking ===")
        create_booking(customer_token, properties[0]['id'])
```

Run the test:
```bash
python test_api.py
```

## Unit Tests

Run all villa app tests:
```bash
python manage.py test villas --verbosity=2
```

Run specific test class:
```bash
python manage.py test villas.tests.PropertyAPITestCase --verbosity=2
```

Run specific test method:
```bash
python manage.py test villas.tests.PropertyAPITestCase.test_list_properties_unauthenticated --verbosity=2
```

## Expected Results Summary

### Property List (Unauthenticated)
- ✅ Should return only published properties
- ✅ Should include media files
- ✅ Should include location coordinates

### Property List (Admin)
- ✅ Should return all properties (draft, published, etc.)
- ✅ Should include assigned agent info

### Property List (Agent)
- ✅ Should return only assigned properties

### Create Property
- ✅ Admin/Manager: Success (201)
- ❌ Customer: Forbidden (403)
- ❌ Unauthenticated: Unauthorized (401)

### Update Property
- ✅ Admin/Manager: Success (200)
- ✅ Assigned Agent with full_access: Success (200)
- ❌ Unassigned Agent: Forbidden (403)
- ❌ Customer: Forbidden (403)

### Delete Property
- ✅ Admin/Manager: Success (204)
- ❌ Agent: Forbidden (403)
- ❌ Customer: Forbidden (403)

### Create Booking
- ✅ Authenticated User: Success (201)
- ❌ Unauthenticated: Unauthorized (401)
- ❌ Past check-in date: Bad Request (400)
- ❌ Check-out before check-in: Bad Request (400)

### Update Booking
- ✅ Admin/Manager: Success (200)
- ❌ Customer: Forbidden (403)

### View Booking
- ✅ Owner: Success (200)
- ✅ Admin/Manager: Success (200)
- ❌ Other User: Forbidden (403)

## Database State After populate_villas

After running `python manage.py populate_villas --properties 10 --bookings 20 --media-per-property 5`:

- **Users**: 1 Admin, 1 Manager, 3 Agents, 5 Customers
- **Properties**: 10 properties (mix of published, draft, pending_review)
- **Media Files**: 50 media files (5 per property)
- **Bookings**: 20 bookings with various statuses

## Troubleshooting

### Issue: 401 Unauthorized
- Check if token is valid
- Check if token is in correct format: `Bearer YOUR_TOKEN`
- Token might be expired (refresh or login again)

### Issue: 403 Forbidden
- User doesn't have required role
- Agent might not have full_access permission
- Agent might not be assigned to the property

### Issue: 400 Bad Request
- Check date formats (YYYY-MM-DD)
- Check required fields
- Check JSON syntax
- Check that check_out > check_in

### Issue: 500 Internal Server Error
- Check server logs
- Check Google Calendar configuration
- Check database migrations

## Additional Notes

1. The server must be running: `python manage.py runserver 8888`
2. Database must be migrated: `python manage.py migrate`
3. Test data can be populated: `python manage.py populate_villas`
4. Use tools like Postman, Insomnia, or curl for testing
5. Check Django admin at http://localhost:8888/admin/
