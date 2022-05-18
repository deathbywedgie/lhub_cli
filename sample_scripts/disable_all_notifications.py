#!/usr/bin/env python3

import argparse
from sys import stderr

import lhub_cli

SCRIPT_DESCRIPTION = "Disable all notifications for the authenticated user"
OUTPUT_LEVEL = 2


# available args and expected input
def get_args():
    _parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)

    # Inputs required from user
    _parser.add_argument("instance_name", help="Nickname of the instance from stored config")

    output = _parser.add_mutually_exclusive_group()
    output.add_argument("-q", "--quiet", action="store_true", help="Operate quietly: minimal output")
    output.add_argument("-s", "--silent", action="store_true", help="Operate silently: suppress all output")
    final_parser, logger = lhub_cli.common.args.build_args_and_logger(
        parser=_parser,
        include_credential_file_arg=True,
        include_list_output_args=True,
        include_logging_args=True,
        default_log_level="INFO"
    )

    global OUTPUT_LEVEL
    if final_parser.silent:
        OUTPUT_LEVEL = 0
    elif final_parser.quiet:
        OUTPUT_LEVEL = 1

    return final_parser, logger


def print_quiet(msg):
    if OUTPUT_LEVEL >= 1:
        print(msg)


def print_normal(msg):
    if OUTPUT_LEVEL >= 2:
        print(msg)


args, _ = get_args()


def main():
    # If the instance name does not already exist as a saved connection, this will assist the user in saving a new one.
    cli = lhub_cli.LogicHubCLI(
        credentials_file_name=args.credentials_file_name,
        instance_name=args.instance_name
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
    lhub_cli.common.shell.main_script_wrapper(main)
