#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, OVH SAS
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = """
---
module: zabbix_trigger
short_description: Create/update/delete Zabbix trigger
description:
    - Create/update/delete Zabbix trigger.
author:
    - "Michalis Michalis"
requirements:
    - "python >= 3.9"
options:
    name:
        description:
            - Name of Zabbix trigger
        required: true
        type: str
    host:
        description:
            - Name of Zabbix host trigger is linked to
        required: true
        type: str
    expression:
        description:
            - Reduced trigger expression. (required for create operations)
        required: true
        type: str
    priority:
        description:
            - "Severity of the trigger."
        required: false
        choices: [not_classified, information, warning, average, high, disaster]
        default: "not_classified"
        type: str
    status:
        description:
            - "Whether the trigger is enabled or disabled."
        required: false
        choices: [enabled, disabled]
        default: "enabled"
        type: str
    type:
        description:
            - "Whether the trigger can generate multiple problem events."
        required: false
        choices: [single, multiple]
        default: "single"
        type: str
    manual_close:
        description:
            - "	Allow manual close."
        required: false
        choices: [no, yes]
        default: "no"
        type: str
    state:
        description:
            - "State: present - create/update service; absent - delete service."
        required: false
        choices: [present, absent]
        default: "present"
        type: str
    tags:
        description:
            - Tags to be created for the trigger.
        required: false
        type: list
        elements: dict
        suboptions:
            tag:
                description:
                    - Service tag name.
                required: true
                type: str
            value:
                description:
                    - Service tag value.
                required: false
                type: str

extends_documentation_fragment:
- community.zabbix.zabbix

"""

EXAMPLES = """
---
# If you want to use Username and Password to be authenticated by Zabbix Server
- name: Set credentials to access Zabbix Server API
  ansible.builtin.set_fact:
    ansible_user: Admin
    ansible_httpapi_pass: zabbix

# If you want to use API token to be authenticated by Zabbix Server
# https://www.zabbix.com/documentation/current/en/manual/web_interface/frontend_sections/administration/general#api-tokens
- name: Set API token
  ansible.builtin.set_fact:
    ansible_zabbix_auth_key: 8ec0d52432c15c91fcafe9888500cf9a607f44091ab554dbee860f6b44fac895

- name: Create Zabbix trigger
  # set task level variables as we change ansible_connection plugin here
  vars:
    ansible_network_os: community.zabbix.zabbix
    ansible_connection: httpapi
    ansible_httpapi_port: 443
    ansible_httpapi_use_ssl: true
    ansible_httpapi_validate_certs: false
    ansible_zabbix_url_path: "zabbixeu"  # If Zabbix WebUI runs on non-default (zabbix) path ,e.g. http://<FQDN>/zabbixeu
    ansible_host: zabbix-example-fqdn.org
  community.zabbix.zabbix_trigger:
    name: nginx.service not running SLA
    host: omiliaprdn1
    expression: "last(/omiliaprdn1.central.root.alpha.gr/systemd.service.active_state[\"nginx.service\"])<>1"
    state: present
    priority: warning
    status: enabled
    type: single
    manual_close: no
    tags:
      - tag: scope
        value: availability
      - tag: service
        value: omiliaprdn1-nginx
"""

RETURN = """
---
"""


from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.zabbix.plugins.module_utils.base import ZabbixBase
import ansible_collections.community.zabbix.plugins.module_utils.helpers as zabbix_utils


