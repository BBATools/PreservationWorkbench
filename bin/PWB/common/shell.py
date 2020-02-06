#! python3

# Copyright (C) 2019 Morten Eek

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

class Cmd:
    def __init__(self, cmdArgs, stdin=None):
        self.cmd = ' '.join(cmdArgs)
        self.cmdArgs = cmdArgs
        self.stdin = stdin
        self.stdout = None
        self.stderr = None
        self.returncode = None
        self.succeeded = None

        if stdin and type(stdin) is str:
            if stdin[-1] == '\n':
                self.stdin = str.encode(stdin[:-1])
            else:
                self.stdin = str.encode(stdin)


def pwb_cmd(cmdArgs, stdin=None, piped=False):
    if len(cmdArgs) == 1 and '|' in cmdArgs[0]:
        args = [i.strip().split(' ') for i in cmdArgs[0].split('|')]
        return runCmd(args, piped=True)

    if piped:
        if len(cmdArgs) > 2:
            return runCmd(
                cmdArgs[-1], stdin=runCmd(cmdArgs[:-1], piped=True).stdout)
        elif len(cmdArgs) == 2:
            return runCmd(
                cmdArgs[1], stdin=runCmd(cmdArgs[0], piped=False).stdout)

    cmd = Cmd(cmdArgs, stdin)

    try:
        if cmd.stdin:
            if sys.version_info[1] < 7:  # Add capture_output for Python version 3.7 or greater
                result = subprocess.run(
                    cmd.cmdArgs,
                    input=cmd.stdin,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    #timeout=600,
                    check=True)
            else:
                result = subprocess.run(
                    cmd.cmdArgs,
                    input=cmd.stdin,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    capture_output=True,  # python >= 3.7
                    #timeout=600,
                    check=True)
        else:
            if sys.version_info[1] < 7:
                result = subprocess.run(
                    cmd.cmdArgs,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    #timeout=600,
                    check=True)

            else:
                result = subprocess.run(
                    cmd.cmdArgs,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    capture_output=True,  # python >= 3.7
                    #timeout=600,
                    check=True)

        cmd.stdout = result.stdout.decode("utf-8")
        cmd.stderr = result.stderr.decode("utf-8")

    except subprocess.CalledProcessError as e:
        cmd.succeeded = False
        cmd.returncode = e.returncode
        cmd.stdout = e.stdout.decode("utf-8")
        cmd.stderr = e.stderr.decode("utf-8")
    except subprocess.TimeoutExpired as e:

        cmd.succeeded = False
        cmd.stdout = 'COMMAND TIMEOUT ({}s)'.format(e.timeout)
    except Exception as e:
        cmd.succeeded = False
        cmd.stdout = ''
        if hasattr(e, 'message'):
            cmd.stderr = e.message
        else:
            cmd.stderr = str(e)
    else:
        cmd.returncode = 0
        cmd.succeeded = True
    finally:
        return cmd

