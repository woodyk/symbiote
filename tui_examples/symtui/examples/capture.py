"""
    capture
    ~~~~~~~

    An example showing how to capure output from a running terminal app.

    :copyright: (c) 2015 by pyte authors and contributors,
                see AUTHORS for details.
    :license: LGPL, see LICENSE for more details.
"""

import os
import pty
import signal
import select
import sys


if __name__ == "__main__":
    try:
        output_path, *argv = sys.argv[1:]
    except ValueError:
        sys.exit("usage: %prog% output command [args]")

    p_pid, master_fd = pty.fork()
    if p_pid == 0:  # Child.
        env = os.environ.copy()
        env.update(dict(TERM="linux", COLUMNS="80", LINES="24"))
        os.execvpe(argv[0], argv, env=env)

    with open(output_path, "wb") as handle:
        while True:
            try:
                [_master_fd], _wlist, _xlist = select.select(
                    [master_fd], [], [], 1)
            except (KeyboardInterrupt,  # Stop right now!
                    ValueError):        # Nothing to read.
                break

            try:
                data = os.read(master_fd, 1024)
            except OSError:
                break

            if not data:
                break

            handle.write(data)

        os.kill(p_pid, signal.SIGTERM)
