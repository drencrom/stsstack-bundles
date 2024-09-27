"""
Get names of test targets that OSCI would run for the given charm. Should be
run from within the charm root.

Outputs space separated list of target names.
"""
import os
import re

import yaml
from common import OSCIConfig  # pylint: disable=import-error

CLASSIC_TESTS_YAML = 'tests/tests.yaml'
REACTIVE_TESTS_YAML = os.path.join('src', CLASSIC_TESTS_YAML)


def extract_targets(bundle_list):
    """
    Targets are provided as strings or dicts where the target name is the
    value so this accounts for both formats.
    """
    extracted = []
    for item in bundle_list or []:
        if isinstance(item, dict):
            values = list(item.values())
            if isinstance(values, list):
                # these are overlays so we use the key name
                bundle = list(item.keys())[0]
                extracted.append(bundle)
            else:
                # its a bundle name
                extracted.append(values[0])
        else:
            extracted.append(item)

    return extracted


def get_aliased_targets(bundles):
    """
    Extract aliased targets. A charm can define aliased targets which is where
    Zaza tests are run and use configuration steps from an alias section rather
    than the default (see 'configure:' section in tests.yaml for aliases). An
    alias is run by specifying the target to be run as a tox command using a
    job definition in osci.yaml where the target name has a <alias>: prefix.

    We extract any aliased targets here and return as a list.

    @param bundles: list of extracted bundles
    """
    targets = []
    osci = OSCIConfig()
    jobs = list(osci.project_check_jobs) + bundles
    for jobname in jobs:
        for job in osci.jobs:
            if job['name'] != jobname:
                continue

            if 'tox_extra_args' not in job['vars']:
                continue

            ret = re.search(r"-- (.+)",
                            str(job['vars']['tox_extra_args']))
            if ret:
                target = ret.group(1)
                # NOTE: will need to reverse this when we use the target name
                target = target.replace(' ', '+')
                targets.append(target)
                if jobname in bundles:
                    bundles.remove(jobname)

    return targets + bundles


def get_tests_bundles():
    """
    Extract test targets from primary location i.e. {src/}test/tests.yaml.
    """
    if os.path.exists(REACTIVE_TESTS_YAML):
        tests_file = REACTIVE_TESTS_YAML
    else:
        tests_file = CLASSIC_TESTS_YAML

    with open(tests_file, encoding='utf-8') as fd:
        bundles = yaml.safe_load(fd)

    smoke_bundles = extract_targets(bundles['smoke_bundles'])
    gate_bundles = extract_targets(bundles['gate_bundles'])
    dev_bundles = extract_targets(bundles['dev_bundles'])
    return smoke_bundles + gate_bundles + dev_bundles


if __name__ == "__main__":
    bundles = get_tests_bundles()
    bundles = get_aliased_targets(bundles)
    print(' '.join(sorted(bundles)))
