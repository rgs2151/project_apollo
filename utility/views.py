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
from django.http import Http404, HttpResponseNotAllowed
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
            
            request.N_Query_Parameters = {}
            if query_dict_schema:
                request_get = serialize_query_dict_object(request.GET)
                status = validator.validate(request_get, query_dict_schema)
                if not status:
                    raise APIException("RequestValidationFailed", {"validation_failed_for": "query_parameters", "failed_validations": validator.errors})
                request.N_Query_Parameters = validator.normalized(request_get)
                
            
            request.N_Payload = {}
            if schema:
                request_payload = request.data
                status = validator.validate(request_payload, schema)
                if not status:
                    raise APIException("RequestValidationFailed", {"validation_failed_for": "payload", "failed_validations": validator.errors}, status_code=400)
                request.N_Payload = validator.normalized(request_payload)

            
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



class UtilityViewMixin:


    def _u_type_check_model(self, model):
        if not hasattr(self, "model") and not isinstance(self.model, models.Model):
            raise TypeError(f"{self.__class__.__name__} model field is not defined or is invalid")
        
    
    def _u_type_check_serializer(self, serializer):
        if not hasattr(self, "serializer") and not isinstance(serializer, ModelSerializer):
            raise TypeError(f"{self.__class__.__name__} model field is not defined or is invalid")
        

    def _u_type_check_paginator(self, pagination):
        if not hasattr(self, "pagination") and not isinstance(pagination, PageNumberPagination):
            raise TypeError(f"{self.__class__.__name__} model field is not defined or is invalid")


    def _u_check_serializer_belongs_to_model(self, model, serizlizer):
        if not (
            hasattr(serizlizer, 'Meta') and
            hasattr(serizlizer.Meta, 'model') and
            serizlizer.Meta.model == model
        ): raise ValueError(f"serializer class [{serizlizer}] does not belong to the model provided [{model}]")

    
    def _u_check_allowed_methods(self, allowed_methods: list):
        if not (
            self.allow_methods and
            isinstance(self.allow_methods, list) and
            all(method in ["GET", "POST", "PUT", "DELETE"] for method in self.allow_methods)
        ): raise ValueError(f"allow method invalid for class {self.__class__.__name__}")


    def _u_check_filters_with_model(self, allow_filters, model, ignore_filter=[]):
        if allow_filters:
            filters = allow_filters.copy()
            awailable_fields = model._meta.get_fields()
            for field in filters:
                
                # for some reason this key comming even if we ignore it
                if ignore_filter and field in ignore_filter: continue

                if not any(field.startswith(key.name) for key in awailable_fields):
                    raise ValueError(f"{self.__class__.__name__} allow_filters, key not found: {field}")
                

    def _u_attach_exception_handler(self, method_name, **kwargs):
        method = self.__getattribute__(method_name)
        self.__setattr__(method_name, exception_handler(**kwargs)(method))
        

    def _u_attach_request_validator(self, method_name, excep_handler=None, **kwargs):
        method = self.__getattribute__(method_name)
        if not excep_handler: excep_handler = exception_handler()
        self.__setattr__(method_name, excep_handler(request_schema_validation(**kwargs)(method)))


    def _u_get_filters(self, filters, request):
        _filters = filters.copy()
        _filters = {k: v if not callable(v) else v(request) for k, v in _filters.items()}
        return _filters


class UtilityMongoViewMixin(UtilityViewMixin):


    def _u_check_filters_with_model(self, allow_filters, model, ignore_filter=[]):
        if allow_filters:
            filters = allow_filters.copy()
            awailable_fields = model._fields
            for field in filters:
                
                # for some reason this key comming even if we ignore it
                if ignore_filter and field in ignore_filter: continue

                if not any(field.startswith(name) for name in awailable_fields):
                    raise ValueError(f"{self.__class__.__name__} allow_filters, key not found: {field}")


class DefaultPagination(PageNumberPagination):
    
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def __init__(self, page_size=10) -> None:
        self.page_size = page_size
        super().__init__()


