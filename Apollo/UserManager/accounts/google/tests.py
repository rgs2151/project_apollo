from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.test import APIRequestFactory
from rest_framework.response import Response
from .auhentication import *
from .model import *
from unittest.mock import patch, MagicMock


"python manage.py test UserManager.accounts.google.tests.TestGoogle.test_redirect_route"
"python manage.py test UserManager.accounts.google.tests.TestGoogle.test_create_google_user"
"python manage.py test UserManager.accounts.google.tests.TestGoogle.test_get_or_create_instance"
class TestGoogle(TestCase):

    
    success_token_response = {
        'access_token': 'ya29.a0AcM612zbEeywSC_14GD9GXnZQJ4ceL2BXy-3OZfBwkMpaUoKuFHbxOw9zn5bYEBtu5rSFjlVtu_D77xwwzgZTdVl8QzqGtjWenKdfXORiNK5uX4KK3k3IU_Vx9yoR0ZBFam8xKZjcbTae9AGtpReYtVTNSE6yX38oAgnaCgYKAf0SARMSFQHGX2MiNGPAKHFuPgCBPfN8Ul4U5g0171',
        'expires_in': 3599,
        'refresh_token': '1//0gfV4RwNQg1mwCgYIARAAGBASNwF-L9IrSKT4UVyOGT3YTV69tHSFiEuXuKbA4hfkzentVck9Ev3VMj0nIUti26LKy7pU_eSY0U4',
        'scope': 'https://www.googleapis.com/auth/userinfo.email openid',
        'token_type': 'Bearer',
        'id_token': 'eyJhbGciOiJSUzI1NiIsImtpZCI6ImQyZDQ0NGNmOGM1ZTNhZTgzODZkNjZhMTNhMzE2OTc2YWEzNjk5OTEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiI2MDY2NzI0MjM1MC1iY2g5aGI0NzM5aWFxczZ0OTFkZGRjMWpsYm5pYnFiZy5hcHBzLmdvb2dsZXVzZXJjb250ZW50LmNvbSIsImF1ZCI6IjYwNjY3MjQyMzUwLWJjaDloYjQ3MzlpYXFzNnQ5MWRkZGMxamxibmlicWJnLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwic3ViIjoiMTA4Mjg0OTEyNDQzNjg0ODk5NzAyIiwiZW1haWwiOiJsdWNreWNhc3VhbGd1eUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiYXRfaGFzaCI6IjFhMWhrWjBUUW80bkxBeXU4SnhVY1EiLCJpYXQiOjE3MjM4MTU5NjYsImV4cCI6MTcyMzgxOTU2Nn0.FPf-jlaisEpyyhEv5n8Twh1hNOpygzSaEk25U8XIQ0V1PBsRBy0hJdy_49I65YzA_zoUn3uCoDh1Gr_oy1FoTaEhlEhQib8SF6OxakLPfrfEKEGZWPmPMZhMpNieYfIkPJZrGfA-d6qrj_Q4f3HpIjDfqoIFs9sHF9la0aEyD91klkunTEWkj3aGauzWHL03MGh93DZYvjwcFLRL1r4e3dQpLJhj0DImPx3jjk_z829rz2gG9cAY5Sakok2O62OMBH3Nndb1lylkJmmMEPYJX5xknVpsVB_wy05PL64loNt0FJjNWhjUgyYfA-mbwMC6gorm0yCLImNWU5s2HcfC1g'
    }

    {
        'access_token': 'ya29.a0AcM612zOWlNXutyMP2YwwDtMUwgHV47r81C7K_q5QgySNw4_tA7AahoDITblEcD_6sYVjU4rGZTPkpgXPAvJqZkd39i0NM5HOTPno8ynZvuavTViMDSJQcN9gs2xWk17b20TLfOSrZV26ssyOZJbVyWwXgmyI4ZiiBvjWI4caCgYKAeISARMSFQHGX2MiEiiey4cqXbRCu6eYyhab2w0175',
        'expires_in': 3571,
        'scope': 'https://www.googleapis.com/auth/userinfo.email openid',
        'token_type': 'Bearer',
        'id_token': 'eyJhbGciOiJSUzI1NiIsImtpZCI6ImE0OTM5MWJmNTJiNThjMWQ1NjAyNTVjMmYyYTA0ZTU5ZTIyYTdiNjUiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiI2MDY2NzI0MjM1MC1iY2g5aGI0NzM5aWFxczZ0OTFkZGRjMWpsYm5pYnFiZy5hcHBzLmdvb2dsZXVzZXJjb250ZW50LmNvbSIsImF1ZCI6IjYwNjY3MjQyMzUwLWJjaDloYjQ3MzlpYXFzNnQ5MWRkZGMxamxibmlicWJnLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwic3ViIjoiMTA4Mjg0OTEyNDQzNjg0ODk5NzAyIiwiZW1haWwiOiJsdWNreWNhc3VhbGd1eUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiYXRfaGFzaCI6InhjamRYUzBlZ1RobXh2alJSTXRWQ2ciLCJpYXQiOjE3MjQzOTQ3MjgsImV4cCI6MTcyNDM5ODMyOH0.qfGDwyozG3lri-iGHcPKbj6UkGF3Cxz-nH3yVPnaesI-OsAGgOtlfLnExLh-JyhwpmxBhXALIIaVVqAcXKAicOKXywgaSgbEMx9NoFscJcoAFWCrmvIUazo0vvdShnwgUFqORD_y8-3ql-dOEHEqgshlah0GR4JKWbaq7oS29pM2jQDFU8gY-vrGuzW_lCE525PG39dvLkbrI7GBWSEfP9ZHu4sbLXdzxLbbW_eJln2AKpQ53C6kEmyjP04LP7wjEK9FXffkaf2bkPMfT5F0Lc_G0QrWIK3wrdTYL58rnbIIs1slrH2XQ0AuOqCJtEyx56sgZTAJYhvoA1bvaht6gA'
    }

    success_user_info_response = {
        "id": "108284912443684899702",
        "email": "luckycasualguy@gmail.com",
        "verified_email": True,
        "name": "Manan Lad",
        "picture": "https://lh3.googleusercontent.com/a-/ALV-UjVX8-LmHHxWswIhQPaXUV2vYxrXUr9tefzha7I-DDjRlUQ52zJ8=s96-c"
    }


    def setUp(self):
        
        self.factory = APIRequestFactory()
        self.state = "69c146bad976ba33f6003f3c20feda9aaf41659559cb1cefcd317c673ee8bc22"
        self.redirect_url_query = f"?state={self.state}&code=4/0AcvDMrCb_rJPYXeGqXmdQ3_43cNUEqDI0o3fANigmjGhizU05J280OtvqpCwUW-u8uwrAA&scope=email%20openid%20https://www.googleapis.com/auth/userinfo.email&authuser=0&prompt=consent"
        self.redirected_url = f"http://127.0.0.1:8000/user/google-redirect{self.redirect_url_query}"
        self.redirected_request = self.factory.get(self.redirected_url)

    @patch("UserManager.accounts.google.model.Google.get_token")
    @patch("UserManager.accounts.google.model.Google.get_user_info")
    def test_redirect_route(self, mock_user_info, mock_get_token):

        mock_get_token.return_value = self.success_token_response
        mock_user_info.return_value = self.success_user_info_response

        response = self.client.get(reverse('user-google-redirect'))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse('user-google-redirect') + self.redirect_url_query, HTTP_STATE=self.state, follow=True)
        self.assertEqual(response.status_code, 200)

        user_details = UserDetails.objects.filter(user__email=self.success_user_info_response["email"]).first()
        self.assertTrue(user_details)
        self.assertTrue(user_details.user.email)
        self.assertTrue(user_details.user.first_name)
        self.assertTrue(user_details.user.last_name)
        self.assertEqual(user_details.login_type, LoginType.make_sure_has("google", "v2"))

        user_details_count = UserDetails.objects.filter(user__email=self.success_user_info_response["email"]).count()
        self.assertEqual(user_details_count, 1)

        google = Google.objects.filter(user_details=user_details).first()
        self.assertTrue(google)
        self.assertTrue(google.refresh_token)
        self.assertTrue(google.google_id)

        response = self.client.get(reverse('user-google-redirect') + self.redirect_url_query, HTTP_STATE=self.state, follow=True)
        self.assertEqual(response.status_code, 200)

        user_details_count = UserDetails.objects.filter(user__email=self.success_user_info_response["email"]).count()
        self.assertEqual(user_details_count, 1)


    def test_get_redirect_data(self):
        
        redirected_data = Google.get_redirect_data(self.redirected_request)

        self.assertIsInstance(redirected_data, dict)
        
        self.assertIn("code", redirected_data)
        self.assertIn("state", redirected_data)
        self.assertIn("scope", redirected_data)
        self.assertIn("authuser", redirected_data)
        self.assertIn("prompt", redirected_data)

        self.assertEqual(self.state, redirected_data["state"])

    
    @patch("requests.post")
    def test_get_token(self, mock_post):
        
        mock_success_token_resonse = MagicMock()
        mock_success_token_resonse.status_code = 200
        mock_success_token_resonse.json.return_value = self.success_token_response
        mock_post.return_value = mock_success_token_resonse

        token_data = Google.get_token(self.redirected_request)

        mock_post.assert_called_once()
        mock_success_token_resonse.json.assert_called_once()

        self.assertIn("access_token", token_data)
        self.assertTrue(token_data.get("access_token"))


    @patch('requests.get')
    def test_get_user_info(self, mock_get):
        
        mock_user_info_response = MagicMock()
        mock_user_info_response.status_code = 200
        mock_user_info_response.json.return_value = self.success_user_info_response
        mock_get.return_value = mock_user_info_response

        token_data = self.success_token_response

        self.assertIn('access_token', token_data)

        user_info = Google.get_user_info(token_data['access_token'])

        mock_user_info_response.json.assert_called_once()
        mock_get.assert_called_once_with(Google.USER_INFO_URL, headers={'Authorization': f'Bearer {token_data["access_token"]}'})


    @patch('requests.get')
    def test_validate_token(self, mock_get):

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = self.success_user_info_response
        mock_get.return_value = mock_response

        access_token = 'ya29.a0AcM612zOWlNXutyMP2YwwDtMUwgHV47r81C7K_q5QgySNw4_tA7AahoDITblEcD_6sYVjU4rGZTPkpgXPAvJqZkd39i0NM5HOTPno8ynZvuavTViMDSJQcN9gs2xWk17b20TLfOSrZV26ssyOZJbVyWwXgmyI4ZiiBvjWI4caCgYKAeISARMSFQHGX2MiEiiey4cqXbRCu6eYyhab2w0175'
        status = Google.validate_token(access_token)
        self.assertTrue(status)


    def test_create_google_user(self):
        request = self.factory.get("some/api")
        user_details_data = {
            "email": "some@email.com",
            "first_name": "test",
            "last_name": "user"
        }
        user_details = Google.create_google_user(user_details_data, request)

        self.assertIsInstance(user_details, UserDetails)
        self.assertTrue(user_details.user.id)
        self.assertEqual(user_details_data['email'], user_details.user.email)


    @patch("UserManager.accounts.google.model.Google.get_token")
    @patch("UserManager.accounts.google.model.Google.get_user_info")
    def test_get_or_create_instance(self, mock_user_info, mock_get_token):

        mock_get_token.return_value = self.success_token_response
        mock_user_info.return_value = self.success_user_info_response

        state = Google.generate_state()
        request = self.factory.get(f'/redirect?state={state}&code=4/0AcvDMrCb_rJPYXeGqXmdQ3_43cNUEqDI0o3fANigmjGhizU05J280OtvqpCwUW-u8uwrAA&scope=email%20openid%20https://www.googleapis.com/auth/userinfo.email&authuser=0&prompt=consent', HTTP_state="")

        google_token, access_token = Google.get_or_create_instance(request)

        self.assertIsInstance(google_token, Google)
        self.assertIsInstance(access_token, str)

        self.assertEqual(google_token.user_details.user.email, self.success_user_info_response["email"])


    def test_refresh(self):
        google_token, access_token = self.get_google_user()
        google_token.refresh()



    @classmethod
    @patch("UserManager.accounts.google.model.Google.get_token")
    @patch("UserManager.accounts.google.model.Google.get_user_info")
    def get_google_user(cls, mock_user_info, mock_get_token):

        mock_get_token.return_value = cls.success_token_response
        mock_user_info.return_value = cls.success_user_info_response

        state = Google.generate_state()
        factory = RequestFactory()
        request = factory.get(f'/redirect?state={state}&code=4/0AcvDMrCb_rJPYXeGqXmdQ3_43cNUEqDI0o3fANigmjGhizU05J280OtvqpCwUW-u8uwrAA&scope=email%20openid%20https://www.googleapis.com/auth/userinfo.email&authuser=0&prompt=consent', HTTP_state="")
        return Google.get_or_create_instance(request)



