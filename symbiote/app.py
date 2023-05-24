#!/usr/bin/env python3
#

import openai
import sys
import os
import re
import select

# subprocess terminal
import tty
import termios
import subprocess

import symbiote.chat as chat

openai.api_key = os.getenv("OPENAI_API_KEY")
# Pull a list of available models to use.
# available_models = openai.Model.list()

def main():
    ''' Main function '''
    global conversations_file
    global current_conversation
    global token_track
    global toolbar_data

    current_path = os.getcwd()

    schat = chat.symchat(working_directory=current_path)
    schat.chat()

    def custom_command(func, *args, **kwargs):
        # Restore the original stdin and stdout
        os.dup2(old_stdin, new_stdin)
        os.dup2(old_stdout, new_stdout)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        #os.system('reset')

        # Close the file descriptors of the pty_slave and pty_master
        os.close(pty_slave)
        os.close(pty_master)

        func(*args, **kwargs)

        # Restore the new stdin and stdout
        #os.dup2(new_stdin, old_stdin)
        #os.dup2(new_stdout, old_stdout)

        # Restore the terminal settings
        #termios.tcsetattr(sys.stdin, termios.TCSADRAIN, new_settings)
        #os.system('reset')

        launch_shell()


    def launch_shell():
        # Save the terminal settings
        old_stdin = sys.stdin.fileno() 
        old_stdout = sys.stdout.fileno()

        old_settings = termios.tcgetattr(old_stdin)

        prompt = 'symshell> '
        os.environ['PS1'] = prompt
        prompt_re = re.escape(prompt.strip())
        shell = ['bash', '--norc', '--noprofile']
        shell_env = {}
        pty_master, pty_slave = os.openpty()
        command_shell = subprocess.Popen(shell, stdin=pty_slave, stdout=pty_slave, stderr=pty_slave, start_new_session=True)

        # Save the new terminal settings
        new_stdin = sys.stdin.fileno()
        new_stdout = sys.stdout.fileno()

        new_settings = termios.tcgetattr(new_stdin)

        # Set the terminal to raw mode
        tty.setraw(sys.stdin)

        live_mode = False
        command_buffer = ""
        response_buffer = ""

        globals().update(locals())

    command_buffer = ""
    response_buffer = ""

    session_data = []
    response = ""
    command = ""
    live_mode = False

    launch_shell()
    #prompt_response = r'\x1b\[\?2004hsymshell>(.*)\x1b\[\?2004l'
    prompt_response = r'\x1b\[\?2004hsymshell> (.*)\r\n'
    prompt_replace  = r'\x1b\[\?2004h|\x1b\[\?2004l|symshell>'

    while True:
        r, _, _ = select.select([sys.stdin, pty_master], [], [])
        if sys.stdin in r:
            # Read input from the user
            data = os.read(sys.stdin.fileno(), 1024)
            command_buffer += data.decode('utf-8')

            '''
            if '\r' in command_buffer:
                # Strip out command from response buffer
                command = command_buffer.strip()
            '''

            if 'chat::\r' in command_buffer:
                custom_command(schat.chat, working_directory=current_path)
                command_buffer = ""
                continue

            if 'help::\r' in command_buffer:
                custom_command(schat.symhelp)
                command_buffer = ""
                continue

            if 'convo::\r' in command_buffer:
                custom_command(schat.symconvo)
                command_buffer = ""
                continue

            if 'role::\r' in command_buffer:
                custom_command(schat.symrole)
                command_buffer = ""
                continue

            if 'model::\r' in command_buffer:
                custom_command(schat.symmodel)
                command_buffer = ""
                continue

            if 'tokens::\r' in command_buffer:
                custom_command(schat.symtokens)
                command_buffer = ""
                continue

            if 'live::\r' in command_buffer:
                if live_mode == True:
                    live_mode = False
                else:
                    live_mode = True

                command_buffer = ""
                continue

            if 'send::\r' in command_buffer:
                custom_command(schat.send_message, session_data)
                session_data.clear()
                command_buffer = ""
                continue

            os.write(pty_master, data)

        if pty_master in r:
            # Read output from the subprocess
            response_data = os.read(pty_master, 1024)
            response_buffer += response_data.decode('utf-8')

            if prompt_re in response_buffer:
                # Check if our command has executed.
                if len(response) > 0:
                    session_data.append({ "command": command, "response": response })
                    response = ""
                    command = ""

                # Strip out command from response buffer
                match = re.search(prompt_response, response_buffer)
                if match:
                    command = match.group(1).strip()
                    response_buffer = ""

            if '\r\n' in response_buffer:
                    response += response_buffer
                    response_buffer = ""

            # Check if the subprocess has exited
            if not response_data:
                os.system('reset')
                break    

            os.write(sys.stdout.fileno(), response_data)

        check_cd = re.search(r'^cd (.*)', command)
        if check_cd:
            current_path = check_cd.group(1).strip()
            if current_path == "":
                current_path = '~/'
            command = ""

        if live_mode and len(session_data) > 0:
            custom_command(schat.send_message, session_data)
            session_data.clear()

        continue

def entry_point() -> None:
    os.system('reset')
    main()

if __name__ == "__main__":
    os.system('reset')
    main()

os.system('reset')
