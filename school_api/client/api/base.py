# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals


class BaseSchoolApi(object):
    """ WeChat API base class """

    def __init__(self, client=None):
        self._client = client

    def _get(self, url, **kwargs):
        return self._client.get(url, **kwargs)

    def _post(self, url, **kwargs):
        return self._client.post(url, **kwargs)

    def _head(self, url, **kwargs):
        return self._client.head(url, **kwargs)

    def _get_view_state(self, url, **kwargs):
        return self._client.get_view_state(url, **kwargs)

    def _update_headers(self, headers_dict):
        return self._client.update_headers(headers_dict)

    def _get_login_view_state(self, **kwargs):
        return self._client.get_login_view_state(**kwargs)

    def _set_proxy(self):
        return self._client.set_proxy()

    @property
    def code(self):
        return self._client.school.code

    @property
    def account(self):
        return self._client.account

    @property
    def password(self):
        return self._client.password

    @property
    def session(self):
        return self._client.session

    @property
    def user_type(self):
        return self._client.user_type

    @property
    def base_url(self):
        return self._client.base_url

    @property
    def school_url(self):
        return self._client.school.url_endpoint[self.user_type]

    @property
    def time_list(self):
        return self._client.school.time_list
