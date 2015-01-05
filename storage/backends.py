# -*- coding: utf-8 -*-
"""
"""
from cStringIO import StringIO
import logging
import mimetypes
import os
import urlparse

import boto
from boto.s3.key import Key
from boto.exception import S3ResponseError
import requests

import config as cfg
from config import settings
from lib.utils import random_str


RACKSPACE_CONN_TIMEOUT_SEC = 20
RACKSPACE_NUM_UPLOAD_ATTEMPTS = 4
RACKSPACE_UPLOAD_DELAY_SEC = 2


log = logging.getLogger(__name__)


class LocalStorage(object):
  """ Use local filesystem to store files
  """
  @staticmethod
  def store_file(file_name, data):
    file_path = os.path.join(settings.filestorage.local.local_path, file_name)
    with open(file_path, 'wb') as f:
      f.write(data)

  @staticmethod
  def read_file(file_name):
    file_path = os.path.join(settings.filestorage.local.local_path, file_name)
    data = None
    with open(file_path, 'rb') as f:
      data = f.read()
    return data

  @classmethod
  def copy_to_temp(cls, existing_file_name):
    """Copy contents of local file to new temp file"""
    temp_filepath = os.path.join('/tmp', random_str(20))
    to_write = cls.read_file(existing_file_name)
    with open(temp_filepath, 'wb') as wf:
      wf.write(to_write)
    return temp_filepath

  @staticmethod
  def get_file_object(hosted_path):
    """returns a string buffer of a local file"""
    file_name = hosted_path.replace(settings.filestorage.local.hosted_path, '')
    file_path = os.path.join(settings.filestorage.local.local_path, file_name)
    return open(file_path, 'rb')

  @staticmethod
  def delete_temp_file(file_path):
    if os.path.exists(file_path) and os.path.split(file_path)[0] == '/tmp':
      os.unlink(file_path)

  @staticmethod
  def file_exists(file_name):
    file_path = os.path.join(settings.filestorage.local.local_path, file_name)
    return os.path.exists(file_path)

  @staticmethod
  def delete_file(file_name):
    file_path = os.path.join(settings.filestorage.local.local_path, file_name)
    if os.path.exists(file_path):
      os.unlink(file_path)

  @staticmethod
  def get_url_for_file(file_name):
    return "%s%s" % (settings.filestorage.local.hosted_path, file_name)

  @staticmethod
  def list_files():
    """returns a list/generator of files in storage.
    """
    p = settings.filestorage.local.hosted_path
    all_files = os.listdir(p)
    return [f for f in all_files if os.path.isfile(os.path.join(p, f))]


