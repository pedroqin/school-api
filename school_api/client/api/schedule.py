# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from six.moves.urllib import parse

from bs4 import BeautifulSoup
from requests import RequestException

from school_api.client.api.base import BaseSchoolApi
from school_api.client.api.utils import get_tip, get_view_state_from_html
from school_api.client.api.utils.schedule_parse import ScheduleParse
from school_api.client.utils import ScheduleType, UserType
from school_api.utils import to_text
from school_api.exceptions import ScheduleException


class Schedule(BaseSchoolApi):
    schedule_type = None
    schedule_year = None
    schedule_term = None
    schedule_url = None

    def get_schedule(self, schedule_year=None, schedule_term=None, schedule_type=None, **kwargs):
        ''' 课表信息 获取入口 '''
        self.schedule_type = ScheduleType.CLASS if self.user_type \
            else schedule_type or ScheduleType.PERSON
        self.schedule_year = schedule_year
        self.schedule_term = str(schedule_term)
        self.schedule_url = self.school_url["SCHEDULE_URL"][self.schedule_type]

        if self.user_type != UserType.DEPT:
            self.schedule_url += self.account
            data = self._get_api(**kwargs)
        else:
            self.schedule_url += parse.quote(self.account.encode('gb2312'))
            data = self._get_api_by_bm(**kwargs)

        return data

    def _get_api(self, **kwargs):
        coding = 'gbk' if self.user_type else 'GB18030'
        try:
            res = self._get(self.schedule_url, **kwargs)

            if res.status_code == 302:
                raise ScheduleException(self.code, '课表接口已关闭')
            elif res.status_code != 200:
                raise RequestException
        except RequestException:
            raise ScheduleException(self.code, '获取课表请求参数失败')

        html = res.content.decode(coding)
        tip = get_tip(html)
        if tip:
            raise ScheduleException(self.code, tip)

        schedule = ScheduleParse(html, self.time_list, self.schedule_type).get_schedule_dict()
        # 第一次请求的时候，教务系统默认返回最新课表
        # 如果设置了学年跟学期，匹配学年跟学期，不匹配则获取指定学年学期的课表
        if self.schedule_year and self.schedule_term:
            if self.schedule_year != schedule['schedule_year'] or \
                    self.schedule_term != schedule['schedule_term']:

                payload = self._get_payload(res.text)

                try:
                    res = self._post(self.schedule_url, data=payload, **kwargs)
                    if res.status_code != 200:
                        raise RequestException
                except RequestException:
                    raise ScheduleException(self.code, '获取课表信息失败')

                html = res.content.decode(coding)
                schedule = ScheduleParse(
                    html,
                    self.time_list,
                    self.schedule_type
                ).get_schedule_dict()

        return schedule

    def _get_payload(self, html):
        ''' 获取课表post 的参数 '''
        view_state = get_view_state_from_html(html)
        payload = {
            '__VIEWSTATE': view_state,
            ['xnd', 'xn'][self.schedule_type]: self.schedule_year,
            ['xqd', 'xq'][self.schedule_type]: self.schedule_term
        }
        return payload

    def _get_api_by_bm(self, class_name, **kwargs):
        ''' 部门教师 查询学生班级课表 共3个请求'''

        # steps 1: 获取课表 view_state
        try:
            res = self._get(self.schedule_url, **kwargs)
            if res.status_code != 200:
                raise RequestException
            view_state = get_view_state_from_html(res.text)
        except RequestException:
            raise ScheduleException(self.code, '获取课表请求参数失败')

        # steps 2: 选择课表 学年学期
        if self.schedule_year and self.schedule_term:
            payload = {
                '__VIEWSTATE': view_state,
                'xn': self.schedule_year,
                'xq': self.schedule_term
            }
            try:
                res = self._post(self.schedule_url, data=payload, **kwargs)
                if res.status_code != 200:
                    raise RequestException
            except RequestException:
                raise ScheduleException(self.code, '获取课表请求参数失败')

        # steps 3: 获取课表数据
        payload = self._get_payload_by_bm(
            res.content.decode('gbk'),
            class_name
        )
        try:
            res = self._post(self.schedule_url, data=payload, **kwargs)
            if res.status_code != 200:
                raise RequestException
        except RequestException:
            raise ScheduleException(self.code, '获取课表信息失败')

        html = res.content.decode('gbk')
        schedule = ScheduleParse(
            html,
            self.time_list,
            self.schedule_type
        ).get_schedule_dict()

        return schedule

    @staticmethod
    def _get_payload_by_bm(html, class_name):
        ''' 提取页面参数用于请求课表 '''
        pre_soup = BeautifulSoup(html, "html.parser")
        view_state = pre_soup.find(attrs={"name": "__VIEWSTATE"})['value']
        schedule_id_list = pre_soup.find(id='kb').find_all('option')
        class_name = to_text(class_name)
        schedule_id = ''
        for name in schedule_id_list:
            if name.text == class_name:
                schedule_id = name['value']
                break

        # 获取班级课表
        payload = {
            '__VIEWSTATE': view_state,
            'kb': schedule_id
        }
        return payload