"python manage.py test UserManager.accounts.google.tests.TestAuthentication.test_state_authentication"
"python manage.py test UserManager.accounts.google.tests.TestAuthentication.test_token_authentication"
class TestAuthentication(TestCase):
    

    def setUp(self):
        self.factory = APIRequestFactory()
        self.state_authentication = StateAuthentication()
        self.token_authentication = TokenAuthentication()

    
    def test_state_authentication(self):

        state = Google.generate_state()
        request = self.factory.get(f'/redirect?state={state}&code=4/0AcvDMrCb_rJPYXeGqXmdQ3_43cNUEqDI0o3fANigmjGhizU05J280OtvqpCwUW-u8uwrAA&scope=email%20openid%20https://www.googleapis.com/auth/userinfo.email&authuser=0&prompt=consent', HTTP_state="")
    
        with self.assertRaises(AuthenticationFailed):
            self.state_authentication.authenticate(request)
    
        request = self.factory.get(f'/redirect?state={state}&code=4/0AcvDMrCb_rJPYXeGqXmdQ3_43cNUEqDI0o3fANigmjGhizU05J280OtvqpCwUW-u8uwrAA&scope=email%20openid%20https://www.googleapis.com/auth/userinfo.email&authuser=0&prompt=consent', HTTP_state=state)
        self.state_authentication.authenticate(request)
        self.assertEqual(state, request.state)

        request = self.factory.get(f'/redirect?state={state}&code=4/0AcvDMrCb_rJPYXeGqXmdQ3_43cNUEqDI0o3fANigmjGhizU05J280OtvqpCwUW-u8uwrAA&scope=email%20openid%20https://www.googleapis.com/auth/userinfo.email&authuser=0&prompt=consent')
        request.COOKIES["State"] = state
        self.state_authentication.authenticate(request)
        self.assertEqual(state, request.state)


    @patch("UserManager.accounts.google.model.Google.validate_token")
    def test_token_authentication(self, mock_validate_token):

        mock_validate_token.return_value = True
        
        request = self.factory.get("some/path")

        with self.assertRaises(AuthenticationFailed):
            self.token_authentication.authenticate(request)

        goole_token, access_token = TestGoogle.get_google_user()
        self.assertIsInstance(goole_token, Google)
        self.assertIsInstance(access_token, str)
        
        auth_token = goole_token.issue_token(request, access_token)
        request = self.factory.get("some/path", HTTP_AUTHORIZATION=f"Bearer {auth_token}")
        self.token_authentication.authenticate(request)
        self.assertTrue(request.user_details)
        self.assertTrue(request.user_details.user)

        request = self.factory.get("some/path", HTTP_AUTHORIZATION=f"Bearer {auth_token}")
        request.COOKIES["Authorization"] = f"Bearer {auth_token}"
        self.token_authentication.authenticate(request)
        self.assertTrue(request.user_details)
        self.assertTrue(request.user_details.user)