class _FilteredListView:

    model = None
    serializer = None
    pagination: bool = True

    allow_filters = {}

    static_filters = {}
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._check_view()

    
    def _check_view(self):

        self._u_type_check_model(self.model)
        self._u_type_check_serializer(self.serializer)
        # if self.pagination: self._u_type_check_paginator(self.pagination)

        # check allow_filters:
        self._u_check_filters_with_model(self.allow_filters, self.model, ignore_filter=["page", "page_size"])

        # check static filters present in model
        self._u_check_filters_with_model({k: "" for k in self.static_filters}, self.model)

        self.validator = cerberus.Validator()

        # adding page number rule to schema which will defualt to 1
        if self.pagination:
            self.allow_filters["page"] = {"coerce": int, "type": "integer", "required": False, "min": 1, "default": 1}
            self.allow_filters["page_size"] = {"coerce": int, "type": "integer", "required": False, "min": 1, "default": self.pagination.page_size}

        # decorating get method
        self.get = exception_handler()(request_schema_validation(query_dict_schema=self.allow_filters)(self.get))


    def get_static_filters(self, request):
        return self._u_get_filters(self.static_filters, request)
        

    def get_paginator(self, page_size: int):
        return DefaultPagination(page_size=page_size)


    def get(self, request, *args, **kwargs):
        
        req: dict = request.N_Query_Parameters
        page_no: int = None
        page_size: int = None
        pagination: DefaultPagination = None
        if self.pagination:
            page_no = req.pop("page")
            page_size = req.pop("page_size")
            pagination = self.get_paginator(page_size)

        req.update(self.get_static_filters(request))

        queryset = self.model.objects.filter(**req)

        response = {}

        if self.pagination:
            try:
                queryset = pagination.paginate_queryset(queryset, request)
                response["page"] = {"current": page_no, "count": pagination.page.paginator.num_pages}
            except NotFound as err: raise Http404(request)

        
        response["data"] = self.serializer(queryset, many=True).data


        return Response(response)


class FilteredListView(UtilityViewMixin, _FilteredListView, APIView): pass