class Trigger(ZabbixBase):
    # DONE
    def get_trigger_ids(self, host, trigger_name):
        trigger_ids = []
        triggers = self._zapi.trigger.get({"filter": {"host": host}})
        for trigger in triggers:
            if trigger['description'] == trigger_name:
                trigger_ids.append(trigger["triggerid"])
        return trigger_ids
    # DONE
    def delete_trigger(self, trigger_ids):
        if self._module.check_mode:
            self._module.exit_json(changed=True)
        self._zapi.trigger.delete(trigger_ids)
    # DONE
    def dump_triggers(self, trigger_ids):
        triggers = self._zapi.trigger.get({"output": "extend", "filter": {"triggerids": trigger_ids}, "selectHosts": "extend",
                                           "selectHostGroups": "extend", "selectTriggerDiscovery": "extend",
                                           "selectItems": "extend", "selectFunctions": "extend", "selectDependencies": "extend",
                                           "selectDiscoveryRule": "extend", "selectTags": "extend"})

        return triggers
    # DONE
    def generate_trigger_config(self, description, expression, priority, status, recovery_mode, manual_close, tags):

        request = {
            "description": description,
            "expression": expression,
            "recovery_mode": "0" # unsupported
        }

        if tags:
            request["tags"] = tags
        else:
            request["tags"] = []

        request["priority"] = "0"
        if priority:
            priority_map = {"not_classified": "0", "information": "1", "warning": "2",
                      "average": "3", "high": "4", "disaster": "5"}
            if priority not in priority_map:
                self._module.fail_json(msg="Wrong value for 'priority' parameter.")
            else:
                request["priority"] = pv_map[priority]

        request["status"] = "0"
        if status:
            status_map = {"enabled": "0", "disabled": "1"}
            if status not in status_map:
                self._module.fail_json(msg="Wrong value for 'status' parameter.")
            else:
                request["status"] = status_map[status]

        request["type"] = "0"
        if type:
            type_map = {"single": "0", "multiple": "1"}
            if type not in type_map:
                self._module.fail_json(msg="Wrong value for 'type' parameter.")
            else:
                request["type"] = status_map[type]

        request["manual_close"] = "0"
        if manual_close:
            manual_close_map = {"no": "0", "yes": "1"}
            if manual_close not in manual_close_map:
                self._module.fail_json(msg="Wrong value for 'manual_close' parameter.")
            else:
                request["manual_close"] = status_map[manual_close]


        return request
    # DONE
    def create_trigger(self, description, expression, priority, status, recovery_mode, manual_close, tags):
        if self._module.check_mode:
            self._module.exit_json(changed=True)

        self._zapi.trigger.create(self.generate_trigger_config(description, expression, priority, status, recovery_mode, manual_close, tags))
    # DONE
    def update_trigger(self, trigger_id, description, expression, priority, status, recovery_mode, manual_close, tags):
        generated_config = self.generate_trigger_config(description, expression, priority, status, recovery_mode, manual_close, tags)
        live_config = self.dump_triggers(trigger_id)[0]

        change_parameters = {}
        difference = zabbix_utils.helper_cleanup_data(zabbix_utils.helper_compare_dictionaries(generated_config, live_config, change_parameters))

        if difference == {}:
            self._module.exit_json(changed=False, msg="Trigger %s up to date" % name)

        if self._module.check_mode:
            self._module.exit_json(changed=True)
        generated_config["triggerid"] = trigger_id
        self._zapi.trigger.update(generated_config)
        self._module.exit_json(changed=True, msg="Trigger %s updated" % name)


def main():
    argument_spec = zabbix_utils.zabbix_common_argument_spec()
    argument_spec.update(dict(
        host=dict(type="str", required=True),
        name=dict(type="str", required=True),
        expression=dict(type="str", required=True),
        state=dict(default="present", choices=["present", "absent"]),
        priority=dict(type="str", required=False),
        recovery_mode=dict(type="str", required=False),
        status=dict(type="str", required=False),
        type=dict(type="str", required=False),
        manual_close=dict(type="str", required=False),
        tags=dict(
            type="list",
            required=False,
            elements="dict",
            options=dict(
                tag=dict(
                    type="str",
                    required=True
                ),
                value=dict(
                    type="str",
                    required=False
                )
            )
        ),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    host = module.params["host"]
    description = module.params["name"]
    expression = module.params["expression"]
    state = module.params["state"]
    priority = module.params["priority"]
    status = module.params["status"]
    type = module.params["type"]
    manual_close = module.params["manual_close"]
    recovery_mode = module.params["recovery_mode"]
    tags = module.params["tags"]


    # Load trigger module
    trigger = Trigger(module)
    trigger_ids = trigger.get_trigger_ids(host, name)

    # Delete trigger
    if state == "absent":
        if not trigger_ids:
            module.exit_json(changed=False, msg="Trigger not found, no change: %s" % name)
        trigger.delete_trigger(trigger_ids)
        module.exit_json(changed=True, result="Successfully deleted trigger(s) %s" % name)

    elif state == "present":
        # Does not exists going to create it
        if not trigger_ids:
            trigger.create_trigger(description, expression, priority, status, recovery_mode, manual_close, tags)
            module.exit_json(changed=True, msg="Trigger %s created" % name)
        # Else we update it if needed
        else:
            trigger.update_trigger(trigger_ids[0], description, expression, priority, status, recovery_mode, manual_close, tags)


if __name__ == "__main__":
    main()
