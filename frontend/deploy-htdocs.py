#!/usr/bin/env python3

import os
import sys
import time
import datetime
import boto3
import json
import logging
import mimetypes

class CloudFrontDistribution(object):
    def __init__(self, distribution_id):
        session = boto3.Session(profile_name='sparkshot')
        self.cloudfront = session.client('cloudfront')
        self.distribution_id = distribution_id

    def invalidate_all(self):
        print("invalidating %s, path: /*" % self.distribution_id)
        paths = {'Quantity': 1,
                 'Items':    ['/*']}
        batch = {"Paths": paths,
                 "CallerReference": "myref-{}".format(datetime.datetime.now())}
        i = self.cloudfront.create_invalidation(
            DistributionId=self.distribution_id,
            InvalidationBatch=batch)
        print(json.dumps(i, indent=1, sort_keys=True,
                         default=lambda x: str(x)))


mimetypes.init()
mimetypes.add_type("model/gltf+json", '.gltf')
mimetypes.add_type("application/octet-stream", '.fnt')
mimetypes.add_type("application/json", '.json')

def mime_type(path):
    ctype, _ = mimetypes.guess_type(path)
    return ctype

def mime_encoding(path):
    _, encoding = mimetypes.guess_type(path)
    return encoding

def mime_type_encoding(path):
    return mimetypes.guess_type(path)

##############################################################

class S3Interface(object):
    def __init__(self, bucket, mock_s3=None):
        self.mock_s3 = mock_s3
        if self.mock_s3:
            return
        session = boto3.Session(profile_name='sparkshot')
        self.s3 = session.resource('s3')
        buckets = set(self.iter_all_buckets())
        #print(buckets)
        assert bucket in buckets, "unknown bucket %s" % bucket
        logging.debug("tgt bucket: %s" % bucket)
        self.bucket_name = bucket
        self.bucket = self.s3.Bucket(bucket)

    def iter_all_buckets(self):
        for bucket in self.s3.buckets.all():
            yield bucket.name

    def file_content(self, src_path):
        with open(src_path, "rb") as f:
            content = f.read()
        return content

    def put_content(self, content, mime, dst):
        logging.debug("putting: %s %s" % (dst, mime))
        start_time = time.time()
        if self.mock_s3:
            dst = os.path.join(self.mock_s3, dst)
            if not os.path.exists(os.path.dirname(dst)):
                os.makedirs(os.path.dirname(dst))
            with open(dst, "wb") as f:
                f.write(content)
        else:
            if mime:
                _ = self.bucket.put_object(Key=dst, ContentType=mime,
                                           Body=content)
            else:
                _ = self.bucket.put_object(Key=dst, Body=content)
        logging.debug("time: %.4f seconds" % (time.time() - start_time))

    def put_file(self, src_path, dst_path):
        content = self.file_content(src_path)
        mime = mime_type(src_path)
        self.put_content(content, mime, dst_path)

    def rm(self, path):
        if self.mock_s3:
            target = os.path.join(self.mock_s3, path)
            os.remove(target)
        else:
            #k = boto3.s3.key.Key(self.bucket)
            #k.key = path
            #self.bucket.delete_key(k)
            self.s3.Object(self.bucket_name, path).delete()

    def rm_dir(self, path):
        if self.mock_s3:
            target = os.path.join(self.mock_s3, path)
            os.rmdir(target)
        else:
            #k = boto3.s3.key.Key(self.bucket)
            #k.key = path
            #self.bucket.delete_key(k)
            self.s3.Object(self.bucket_name, path).delete()


class S3BucketDeploy(S3Interface):
    def __init__(self, src_dir, bucket):
        super().__init__(bucket, mock_s3=None)
        self.src_dir = os.path.abspath(src_dir)

    def _iter_htdocs(self):
        for dirpath, _, filenames in os.walk(self.src_dir):
            for f in filenames:
                yield os.path.join(dirpath, f)

    def dst_path(self, path):
        dst_path = path[len(self.src_dir) + 1:]
        #print(dst_path)
        if dst_path.endswith(".html") and dst_path != "index.html":
            dst_path = dst_path[:-5]
        return dst_path

    def put_dir(self):
        for src_path in self._iter_htdocs():
            self.put_file(src_path, self.dst_path(src_path))


SOURCE_DIR = "htdocs/"
S3_BUCKET = "onion.studio"
CLOUDFRONT_DISTRIBUTION = "E1SR2TKM48WX7C"
start_time = time.time()
s3 = S3BucketDeploy(SOURCE_DIR, S3_BUCKET)
s3.put_dir()
print("invalidating")
cf = CloudFrontDistribution(CLOUDFRONT_DISTRIBUTION)
cf.invalidate_all()

print("deploy total time: %.4f seconds" % (time.time() - start_time))
