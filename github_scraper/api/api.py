from flask import Flask
from flask_restful import abort, reqparse

from ..storage import Storage, Q

from .lib import Api, Resource


def get_app(storage: Storage) -> Flask:
    """ Return Flask app with API endpoints
    """
    app = Flask(__name__)

    api = Api(storage, app)
    api.add_resource(UserList, '/users')
    api.add_resource(User, '/users/<user>')
    api.add_resource(RepoList, '/users/<user>/repos')

    return app


class User(Resource):
    """ User API endpoint: /users/<user>
    """
    def get(self, user):
        user = self.storage.get_user({'login': user})
        if not user:
            abort(404, message='user not found')
        return self.to_dict(user)


class UserList(Resource):
    """ User List API endpoint: /users

    Available filters:
    * since=<int> only display users with id higher than the specified
    """
    def get(self):
        lookup = self.get_lookup()
        since = lookup.pop('since')
        return self.to_list(self.storage.list_users(Q('id') > since,
                                                    lookup,
                                                    limit=30))

    def get_lookup(self):
        parser = reqparse.RequestParser()
        parser.add_argument('since', type=int, default=0)
        return parser.parse_args()


class RepoList(Resource):
    """ User's Repository List endpoint: /users/<user>/repos

    Available filters:
    * description=<text> filters repositories by description
    * language=<text> filters repositories by language
    """
    def get(self, user):
        user = self.storage.get_user({'login': user})
        if not user:
            abort(404, message='user not found')
        repo_lookup = self.get_lookup()
        repo_lookup['user_id'] = user.id
        return self.to_list(self.storage.list_repos(repo_lookup))

    def get_lookup(self):
        parser = reqparse.RequestParser()
        parser.add_argument('description', type=str, store_missing=False)
        parser.add_argument('language', type=str, store_missing=False)
        return parser.parse_args()
