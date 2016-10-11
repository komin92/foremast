"""Foremast CLI commands."""
import argparse
import collections
import logging
import os

from . import runner, tester
from .args import add_debug, add_env
from .consts import LOGGING_FORMAT, SHORT_LOGGING_FORMAT

LOG = logging.getLogger(__name__)


def add_infra(subparsers):
    """Infrastructure subcommands."""
    infra_parser = subparsers.add_parser('infra', help=runner.prepare_infrastructure.__doc__)
    infra_parser.set_defaults(func=runner.prepare_infrastructure)


def add_pipeline(subparsers):
    """Pipeline subcommands."""
    pipeline_parser = subparsers.add_parser(
        'pipeline', help=add_pipeline.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    pipeline_parser.set_defaults(func=pipeline_parser.print_help)

    pipeline_subparsers = pipeline_parser.add_subparsers(title='Pipelines')

    pipeline_full_parser = pipeline_subparsers.add_parser(
        'app', help=runner.prepare_app_pipeline.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    pipeline_full_parser.set_defaults(func=runner.prepare_app_pipeline)

    pipeline_onetime_parser = pipeline_subparsers.add_parser(
        'onetime', help=runner.prepare_onetime_pipeline.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    pipeline_onetime_parser.set_defaults(func=runner.prepare_onetime_pipeline)
    add_env(pipeline_onetime_parser)


def add_rebuild(subparsers):
    """Rebuild Pipeline subcommands."""
    rebuild_parser = subparsers.add_parser(
        'rebuild', help=runner.rebuild_pipelines.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    rebuild_parser.set_defaults(func=runner.rebuild_pipelines)
    rebuild_parser.add_argument('-a', '--all', action='store_true', help='Rebuild all Pipelines')
    rebuild_parser.add_argument(
        'project',
        nargs='?',
        default=os.getenv('REBUILD_PROJECT'),
        help='Project to rebuild, overrides $REBUILD_PROJECT')


def add_autoscaling(subparsers):
    """Auto Scaling Group Policy subcommands."""
    autoscaling_parser = subparsers.add_parser(
        'autoscaling',
        help=runner.create_scaling_policy.__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    autoscaling_parser.set_defaults(func=runner.create_scaling_policy)


def add_tester(subparsers):
    """Test Spinnaker setup."""
    tester_parser = subparsers.add_parser(
        'tester', help=add_tester.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    tester_parser.set_defaults(func=tester_parser.print_help)

    tester_subparsers = tester_parser.add_subparsers(title='Testers')

    tester_all_parser = tester_subparsers.add_parser(
        'all', help=tester.all_tests.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    tester_all_parser.set_defaults(func=tester.all_tests)


def main(manual_args=None):
    """Foremast, your ship's support."""
    parser = argparse.ArgumentParser(description=main.__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.set_defaults(func=parser.print_help)
    add_debug(parser)
    parser.add_argument(
        '-s',
        '--short-log',
        action='store_const',
        const=SHORT_LOGGING_FORMAT,
        default=LOGGING_FORMAT,
        help='Truncated logging format')

    subparsers = parser.add_subparsers(title='Commands', description='Available activies')

    add_infra(subparsers)
    add_pipeline(subparsers)
    add_rebuild(subparsers)
    add_autoscaling(subparsers)
    add_tester(subparsers)

    CliArgs = collections.namedtuple('CliArgs', ['parsed', 'extra'])

    parsed, extra = parser.parse_known_args(args=manual_args)
    args = CliArgs(parsed, extra)

    logging.basicConfig(format=args.parsed.short_log)

    package, *_ = __package__.split('.')
    logging.getLogger(package).setLevel(args.parsed.debug)

    LOG.debug('Arguments: %s', args)

    try:
        args.parsed.func(args)
    except (AttributeError, TypeError):
        args.parsed.func()


if __name__ == '__main__':
    main()
