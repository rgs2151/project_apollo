from django.test import TestCase, override_settings, RequestFactory
from rest_framework.test import APIRequestFactory
from .models import User, UserDetails
from rest_framework.response import Response
from django.urls import reverse
from django.conf import settings
import requests

from utility.secret import *
from .middleware import TokenAuthMiddleware
from .authentication import TokenAuthentication
from .permissions import *

from django.db.models import Field


"""
when,

USER_MANAGER_SETTINGS.TESTING_MODE = True

Following settings are overwritten
EMAIL.SEND = False

therefore no need to @override_settings

"""

"python manage.py test UserManager"


"python manage.py test UserManager.tests.TestUserDetails.test_issue_token"
"python manage.py test UserManager.tests.TestUserDetails.test_email_verification_get_api"
"python manage.py test UserManager.tests.TestUserDetails.test_issue_password_change"
"python manage.py test UserManager.tests.TestUserDetails.test_change_password"
"python manage.py test UserManager.tests.TestUserDetails.test_say"
"python manage.py test UserManager.tests.TestUserDetails.test_user_login_with_cookies"
class TestUserDetails(TestCase):
    
    serialized_rollback = True
    
    
    def setUp(self) -> None:
        self.factory = RequestFactory()
        
    
    def test_create_django_email_user(self):
        
        user_details = {
            "email": "sample@email.com",
            "password": "SomeValidPassword@123",
            "first_name": "name fields are not compulsory",
            # "last_name": None
        }
        user: User = UserDetails.create_django_email_user(**user_details)
        
        self.assertIsInstance(user, User)
        self.assertTrue(user.password)
        self.assertTrue(user.check_password(user_details["password"]))
    
    
    def get_sample_user(self):
        user_details = {
            "email": "sample@email.com",
            "password": "SomeValidPassword@123",
            "first_name": "name fields are not compulsory",
            # "last_name": None
        }
        return UserDetails.create_django_email_user(**user_details)
    
    
    def test_initialize_user_details(self):
        user = self.get_sample_user()
        request = self.factory.post('/some-url-that-does-not-exist')
        user_details = UserDetails.initialize_user_details(user, request)
        
        self.assertIsInstance(user_details, UserDetails)
        
        email_secret_link, email_sent = user_details.issue_email_secret(request)
        self.assertIsInstance(email_sent, bool)
        
        secret = email_secret_link.split('/')[-1]
        user_details_instance, secret_data = user_details.validate_secret(secret)
        self.assertEqual(user_details_instance.user.id, user_details.user.id)
        self.assertEqual(user_details.user, user)


    def test_user_registration_api_without_email(self):
        response = self.client.post(reverse('user-register'))
        self.assertEqual(response.status_code, 400)
        
        response = self.client.post(reverse('user-register'), {
            "first_name": "manan",
            "last_name": "lad",
            "email": "mananlad38@gmail.com",
            "password": "1Password!",
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        

    def test_issue_token(self):
        
        user = self.get_sample_user()
        request = self.factory.post('/some-url-that-does-not-exist')
        user_details = UserDetails.initialize_user_details(user, request)
        token = user_details.issue_token(request)
        email_secret_link, email_sent = user_details.issue_email_secret(request)
        
        self.assertIsInstance(token, str)
        status, user_details_instance = user_details.validate_token(token)
        self.assertTrue(status)
        
        token = "randomjunk"
        status, user_details_instance = user_details.validate_token(token)
        self.assertFalse(status)
        

    def test_user_login(self):
        
        # register user
        register_payload = {
            "first_name": "manan",
            "last_name": "lad",
            "email": "mananlad38@gmail.com",
            "password": "1Password!",
        }
        response = self.client.post(reverse('user-register'), register_payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # user signin
        login_payload = {
            "email": "mananlad38@gmail.com",
            "password": "1Password!",
        }
        response = self.client.post(reverse('user-login'), login_payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # wrong password
        login_payload = {
            "email": "mananlad38@gmail.com",
            "password": "wrongpassword",
        }
        response = self.client.post(reverse('user-login'), login_payload, content_type='application/json')
        self.assertEqual(response.status_code, 405)
        response = response.json()
        self.assertIn('error', response)
        self.assertIsInstance(response['error'], dict)
        self.assertIn("code", response['error'])
        self.assertEqual(response['error']['code'], "InvalidPassword")


    def test_user_login_with_cookies(self):
        # register user
        register_payload = {
            "first_name": "manan",
            "last_name": "lad",
            "email": "mananlad38@gmail.com",
            "password": "1Password!",
        }
        response = self.client.post(reverse('user-register'), register_payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.cookies['Authorization'].value)
        
        # user signin
        login_payload = {
            "email": "mananlad38@gmail.com",
            "password": "1Password!",
        }
        response = self.client.post(reverse('user-login'), login_payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.cookies['Authorization'].value)
        

    def test_user_details_get(self):
        user_details_instance, response = self.register_user(self.client)
        response = response.json()
        response_ = self.client.get(reverse('user-details'), HTTP_AUTHORIZATION=f"Bearer {response['auth_token']}")
        self.assertEqual(response_.status_code, 200)
        
        response_ = response_.json()
        self.assertEqual(user_details_instance.user.id, response_['user_details']["user"]['id'])
        
        
        response_ = self.client.get(reverse('user-details'), HTTP_AUTHORIZATION=f"Bearer invalidtoken")
        self.assertEqual(response_.status_code, 403)


    def test_email_verification(self):
        user_details_instance, response = self.register_user(self.client)
        response = response.json()
        email_verification_link = response['email_verification_link']
        
        self.assertFalse(user_details_instance.email_verified_at)
        
        status, user_details_instance = user_details_instance.validate_email(email_verification_link.split(r'/')[-1])
        self.assertTrue(status)
        
        user_details_instance = UserDetails.objects.get(user=user_details_instance.user.id)
        self.assertTrue(user_details_instance.email_verified_at)
        
        
    def test_email_verification_get_api(self):
        
        user_details_instance, response = self.register_user(self.client)
        self.assertFalse(user_details_instance.email_verified_at)
        
        response  = response.json()
        email_verification_link = response['email_verification_link']
        
        secret = email_verification_link.split(r'/')[-1]
        response = self.client.get(reverse('user-verify-email', kwargs={"secret": secret}), follow=True)
        self.assertEqual(response.status_code, 200)
        
        user_details_instance = UserDetails.objects.get(user=user_details_instance.user.id)
        self.assertTrue(user_details_instance.email_verified_at)
        
    
    def test_resend_email_verification(self):
        
        user_details_instance, response = self.register_user(self.client)
        response = response.json()
        
        response_ = self.client.post(reverse('user-resend-email-verification'), HTTP_AUTHORIZATION=f"Bearer {response['auth_token']}")
        response_ = response_.json()
        self.assertIn("error", response_)
        self.assertIn("code", response_['error'])
        self.assertEqual(response_['error']["code"], "OnCooldown")
        
    
    def test_user_update_api(self):
        user_details_instance, response = self.register_user(self.client)
        response = response.json()
        
        response_ = self.client.put(reverse('user-update'), data={
            "first_name": "hello",
            "last": "world",
        }, HTTP_AUTHORIZATION=f"Bearer {response['auth_token']}", content_type='application/json')
        response_ = self.client.put(reverse('user-update'), data={}, HTTP_AUTHORIZATION=f"Bearer {response['auth_token']}", content_type='application/json')
        
        print("PENDING TESTCASES for `test_user_update_api`")
        
    
    def test_issue_password_change(self):
        user_details_instance, response = self.register_user(self.client)
        response = response.json()
        request = self.factory.post('some/api', HTTP_AUTHENTICATION=f"Bearer {response['auth_token']}")
        password_change_link, email_sent = user_details_instance.issue_password_change(request)

        user_details_instance = UserDetails.objects.get(user = user_details_instance.user.id)
        self.assertTrue(user_details_instance.password_change_secret)


    def test_change_password(self):

        user_details_instance, response = self.register_user(self.client)
        response = response.json()
        request = self.factory.post('some/api', HTTP_AUTHENTICATION=f"Bearer {response['auth_token']}")
        password_change_link, email_sent = user_details_instance.issue_password_change(request)
        
        password_change_secret = password_change_link.split('/')[-1]
        old_password = "1Password!"
        new_password = "someotherrandompassword"
        status, user_details_instance_after_change_passoword = UserDetails.change_password(password_change_secret, old_password, new_password)
        
        self.assertTrue(status)
        self.assertEqual(user_details_instance.user, user_details_instance_after_change_passoword.user)

        new_passowrd_status = user_details_instance_after_change_passoword.user.check_password(new_password)
        self.assertTrue(new_passowrd_status)
    

    def test_say(self):
        print(">>", len(dir(UserDetails)))
        for attr in dir(UserDetails):
            print(type(getattr(UserDetails, attr)))
            if issubclass(Field, getattr(UserDetails, attr).__class__):
                print(getattr(UserDetails, attr))


    @staticmethod
    def register_user(client):
        
        response = None
        response = client.post(reverse('user-register'), {
            "first_name": "manan",
            "last_name": "lad",
            "email": "mananlad38@gmail.com",
            "password": "1Password!",
        }, content_type='application/json')
        
        if response.status_code == 200:
            response_ = response.json()
            user_details_instance = UserDetails.objects.get(user = response_["user_details"]["user"]["id"])
            return user_details_instance, response
            
        return None, response


"python manage.py test UserManager.tests.TestTokenAuthMiddleware.test_middleware"
class TestTokenAuthMiddleware(TestCase):
    
    def setUp(self):
        
        self.factory = RequestFactory()
        self.middleware = TokenAuthMiddleware(lambda request: Response({'status': 'ok'}, status=200))
        
        self.user_details_instance, response = TestUserDetails.register_user(self.client)
        

    def test_middleware(self):
        
        auth_token = self.user_details_instance.issue_token()
        request = self.factory.get('/some-url-that-does-not-exist', HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        self.middleware.process_request(request)
        
        self.assertIsInstance(request.user_details, UserDetails)
        self.assertIsInstance(request.user, User)
        self.assertEqual(self.user_details_instance, request.user_details)


"python manage.py test UserManager.tests.TestTokenAuthentication.test_authenticator"
"python manage.py test UserManager.tests.TestTokenAuthentication.test_authenticator_cookie_based"
class TestTokenAuthentication(TestCase):
    
    def setUp(self):
        self.factory = APIRequestFactory()
        self.authentication = TokenAuthentication()
        self. user_details_instance, response = TestUserDetails.register_user(self.client)


    def test_authenticator(self):
        
        auth_token = self.user_details_instance.issue_token()
        request = self.factory.get('/some-url-that-does-not-exist', HTTP_AUTHORIZATION=f'Bearer {auth_token}')
        self.authentication.authenticate(request)
        self.assertIsInstance(request.user_details, UserDetails)
        self.assertIsInstance(request.user, User)
        self.assertEqual(self.user_details_instance, request.user_details)



    def test_authenticator_cookie_based(self):
        auth_token = self.user_details_instance.issue_token()
        request = self.factory.get('/some-url-that-does-not-exist')
        request.COOKIES["Authorization"] = f'Bearer {auth_token}'
        self.authentication.authenticate(request)
        self.assertIsInstance(request.user_details, UserDetails)
        self.assertIsInstance(request.user, User)
        self.assertEqual(self.user_details_instance, request.user_details)


from django.contrib.auth.models import Group



"python manage.py test UserManager.tests.TestPermissions.test_verify_email_permission"
"python manage.py test UserManager.tests.TestPermissions.test_is_super_user_permission"
"python manage.py test UserManager.tests.TestPermissions.test_has_group"
class TestPermissions(TestCase):
    
    def setUp(self) -> None:
        self.factory = RequestFactory()
        

    def test_verify_email_permission(self):
        # should allow only if email is not verified
        
        request = self.factory.get('some/path')
        user_details_instance, response = TestUserDetails.register_user(self.client)
        response = response.json()
        user_details_instance: UserDetails

        
        secret = response['email_verification_link'].split(r'/')[-1]
        status, user_details_instance = user_details_instance.validate_email(secret)
        request.user_details = user_details_instance
                
        self.assertTrue(IsEmailVerified().has_permission(request, None))


    def test_is_super_user_permission(self):


        request = self.factory.get('some/path')
        user_details_instance, response = TestUserDetails.register_user(self.client)
        response = response.json()
        user_details_instance: UserDetails

        self.assertFalse(IsSuperUser().has_permission(request, None))
        
        user_details_instance.user.is_superuser = 1
        user_details_instance.user.save()
        request.user_details = user_details_instance

        self.assertTrue(IsSuperUser().has_permission(request, None))


    def test_has_group(self):

        default_group, created_status = Group.objects.get_or_create(name="default")
        doctor_group, created_status = Group.objects.get_or_create(name="doctor")

        request = self.factory.get('some/path')
        user_details_instance, response = TestUserDetails.register_user(self.client)
        response = response.json()
        user_details_instance: UserDetails

        self.assertFalse(HasGroupPermissions("doctor").has_permission(request, None))

        user_details_instance.user.groups.add(doctor_group)
        user_details_instance.user.save()
        request.user_details = user_details_instance
       
        self.assertEqual(Group.objects.all().count(), 2)
        self.assertEqual(user_details_instance.user.groups.all().count(), 1)
        self.assertEqual(user_details_instance.user.groups.first().name, doctor_group.name)

        self.assertTrue(HasGroupPermissions("doctor").has_permission(request, None))
        



