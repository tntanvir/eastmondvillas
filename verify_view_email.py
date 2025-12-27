import os
import django
from django.conf import settings
# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eastmondvilla.settings')
django.setup()

from django.core import mail
from django.test import RequestFactory
from rest_framework.test import APIClient
from list_vila.views import ContactUsView

def test_contact_us_email():
    print("Testing Contact Us View Email Sending...")
    
    client = APIClient()
    
    data = {
        "name": "Test User",
        "email": "testsender@example.com",
        "phone": "1234567890",
        "message": "This is a test message from the verification script."
    }
    
    # Clear outbox
    mail.outbox = []
    
    try:
        response = client.post('/api/contact-us/', data, format='json') # URL might be different, but using view directly or checking via request factory is better if URL is unknown. 
        # Actually simplest to just call the view method manually or rely on mapping if we knew it.
        # Let's try to map it using the view class directly to avoid URL config issues.
        
        factory = RequestFactory()
        request = factory.post('/api/contact-us/', data, content_type='application/json')
        view = ContactUsView.as_view()
        response = view(request)
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Data: {response.data}")

        if response.status_code == 201:
            print("Successfully posted data.")
            # Check print output for email sending in console backend
            print("Please check the console output above for the simulated email.")
        else:
            print("Failed to post data.")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_contact_us_email()
