#!/usr/bin/env python3

import cmd
from .connection_manager import LogicHubConnection
from lhub.log import Logger

log = Logger()


# ToDo make sure Shell.session doesn't have to be set explicitly in order to use this
class Shell(cmd.Cmd):
    # Override the default prompt of "(cmd) "
    # prompt = "(logichub) "
    # Fancy colorful version
    prompt = '\x1b[6;30;47m' + 'Logic' + '\x1b[6;31;47m' + 'Hub' + '\x1b[0m % '
    session: LogicHubConnection = None

    def __init__(self):
        super().__init__()
        if not self.session:
            self.session = LogicHubConnection()

    # ToDo Finish or remove; overriding in order to try to allow keyboard interrupts
    def cmdloop(self, intro=None):
        """
        Repeatedly issue a prompt, accept input, parse an initial prefix off the
        received input, and dispatch to action methods, passing them the
        remainder of the line as argument.

        :param intro:
        :return:
        """

        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                import readline
                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                readline.parse_and_bind(self.completekey+": complete")
            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro)+"\n")
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    if self.use_rawinput:
                        line = ''
                        try:
                            line = input(self.prompt)
                        except KeyboardInterrupt:
                            print()
                        except EOFError:
                            line = 'EOF'
                    else:
                        self.stdout.write(self.prompt)
                        self.stdout.flush()
                        line = self.stdin.readline()
                        if not len(line):
                            line = 'EOF'
                        else:
                            line = line.rstrip('\r\n')
                line = self.precmd(line)
                try:
                    stop = self.onecmd(line)
                    stop = self.postcmd(stop, line)
                except Exception as err:
                    print(f"Error: {str(err)}")
            self.postloop()
        finally:
            if self.use_rawinput and self.completekey:
                try:
                    import readline
                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass

    def do_info(self, *args):
        """ Show current session info """
        try:
            print(f"Instance selected: {self.session.instance}")
        except ValueError:
            print("No instance selected")
        else:
            self.session.config.list_configured_instances()
            print(f"Credentials: {self.session.credentials}")
            print(dir(self.session.config))

    def do_connect(self, instance):
        """
        Switch connection to a different instance

        :param instance: Alias for the instance to which you want to connect
        :return:
        """
        log.info(f"Connecting to instance {instance}")
        self.session.instance = instance
        log.info(f"Connected")

    # I want the user to be able to type "exit" instead of having to type "EOF"
    def do_exit(self, line=None):
        return self.do_EOF()

    # What to do when the shell is exited
    def do_EOF(self, line=None):
        return True

    # Override the default behavior with an empty line, which is to rerun the last command. Instead, just do nothing
    def emptyline(self):
        pass

    # Override default output for unknown command to customize the output
    def default(self, line):
        """
        Called on an input line when the command prefix is not recognized.
        Prints an error message and returns.
        """
        self.stdout.write('*** Unknown command: %s\n' % line)

    # Override default help command response to customize the output
    def do_help(self, arg):
        """List available commands with "help" or detailed help with "help cmd"."""
        if arg:
            # XXX check arg syntax
            try:
                func = getattr(self, 'help_' + arg)
            except AttributeError:
                try:
                    doc = getattr(self, 'do_' + arg).__doc__
                    if doc:
                        self.stdout.write("%s\n" % str(doc))
                        return
                except AttributeError:
                    pass
                self.stdout.write("%s\n" % str(self.nohelp % (arg,)))
                return
            func()
        else:
            names = self.get_names()
            cmds_doc = []
            cmds_undoc = []
            help_dict = {}
            for name in names:
                if name[:5] == 'help_':
                    help_dict[name[5:]] = 1
            names.sort()
            # There can be duplicates if routines overridden
            prevname = ''
            for name in names:
                if name[:3] == 'do_':
                    if name == prevname:
                        continue
                    prevname = name
                    command = name[3:]
                    if command in help_dict:
                        cmds_doc.append(command)
                        del help_dict[command]
                    elif getattr(self, name).__doc__:
                        # cmds_doc.append(command)
                        if command != 'help_dict':
                            cmds_doc.append(command)
                    else:
                        cmds_undoc.append(command)
            self.stdout.write("%s\n" % str(self.doc_leader))
            self.print_topics(self.doc_header,   sorted(cmds_doc),   15, 80)
            self.print_topics(self.misc_header,  list(help_dict.keys()), 15, 80)
            self.print_topics(self.undoc_header, cmds_undoc, 15, 80)


# if __name__ == '__main__':
#     Shell().cmdloop()
