#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common_functions import load_yaml_file, get_repo_list
from ansible.module_utils.registry_utils import (
    validate_user_registry,
    check_reachability,
    find_invalid_cert_paths
)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            timeout=dict(type='int', default=5),
            config_file=dict(type='str', required=True),
        ),
        supports_check_mode=True
    )

    config_path = module.params['config_file']
    timeout = module.params['timeout']

    try:
        config_data = load_yaml_file(config_path)
    except FileNotFoundError as e:
        module.fail_json(msg=str(e))

    user_registry = get_repo_list(config_data, "user_registry")

    # Exit early if user_registry is empty
    if not user_registry:
        module.exit_json(
            changed=False,
            msg="No user registry entries found. Skipping validation.",
            reachable_registries=[],
            unreachable_registries=[],
            unreachable_count=0
        )

    # Validate entries
    is_valid, error_msg = validate_user_registry(user_registry)
    if not is_valid:
        module.fail_json(msg=f"[Validation Error] {error_msg}")

    # Reachability
    reachable, unreachable = check_reachability(user_registry, timeout)

    # Cert path validation
    invalid_paths = find_invalid_cert_paths(user_registry)
    if invalid_paths:
        module.fail_json(msg=f"[Cert Path Error] Invalid cert_path(s): {invalid_paths}")

    module.exit_json(
        changed=False,
        reachable_registries=reachable,
        unreachable_registries=unreachable,
        unreachable_count=len(unreachable)
    )

if __name__ == '__main__':
    main()
