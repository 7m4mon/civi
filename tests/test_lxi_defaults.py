import base64,json
from pathlib import Path
from unittest.mock import AsyncMock
import pytest
from aiohttp.test_utils import TestClient,TestServer
from lxml import etree
from civi.config import load
from civi.network import Discovery
from civi.server import make_web
from civi.lxi_api import PROBLEM_NS

AUTH={'Authorization':'Basic '+base64.b64encode(b'admin:mock-test-password').decode(),'X-CIVI-Request':'1'}


@pytest.mark.parametrize('blank',['','   ','\t\n'])
async def test_description_factory_reset_is_saved_and_survives_reload(service,tmp_path,blank):
    path=tmp_path/'config.toml'
    path.write_text(Path('config.example.toml').read_text().replace('description = "CIVI CIVI-0001"','description = "Configured custom name"'))
    service.config.update(load(path))
    discovery=Discovery(); discovery.refresh=AsyncMock()
    async with TestClient(TestServer(make_web(service,'mock-test-password',discovery))) as client:
        url='/api/network'; data={'description':blank,'discovery':False}
        assert (await client.post(url,json=data)).status==401
        assert (await client.post(url,json=data,headers={'Authorization':AUTH['Authorization']})).status==403
        response=await client.post(url,json=data,headers=AUTH)
        assert response.status==200
        assert (await response.json())['description']=='CIVI CIVI-0001'
        assert load(path)['description']=='CIVI CIVI-0001'
        assert json.loads((tmp_path/'.civi-network.json').read_text())=={'description':'CIVI CIVI-0001','discovery':False}
        html=await (await client.get('/network')).text()
        assert 'id="description" value="CIVI CIVI-0001" required' not in html


async def test_default_save_failure_keeps_existing_description(service,tmp_path):
    service.config['description']='User name'
    service.config['network_settings_file']=str(tmp_path/'missing'/'settings.json')
    discovery=Discovery(); discovery.refresh=AsyncMock()
    async with TestClient(TestServer(make_web(service,'mock-test-password',discovery))) as client:
        response=await client.post('/api/network',json={'description':'','discovery':False},headers=AUTH)
        assert response.status==503
        assert service.config['description']=='User name'
        discovery.refresh.assert_not_awaited()


async def test_schema_aliases_and_lxi_problem_responses(service,monkeypatch):
    async with TestClient(TestServer(make_web(service,'mock-test-password'))) as client:
        old=await (await client.get('/InstrumentIdentification/2.0')).read()
        new=await (await client.get('/lxi/schemas/InstrumentIdentification/2.0')).read()
        assert old==new
        schema=etree.XMLSchema(etree.fromstring(await (await client.get('/lxi/schemas/LXIProblemDetails/1.0')).read()))
        for method,path,status in [('POST','/lxi/identification',405),
                                   ('GET','/devices/radio/lxi/identification',404),
                                   ('GET','/lxi/schemas/missing',404)]:
            response=await client.request(method,path)
            assert response.status==status and response.content_type=='application/xml'
            root=etree.fromstring(await response.read()); schema.assertValid(root)
            assert root.find(f'{{{PROBLEM_NS}}}Title').text
            if status==405: assert 'GET' in response.headers['Allow']
        response=await client.get('/api/status')
        assert response.status==401 and response.content_type=='application/json'
        def fail(*a,**kw): raise OSError('private internal information')
        monkeypatch.setattr('civi.server.identification_xml',fail)
        response=await client.get('/lxi/identification')
        assert response.status==503
        body=await response.read(); schema.assertValid(etree.fromstring(body))
        assert b'private internal information' not in body
