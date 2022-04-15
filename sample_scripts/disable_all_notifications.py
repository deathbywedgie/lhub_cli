#!/usr/bin/env python3

import argparse
from sys import stderr

import lhub_cli

SCRIPT_DESCRIPTION = "Disable all notifications for the authenticated user"
OUTPUT_LEVEL = 2


# available args and expected input
def get_args():
    parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)

    # Inputs required from user
    parser.add_argument("instance_name", help="Nickname of the instance from stored config")
    parser.add_argument("-cred", "--credentials_file_name", default=None, help="Alternate credentials file name to use (default: \"credentials\")")

    output = parser.add_mutually_exclusive_group()
    output.add_argument("-q", "--quiet", action="store_true", help="Operate quietly: minimal output")
    output.add_argument("-s", "--silent", action="store_true", help="Operate silently: suppress all output")
    output.add_argument("--debug", action="store_true", help="Enable debug logging")
    _args = parser.parse_args()

    global OUTPUT_LEVEL
    if _args.silent:
        OUTPUT_LEVEL = 0
    elif _args.quiet:
        OUTPUT_LEVEL = 1

    return _args


def print_quiet(msg):
    if OUTPUT_LEVEL >= 1:
        print(msg)


def print_normal(msg):
    if OUTPUT_LEVEL >= 2:
        print(msg)


def main():
    args = get_args()

    log_level = None
    if args.debug:
        log_level = "DEBUG"
    elif args.silent:
        log_level = "FATAL"

    # If the instance name does not already exist as a saved connection, this will assist the user in saving a new one.
    cli = lhub_cli.LogicHubCLI(
        credentials_file_name=args.credentials_file_name,
        instance_name=args.instance_name,

        # If the --debug option was passed by the user, set log level to debug, otherwise leave it default
        log_level=log_level
    )

    # Disable all notification preferences that exist as of m94.10
    print_quiet(f"Updating preferences for {args.instance_name} [{cli.session.api.session_hostname}]")
    results = cli.session.actions.update_current_user_preferences(
        assigneePreference=False,
        reporterPreference=False,
        myGroupIsAssigneePreference=False,
        commentCommandAddedPreference=False,
        defaultFieldsUpdatedPreference=False,
        taskCreatedInTheCasePreferences=False,
        updatesInAdditionalFieldsPreference=False,
        myMentionInCommentPreference=False,

        # Other preferences that can be set: change from None to True or False if desired
        advancedModePreference=None,
        flowBuilderPersistPreference=None
    )

    print_quiet(f"Preferences updated for user: {cli.session.api.session_username}")
    if OUTPUT_LEVEL >= 2:
        print()
        preferences = results['result']['preferences']
        summary = {k: [] for k in list(set([r['kind'] for r in preferences]))}
        for r in preferences:
            summary[r['kind']].append(f"{r['label']}:\n\t{r['value']}")
        for k, v in summary.items():
            print_normal(f"Section: {k}\n")
            for s in v:
                print_normal(f"\t{s}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Control-C Pressed, stopping...", file=stderr)
