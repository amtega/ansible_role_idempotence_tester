# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import argparse
import re
import sys
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def get_command_line(self,
                         inventory,
                         group,
                         playbook="",
                         tag="test-idempotence",
                         append=""):
        """Return command line to run idempotence tests.

        Args:
            inventory (str): inventory to use.
            group (str): group that contains the hosts to test.
            playbook (str): path to the playbook to use.
            tag (str): tag to select the tests to run.
            append (str): content to append to command line.

        Returns:
            str: full command line to run the tests.
        """
        # Setup argument parser

        parser = argparse.ArgumentParser()
        parser.add_argument("--skip-tags")
        parser.add_argument("-t", "--tags")
        parser.add_argument("-i", "--inventory-file")
        parser.add_argument("-l", "--limit")
        parser.add_argument("command", nargs=1)

        # Parse argv and extract specific arguments

        known_args, unknown_args = parser.parse_known_args(sys.argv)
        command = known_args.command[0]
        tags = known_args.tags
        skip_tags = known_args.skip_tags
        extra_args = unknown_args

        # Extract all playbooks present in extra_args

        playbook_files = list()
        for arg in extra_args:
            if re.search(r'.*\.yml', arg):
                playbook_files.append(arg)

        # Setup current playbook if one is not specified

        if len(playbook) == 0:
            playbook = playbook_files[0]

        # Remove from all playbook from extra args

        for p in playbook_files:
            extra_args.remove(p)

        # Build strings that will compose the final command line, adjusting
        # --tags and --skip-tags

        if skip_tags is not None:
            skip_tags = "--skip-tags " \
                        + skip_tags.replace("," + tag, "")
            skip_tags = skip_tags.replace(tag + ",", "")

        if tags is None:
            tags = "--tags " + tag
        else:
            tags = tags + "," + tag

        if len(extra_args) > 0:
            extra_args = " ".join(extra_args)
        else:
            extra_args = ""

        if inventory:
            inventory_args = "-i " + inventory
        else:
            inventory_args = ""

        limit_args = '--limit="' + group + '"'

        components = [command,
                      tags,
                      skip_tags,
                      extra_args,
                      inventory_args,
                      limit_args,
                      playbook,
                      append]

        # Build the full command line

        non_empty_components = []
        for c in components:
            if c is not None and len(c) > 0:
                non_empty_components.append(c)

        full_command_line = " ".join(non_empty_components)

        return full_command_line

    def execute_test(self,
                     task_vars,
                     tmp,
                     inventory,
                     group,
                     playbook,
                     tag,
                     append):
        """Execute the test.

        Args:
            task_vars (dict): variables associated with this task.
            tmp (str): temporary directory.
            inventory (str): inventory file to use in the tests.
            group (str): group that contains the hosts to test.
            tag (str): the tag to select the tests to run.
            playbook (str): path to the playbook file to use.
            append (str): content to append to command line.

        Returns:
            dict: result of task execution
        """
        result = self._execute_module(
            module_name='command',
            module_args=dict(
                _uses_shell=True,
                _raw_params=self.get_command_line(inventory,
                                                  group,
                                                  playbook,
                                                  tag,
                                                  append)),
            task_vars=task_vars,
            tmp=tmp)

        if "changed" in result:
            result.pop("changed")

        if "invocation" in result:
            result.pop("invocation")

        if "warning" in result:
            result.pop("warnings")

        return result

    def parse_result(self, run, result):
        """Parse run result.

        Args:
            run (int): run number.
            result (dict): result of the run to parse.

        Returns:
            tuple: (failed, changed, msg)
        """
        # Initialize counters

        failed_count = 0
        unreachable_count = 0
        changed_count = 0
        not_changed_count = 0

        # Extract play recap

        play_recap_header = re.compile(r"PLAY RECAP \*+")
        stdout = result['stdout_lines']
        header_position = -1
        i = 0
        while i < len(stdout) and header_position < 0:
            if play_recap_header.match(stdout[i]):
                header_position = i
            i += 1
        play_recap = stdout[header_position + 1:]

        # Take metrics from execution summary

        play_recap_line = \
            re.compile("(.*): ok=.+changed=.+unreachable=.+failed=.+")
        failed_zero_line = \
            re.compile(".+changed=.+unreachable=.+failed=0.+")
        unreachable_zero_line = \
            re.compile(".+changed=.+unreachable=0.+failed=.+")
        changed_zero_line = \
            re.compile(".+changed=0.+unreachable=.+failed=.+")

        for line in play_recap:
            match = play_recap_line.match(line)
            if match:
                if not failed_zero_line.match(line):
                    failed_count += 1
                if not unreachable_zero_line.match(line):
                    unreachable_count += 1
                if changed_zero_line.match(line):
                    not_changed_count += 1
                else:
                    changed_count += 1

        # Analice stderr

        if len(result['stderr_lines']) > 0:
            output = (True,
                      False,
                      "Run " + str(run) + " finished with error(s)")
            return output

        # Analize metrics

        output = (False, True, "")

        if run == 1 and not_changed_count > 0:
            output = (True,
                      False,
                      "Run " + str(run) + " finished with unchanged hosts")

        if run > 1 and changed_count > 0:
            output = (True,
                      True,
                      "Run " + str(run) + " finished with changed hosts")

        if unreachable_count > 0:
            output = (True,
                      (changed_count > 1),
                      "Run " + str(run) + " finished with unreachable hosts")

        if failed_count > 0:
            output = (True,
                      (changed_count > 1),
                      "Run " + str(run) + " finished with failed hosts")

        return output

    def run(self, tmp=None, task_vars=None):
        """Ansible action plugin main run method."""

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        inventory = self._task.args.get("inventory")
        tag = self._task.args.get("tag")
        playbook = self._task.args.get("playbook")
        group = self._task.args.get("group")
        append = self._task.args.get("append")
        ignore = self._task.args.get("ignore")

        runs = list()
        result['changed'] = True

        # Launch first run

        run_result = self.execute_test(task_vars,
                                       tmp,
                                       inventory,
                                       group,
                                       playbook,
                                       tag,
                                       append)
        runs.append(run_result)
        result['failed'], result['changed'], result['msg'] = \
            self.parse_result(1, run_result)

        # Launch second run

        if not result['failed']:
            run_result = self.execute_test(task_vars,
                                           tmp,
                                           inventory,
                                           group,
                                           playbook,
                                           tag,
                                           append)
            runs.append(run_result)
            result['failed'], result['changed'], result['msg'] = \
                self.parse_result(2, run_result)
            result['runs'] = runs

        if not result['failed'] or self._play_context.verbosity > 0:
            result['runs'] = runs

        if ignore:
            result['failed'] = False

        return result
