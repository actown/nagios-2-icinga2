import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--in', dest='in_file')
parser.add_argument('--out', dest='out_file')
args = parser.parse_args()

nagios_file = open(args.in_file, 'r')
icinga_file = open(args.out_file, 'w')

nagios_file = nagios_file.readlines()

resources = []


def parse_graphite(check_cmd):
    check = check_cmd.split('!')
    return {'command': check[0].lstrip('check_'), 'period': check[1], 'warn': check[2], 'crit': check[3], 'target': check[4].replace('"', '\\"')}


def parse_zk_node(check_cmd):
    check = check_cmd.split('!')
    return {'command': check[0].lstrip('check_'), 'key': check[1], 'warn': check[2], 'crit': check[3]}

for line in nagios_file:
    if line[0] is '#':
        continue
    elif 'define service {' in line:
        nagios_object = {'host_name': '', 'service_name': '', 'check_command': ''}
    elif 'host_name' in line:
        nagios_object['host_name'] = line.strip().lstrip('host_name').strip()
    elif 'service_description' in line:
        nagios_object['service_name'] = line.strip().lstrip('service_description').strip()
    elif 'check_command' in line:
        nagios_object['check_command'] = line.strip().lstrip('check_command').strip()
    elif '}' in line:
        resources.append(nagios_object)

for resource in resources:
    if 'check_graphite' in resource['check_command']:
        graphite = parse_graphite(resource['check_command'])
        text = """apply Service \"%s\" {
    import "graphite-service"
    display_name = \"%s\"

    vars.graphite_target = \"%s\"
    vars.graphite_period = \"%s\"
    vars.graphite_warn = \"%s\"
    vars.graphite_crit = \"%s\"

    check_command = \"%s\"

    assign where host.name == \"%s\"
}
""" % (resource['service_name'].replace(' ', '_').lower(), resource['service_name'], graphite['target'], graphite['period'], graphite['warn'], graphite['crit'], graphite['command'], resource['host_name'])
    if 'check_zk_node' in resource['check_command']:
        zk_node = parse_zk_node(resource['check_command'])
        text = """apply Service \"%s\" {
    display_name = \"%s\"

    vars.zookeeper_key = \"%s\"
    vars.zookeeper_warn = \"%s\"
    vars.zookeeper_crit = \"%s\"

    check_command = "zookeeper_node"

    assign where host.name == \"%s\"
}
""" % (resource['service_name'].replace(' ', '_').lower(), resource['service_name'], zk_node['key'],  zk_node['warn'], zk_node['crit'], resource['host_name'])
    icinga_file.write(text)
