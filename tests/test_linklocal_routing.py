import json
import threading
from types import SimpleNamespace
import pytest
from civi.pi.linklocal import LinkLocalRoutes,TABLE,PRIORITY
from civi.pi.broker import dispatch


class Kernel:
    def __init__(self):
        self.rules=[{'priority':32766,'src':'all','table':'main'}]
        self.routes=[{'dst':'default','gateway':'192.0.2.1','dev':'wlan0','table':'main'}]
        self.mutations=[]
    def __call__(self,args,**kwargs):
        if '-j' in args:
            data=self.rules if 'rule' in args else self.routes
            return SimpleNamespace(returncode=0,stdout=json.dumps(data),stderr='')
        self.mutations.append(args)
        if 'rule' in args:
            record={'priority':PRIORITY,'src':args[args.index('from')+1].removesuffix('/32'),'table':TABLE}
            if 'add' in args:self.rules.append(record)
            else:self.rules.remove(record)
        else:
            record={'dst':'default','dev':'eth0','table':TABLE,'scope':'link','protocol':'static'}
            if 'add' in args:self.routes.append(record)
            else:self.routes.remove(record)
        return SimpleNamespace(returncode=0,stdout='',stderr='')


def test_exact_autoip_sources_added_and_removed_without_changing_wlan(tmp_path):
    kernel=Kernel();addresses={'169.254.1.2'}
    router=LinkLocalRoutes('eth0',SimpleNamespace(lock=threading.RLock()),tmp_path,runner=kernel,addresses=lambda interface:addresses.copy())
    router.update()
    assert {'priority':PRIORITY,'src':'169.254.1.2','table':TABLE} in kernel.rules
    assert all('169.254.0.0/16' not in command for command in kernel.mutations)
    assert router.snapshot()['sources']==['169.254.1.2']
    addresses.clear();router.update()
    assert kernel.rules==[{'priority':32766,'src':'all','table':'main'}]
    assert kernel.routes==[{'dst':'default','gateway':'192.0.2.1','dev':'wlan0','table':'main'}]


@pytest.mark.parametrize('foreign',[{'priority':PRIORITY,'src':'all','table':254},
                                   {'priority':PRIORITY,'src':'169.254.1.2','table':TABLE,'iif':'wlan0'}])
def test_unowned_rules_are_rejected_without_mutation(tmp_path,foreign):
    kernel=Kernel();kernel.rules.append(foreign)
    router=LinkLocalRoutes('eth0',SimpleNamespace(lock=threading.RLock()),tmp_path,runner=kernel,addresses=lambda interface:{'169.254.1.2'})
    with pytest.raises(RuntimeError,match='unowned'):router.update()
    assert not kernel.mutations


def test_routing_failure_is_exposed_through_existing_helper_health():
    tx=SimpleNamespace(conflict_guard=SimpleNamespace(snapshot=lambda:{'running':True,'error':None}),
        linklocal_routes=SimpleNamespace(snapshot=lambda:{'running':True,'error':'Routing failed','sample_age_seconds':0}))
    result=dispatch(tx,{'op':'conflict_status'})
    assert result['error']=='Routing failed'
