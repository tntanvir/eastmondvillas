from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.files.base import ContentFile
from decimal import Decimal
from datetime import date, timedelta
import random
import io
from PIL import Image

from accounts.models import User
from villas.models import Property, Media, Booking


class Command(BaseCommand):
    help = 'Populate the database with bulk villa data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--properties',
            type=int,
            default=10,
            help='Number of properties to create (default: 10)'
        )
        parser.add_argument(
            '--bookings',
            type=int,
            default=20,
            help='Number of bookings to create (default: 20)'
        )
        parser.add_argument(
            '--media-per-property',
            type=int,
            default=5,
            help='Number of media files per property (default: 5)'
        )

    def handle(self, *args, **options):
        properties_count = options['properties']
        bookings_count = options['bookings']
        media_per_property = options['media_per_property']

        self.stdout.write(self.style.WARNING('Starting bulk data creation...'))

        # Get or create users
        admin_user = self._get_or_create_admin()
        manager_user = self._get_or_create_manager()
        agent_users = self._get_or_create_agents(3)
        customer_users = self._get_or_create_customers(5)

        self.stdout.write(self.style.SUCCESS(f'✓ Created/verified users'))

        # Create properties
        properties = self._create_properties(properties_count, admin_user, agent_users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(properties)} properties'))

        # Create media for properties
        total_media = self._create_media_for_properties(properties, media_per_property)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {total_media} media files'))

        # Create bookings
        bookings = self._create_bookings(bookings_count, properties, customer_users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(bookings)} bookings'))

        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Bulk data creation completed successfully!'))
        self.stdout.write(self.style.SUCCESS(f'Total Properties: {len(properties)}'))
        self.stdout.write(self.style.SUCCESS(f'Total Media Files: {total_media}'))
        self.stdout.write(self.style.SUCCESS(f'Total Bookings: {len(bookings)}'))
        self.stdout.write(self.style.SUCCESS('='*50))

    def _get_or_create_admin(self):
        """Get or create an admin user"""
        admin, created = User.objects.get_or_create(
            email='admin@eastmondvilla.com',
            defaults={
                'name': 'Admin User',
                'role': 'admin',
                'phone': '+1234567890',
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
        return admin

    def _get_or_create_manager(self):
        """Get or create a manager user"""
        manager, created = User.objects.get_or_create(
            email='manager@eastmondvilla.com',
            defaults={
                'name': 'Manager User',
                'role': 'manager',
                'phone': '+1234567891',
            }
        )
        if created:
            manager.set_password('manager123')
            manager.save()
        return manager

    def _get_or_create_agents(self, count):
        """Get or create agent users"""
        agents = []
        for i in range(count):
            agent, created = User.objects.get_or_create(
                email=f'agent{i+1}@eastmondvilla.com',
                defaults={
                    'name': f'Agent {i+1}',
                    'role': 'agent',
                    'phone': f'+123456789{i+2}',
                }
            )
            if created:
                agent.set_password('agent123')
                agent.save()
            agents.append(agent)
        return agents

    def _get_or_create_customers(self, count):
        """Get or create customer users"""
        customers = []
        for i in range(count):
            customer, created = User.objects.get_or_create(
                email=f'customer{i+1}@example.com',
                defaults={
                    'name': f'Customer {i+1}',
                    'role': 'customer',
                    'phone': f'+198765432{i}',
                }
            )
            if created:
                customer.set_password('customer123')
                customer.save()
            customers.append(customer)
        return customers

    def _create_properties(self, count, admin_user, agent_users):
        """Create sample properties"""
        properties = []

        villa_names = [
            'Sunset Paradise Villa', 'Ocean Breeze Estate', 'Mountain View Retreat',
            'Tropical Haven', 'Luxury Beach House', 'Palm Tree Villa',
            'Seaside Sanctuary', 'Coastal Dream Home', 'Island Paradise',
            'Beachfront Oasis', 'Mediterranean Villa', 'Lakeside Retreat',
            'Cliffside Escape', 'Garden Villa', 'Private Beach House',
            'Hillside Haven', 'Waterfront Estate', 'Sunset Bay Villa',
            'Emerald Coast House', 'Azure Waters Villa'
        ]

        cities = [
            'Miami', 'Los Angeles', 'San Diego', 'Honolulu', 'Key West',
            'Santa Barbara', 'Malibu', 'Naples', 'Sarasota', 'Charleston',
            'Maui', 'Cabo San Lucas', 'Cancun', 'Tulum', 'Punta Cana',
            'Nassau', 'San Juan', 'Cartagena', 'Barbados', 'Jamaica'
        ]

        amenities_options = [
            {'wifi': True, 'pool': 'private', 'parking': True, 'gym': True, 'hot_tub': True},
            {'wifi': True, 'pool': 'shared', 'parking': True, 'beach_access': True},
            {'wifi': True, 'fireplace': True, 'mountain_view': True, 'bbq': True},
            {'wifi': True, 'pool': 'private', 'beach_front': True, 'chef': True},
            {'wifi': True, 'pool': 'infinity', 'parking': True, 'concierge': True},
        ]

        descriptions = [
            'Stunning beachfront property with breathtaking ocean views. Perfect for families and groups.',
            'Luxurious villa featuring modern amenities and elegant design. Close to all major attractions.',
            'Cozy retreat surrounded by natural beauty. Ideal for a peaceful getaway.',
            'Spacious estate with private pool and beautiful gardens. Great for entertaining.',
            'Contemporary home with spectacular views and high-end finishes throughout.',
        ]

        for i in range(count):
            status_choice = random.choice(['published', 'published', 'published', 'draft', 'pending_review'])
            
            property_obj = Property.objects.create(
                title=villa_names[i % len(villa_names)],
                description=random.choice(descriptions),
                price=Decimal(str(random.randint(200, 1500))) + Decimal('0.00'),
                booking_rate={
                    'weekly': random.randint(1000, 8000),
                    'monthly': random.randint(3500, 25000)
                },
                listing_type=random.choice(['rent', 'rent', 'rent', 'sale']),
                status=status_choice,
                address=f'{random.randint(100, 9999)} {random.choice(["Ocean", "Beach", "Palm", "Sunset", "Sea"])} {random.choice(["Drive", "Avenue", "Road", "Boulevard"])}',
                city=cities[i % len(cities)],
                add_guest=random.randint(4, 16),
                bedrooms=random.randint(2, 8),
                bathrooms=random.randint(2, 6),
                has_pool=random.choice([True, True, False]),
                amenities=random.choice(amenities_options),
                latitude=Decimal(str(random.uniform(25.0, 40.0))),
                longitude=Decimal(str(random.uniform(-120.0, -80.0))),
                seo_title=f'Luxury {villa_names[i % len(villa_names)]} - Book Now',
                seo_description=f'Experience luxury at {villa_names[i % len(villa_names)]}. Book your dream vacation today!',
                signature_distinctions=['Ocean View', 'Private Beach Access', 'Concierge Service'][:random.randint(1, 3)],
                staff=[
                    {'role': 'Property Manager', 'name': f'Manager {i+1}'},
                    {'role': 'Housekeeper', 'name': f'Housekeeper {i+1}'}
                ],
                created_by=admin_user,
                assigned_agent=random.choice(agent_users) if status_choice == 'published' else None,
                created_at=timezone.now() - timedelta(days=random.randint(1, 90))
            )
            properties.append(property_obj)

        return properties

    def _generate_test_image(self, color=None):
        """Generate a test image"""
        if color is None:
            color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )
        
        image = Image.new('RGB', (800, 600), color=color)
        file = io.BytesIO()
        image.save(file, format='JPEG')
        file.seek(0)
        return ContentFile(file.read(), name=f'test_image_{random.randint(1000, 9999)}.jpg')

    def _create_media_for_properties(self, properties, media_per_property):
        """Create media files for properties"""
        total_created = 0
        categories = ['exterior', 'bedroom', 'bathroom', 'media', 'other']
        
        for property_obj in properties:
            for i in range(media_per_property):
                Media.objects.create(
                    listing=property_obj,
                    file=self._generate_test_image(),
                    category=categories[i % len(categories)],
                    caption=f'{categories[i % len(categories)].title()} view {i+1}',
                    is_primary=(i == 0),
                    order=i
                )
                total_created += 1

        return total_created

    def _create_bookings(self, count, properties, customer_users):
        """Create sample bookings"""
        bookings = []
        
        # Only create bookings for published properties
        published_properties = [p for p in properties if p.status == 'published']
        
        if not published_properties:
            self.stdout.write(self.style.WARNING('No published properties available for bookings'))
            return bookings

        statuses = ['pending', 'approved', 'rejected', 'completed', 'cancelled']

        for i in range(count):
            property_obj = random.choice(published_properties)
            customer = random.choice(customer_users)
            
            # Generate random dates
            days_ahead = random.randint(1, 90)
            check_in = date.today() + timedelta(days=days_ahead)
            duration = random.randint(3, 14)
            check_out = check_in + timedelta(days=duration)
            
            # Calculate total price
            total_price = property_obj.price * duration
            
            booking = Booking.objects.create(
                property=property_obj,
                user=customer,
                full_name=customer.name,
                email=customer.email,
                phone=customer.phone or f'+1234567{random.randint(100, 999)}',
                check_in=check_in,
                check_out=check_out,
                status=random.choice(statuses),
                total_price=total_price,
                created_at=timezone.now() - timedelta(days=random.randint(1, 60))
            )
            bookings.append(booking)

        return bookings
