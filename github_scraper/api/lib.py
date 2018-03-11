from flask_restful import Api as BaseApi, Resource as BaseResource

from ..storage import Storage


class Api(BaseApi):
    def __init__(self, storage: Storage, *args, **kwargs):
        self.storage = storage
        super(Api, self).__init__(*args, **kwargs)

    def add_resource(self, resource, url):
        kwargs = {
            'resource_class_kwargs': {'storage': self.storage},
        }
        super(Api, self).add_resource(resource, url, **kwargs)


class Resource(BaseResource):
    def __init__(self, storage: Storage, *args, **kwargs):
        self.storage = storage
        super(Resource, self).__init__(*args, **kwargs)

    def to_list(self, obj_list) -> list:
        return [self.to_dict(obj) for obj in obj_list]

    def to_dict(self, obj) -> dict:
        return obj._asdict()
