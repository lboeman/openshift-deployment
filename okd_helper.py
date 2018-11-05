#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to help in templating and creating/updating OKD objects
"""
import argparse
import base64
import difflib
import json
import os
import random
import string
import subprocess
import sys


import boto3
from jinja2 import Environment, FileSystemLoader, StrictUndefined
import yaml


def random_digit_string(length):
    return ''.join(
        random.SystemRandom().choice(
            string.ascii_uppercase + string.ascii_lowercase + string.digits)
        for i in range(length))


def ensure_bytes(bytes_or_str):
    try:
        out = bytes_or_str.encode('utf-8')
    except AttributeError:
        out = bytes_or_str
    return out


def ensure_str(bytes_or_str):
    try:
        out = bytes_or_str.decode('utf-8')
    except AttributeError:
        out = bytes_or_str
    return out


def b64encode(value):
    return ensure_str(base64.b64encode(ensure_bytes(value)))


def to_json(value):
    return json.dumps(value)


def random_constructor(loader, node):
    value = loader.construct_scalar(node)
    return random_digit_string(int(value))


def ssm_constructor(loader, node):
    value = loader.construct_scalar(node)
    client = boto3.client('ssm')
    resp = client.get_parameter(Name=value, WithDecryption=True)
    return resp['Parameter']['Value']


yaml.add_constructor('!random', random_constructor)
yaml.add_constructor('!ssm', ssm_constructor)


def make_parser():
    parser = argparse.ArgumentParser(
        description=(
            'Provide helpers to template OpenShift yaml config files,'
            ' apply changes, and see differences'),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    def print_help(args):
        parser.print_help()
        return ''
    parser.set_defaults(func=print_help)

    subparsers = parser.add_subparsers(help='Sub-commands')
    apply_parser = subparsers.add_parser(
        'apply', help='Apply the new config',
        description='Apply the config to OpenShift (create or update objects)')
    apply_parser.set_defaults(func=apply_config)

    diff_parser = subparsers.add_parser(
        'diff', help='Show differences',
        description='Show the difference between the current and new configs')
    diff_parser.set_defaults(func=diff_config)

    template_parser = subparsers.add_parser(
        'template', help='Template the config files',
        description='Only template and print the configs')
    template_parser.set_defaults(func=template_config)

    for p in (diff_parser, apply_parser, template_parser):
        p.add_argument('path',
                       help='File or folder to template and apply/diff')
        p.add_argument('-n', '--namespace',
                       help='OpenShift project namespace')

    random_parser = subparsers.add_parser(
        'random', help='Generate a random string',
        description='Generate a random alphanumeric string')
    random_parser.add_argument('length', type=int,
                               help='Length of random string')
    random_parser.set_defaults(func=random_print)

    args = parser.parse_args()
    return args


def load_vars(path):
    fargs = {}
    if os.path.isfile(path):
        args = yaml.load(open(path, 'r'))
        if 'include' in args:
            for apath in args['include']:
                # each succesive includes overwrites previous
                fargs.update(yaml.load(
                    open(os.path.join(
                        os.path.dirname(path),
                        apath), 'r')))
        fargs.update(args)
    return fargs


class RelEnvironment(Environment):
    def join_path(self, template, parent):
        return os.path.join(os.path.dirname(parent), template)


def render_templates(args):
    path = os.path.expanduser(args.path)
    if os.path.isdir(path):
        basedir = path
        recurse = True
    else:
        basedir = os.path.dirname(path)
        recurse = False

    env = RelEnvironment(
        loader=FileSystemLoader(basedir, followlinks=True),
        undefined=StrictUndefined,
        autoescape=False)

    env.filters['b64encode'] = b64encode
    env.filters['to_json'] = to_json

    if recurse:
        all_templates = env.list_templates(
            filter_func=lambda x: x.endswith('.yml'))
    else:
        all_templates = [os.path.basename(path),]

    templated_configs = []
    for template_file in all_templates:
        template = env.get_template(template_file)
        vars_path = os.path.join(os.path.dirname(template.filename), 'vars')
        rendered = template.render(**load_vars(vars_path))
        templated_configs.append((rendered, template_file))
    return templated_configs


def template_config(args):
    templated_configs = render_templates(args)
    return '\n---\n'.join(list(zip(*templated_configs))[0])


def get_last_applied(kind, name, namespace=None):
    cmd = ['oc', 'apply', 'view-last-applied', kind, name]
    if namespace is not None:
        cmd += ['-n', namespace]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if b'NotFound' in e.output:
            out = ''
        else:
            print(ensure_str(e.output))
            sys.exit(e.returncode)
    return ensure_str(out)


def diff_config(args):
    templated_configs = render_templates(args)

    def make_diff(templated_config, filename):
        config_yaml = yaml.load(templated_config)
        last_applied = get_last_applied(
            config_yaml['kind'], config_yaml['metadata']['name'],
            args.namespace)
        config_sorted_text = yaml.dump(config_yaml, default_flow_style=False)
        diff = ''.join(
            difflib.unified_diff(
                last_applied.splitlines(1),
                config_sorted_text.splitlines(1),
                fromfile='Current',
                tofile=filename))

        return diff
    return ('\n'+'='*40+'\n').join([make_diff(tc, f)
                                    for tc, f in templated_configs])


def apply_template(template, namespace=None):
    cmd = ['oc', 'apply', '-f', '-']
    if namespace is not None:
        cmd.extend(['-n', namespace])
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE)
    out, err = proc.communicate(input=ensure_bytes(template))
    return ensure_str(out)


def apply_config(args):
    one_big_template = template_config(args)
    return apply_template(one_big_template, args.namespace)


def random_print(args):
    return random_digit_string(args.length)


def main():
    args = make_parser()
    out = args.func(args)
    print(out)


if __name__ == '__main__':
    main()
