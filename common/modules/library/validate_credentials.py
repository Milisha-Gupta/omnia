# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/python

""" This module is used to validate credentials"""

import json
import os
import re
from configparser import ConfigParser

from ansible.module_utils.basic import AnsibleModule


def load_rules(file_path):
    """Loads validation rules from a JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def validate_input(field, value, rules):
    """Validates input against rules."""
    if field not in rules:
        return (False, f"Validation rules not found for '{field}'")

    rule = rules[field]
    if not rule["minLength"] <= len(value) <= rule["maxLength"]:
        return (False, f"'{field}' length must be between {rule['minLength']} and \
                {rule['maxLength']} characters")

    if "pattern" in rule and not re.match(rule["pattern"], value):
        return (False, f"'{field}' format is invalid. Expected pattern: {rule['pattern']}")
    return (True, f"'{field}' is valid")

def main():
    """Main module function."""
    parser = ConfigParser()
    cfg_path = os.path.join(os.getcwd(), 'ansible.cfg')
    parser.read(cfg_path)
    module_utils_base = parser.get('defaults', 'module_utils', fallback=None)
    credentials_schema = os.path.join(module_utils_base,'input_validation','schema',\
                                      'credential_rules.json')
    module_args = dict(
        credential_field=dict(type="str", required=True),
        credential_input=dict(type="str", required=True),
        rules_file=dict(type="str", required=False, default=credentials_schema)
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    params = module.params

    # Load validation rules
    try:
        rules = load_rules(params["rules_file"])
    except ValueError as e:
        module.fail_json(msg=f"Failed to load rules: {e}")

    # Validate credential
    credential_valid, credential_msg = validate_input(params["credential_field"], \
                                                      params["credential_input"], rules)

    if credential_valid:
        module.exit_json(changed=False, msg=f"{credential_msg}")
    else:
        module.fail_json(msg=f"Validation failed: {credential_msg}")

if __name__ == "__main__":
    main()
