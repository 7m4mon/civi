import base64
import json
from pathlib import Path
import pytest
from aiohttp.test_utils import TestClient, TestServer
from civi.auth import PasswordStore, has_saved_password, save_local_password
from civi.pi.lci import write_private, reload_recovery
from civi.server import make_web

OLD='old-test-password'
NEW='new-test-password'


def auth(password):
    return {'Authorization':'Basic '+base64.b64encode(('admin:'+password).encode()).decode(),'X-CIVI-Request':'1'}


@pytest.fixture
def settings(config,tmp_path):
    config['network_settings_file']=str(tmp_path/'.civi-network.json')
    return config


def test_hash_saved_restart_and_previous_password_invalid(settings,tmp_path):
    store=PasswordStore(settings,OLD)
    store.change(OLD,NEW,NEW)
    assert store.verify(NEW) and not store.verify(OLD)
    assert NEW not in (tmp_path/'.civi-web-auth.json').read_text()
    assert has_saved_password(settings)
    restarted=PasswordStore(settings,'ignored-environment-password')
    assert restarted.verify(NEW) and not restarted.verify('ignored-environment-password')


def test_local_reset_supersedes_saved_custom_password(settings,tmp_path):
    settings['pi_network']['enabled']=True
    store=PasswordStore(settings,OLD)
    store.change(OLD,NEW,NEW)
    write_private(settings['network_settings_file'],{'description':'Test radio','discovery':True})
    write_private(tmp_path/'.civi-lci.json',{'password':'recovery-test-password','revision':'reset-1'})
    assert reload_recovery(settings,store)=='reset-1'
    assert store.verify('recovery-test-password') and not store.verify(NEW)
    store.change('recovery-test-password',NEW,NEW)
    assert PasswordStore(settings,'').verify(NEW)
    # The initial monitor reload after a restart must preserve a newer Web password.
    restarted=PasswordStore(settings,'')
    reload_recovery(settings,restarted)
    assert restarted.verify(NEW) and not restarted.verify('recovery-test-password')


@pytest.mark.parametrize('new,confirmation',[('short','short'),(NEW,'mismatch'),('x'*257,'x'*257),('new\npassword-long','new\npassword-long')])
def test_invalid_new_password_not_saved(settings,tmp_path,new,confirmation):
    store=PasswordStore(settings,OLD)
    with pytest.raises(ValueError): store.change(OLD,new,confirmation)
    assert store.verify(OLD) and not (tmp_path/'.civi-web-auth.json').exists()


async def test_web_change_auth_csrf_and_immediate_effect(service,settings):
    store=PasswordStore(settings,OLD)
    data={'new_password':NEW,'confirm_password':NEW}
    async with TestClient(TestServer(make_web(service,store))) as web:
        assert (await web.post('/api/password',json=data)).status==401
        assert (await web.post('/api/password',json=data,headers=auth('wrong-password'))).status==401
        assert (await web.post('/api/password',json=data,headers={'Authorization':auth(OLD)['Authorization']})).status==403
        assert (await web.post('/api/password',json=data,headers={**auth(OLD),'Origin':'https://evil.invalid'})).status==403
        mismatch=await web.post('/api/password',json={**data,'confirm_password':'mismatch'},headers=auth(OLD))
        assert mismatch.status==400 and 'match' in (await mismatch.json())['error']
        result=await web.post('/api/password',json=data,headers=auth(OLD))
        assert result.status==200 and await result.json()=={'saved':True}
        assert (await web.get('/api/status',headers=auth(OLD))).status==401
        assert (await web.get('/api/status',headers=auth(NEW))).status==200
        assert 'Change Web password' in await (await web.get('/network')).text()


async def test_write_failure_keeps_current_password(service,settings,monkeypatch):
    store=PasswordStore(settings,OLD)
    def fail(*args): raise OSError('unwritable')
    monkeypatch.setattr('civi.auth.write_private',fail)
    async with TestClient(TestServer(make_web(service,store))) as web:
        result=await web.post('/api/password',json={'new_password':NEW,'confirm_password':NEW},headers=auth(OLD))
        assert result.status==503
        assert store.verify(OLD) and not store.verify(NEW)


def test_forgotten_password_reset_retains_other_settings_and_reloads(settings,tmp_path):
    from civi.pi.password import reset_password
    settings['pi_network']['enabled']=True
    write_private(settings['network_settings_file'],{'description':'My radio','discovery':False})
    write_private(tmp_path/'.civi-lci.json',{'password':'recovery-test-password','revision':'reset-1'})
    write_private(tmp_path/'.civi-lci-default.json',{'password':'recovery-test-password'})
    before={p.name:p.read_bytes() for p in tmp_path.iterdir()}
    store=PasswordStore(settings,'')
    store.change('recovery-test-password',OLD,OLD)
    assert store.verify(OLD) # populate the successful verifier cache
    values=iter([NEW,NEW]); output=[]
    assert reset_password(settings,prompt=lambda _:'PASSWORD RESET',read_password=lambda _:next(values),output=output.append)
    assert store.refresh_saved() and not store.refresh_saved()
    assert store.verify(NEW) and not store.verify(OLD) and not store.verify('recovery-test-password')
    assert PasswordStore(settings,'').verify(NEW)
    assert all((tmp_path/name).read_bytes()==value for name,value in before.items())
    assert all(NEW not in line for line in output)


def test_password_reset_cancel_and_mismatch_are_non_mutating(settings,tmp_path):
    from civi.pi.password import reset_password
    assert not reset_password(settings,prompt=lambda _:'no',read_password=lambda _:pytest.fail('Must not prompt'),output=lambda _:None)
    assert not list(tmp_path.iterdir())
    values=iter([NEW,'mismatch'])
    with pytest.raises(ValueError,match='match'):
        reset_password(settings,prompt=lambda _:'PASSWORD RESET',read_password=lambda _:next(values),output=lambda _:None)
    assert not list(tmp_path.iterdir())


def test_removing_saved_file_does_not_allow_empty_password(settings,tmp_path):
    store=PasswordStore(settings,OLD)
    store.change(OLD,NEW,NEW)
    (tmp_path/'.civi-web-auth.json').unlink()
    assert not store.refresh_saved()
    assert store.verify(NEW) and not store.verify('') and not store.verify(OLD)


def test_local_reset_save_failure_preserves_existing_password(settings,monkeypatch):
    store=PasswordStore(settings,OLD);store.change(OLD,NEW,NEW)
    def fail(*args): raise OSError('unwritable')
    monkeypatch.setattr('civi.auth.write_private',fail)
    with pytest.raises(OSError): save_local_password(settings,'replacement-password','replacement-password')
    assert PasswordStore(settings,'').verify(NEW)


def test_password_reset_cli_refuses_ssh(monkeypatch):
    from civi.pi.password import main
    monkeypatch.setattr('sys.argv',['password'])
    monkeypatch.setattr('civi.pi.password.platform.system',lambda:'Linux')
    monkeypatch.setenv('SSH_CONNECTION','test')
    with pytest.raises(SystemExit) as error: main()
    assert error.value.code==1
