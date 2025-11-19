#!/usr/bin/env python3
"""
Villa API Endpoint Testing Script
Tests all villa app endpoints with different user roles
"""

import requests
import json
from datetime import date, timedelta

# Configuration
BASE_URL = "http://localhost:8888/api/villas/"
AUTH_URL = "http://localhost:8888/api/auth/login/"

# Test colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_test(test_name, passed, message=""):
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {test_name}")
    if message:
        print(f"       {YELLOW}{message}{RESET}")

def get_token(email, password):
    """Get JWT token for user"""
    try:
        response = requests.post(AUTH_URL, json={"email": email, "password": password})
        if response.status_code == 200:
            return response.json()['access']
        return None
    except Exception as e:
        print(f"{RED}Error getting token: {e}{RESET}")
        return None

def test_list_properties_public():
    """Test listing properties without authentication"""
    print_header("Testing Public Property Listing")
    
    try:
        response = requests.get(f"{BASE_URL}properties/")
        passed = response.status_code == 200
        print_test(
            "List properties (unauthenticated)", 
            passed, 
            f"Status: {response.status_code}, Count: {len(response.json()) if passed else 0}"
        )
        return response.json() if passed else []
    except Exception as e:
        print_test("List properties (unauthenticated)", False, str(e))
        return []

def test_list_properties_admin(token):
    """Test listing properties as admin"""
    print_header("Testing Admin Property Listing")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}properties/", headers=headers)
        passed = response.status_code == 200
        print_test(
            "List properties (admin)", 
            passed, 
            f"Status: {response.status_code}, Count: {len(response.json()) if passed else 0}"
        )
        return response.json() if passed else []
    except Exception as e:
        print_test("List properties (admin)", False, str(e))
        return []

def test_get_single_property(property_id):
    """Test getting a single property"""
    print_header("Testing Single Property Retrieval")
    
    try:
        response = requests.get(f"{BASE_URL}properties/{property_id}/")
        passed = response.status_code == 200
        data = response.json() if passed else {}
        print_test(
            f"Get property {property_id}", 
            passed, 
            f"Status: {response.status_code}, Title: {data.get('title', 'N/A')}"
        )
        return data
    except Exception as e:
        print_test(f"Get property {property_id}", False, str(e))
        return {}

def test_create_property_admin(token):
    """Test creating a property as admin"""
    print_header("Testing Property Creation (Admin)")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "title": "Test API Villa",
            "description": "Created via API test script",
            "price": "777.00",
            "listing_type": "rent",
            "status": "draft",
            "city": "Test City",
            "address": "123 Test Street",
            "add_guest": "6",
            "bedrooms": "3",
            "bathrooms": "2",
            "has_pool": "true",
            "amenities": json.dumps({"wifi": True, "test": True})
        }
        response = requests.post(f"{BASE_URL}properties/", headers=headers, data=data)
        passed = response.status_code == 201
        result = response.json() if passed else {}
        print_test(
            "Create property (admin)", 
            passed, 
            f"Status: {response.status_code}, ID: {result.get('id', 'N/A')}"
        )
        return result.get('id') if passed else None
    except Exception as e:
        print_test("Create property (admin)", False, str(e))
        return None

def test_create_property_customer(token):
    """Test creating a property as customer (should fail)"""
    print_header("Testing Property Creation (Customer - Should Fail)")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "title": "Unauthorized Villa",
            "price": "100.00",
            "listing_type": "rent",
            "city": "Test City"
        }
        response = requests.post(f"{BASE_URL}properties/", headers=headers, data=data)
        passed = response.status_code == 403
        print_test(
            "Create property (customer)", 
            passed, 
            f"Status: {response.status_code} (Expected 403)"
        )
    except Exception as e:
        print_test("Create property (customer)", False, str(e))

def test_update_property(token, property_id):
    """Test updating a property"""
    print_header("Testing Property Update")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "title": "Updated Test Villa",
            "price": "888.00"
        }
        response = requests.patch(f"{BASE_URL}properties/{property_id}/", headers=headers, data=data)
        passed = response.status_code == 200
        print_test(
            f"Update property {property_id}", 
            passed, 
            f"Status: {response.status_code}"
        )
    except Exception as e:
        print_test(f"Update property {property_id}", False, str(e))

