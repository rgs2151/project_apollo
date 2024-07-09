
import cerberus, re
import traceback as tb
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework.serializers import ModelSerializer
from rest_framework.pagination import PageNumberPagination
from django.urls.exceptions import NoReverseMatch
from django.urls import reverse, get_resolver, get_callable
from django.http import Http404
from django.db import models


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
                if handler_404: return handler_404(err.request, "")
                else: 
                    trace = ''.join(tb.format_exception(None, err, err.__traceback__))
                    return APIException("Not Found", "page not found", trace=trace, status_code=400).get_response()

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


class FilteredListView(APIView):
    
    model = None
    serializer = None
    pagination = None

    allow_filters = {}
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._check_view()

    def _check_view(self):

        if not hasattr(self, "model") and not isinstance(self.model, models.Model):
            raise TypeError(f"{self.__class__.__name__} model field is not defined or is invalid")
        
        if not hasattr(self, "serializer") and not isinstance(self.serializer, ModelSerializer):
            raise TypeError(f"{self.__class__.__name__} model field is not defined or is invalid")
        
        if not hasattr(self, "pagination") and not isinstance(self.pagination, PageNumberPagination):
            raise TypeError(f"{self.__class__.__name__} model field is not defined or is invalid")

        # check allow_filters:
        
        if self.allow_filters:
            filters = self.allow_filters.copy()
            awailable_fields = self.model._meta.get_fields()
            for field in filters:
                
                # for some reason this key comming even if we ignore it
                if field == "page": continue

                if not any(field.startswith(key.name) for key in awailable_fields):
                    raise ValueError(f"{self.__class__.__name__} allow_filters, key not found: {field}")
                

        self.validator = cerberus.Validator()

        # adding page number rule to schema which will defualt to 1
        self.allow_filters["page"] = {"coerce": int, "type": "integer", "required": False, "min": 1, "default": 1}

        # decorating get method
        self.get = exception_handler()(request_schema_validation(query_dict_schema=self.allow_filters)(self.get))
                

    def get(self, request, *args, **kwargs):
        
        req = serialize_query_dict_object(request.GET)
        _ = req.pop("page", 1)

        if not self.allow_filters: queryset = self.model.objects.all()
        else: queryset = self.model.objects.filter(**req)

        try: paginated_queryset = self.pagination.paginate_queryset(queryset, request)
        except NotFound as err: raise Http404(request)

        serialized = self.serializer(paginated_queryset, many=True)

        return Response({"data": serialized.data})


