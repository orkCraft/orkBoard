from itertools import product
from orkboard.core import idea_talk as t, idea_sections as s, idea_accept as a
from orkboard.realm import agent_rules_text as r, seat_frames as f, roles

def outputs():
    out = {}
    crafts = sorted(set(roles.CRAFTS) | {'', 'tech','game-design','art','run','liveops','release','unknown','product'})
    for craft in crafts:
        for second in (False, True):
            for bits in product((False, True), repeat=7):
                opts = {k: ('\nOPTION '+k, ', "'+k+'": "value"') if on else ('','') for k,on in zip(('project','after','weight','prop','again'),bits[2:])}
                opts.update(for_rule='\nFOR RULE' if bits[0] else '', mine='Custom party' if bits[1] else 'your party', second=second)
                key=f'talk/{craft}/{second}/{bits}'
                out[key]=t.instruction(craft, **opts)
                out[key+'/rules']=t.rules(craft, **opts)
        for seat in ('orkmaster','leader','taskmaster','grunt'):
            out[f'role/{seat}/{craft}']=r.seat_text(seat,craft)
            for wiki,dec in ((f.WIKI,f.DECISIONS),('custom/wiki','custom/decisions.md')):
                out[f'body/{seat}/{craft}/{wiki}']=r.role_body(seat,craft,wiki,dec,'Named seat')
        for seat in ('orkmaster','leader','tech-leader','game-design-leader','taskmaster','grunt'):
            for step in f.steps(seat):
                for wiki,dec in ((f.WIKI,f.DECISIONS),('custom/wiki','custom/decisions.md')):
                    out[f'frame/{seat}/{step}/{craft}/{wiki}']=f.agent(seat,step,craft,wiki,dec)
    for why, sketch, prop in product((s.WHY_FREE,s.WHY_CAUSE,'','CUSTOM WHY'),('','\nSKETCH'),(('', ''),('\nPROPOSAL', ', "proposal": []'))):
        out[f'section/{why}/{sketch}/{prop}']=s.instruction(why=why,sketched=sketch,prop=prop)
    for context in (s.JOIN_CONTEXT_NOTE,'','CUSTOM CONTEXT\n'):
        out[f'join/{context}']=s.join_instruction(context)
    for reads,last,body,lines in product((a.ACCEPT_READS,'','CUSTOM READ'),(a.ACCEPT_LAST_NOTE,'','Look 2','Last look'),(a.ACCEPT_CONTEXT_NOTE,'','CONTEXT\n'),('as many *Done when* lines as your section holds','0 *Done when* lines','1 *Done when* line','3 *Done when* lines')):
        out[f'accept/{reads}/{last}/{body}/{lines}']=a.instruction(title='Custom party',reads=reads,last=last,body=body,lines=lines)
    out['project/default']=t.project_rules()
    out['project/tail']=t.project_rules(' Already known: stack.')
    return out
