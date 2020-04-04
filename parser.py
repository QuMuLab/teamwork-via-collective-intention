
from pdkb.problems import parse_action, read_pdkbddl_file as read_with_imports
from pdkb.rml import Literal

from teamwork import TWProblem


def parse_proposition(prop, types):
    if '' == prop:
        return ['']
    elif '<' != prop[0]:
        return [prop.split('(')[0] + suf for suf in parse_proposition(prop.split('(')[1], types)]
    else:
        t = prop[:-1].split(',')[0][1:-1]
        suf = ','.join(prop.split(',')[1:])
        return ['_'+obj+rest for obj in types[t] for rest in parse_proposition(suf, types)]

def parse_general_rml(rml, types):
    if '<' not in rml:
        return [rml]

    toRet = []
    pre = rml.split('<')[0]
    t = rml.split('<')[1].split('>')[0]
    suf = '>'.join(rml.split('>')[1:])

    for o in types[t]:
        toRet.extend(parse_general_rml(pre+o+suf, types))

    return toRet

def parse(fname):

    # Read the file (with imports) which strips out the comments / empty lines
    lines = read_with_imports(fname)

    name = lines.pop(0).split('Name:')[1]

    max_depth = int(lines.pop(0).split('Max-Depth:')[1])

    trust_settings = {}
    trust_settings['fof'] = lines.pop(0).split('Trust-Friend-Of-Friend:')[1] == 'yes'
    trust_settings['foe'] = lines.pop(0).split('Trust-Friend-Of-Enemy:')[1] == 'yes'
    trust_settings['eof'] = lines.pop(0).split('Trust-Enemy-Of-Friend:')[1] == 'yes'
    trust_settings['eoe'] = lines.pop(0).split('Trust-Enemy-Of-Enemy:')[1] == 'yes'
    trust_settings['symmetric'] = lines.pop(0).split('Trust-Symmetric:')[1] == 'yes'
    trust_settings['team'] = lines.pop(0).split('Team-Trust:')[1]

    agents = set(lines.pop(0).split('Agents:')[1].split(','))

    num_trusts = int(lines.pop(0).split('Trust-Configuration:')[1])
    trust_settings['trust'] = []
    trust_settings['mistrust'] = []
    for i in range(num_trusts):
        if '!' in lines[0]:
            trust_settings['mistrust'].append(lines.pop(0).split('!>'))
        else:
            trust_settings['trust'].append(lines.pop(0).split('>'))


    num_types = int(lines.pop(0).split('Types:')[1])
    types = {}
    for i in range(num_types):
        t = lines[0].split(':')[0]
        v = lines[0].split(':')[1].split(',')
        types[t] = v
        lines.pop(0)


    capabilities = {}
    bargains = {}

    for i in range(len(agents)):

        ag = lines.pop(0).split('Agent:')[1]
        assert ag in agents

        num_cap = int(lines.pop(0).split('Capabilities:')[1])
        agent_cap = []
        for j in range(num_cap):
            agent_cap.extend(parse_general_rml(lines.pop(0), types))
        capabilities[ag] = agent_cap

        num_bar = int(lines.pop(0).split('Bargain:')[1])
        agent_bar = []
        for j in range(num_bar):
            agent_bar.extend(parse_general_rml(lines.pop(0), types))
        bargains[ag] = agent_bar


    propositions = []
    num_prop = int(lines.pop(0).split('Propositions:')[1])
    for i in range(num_prop):
        propositions.extend(parse_proposition(lines.pop(0), types))
    propositions = set(map(Literal, propositions))


    num_actions = int(lines.pop(0).split('Actions:')[1])
    actions = []
    for i in range(num_actions):
        new_lines = '////' + lines.pop(0)
        while lines and 'name:' != lines[0][:5] and 'problem:' != lines[0][:8]:
            new_lines += '////' + lines.pop(0)

        action_lines = [new_lines]
        for t in types:
            new_action_lines = []
            for old_act_line in action_lines:
                if "<%s>" % t not in old_act_line:
                    new_action_lines.append(old_act_line)
                else:
                    for v in types[t]:
                        new_action_lines.append(v.join(old_act_line.split("<%s>" % t)))
            action_lines = new_action_lines
        for act_line in action_lines:
            actions.append(parse_action(act_line.split('////')[1:], max_depth, agents, propositions))

    assert 'problem:' in lines[0]
    assert 'projection:' == lines[1][:11]
    assert 'init:' == lines[2][:5]

    init_lines = []
    num_init = int(lines[2].split(':')[1])
    for line in lines[3:3+num_init]:
        init_lines.extend(parse_general_rml(line, types))

    goal_lines = []
    num_goals = int(lines[3+num_init].split(':')[1])
    assert len(lines) == 4 + num_init + num_goals
    for line in lines[4+num_init:]:
        goal_lines.extend(parse_general_rml(line, types))

    instance_lines = lines[0:2] + [lines[2].split(':')[0]+':'+str(len(init_lines))] + init_lines + \
                     [lines[3+num_init].split(':')[0]+':'+str(len(goal_lines))] + goal_lines

    return TWProblem(name, max_depth, trust_settings, agents, types, capabilities, bargains, propositions, actions, instance_lines)
