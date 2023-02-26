import json
import os
import sys
import time
import arcgis
from arcgis.gis import GIS
from arcgis.gis.admin import PortalAdminManager
import boto3
import concurrent.futures
import datetime as _dt
from typing import Any
from pprint import pprint


def get_gis(event):
    return GIS(
        url=event.get('url'),
        username=event.get('username'),
        password=event.get('password'),
    )


def get_logs(gis):
    """
    Query logs from portal and servers
    """

    # set up object types
    admin: PortalAdminManager = gis.admin
    servers: dict[str, list[str, Any]] = {admin.url: []}
    days_back: int
    ref: dict[str, Any] = {admin.url: admin.logs}
    start: _dt.datetime = _dt.datetime.now()
    jobs = {}

    # concurrent jobs to get logs
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as tp:

        # get logs settings from portal
        days_back = admin.logs.settings.get("maxLogFileAge", 90)

        # gather the portal logs through gis.admin.logs.query()
        # Parameters: start_time, end_time - can query logs from any desired time ranges
        # Parameters: level - can query different types of logs [SEVERE, WARNING, INFO, DEBUG...]
        # Parameters: query_filter - can use any combinations of users and source components, e.g. {“users”:[“admin”,”jcho”]}
        # Parameters: page_size - can define numbers of logs to return
        for d in range(days_back):
            future = tp.submit(admin.logs.query, **{"start_time": start - _dt.timedelta(days=d), "end_time": start - _dt.timedelta(days=d + 1)})
            jobs[future] = {"server": admin.url, 'start_time': start - _dt.timedelta(days=d), 'end_time': start - _dt.timedelta(days=d + 1)}

        # loop through all federated servers and gather the server logs
        for server in admin.servers.list():
            servers[server.url] = []
            ref[server.url] = server
            days_back = server.logs.settings.get("maxLogFileAge", 90)
            for d in range(days_back):
                future = tp.submit(server.logs.query, **{"start_time": start - _dt.timedelta(days=d), "end_time": start - _dt.timedelta(days=d + 1)})
                jobs[future] = {"server": server.url, 'start_time': start - _dt.timedelta(days=d), 'end_time': start - _dt.timedelta(days=d + 1)}

        #  loop through the concurrent jobs and push the log entries into the servers.
        for job in concurrent.futures.as_completed(jobs):
            try:
                records = job.result()
                servers[jobs[job]['server']].extend(
                    records.get("logMessages", [])
                )
            except:
                # retry the operation on 504 timeout
                params = jobs[job]
                server_url = params.pop('server')
                print('retrying the query')
                time.sleep(2)
                servers[server_url].extend(
                    ref[server_url].logs.query(**params)
                )

        return servers


def put_data_to_s3(data):
    """
    push logs to s3 bucket
    """

    # set up file name in s3
    DEFAULT_FILENAME = f'logs-{int(_dt.datetime.utcnow().timestamp())}.json'

    # parse logs to json format
    body = get_json_bytes(data)

    # connect to s3 client
    s3_client = boto3.client('s3')

    # put logs to s3 with a time stamp
    s3_client.put_object(
        Body=body,
        Bucket=os.environ.get('AWS_S3_BUCKET', 'devsummit-logging-archive'),
        Key=os.environ.get('AWS_S3_LOG_FILENAME', DEFAULT_FILENAME)
    )


def get_json_bytes(data):
    """
    Get JSON as binary for provided input data
    """
    json_pretty_utf8_str = json.dumps(data, indent=4).encode('utf-8')
    return json_pretty_utf8_str


def get_main_args():
    args = sys.argv[-3:]  # last 3 args
    # validate args
    try:
        url, username, password = args
        if not url.startswith('http'):
            raise ValueError('first parameter must be Url')
    except ValueError:
        print('Usage: python app.py <url> <username> <password>')
        print('Please pass url, username, password as ordered args')
        sys.exit(1)
    return args


def main():
    url, username, password = get_main_args()
    gis: GIS = GIS(url=url, username=username, password=password)
    logs_by_server = get_logs(gis)
    put_data_to_s3(logs_by_server)
    pprint(logs_by_server)


if __name__ == '__main__':
    main()
