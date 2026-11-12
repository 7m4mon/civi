"""XML errors for standardized identification resources, not CIVI JSON APIs."""
import logging
from http import HTTPStatus
from xml.etree import ElementTree as ET
from aiohttp import web

PROBLEM_NS = 'http://lxistandard.org/schemas/LXIProblemDetails/1.0'
PROBLEM_SCHEMA_PATH = '/lxi/schemas/LXIProblemDetails/1.0'


def is_lxi_resource(path):
    return (path.startswith('/lxi/') and path != '/lxi/'
            or path == '/devices/radio/lxi/identification'
            or path == '/InstrumentIdentification/2.0')


def problem(status, headers=None):
    root = ET.Element(f'{{{PROBLEM_NS}}}LXIProblemDetails', {
        '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation':
            f'{PROBLEM_NS} {PROBLEM_SCHEMA_PATH}'})
    ET.SubElement(root, f'{{{PROBLEM_NS}}}Title').text = HTTPStatus(status).phrase
    clean = {k:v for k,v in (headers or {}).items()
             if k.lower() not in ('content-type','content-length','content-encoding','transfer-encoding')}
    clean['Cache-Control'] = 'no-store'
    clean['X-Content-Type-Options'] = 'nosniff'
    return web.Response(status=status, body=ET.tostring(root,encoding='utf-8',xml_declaration=True),
                        content_type='application/xml',headers=clean)


@web.middleware
async def identification_errors(request, handler):
    if not is_lxi_resource(request.path):
        return await handler(request)
    try:
        response = await handler(request)
    except web.HTTPException as error:
        if error.status < 400: raise
        return problem(error.status,error.headers)
    except Exception as error:
        logging.getLogger('civi').error('LXI resource failed: %s',type(error).__name__)
        return problem(503)
    if response.status >= 400:
        return problem(response.status,response.headers)
    return response
