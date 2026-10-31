"""Rebuild only BATCH2 synthetic observations from emitted targets; no execution."""
import copy
import json
from linuxgcb.catalog import ROOT
from linuxgcb.batch2 import ADDED, MARKER, guarded, specs
from linuxgcb.policy import emit_rule


def generated():
    checks={c['id']:c for p in (ROOT/'policies').glob('*.yml') for c in json.loads(p.read_text())['checks']}
    result={}
    for n,items in specs().items():
        check=checks[900000+n]
        targets={rule.split(' -> ',1)[0].removeprefix('not ') for rule in check['rules']}
        positive={t:dict(stdout='',exit_code=0) for t in targets}
        for cmd,pattern,good,bad in items:
            rule=emit_rule(guarded(cmd),pattern)
            assert rule in check['rules'], (n,rule)
            target=rule.split(' -> ',1)[0].removeprefix('not ')
            positive[target]['stdout']+='\n'+good
        for obs in positive.values():
            obs['stdout']=obs['stdout'].strip('\n')+'\n'+MARKER
        # One counterexample per source predicate, preserving all other targets.
        mutations=[]
        for cmd,pattern,good,bad in items:
            obs=copy.deepcopy(positive)
            target=guarded(cmd)
            # Keep other predicates on the same command intact; adding an extra
            # invalid member is the decisive negative case for collection rules.
            if pattern.startswith('!'):
                obs[target]['stdout']+='\n'+bad
            else:
                obs[target]['stdout']=obs[target]['stdout'].replace(good,bad)
            mutations.append(dict(rule=emit_rule(target,pattern),observations=obs))
        result[str(check['id'])]=dict(positive=positive,negative=mutations[0]['observations'],
            missing={},empty={t:dict(stdout='',exit_code=0) for t in targets},
            error={t:dict(error='SYNTHETIC command error') for t in targets},
            nonzero_matching={t:dict(stdout=o['stdout'],exit_code=1,stderr='SYNTHETIC failure despite matching stdout') for t,o in positive.items()},
            predicate_negatives=mutations)
    return result


def main():
    path=ROOT/'tests/fixtures/rule_outputs.json'
    data=json.loads(path.read_text())
    for key in list(data['checks']):
        if int(key)-900000 in ADDED: del data['checks'][key]
    data['checks'].update(generated())
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__': main()
