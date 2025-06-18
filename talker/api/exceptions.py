#!/usr/bin/env python
# encoding: utf-8

class VivoGPTError(Exception):
    """蓝心大模型API错误"""
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"错误码: {code}, 错误信息: {message}") 