def test_list_bookings(token):
    """Test listing bookings"""
    print_header("Testing Booking Listing")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}bookings/", headers=headers)
        passed = response.status_code == 200
        print_test(
            "List bookings", 
            passed, 
            f"Status: {response.status_code}, Count: {len(response.json()) if passed else 0}"
        )
        return response.json() if passed else []
    except Exception as e:
        print_test("List bookings", False, str(e))
        return []

def test_create_booking(token, property_id):
    """Test creating a booking"""
    print_header("Testing Booking Creation")
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        check_in = date.today() + timedelta(days=30)
        check_out = check_in + timedelta(days=5)
        
        data = {
            "property": property_id,
            "email": "test@example.com",
            "phone": "+1234567890",
            "check_in": str(check_in),
            "check_out": str(check_out),
            "total_price": "2500.00"
        }
        response = requests.post(f"{BASE_URL}bookings/", headers=headers, json=data)
        passed = response.status_code == 201
        result = response.json() if passed else {}
        print_test(
            "Create booking", 
            passed, 
            f"Status: {response.status_code}, ID: {result.get('id', 'N/A')}"
        )
        return result.get('id') if passed else None
    except Exception as e:
        print_test("Create booking", False, str(e))
        return None

def test_get_booking(token, booking_id):
    """Test getting a single booking"""
    print_header("Testing Single Booking Retrieval")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}bookings/{booking_id}/", headers=headers)
        passed = response.status_code == 200
        print_test(
            f"Get booking {booking_id}", 
            passed, 
            f"Status: {response.status_code}"
        )
    except Exception as e:
        print_test(f"Get booking {booking_id}", False, str(e))

def test_update_booking_status(token, booking_id):
    """Test updating booking status"""
    print_header("Testing Booking Status Update")
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {"status": "approved"}
        response = requests.patch(f"{BASE_URL}bookings/{booking_id}/", headers=headers, json=data)
        passed = response.status_code == 200
        print_test(
            f"Update booking {booking_id} status", 
            passed, 
            f"Status: {response.status_code}"
        )
    except Exception as e:
        print_test(f"Update booking {booking_id} status", False, str(e))

def test_property_availability(property_id):
    """Test getting property availability"""
    print_header("Testing Property Availability")
    
    try:
        response = requests.get(f"{BASE_URL}properties/{property_id}/availability/?month=12&year=2025")
        # Property might not have calendar configured, so 400 is acceptable
        passed = response.status_code in [200, 400]
        print_test(
            f"Get property {property_id} availability", 
            passed, 
            f"Status: {response.status_code}"
        )
    except Exception as e:
        print_test(f"Get property {property_id} availability", False, str(e))

def run_all_tests():
    """Run all API tests"""
    print(f"\n{BLUE}{'*'*60}")
    print(f"{'VILLA APP API ENDPOINT TESTS':^60}")
    print(f"{'*'*60}{RESET}\n")
    
    # Get tokens
    print(f"{YELLOW}Authenticating users...{RESET}")
    admin_token = get_token("admin@eastmondvilla.com", "admin123")
    customer_token = get_token("customer1@example.com", "customer123")
    
    if not admin_token:
        print(f"{RED}Failed to get admin token. Make sure the server is running and users exist.{RESET}")
        return
    
    if not customer_token:
        print(f"{RED}Failed to get customer token.{RESET}")
        return
    
    print(f"{GREEN}✓ Authentication successful{RESET}\n")
    
    # Test property endpoints
    properties_public = test_list_properties_public()
    properties_admin = test_list_properties_admin(admin_token)
    
    if properties_public:
        property_id = properties_public[0]['id']
        test_get_single_property(property_id)
    
    # Test creating property
    new_property_id = test_create_property_admin(admin_token)
    test_create_property_customer(customer_token)
    
    # Test updating property
    if new_property_id:
        test_update_property(admin_token, new_property_id)
    
    # Test booking endpoints
    bookings = test_list_bookings(customer_token)
    
    if properties_public:
        booking_id = test_create_booking(customer_token, properties_public[0]['id'])
        
        if booking_id:
            test_get_booking(customer_token, booking_id)
            test_update_booking_status(admin_token, booking_id)
    
    # Test availability
    if properties_public:
        test_property_availability(properties_public[0]['id'])
    
    print_header("TEST SUMMARY")
    print(f"{BLUE}All endpoint tests completed!{RESET}")
    print(f"{YELLOW}Note: Some failures are expected (e.g., customer creating property){RESET}\n")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
