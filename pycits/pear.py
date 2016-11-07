#!/usr/bin/env python
#
# PEAR * (assemble overlapping reads)
# https://github.com/xflouris/PEAR
# follow this link to get the binaries.
# http://sco.h-its.org/exelixis/web/software/pear/files/
# pear-0.9.10-bin-64.tar.gz
#
# (c) The James Hutton Institute 2016
# Author: Leighton Pritchard and Peter Thorpe

# WARNING: this module is not yet tested AT ALL.

import os
import sys

import subprocess
from .tools import is_exe


class Pear(object):
    """Class for working with PEAR"""

    def __init__(self, exe_path, logger=False):
        """Instantiate with location of executable"""
        self._logger = logger
        self._no_run = False
        if not is_exe(exe_path):
            if logger:
                self._logger.error("""No PEAR program in PATH (exiting)
        The default name in the PEAR download is NOT PEAR. It is, for example
        pear-0.9.5-bin-64 . We recomment you change directory into the PEAR/bin
        forlder and 'cp pear-0.9.5-bin-64 pear' . This will create a copy of
        pear in that name. Make sure the PATH to this bin directory is in
        your PATH.

        If you are having troubles installing PEAR, pre-built binaries can be
        found at
        http://sco.h-its.org/exelixis/web/software/pear/files/
        pear-0.9.10-bin-64.tar.gz
        """)
            sys.exit(1)
        self._exe_path = exe_path

    def run(self, L_reads, R_reads, threads, outdir,
            logger=False):
        """Run PEAR on the read files"""
        assert L_reads != R_reads, """Oh no,
        I am trying to assemble two files that are the same!
        Something has gone wrong in determining the left and right
        read files."""
        self.__build_cmd(L_reads, R_reads, str(threads), outdir)
        if not os.path.exists(self._outdirname):
            if logger:
                self._logger.info("Creating output directory: %s" %
                                  self._outdirname)
            os.makedirs(self._outdirname)
        msg = ["Running...", "\t%s" % self._cmd]
        for m in msg:
            if logger:
                self._logger.info(m)

        pipe = subprocess.run(self._cmd, shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              check=True)
        if pipe.returncode != 0:
            if logger:
                self._logger.error("PEAR terminated by " +
                                   "signal %s" % pipe.returncode)
            sys.exit(1)
        else:
            if logger:
                self._logger.info("pear.py returned %s"
                                  % pipe.returncode)
        # print ("\n\npipe.args = ", pipe.args, "\n\n")
        return pipe.args

    def __build_cmd(self, L_reads, R_reads, threads, outdir):
        """Build a command-line for pear to assemble the
        overlapping paired end reads. """
        prefix = L_reads.split("_R")[0]
        prefix = prefix.split("/")[-1]
        self._outdirname = os.path.join(outdir, "%s_PEAR" % (prefix))
        cmd = ["pear",
               "-f", L_reads,
               "-r", R_reads,
               "--threads", str(threads),
               "-o", self._outdirname]
        self._cmd = ' '.join(cmd)
