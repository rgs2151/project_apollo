
import cerberus, re
import traceback as tb
from rest_framework.request import Request
from rest_framework.response import Response
from django.urls.exceptions import NoReverseMatch
from django.urls import reverse, get_resolver, get_callable
from django.http import Http404


def serialize_query_dict_object(query_dict):
    collect = {}
    for key, value in query_dict.items():
        if not value: value = None
        elif len(value) == 1: value = value[0]
        collect[key] = value
    return collect


class APIException(Exception):
    
    def __init__(self, code, message, include_in_response={}, trace="", status_code=500, *args: object) -> None:
        super().__init__(*args)
        
        if not isinstance(status_code, int): raise TypeError("status_code should be of type int")
        self.status_code = status_code
        
        self.code = str(code)
        
        self.message = message
        
        if not isinstance(include_in_response, dict): raise TypeError("include_in_response should be of type dict")
        self.include_in_response = include_in_response.copy()
        
        self.trace = trace
        
        
    def get_response(self):
        response = self.include_in_response.copy()
        response["error"] = {}
        response["error"]["code"] = self.code
        response["error"]["message"] = self.message
        return Response(response, status=self.status_code)
    
    
    @classmethod
    def from_exception(cls, err: Exception, code, message, include_in_response={}, status_code=500, *args: object):
        if not isinstance(err, Exception):
            raise TypeError("err has to be of type Exception")
        
        trace = ''.join(tb.format_exception(None, err, err.__traceback__))
        return cls(code, message, include_in_response={}, trace=trace, status_code=500, *args)


class Http404(Http404):

    def __init__(self, request, *args: object) -> None:
        super().__init__(*args)
        self.request = request


class DefaultValidator(cerberus.Validator):
    
    def _check_with_email(self, field, value):
        pattern = r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+'
        if not (re.match(pattern, value) is not None): self._error(field, "email pattern invalid")
    
    def _check_with_password(self, field, value):
        # Accepted special chars: @, #, $, %, ^, &, +, =, !
        pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{8,}$'
        if not (re.match(pattern, value) is not None): self._error(field, "passowrd pattern invalid")


def request_schema_validation(schema={}, query_dict_schema={}, validator=DefaultValidator(allow_unknown=False)):
    
    def internal_wrapper(func):
    
        def wrapper(*args, **kwargs):
            args_ = [arg for arg in args if isinstance(arg, Request)]
            if not args_ or len(args_) > 1:
                raise Exception("invalid args, no rest_framework.request.Request instance detected in args")
            
            request: Request = args_[0]
            
            if query_dict_schema:
                request_get = serialize_query_dict_object(request.GET)
                status = validator.validate(request_get, query_dict_schema)
                if not status:
                    raise APIException("RequestValidationFailed", {"validation_failed_for": "query_parameters", "failed_validations": validator.errors})
            
            if schema:
                request_payload = request.data
                status = validator.validate(request_payload, schema)
                if not status:
                    raise APIException("RequestValidationFailed", {"validation_failed_for": "payload", "failed_validations": validator.errors}, status_code=400)

            
            return func(*args, **kwargs)
    
        return wrapper
    
    return internal_wrapper


def get_404_handler():
    resolver = get_resolver()
    urlconf_module = resolver.urlconf_module

    handler404_view = None
    if urlconf_module:
        try: handler404_view = get_callable(urlconf_module.handler404)
        except AttributeError: pass

    return handler404_view


def exception_handler(default_code="Internal Server Error", default_message="something went wrong", on_exception = None):
    
    if on_exception and not callable(on_exception):
        raise Exception("on_exception should be callable")
    
    def internal_wrapper(func):

        def wrapper(*args, **kwargs):
            error_object = None
            try: return func(*args, **kwargs)
            
            except APIException as err: error_object = err

            except Http404 as err:
                handler_404 = get_404_handler()
                return handler_404(err.request, "")

            except Exception as err:
                trace = ''.join(tb.format_exception(None, err, err.__traceback__))
                error_object = APIException(default_code, default_message, trace=trace)
                print(">>")
                print(error_object.trace)
                print(">>")
                
            if error_object and on_exception: on_exception(error_object)
            
            return error_object.get_response()
                
        return wrapper
    
    return internal_wrapper


def get_request_ip(request: Request):
    return {
        'REMOTE_ADDR': request.META.get('REMOTE_ADDR', None),
        'HTTP_X_FORWARDED_FOR': request.META.get('HTTP_X_FORWARDED_FOR', None),
        'HTTP_X_REAL_IP': request.META.get('HTTP_X_REAL_IP', None),
    }


def get_url_or_named_url(url, request, kwargs={}):
    
    if url.startswith('http://') or url.startswith('https://'):
        return url
    
    try:
        url = reverse(url, kwargs=kwargs)
        return request.build_absolute_uri(url)
        
    except NoReverseMatch:
        raise ValueError(f"invalid url or url not found")

