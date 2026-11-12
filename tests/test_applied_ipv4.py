"""Observe runtime IPv4, not saved static settings, during DHCP trials."""
import copy
import json
from types import SimpleNamespace

import pytest

from civi.indicator import LanIndicator, PiLanReader
from civi.pi.network import NetworkError, NetworkManager


APPLIED={'data':[{'ipv4':{'method':{'type':'s','data':'auto'},
                          'address-data':{'type':'aa{sv}','data':[]}}},42]}


def manager(monkeypatch, data):
    def runner(args,**kwargs):
        assert args[0]=='busctl' and args[-3:]==['GetAppliedConnection','u','0']
        assert args[6]=='/org/freedesktop/NetworkManager/Devices/2'
        return SimpleNamespace(returncode=0,stdout=json.dumps(data))
    value=NetworkManager(runner=runner)
    monkeypatch.setattr(value,'_read',lambda *args:'/org/freedesktop/NetworkManager/Devices/2')
    return value


def test_applied_auto_and_static_settings_are_read_without_mutation(monkeypatch):
    data=copy.deepcopy(APPLIED);value=manager(monkeypatch,data)
    assert value.applied_ipv4('eth0')=={'method':'auto','addresses':[]}
    data['data'][0]['ipv4']['method']['data']='manual'
    data['data'][0]['ipv4']['address-data']['data']=[{
        'address':{'type':'s','data':'192.0.2.2'},'prefix':{'type':'u','data':24}}]
    assert value.applied_ipv4('eth0')=={'method':'manual','addresses':['192.0.2.2/24']}


@pytest.mark.parametrize('bad', [{}, {'data':[]}, {'data':[{}]},
    {'data':[{'ipv4':{'method':{'type':'b','data':True}}}]},
    {'data':[{'ipv4':{'method':{'type':'s','data':'unknown'}}}]},
    {'data':[{'ipv4':{'method':{'type':'s','data':'manual'},'address-data':{'type':'aa{sv}','data':[{}]}}}]}])
def test_invalid_applied_response_does_not_fall_back_to_saved_profile(monkeypatch,bad):
    with pytest.raises(NetworkError,match='could not be read'):
        manager(monkeypatch,bad).applied_ipv4('eth0')


def test_reader_tracks_temporary_dhcp_expiry_and_static_rollback(monkeypatch):
    addresses=['192.0.2.3'];dhcp=['ip_address = 192.0.2.3']
    applied={'method':'auto','addresses':[]}
    monkeypatch.setattr('civi.indicator.network_info',lambda:{'hostname':'civi','interfaces':[
        {'name':'eth0','up':True,'ipv4':list(addresses),'mac':None}]})
    reader=PiLanReader()
    values={'GENERAL.CON-UUID':'12345678-1234-1234-1234-123456789abc',
            'GENERAL.REASON':'0','GENERAL.STATE':'100 (connected)'}
    def read(*args):
        # In particular, no saved-profile ipv4.method/addresses reads occur.
        if args[1]=='DHCP4.OPTION':return '\n'.join(dhcp)
        return values[args[1]]
    monkeypatch.setattr(reader.manager,'_read',read)
    monkeypatch.setattr(reader.manager,'applied_ipv4',lambda interface:applied)
    indicator=LanIndicator()
    indicator.update(reader());assert indicator.snapshot()['state']=='normal'
    assert indicator.had_lease
    addresses[:]=['169.254.1.2'];dhcp.clear()
    indicator.update(reader());assert indicator.snapshot()['state']=='fault'
    assert indicator.lease_lost
    indicator.update(reader());assert indicator.snapshot()['state']=='fault'
    addresses[:]=['192.0.2.3'];dhcp[:]=['ip_address = 192.0.2.3']
    indicator.update(reader());assert indicator.snapshot()['state']=='normal'
    addresses[:]=['169.254.1.2'];dhcp.clear()
    indicator.update(reader());assert indicator.lease_lost
    applied.update(method='manual',addresses=['192.0.2.2/24']);addresses[:]=['192.0.2.2']
    indicator.update(reader());assert indicator.snapshot()['state']=='normal'
    assert not indicator.had_lease and not indicator.lease_lost


def test_applied_read_failure_is_unknown_rather_than_normal(monkeypatch):
    monkeypatch.setattr('civi.indicator.network_info',lambda:{'hostname':'civi','interfaces':[
        {'name':'eth0','up':True,'ipv4':['192.0.2.2'],'mac':None}]})
    reader=PiLanReader()
    values={'GENERAL.CON-UUID':'12345678-1234-1234-1234-123456789abc','GENERAL.REASON':'0','GENERAL.STATE':'100'}
    monkeypatch.setattr(reader.manager,'_read',lambda *args:values[args[1]])
    def fail(interface):raise NetworkError('Applied IPv4 settings unavailable')
    monkeypatch.setattr(reader.manager,'applied_ipv4',fail)
    indicator=LanIndicator();indicator.update(reader())
    assert indicator.snapshot()['state']=='unknown'
