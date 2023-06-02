#!/usr/bin/env xonsh

if __name__ == '__main__':
	d=p"$XONSH_SOURCE".resolve().parent; source f'{d}/bootstrap.xsh'
	MINICLUSTER.ARGPARSE.add_argument('--handle')
	MINICLUSTER = MINICLUSTER.bootstrap_finished(MINICLUSTER)

import logging
import cluster.functions
import json
import psutil
import time
import sys
import os

def command_umount_image_xsh(cwd, logger, handle):
	mountpoint = f"{cwd}/{handle}"

	pidfile = f"/tmp/guestmount-{handle}.pid"

	pid = None
	if os.path.exists(pidfile):
		with open(pidfile, 'r') as f:
			pid = int(f.read().rstrip())

	guestunmount @(mountpoint)

	while pid and psutil.pid_exists(pid):
		logger.info("pid exists")
		time.sleep(0.2)

if __name__ == '__main__':
	cwd = MINICLUSTER.CWD_START

	logger = logging.getLogger(__name__)
	handle = MINICLUSTER.ARGS.handle

	$RAISE_SUBPROC_ERROR = True
	command_umount_image_xsh(cwd, logger, handle)
