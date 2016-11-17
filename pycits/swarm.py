#!/usr/bin/env python
#
#
# Swarm (clustering)
# https://github.com/torognes/swarm/blob/master/man/swarm_manual.pdf
#
# (c) The James Hutton Institute 2016
# Author: Leighton Pritchard and Peter Thorpe

import os
import sys

import subprocess
from .tools import is_exe, NotExecutableError


class SwarmError(Exception):
    """Exception raised when swarm fails"""
    def __init__(self, message):
        self.message = message


class Swarm(object):
    """Class for working with SWARM"""
    def __init__(self, exe_path):
        """Instantiate with location of executable"""
        if not is_exe(exe_path):
            msg = "{0} is not an executable".format(exe_path)
            raise NotExecutableError(msg)
        self._exe_path = exe_path


    def run(self, infname, outdir, threads, threshold, dry_run=False):
        """Run swarm to cluster sequences in the passed file

        - infname    - path to sequences for clustering
        - outdir     - output directory for clustered output
        - threads    - number of threads for swarm to use
        - threshold  - clustering threshold for swarm (-d option)
        - dry_run    - if True returns cmd-line but does not run
        """
        self.__build_cmd(infname, threads, threshold, outdir)
        if dry_run:
            return(self._cmd)
        pipe = subprocess.run(self._cmd, shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              check=True) 
        return (self._outfname, pipe.stdout.decode('utf-8'))


    def __build_cmd(self, infname, threads, threshold, outdir):
        """Build a command-line for swarm"""
        self._outfname = os.path.join(outdir, "swarm.out")
        cmd = ["swarm",
               "-t", str(threads),
               "-d", str(threshold),
               "-o", self._outfname,
               infname] 
        self._cmd = ' '.join(cmd)


class SwarmCluster(object):
    """Describes a single Swarm cluster"""
    def __init__(self, amplicons, parent=None):
        self._amplicons = tuple(sorted(amplicons))
        if parent:
            self._parent = parent

    @property
    def amplicons(self):
        """The amplicons in a swarm cluster"""
        return self._amplicons


class SwarmResult(object):
    """Describes the contents of a Swarm output file"""
    def __init__(self, name):
        self._name = name
        self._clusters = list()

    def add_swarm(self, amplicons):
        """Adds a list of amplicon IDs as a SwarmCluster"""
        self._clusters.append(SwarmCluster(amplicons, self))

    def __eq__(self, other):
        """Returns True if all swarms match all swarms in passed result"""
        # this test relies on the amplicons being ordered tuples
        these_amplicons = {c.amplicons for c in self._clusters}
        other_amplicons = {c.amplicons for c in other._clusters}
        return these_amplicons == other_amplicons

    @property
    def swarms(self):
        """The clusters produced by a swarm run"""
        return self._clusters[:]

    @property
    def name(self):
        """The swarm result filename"""
        return self._name


class SwarmParser(object):
    """Parser for Swarm cluster output"""
    def __init__(self):
        pass

    def read(self, fname):
        """Parses the passed Swarm output file into a SwarmResult"""
        result = SwarmResult(fname)
        with open(fname, "rU") as swarms:
            idx = 0
            for swarm in swarms:
                result.add_swarm(swarm.strip().split())
        return result
