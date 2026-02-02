import os
import posixpath

import grpc

from app import utils
from app.enum import DownloadClientEnum
from app.modules.downloadclient.base import BaseDownloader
from app.modules.downloadclient.cloudnas import clouddrive_pb2
from app.modules.downloadclient.cloudnas import clouddrive_pb2_grpc
from app.utils.log import logger


class CloudNas(BaseDownloader):
    config: dict = None
    name = DownloadClientEnum.CLOUDDRIVE.value
    stub = None
    jwt_token = None

    def __init__(self, conf):
        self.jwt_token = None
        self.config = conf
        options = [
            ('grpc.enable_http_proxy', 0),  # 禁用 HTTP 代理
        ]
        if self.config.get('url') and self.config.get("token"):
            self.channel = grpc.insecure_channel(utils.get_host_port(self.config.get('url')), options=options)
            self.stub = clouddrive_pb2_grpc.CloudDriveFileSrvStub(self.channel)
            self.jwt_token = self.config.get("token")
        elif self.config.get('url') and self.config.get('username') and self.config.get('password'):
            self.channel = grpc.insecure_channel(utils.get_host_port(self.config.get('url')), options=options)
            self.stub = clouddrive_pb2_grpc.CloudDriveFileSrvStub(self.channel)
            self.authenticate(self.config.get('username'), self.config.get('password'))

    def authenticate(self, username, password):
        request = clouddrive_pb2.GetTokenRequest(
            userName=username,
            password=password
        )
        response = self.stub.GetToken(request)
        if response.success:
            self.jwt_token = response.token
            print(f"认证成功。令牌过期时间: {response.expiration}")
            return True
        else:
            print(f"认证失败: {response.errorMessage}")
            return False

    def _create_authorized_metadata(self):
        if not self.jwt_token:
            return []
        return [('authorization', f'Bearer {self.jwt_token}')]

    def download(self, magnet, save_path):
        if self.jwt_token:
            self.create_folder(save_path)
            logger.info(f"开始处理CD2离线下载任务：{magnet}")
            metadata = self._create_authorized_metadata()
            request = clouddrive_pb2.AddOfflineFileRequest(urls=magnet, toFolder=save_path)
            try:
                response = self.stub.AddOfflineFiles(request, metadata=metadata)
            except Exception as e:
                logger.error(e)
                return False
            print(response)
            if response.success:
                logger.success(f"离线任务创建成功")
                return True
            else:
                logger.error(f"离线任务创建成功:{response.errorMessage}")
                return False
        return False

    def create_sub_folder(self, parent_path, folder_name):
        request = clouddrive_pb2.CreateFolderRequest(
            parentPath=parent_path,
            folderName=folder_name
        )
        metadata = self._create_authorized_metadata()
        try:
            self.stub.CreateFolder(request, metadata=metadata)
        except Exception as e:
            logger.error(e)

    def create_folder(self, save_path):
        if self.jwt_token:
            save_path = posixpath.normpath(save_path)
            if save_path == "/":
                return
            parts = [p for p in save_path.split("/") if p]
            parent_path = "/"
            for part in parts:
                self.create_sub_folder(parent_path, part)
                parent_path = parent_path + "/" + part
