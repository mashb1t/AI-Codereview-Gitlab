import json
import os

import requests

from biz.utils.log import logger
from biz.utils.i18n import get_translator
_ = get_translator()


class DingTalkNotifier:
    def __init__(self, webhook_url=None):
        self.enabled = os.environ.get('DINGTALK_ENABLED', '0') == '1'
        self.default_webhook_url = webhook_url or os.environ.get('DINGTALK_WEBHOOK_URL')

    def _get_webhook_url(self, project_name=None, url_base=None):
        """
        获取项目对应的 Webhook URL
        :param project_name: 项目名称
        :return: Webhook URL
        :raises ValueError: 如果未找到 Webhook URL
        """
        # 如果未提供 project_name，直接返回默认的 Webhook URL
        if not project_name:
            if self.default_webhook_url:
                return self.default_webhook_url
            else:
                raise ValueError(_("未提供项目名称，且未设置默认的钉钉 Webhook URL。"))

        # 遍历所有环境变量（忽略大小写），找到项目对应的 Webhook URL
        target_key = f"DINGTALK_WEBHOOK_URL_{project_name.upper()}"
        for env_key, env_value in os.environ.items():
            if env_key.upper() == target_key:
                return env_value  # 找到匹配项，直接返回
            
        # url_base 优先级次之
        target_key_url_base = f"WECOM_WEBHOOK_URL_{url_base.upper()}"
        for env_key, env_value in os.environ.items():
            if target_key_url_base !=None and  env_key.upper() == target_key_url_base:
                return env_value  # 找到匹配项，直接返回

        # 如果未找到匹配的环境变量，降级使用全局的 Webhook URL
        if self.default_webhook_url:
            return self.default_webhook_url

        # 如果既未找到匹配项，也没有默认值，抛出异常
        raise ValueError(_("未找到项目 '{}' 对应的钉钉Webhook URL，且未设置默认的 Webhook URL。").format(project_name))

    def send_message(self, content: str, msg_type='text', title='通知', is_at_all=False, project_name=None, url_base = None):
        if not self.enabled:
            logger.info(_("钉钉推送未启用"))
            return

        try:
            post_url = self._get_webhook_url(project_name=project_name, url_base=url_base)
            headers = {
                "Content-Type": "application/json",
                "Charset": "UTF-8"
            }
            if msg_type == 'markdown':
                message = {
                    "msgtype": "markdown",
                    "markdown": {
                        "title": title,  # Customize as needed
                        "text": content
                    },
                    "at": {
                        "isAtAll": is_at_all
                    }
                }
            else:
                message = {
                    "msgtype": "text",
                    "text": {
                        "content": content
                    },
                    "at": {
                        "isAtAll": is_at_all
                    }
                }
            response = requests.post(url=post_url, data=json.dumps(message), headers=headers)
            response_data = response.json()
            if response_data.get('errmsg') == 'ok':
                logger.info(_("钉钉消息发送成功! webhook_url: {}").format(post_url))
            else:
                logger.error(_("钉钉消息发送失败! webhook_url: {}, errmsg: {}").format(post_url, response_data.get('errmsg')))
        except Exception as e:
            logger.error(_("钉钉消息发送失败!"), e)
