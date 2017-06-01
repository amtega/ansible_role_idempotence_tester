# idempotence_tester

This is an [Ansible](http://www.ansible.com) role to run idempotence tests.

The role will call two times ansible-playbook with the same parameters as the running playbook, but limiting the scope to tagged tasks and to a specific group of hosts.

Also, it's possible to specify and alternative inventory file and the group of hosts to consider during test output analysis.

The idempotence will fail if any of the following conditions is true:

- The first run ends without changes.
- The second run ends with changes.
- Any of the runs ends with failed tasks.
- Any of the runs ends with unreachable hosts.

## Requirements

- Ansible >= 2.0

## Role Variables

A list of all the default variables for this role is available in `defaults/main.yml`.

Also, the role setup the following variables during execution:

- idempotence_tester_test_result: contains the result of the idempotence tests.

## Dependencies

This role depends on 'docker_provisioner' role.

## Example Playbook

This is an example playbook:

```yaml
---
- name: launch idempotence test
  hosts: localhost
  roles:
    - role: idempotence_tester

- name: idempotence test
  host: localhost
  tasks:
    - debug: msg="Nothing done, so idempotence test should fail"
  tags:
    - idempotence
```

## Testing

You can run the tests with the following commands:

```shell
$ cd idempotence_tester/test
$ ansible-playbook main.yml
```

## License

Not defined.

## Author Information

- Juan Antonio Valiño García ([juanval@edu.xunta.es](mailto:juanval@edu.xunta.es)). Amtega - Xunta de Galicia
