"""Guard the scope and distinct records of the manually launched LAN fixture."""
import pytest
from tools.mdns_collision_peer import validate, services, TYPES, hostname_answer
from zeroconf import DNSOutgoing, DNSQuestion
from zeroconf._protocol.incoming import DNSIncoming


@pytest.mark.parametrize('address', ['0.0.0.0','127.0.0.1','224.0.0.251','169.254.1.2','8.8.8.8','192.168.73.99'])
def test_unassigned_or_non_test_interface_is_rejected(address):
    with pytest.raises(ValueError):
        validate(address,'civi.local.','CIVI test',{'192.168.73.1'})


@pytest.mark.parametrize('hostname', ['civi.example.com.','a.b.local.','-bad.local.','a'*64+'.local.'])
def test_only_a_single_label_mdns_hostname_is_supported(hostname):
    with pytest.raises(ValueError):
        validate('192.168.73.1',hostname,'CIVI test',{'192.168.73.1'})


def test_all_four_services_have_explicit_address_host_name_and_fixture_identity():
    validate('192.168.73.1','civi.local.','CIVI test',{'192.168.73.1'})
    group=services('192.168.73.1','civi.local.','CIVI test')
    assert {info.type for info in group}==set(TYPES)
    assert all(info.server=='civi.local.' and info.parsed_addresses()==['192.168.73.1'] for info in group)
    assert all(info.name=='CIVI test.'+info.type for info in group)
    assert all(info.properties[b'test']==b'collision-only' and info.host_ttl==30 for info in group)
    assert len({info.port for info in group})==4


@pytest.mark.parametrize('name,type_,respond', [('civi.local.',255,True),('civi.local.',1,True),
    ('different.local.',255,False),('civi.local.',28,False)])
def test_established_hostname_authority_answers_only_matching_ipv4_probes(name,type_,respond):
    query=DNSOutgoing(0);query.add_question(DNSQuestion(name,type_,1))
    record=services('192.168.73.1','civi.local.','Test')[0].dns_addresses()[0]
    reply=hostname_answer(query.packets()[0],'civi.local.',record)
    assert bool(reply)==respond
    if respond:
        incoming=DNSIncoming(reply);assert incoming.valid and incoming.flags==0x8400
        assert len(incoming.answers())==1 and incoming.answers()[0].unique
        assert incoming.answers()[0].address==record.address
