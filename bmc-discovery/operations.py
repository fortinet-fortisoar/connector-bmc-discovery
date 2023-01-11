""" Copyright start
  Copyright (C) 2008 - 2023 Fortinet Inc.
  All rights reserved.
  FORTINET CONFIDENTIAL & FORTINET PROPRIETARY SOURCE CODE
  Copyright end """

from connectors.core.connector import get_logger, ConnectorError
from .bmc_api_auth import *

logger = get_logger('bmc-discovery')


def get_token(config, connector_info):
    try:
        bmc = BMCAuth(config)
        token = bmc.validate_token(config, connector_info)
        return token
    except Exception as err:
        raise ConnectorError(err)


def make_api_call(config, url, method='GET', params=None, body=None, connector_info=None):
    try:
        endpoint = config.get('url') + '/api/v1.1' + url
        token = get_token(config, connector_info)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        }
        response = requests.request(method=method, url=endpoint, params=params, headers=headers, data=body,
                                    verify=config.get('verify_ssl'))

        if response.ok or response.status_code == 204:
            logger.info('Successfully got response for url {0}'.format(url))
            if 'json' in str(response.headers):
                return response.json()
            else:
                return response
        elif response.status_code == 404:
            return response
        else:
            logger.error("{0}".format(response.status_code, ''))
            raise ConnectorError("{0}".format(response.status_code, response.text))
    except requests.exceptions.SSLError:
        raise ConnectorError('SSL certificate validation failed')
    except requests.exceptions.ConnectTimeout:
        raise ConnectorError('The request timed out while trying to connect to the server')
    except requests.exceptions.ReadTimeout:
        raise ConnectorError(
            'The server did not send any data in the allotted amount of time')
    except requests.exceptions.ConnectionError:
        raise ConnectorError('Invalid Credentials')
    except Exception as err:
        raise ConnectorError(str(err))


def search_query(config, params, connector_info):
    endpoint = '/data/search?format=object'
    if params.get('offset') > 0 and not params.get('result_id'):
        return {"message": "'Offset' cannot be specified without 'Results ID'"}
    payload = {
        'query': params.pop('query')
    }
    query_parameter = {k: v for k, v in params.items() if v is not None and v != ''}
    return make_api_call(config, endpoint, method='POST', params=query_parameter, body=payload,
                         connector_info=connector_info)


def get_appliance_details(config, params, connector_info):
    endpoint = '/admin/about'
    return make_api_call(config, endpoint, method='GET', params={},
                         connector_info=connector_info)


def _check_health(config, connector_info):
    try:
        if check(config, connector_info) and get_appliance_details(config, params={}, connector_info=connector_info):
            return True
    except Exception as e:
        logger.error("{0}".format(str(e)))
        raise ConnectorError("{0}".format(str(e)))


operations = {
    'search_query': search_query,
}
