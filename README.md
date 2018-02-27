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

- Ansible >= 2.4

## Role Variables

A list of all the default variables for this role is available in `defaults/main.yml`.

Also, the role setup the following variables during execution:

- idempotence_tester_test_result: contains the result of the idempotence tests.

## Dependencies

- amtega.docker_provisioner
- amtega.docker_presets (only required for testing)

## Example Playbook

This is an example playbook:

```yaml
---
- name: launch idempotence test
  hosts: localhost
  roles:
    - role: amtega.idempotence_tester

- name: idempotence test
  host: localhost
  tasks:
    - debug: msg="Nothing done, so idempotence test should fail"
  tags:
    - idempotence
```

## Testing

Test are based on docker containers. You can run the tests with the following commands:

```shell
$ cd amtega.idempotence_tester/tests
$ ansible-playbook main.yml
```

If you have docker engine configured you can avoid running dependant 'docker_engine' role (that usually requries root privileges) with the following commands:

```shell
$ cd amtega.idempotence_tester/tests
$ ansible-playbook --skip-tags "role::docker_engine" main.yml
```

## License

Copyright (C) 2017 AMTEGA - Xunta de Galicia

This role is free software: you can redistribute it and/or modify
it under the terms of:
GNU General Public License version 3, or (at your option) any later version;
or the European Union Public License, either Version 1.2 or – as soon
they will be approved by the European Commission ­subsequent versions of
the EUPL;

This role is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details or European Union Public License for more details.

## Author Information

- Juan Antonio Valiño García.