class MongoFilteredListView(UtilityMongoViewMixin, _FilteredListView, APIView): pass

    
class _ModelManagerView:

    allow_methods = ["GET", "POST", "PUT", "DELETE"]

    model = None # handles only 1 model at level 1

    serializer = None # default serializer

    unique_primaries = []
    
    # cerberus filters
    # if not provided default will be used and if default not set will raise exception
    # will be injected to request without checking for dtypes
    GET_filter = {}
    GET_serializer = None
    GET_inject = {}

    POST_filter = {}
    POST_serializer = None
    POST_inject = {}

    PUT_filter = {}
    PUT_serializer = None
    PUT_inject = {}

    DELETE_filter = {}
    DELETE_serializer = None
    DELETE_inject = {}


    _request_validator_params = {}


    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.__init()


    def __init(self):

        self._u_type_check_model(self.model)
        if self.serializer:
            self._u_type_check_model(self.serializer)
            self._u_check_serializer_belongs_to_model(self.model, self.serializer)
        if self.GET_serializer: 
            self._u_type_check_model(self.GET_serializer)
            self._u_check_serializer_belongs_to_model(self.model, self.GET_serializer)
        if self.POST_serializer: 
            self._u_type_check_model(self.POST_serializer)
            self._u_check_serializer_belongs_to_model(self.model, self.POST_serializer)
        if self.PUT_serializer: 
            self._u_type_check_model(self.PUT_serializer)
            self._u_check_serializer_belongs_to_model(self.model, self.PUT_serializer)
        if self.DELETE_serializer: 
            self._u_type_check_model(self.DELETE_serializer)
            self._u_check_serializer_belongs_to_model(self.model, self.DELETE_serializer)

        if self.GET_filter: self._u_check_filters_with_model(self.GET_filter, model=self.model)
        if self.POST_filter: self._u_check_filters_with_model(self.POST_filter, model=self.model)
        if self.PUT_filter: self._u_check_filters_with_model(self.PUT_filter, model=self.model)
        if self.DELETE_filter: self._u_check_filters_with_model(self.DELETE_filter, model=self.model)

        # check primaries
        if self.unique_primaries:
            self._u_check_filters_with_model({key: "" for key in self.unique_primaries}, model=self.model)

        self._u_check_allowed_methods(self.allow_methods)
        # check if unique_primaries are present in the put filters
        put_key_checks = list(self.PUT_inject.keys()) + list(self.PUT_filter.keys())
        if not any(primary in put_key_checks for primary in self.unique_primaries):
            raise ValueError("not any unique primaries present in Put_filter")

        
        for method in [x for x in ["GET", "POST", "PUT", "DELETE"] if x not in self.allow_methods]:
            def _method(method):
                def func(*args, **kwargs):
                    raise APIException("Method Not Allowed", f"method {method} not allowed", status_code=405)
                return func
            self.__setattr__(method.lower(),  _method(method))
            self._u_attach_exception_handler(method.lower())
            
        if self.serializer == None:
            for method_name in self.allow_methods:
                if self.__getattribute__(f"{method_name.upper()}_serializer") == None:
                    raise ValueError(f"default serializer is not set, no specific serializer found for the method: {method_name}")

        else:
            for method_name in self.allow_methods:
                if self.__getattribute__(f"{method_name.upper()}_serializer") == None:
                    self.__setattr__(f"{method_name.upper()}_serializer", self.serializer)
        
        if "GET" in self.allow_methods: self._u_attach_request_validator("get", query_dict_schema=self.GET_filter, **self._request_validator_params)
        if "POST" in self.allow_methods: self._u_attach_request_validator("post", schema=self.POST_filter, **self._request_validator_params)
        if "PUT" in self.allow_methods: self._u_attach_request_validator("put", schema=self.PUT_filter, **self._request_validator_params)
        if "DELETE" in self.allow_methods: self._u_attach_request_validator("delete", schema=self.DELETE_filter, **self._request_validator_params)        
        
        
    def check_if_exists(self, filters):
        return self.model.objects.filter(**filters).exists()


    def get(self, request: Request):

        req = request.N_Query_Parameters

        static_filters = self._u_get_filters(self.GET_inject, request)
        req.update(static_filters)


        response = {}
        if self.check_if_exists(req):
            instance = self.model.objects.filter(**req).first()
            response = self.GET_serializer(instance).data

        return Response(response)


    def post(self, request: Request):

        req = request.N_Payload

        # check if primary exists
        primaries = {k: req.get(k) for k in self.unique_primaries}
        if primaries and self.check_if_exists(primaries):
            raise APIException("Already Exists", "required instance aready exists", status_code=400)
        
        try: 
            instance = self.model(**req)
            instance.save()
        except Exception as err: raise APIException("Invalid", "failed to create the instance", status_code=400)

        created_instance = self.POST_serializer(instance).data

        return Response(created_instance)


    def put(self, request: Request):

        req = request.N_Payload

        if not req:
            raise APIException("Request Validation Failed", "nothing to update", status_code=400)

        # get the primaries
        # primaries should be included in the filter provided
        primaries = {primary: req.get(primary) for primary in self.unique_primaries if req.get(primary, False)}
        if not self.check_if_exists(primaries):
            raise APIException("Not Found", "Instance not found", status_code=404)

        try:

            static_filters = self._u_get_filters(self.PUT_inject, request)
            req.update(static_filters)

            instance = self.model.objects(**primaries).first()
            for field, value in req.items(): instance.__setattr__(field, value)
            instance.save()
        except Exception as err: raise APIException("Invalid", "failed to update the instance", status_code=400)

        updated_instance = self.PUT_serializer(instance).data

        return Response(updated_instance)


    def delete(self, request: Request):

        # check if primary exists

        # if exists delete

        # multiple delete allow false

        pass


class ModelManagerView(UtilityViewMixin, _ModelManagerView, APIView): pass


class MongoModelManagerView(UtilityMongoViewMixin, _ModelManagerView, APIView):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


    def check_if_exists(self, filters):
        return self.model.objects.filter(**filters).count()