class RemoteStorageAWS(LocalStorage):
  """
  Remote storage to the Rackspace cloud.  Their API docs:
  http://docs.rackspacecloud.com/api/
  """
  # TODO: error handling

  @staticmethod
  def __get_conn():
    """Get a connection.  For now, just init the connection every time.
    """
    # TODO: investigate reusing a connection.
    return boto.boto.connect_s3(settings.filestorage.remote_aws.access_key,
                                settings.filestorage.remote_aws.secret_key)

  @staticmethod
  def store_file(file_name, data, container=None):
    """store a file to AWS, with the name and data provided.
       ALSO WHAT KIND OF A VARIABLE NAME IS DATA
    """
    container = container or settings.filestorage.remote_aws.container
    conn = RemoteStorageAWS.__get_conn()
    bucket = conn.get_bucket(container, validate=False)
    k = Key(bucket, file_name)
    # guess the mimetype
    content_type = mimetypes.guess_type(file_name)
    if content_type[0]:
      k.content_type = content_type[0]
    try:
      k.set_contents_from_string(data)
    except S3ResponseError:
      log.error("bad response from S3 on store_file call")
      raise ValueError("Response not OK")
    return RemoteStorageAWS.get_url_for_file(file_name)

  @staticmethod
  def read_file(file_name, container=None):
    """return the contents of a file in storage as a string.
    """
    container = container or settings.filestorage.remote_aws.container
    conn = RemoteStorageAWS.__get_conn()
    bucket = conn.get_bucket(container, validate=False)
    k = Key(bucket, file_name)
    try:
      return k.get_contents_as_string()
    except S3ResponseError:
      log.error("bad response from S3 on read_file call")
      raise ValueError("Response not OK")

  @staticmethod
  def get_file_object(hosted_path, container=None):
    """return the contents of a file in storage as file-like obj.
    """
    # first replace cdn_url with nothing, so we get the file name
    file_name = hosted_path.replace(
        "%s/" % settings.filestorage.remote_aws.container_cdn_url, '')
    file_name.replace(container, "")
    return StringIO(RemoteStorageAWS.read_file(file_name, container))

  @staticmethod
  def file_exists(file_name, container=None):
    """return whether or not a file exists on remote storage.
    """
    container = container or settings.filestorage.remote_aws.container
    conn = RemoteStorageAWS.__get_conn()
    bucket = conn.get_bucket(container, validate=False)
    try:
      return bool(bucket.get_key(file_name))
    except S3ResponseError:
      log.error("bad response from S3 on file_exists call")
      # don't reraise here, just return that it doesn't.
      return False

  @staticmethod
  def delete_file(file_name, container=None):
    """delete a file from the container
    """
    container = container or settings.filestorage.remote_aws.container
    conn = RemoteStorageAWS.__get_conn()
    bucket = conn.get_bucket(container, validate=False)
    try:
      bucket.delete_key(file_name)
    except S3ResponseError:
      log.error("bad response from S3 on delete_file call")
      raise ValueError("Response not OK")

  @staticmethod
  def get_url_for_file(file_name):
    return '%s%s' % (settings.filestorage.remote_aws.container_cdn_url,
                     file_name)

  @staticmethod
  def download_file(remote_file_name, container, local_file_name):
    """download a file to local_file_name
    """
    container = container or settings.filestorage.remote_aws.container
    conn = RemoteStorageAWS.__get_conn()
    bucket = conn.get_bucket(container, validate=False)
    k = Key(bucket, remote_file_name)
    try:
      k.get_contents_to_filename(local_file_name)
    except S3ResponseError:
      log.error("bad response from S3 on download_file call")
      raise ValueError("Response not OK")

  @staticmethod
  def upload_file(local_file_name, cloud_file_name, container):
    container = container or settings.filestorage.remote_aws.container
    conn = RemoteStorageAWS.__get_conn()
    bucket = conn.get_bucket(container, validate=False)
    k = Key(bucket, cloud_file_name)
    try:
      k.set_contents_from_filename(local_file_name)
    except S3ResponseError:
      log.error("bad response from S3 on upload_file call")
      raise ValueError("Response not OK")

  @staticmethod
  def list_files(container=None):
    """returns a list/generator of files in storage.
       NOTE: this may screw up a bit if you're adding items to the container as
       you run this, so don't assume this is a 100 percent complete manifest.
    """
    container = container or settings.filestorage.remote_aws.container
    conn = RemoteStorageAWS.__get_conn()
    bucket = conn.get_bucket(container, validate=False)
    return bucket.list()

  @staticmethod
  def store_from_url(url, container=None):
    if url:
      parsed_url = urlparse.urlparse(url)
      # get the last part of the path
      file_name = parsed_url.path.split('/')[-1]
      exists = RemoteStorageAWS.file_exists(file_name, container)
      if file_name and not exists:
        # download it to memory and upload to aws.
        resp = requests.get(url)
        return RemoteStorageAWS.store_file(file_name, resp.content, container)


if settings.filestorage.use_remote_aws and not cfg.test_mode:
  storage = RemoteStorageAWS
else:
  storage = LocalStorage


log.debug("Using %s as Storage Manager", storage.__name__)
