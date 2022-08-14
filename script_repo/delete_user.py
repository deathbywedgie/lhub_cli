#!/usr/bin/env python3

import argparse
import asyncio
import json

import lhub.exceptions.app

import lhub_cli
from lhub_cli.common.output import print_fancy_lists


def get_args():
    _parser = argparse.ArgumentParser(description="Delete a LogicHub user")
    _parser.add_argument("user", help="Username to delete")
    _parser.add_argument("instance_names", nargs="*", help="Nicknames of specific instances from stored config (default: show all)")
    final_args, logger = lhub_cli.common.args.build_args_and_logger(
        parser=_parser,
        include_credential_file_arg=True,
        include_list_output_args=True,
        include_logging_args=True,
    )
    return final_args, logger.log


async def delete_user_from_instance(username, cli_session: lhub_cli.LogicHubCLI):
    new_log = log.new(user=username, instance=cli_session.instance_name)

    try:
        new_log.info(f"Deleting user")
        result = cli_session.actions.delete_user_by_name(username=username)
        new_log.debug(f"Result: {json.dumps(result)}")
        return {**deletion_result_defaults, **{"user": username, "instance": cli_session.instance_name, "result": "successful"}}
    except lhub.exceptions.app.UserNotFound:
        return {**deletion_result_defaults, **{"user": username, "instance": cli_session.instance_name}}


async def delete_user_from_all(username: str, bulk_session: lhub_cli.LogicHubBulkCLI):
    return await asyncio.gather(*[delete_user_from_instance(username=username, cli_session=cli) for cli in bulk_session.sessions])


# Must be run outside of main in order for the full effect of verbose logging
args, log = get_args()
deletion_result_defaults = {"user": None, "instance": None, "result": "not found"}


def main():
    bulk = lhub_cli.LogicHubBulkCLI(credentials_file_name=args.credentials_file_name, instances=args.instance_names, log_progress=True)

    print(
        f"""
                                         &                                         .                                                                       #           /    
                 *#&&&(               &&&&                                     (&&&&                      &&&&#                        @&&&              &&&&,      /&&&&   
     &&%%&&&&&&%&&%&*                 &&&&      .        (&&&&&&%&/(    *      &&&&#               &      &&&&.      *.               &&&&%             ,&&&&.      &&%&&   
     &&&&&&&(        &&&&&   &&%*    /&&&%    &&&&(  #&&&&&%&%%,      &&&      &&&&,             &&&      &&&&    ,&&&&.  &&&       %&&&&&,              %&&&.       /&&&   
       &&&&         &&&&&   &&&&&&    &&&&   &&&&# ,&&&&&.           &&&&#     &&&&             &&&&      &&&&   ,&&&&   &&&&&&    &&%&&&&#              %&&&/       *&&&   
      .&&&&          &&&&   &&&&&&&.  &&&&   #&&&# &&&&#*            &&&&,     &&&&&            &&&&      &&&&*   &&%&  ,&&&&&&&& &&&% /&&&              &&&&%       .&&&   
       &&&&     .(   &&&&   &&&%&&&&%  &&&&  (&&&&  &%&%&&&&&&&#      &&&&     #&&&&             &&&&     &&&&/   &&&&   &&&%,#&&&&&&   &&&.             %&&&%       *&&&   
       &&&&&&&&&&    &&&&    (&&& &&&&&&&&&  /&&&&      ,(&&&&&&&&&   &&&&&&&&&&&&&#             &&&&&&&&&&&&&.   &&&&   (&&&  &&&&&%  &&&&(             ,%&&&       &&&&   
      &&&&&&%        (&&&    &&&&  &&&&%&&&   &&&&             &&&&#  .&&&&&&&%(&&&#             &&&&&&/% &&&&.   /&&&   /&&&   (&&&@  &&&&*              .&&&        &&&*  
       .&&&%         (&&&    %&&&.  #&&&&&&   &&&#            (&&&&    &&&,     &&&&             &&&&     .&&&/    &&&    &&&  .&&&&   (&&&,               &&&        *&&(  
        &&&%         &&&&    %&&&.    &&&&&   &&&,         .%&&&&&     &&&.     &&&&             &&&&      &&&&   .&&&   .&&&           &&&(                &#         /&   
        &&&%         &&&&    .&&&,     (&&&   &&&.       ,#&&&&,       &&&       %&&*            &&&&       &&&   &&&&    #&&           %&&&                *           *   
        &&&&         ,&&&     /&&&      ,&&*  ,&&(     (&&&%          (&&&         &@            &&&&        ,&%   &&&      &&           &&&              &&&&&       &&&&& 
         &&&           &&      &&&        (     && (&&&/              #&&&                       %&&&               @&                    &&              #&&&&,      &&&&# 
          (&/          .       (&&              @                      .&&                         &&                /                                                      
           %                    &&                                      &*                         &&                                                                       
                                                                                                   *"""
    )
    deletion_results = asyncio.run(delete_user_from_all(username=args.user, bulk_session=bulk))

    print_fancy_lists(
        results=deletion_results,
        output_type=args.output,
        table_format=args.table_format,
        output_file=(args.file or None),

        # Enable to provide columns to keep, in order
        # ordered_headers=deletion_result_defaults.keys() if not deletion_results else [],

        # Enable to provide a list of columns for custom sorting
        # sort_order=["user", "instance"],
        sort_order=[{"name": "result", "reverse": True}, "user", "instance"],

        # Change to "False" to always print output even if writing to a file
        file_only=(True if args.file else False)
    )


if __name__ == "__main__":
    # ToDo Why is this no longer catching KeyboardInterrupt??
    lhub_cli.common.shell.main_script_wrapper(main)
