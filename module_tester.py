#!/usr/bin/env python
# THIS IS a tester for module dev only.
#
# TODO - put this functionality under a proper test framework (e.g. nosetests
#        or equivalent)


import errno
import logging
import logging.handlers
import multiprocessing
import os
import sys
import time
import traceback

from argparse import ArgumentParser

from pycits import tools, trimmomatic, pear, error_correction,\
    clean_up, swarm, seq_crumbs, deduplicate, \
    rename_clusters_new_to_old, chop_seq

# setting up some test variables
threads = "4"
left_reads = "./data/reads/DNAMIX_S95_L001_R1_001.fastq"
right_reads = "./data/reads/DNAMIX_S95_L001_R2_001.fastq"

read_prefix = left_reads.split("_R")[0]
read_prefix = read_prefix.split("/")[-1]

# left_trim 53 - this should be default??
left_trim = 53
right_trim = 0


# Report last exception as string
def last_exception():
    """Returns last exception as a string, or use in logging."""
    exc_type, exc_value, exc_traceback = sys.exc_info()
    return ''.join(traceback.format_exception(exc_type, exc_value,
                                              exc_traceback))


# Run as script
if __name__ == '__main__':
    # Set up logging
    logger = logging.getLogger('thapbi_santi_otus.py: %s' % time.asctime())
    logger.setLevel(logging.DEBUG)
    err_handler = logging.StreamHandler(sys.stderr)
    err_formatter = logging.Formatter('%(levelname)s: %(message)s')
    err_handler.setFormatter(err_formatter)
    logger.addHandler(err_handler)

    try:
        logstream = open("module_testing.txt", 'w')
        err_handler_file = logging.StreamHandler(logstream)
        err_handler_file.setFormatter(err_formatter)
        # logfile is always verbose
        err_handler_file.setLevel(logging.INFO)
        logger.addHandler(err_handler_file)
    except:
        logger.error("Could not open %s for logging" %
                     args.logfile)
        sys.exit(1)

    # Report input arguments
    logger.info("Command-line: %s" % ' '.join(sys.argv))
    logger.info("Starting testing: %s" % time.asctime())

    # trimmomatic testing.
    trimmo_prog = "/home/pt40963/scratch/Downloads/Trimmomatic-0.36/" +\
                  "trimmomatic-0.36.jar"

    logger.info("starting trimmomatic testing")
    trim = trimmomatic.Trimmomatic(trimmo_prog, logger)

    logger.info("Trim reads by quality")
    trim.run(trimmo_prog, left_reads, right_reads,
             threads, "trimmed_reads", 0, logger)

    # error correction testing
    ByHam = "/home/pt40963/scratch/Downloads/SPAdes-3.9.0-Linux/bin/spades.py"
    error_correct = error_correction.Error_correction(ByHam,
                                                      logger)
    Left_trimmed = os.path.join("trimmed_reads",
                                read_prefix +
                                "_paired_R1.fq.gz")
    Right_trimmed = os.path.join("trimmed_reads",
                                 read_prefix +
                                 "_paired_R2.fq.gz")
    logger.info("error correction using Bayes hammer")
    error_correct.run(ByHam, Left_trimmed, Right_trimmed,
                      "error_correction", threads, logger)
    L_E_C = os.path.join("error_correction", "corrected",
                         read_prefix + "_paired_R1.fq" +
                         ".00.0_0.cor.fastq.gz")

    R_E_C = os.path.join("error_correction", "corrected",
                         read_prefix + "_paired_R2.fq" +
                         ".00.0_0.cor.fastq.gz")

    # PEAR testing - assemble
    assemble = pear.Pear("pear", logger)
    Left_trimmed = os.path.join("trimmed_reads",
                                read_prefix + "_paired_R1.fq.gz")
    Right_trimmed = os.path.join("trimmed_reads",
                                 read_prefix + "_paired_R2.fq.gz")
    logger.info("assembly using PEAR")
    assemble.run(Left_trimmed, Right_trimmed,
                 threads, "PEAR_assembled", logger)

    # Pear testing with EC reads
    logger.info("assembly using PEAR with error corrected reads")
    assemble.run(L_E_C, R_E_C,
                 threads, "PEAR_assembled_EC", logger)

    # cleaning up unwanted files
    logger.info("testing the removal of unwanted file")
    unwanted_list = ["unpaired_R*.fq.gz",
                     "PEAR_assembled/*.discarded*fastq",
                     "PEAR_assembled/*.unassembled*fastq"]

    delete_file = clean_up.Clean_up("rm", logger)
    for i in unwanted_list:
        delete_file.run(i)

    # convert format
    format_change = seq_crumbs.Convert_Format("convert_format",
                                              logger)
    assembled_reads = os.path.join("PEAR_assembled",
                                   read_prefix +
                                   "_paired_PEAR.assembled.fastq")

    format_change.run(assembled_reads, "fasta_converted",
                      logger)

    # deduplicate read:
    #python deduplicate_rename.py
    #-f DNAMIX_S95_L001_paired_PEAR.assembled.fasta
    #-d database.out
    #-o temp.fasta
    logger.info("deduplicating reads")
    dedup_prog = os.path.join("pycits", "deduplicate_rename.py")
    dedup = deduplicate.Deduplicate(dedup_prog, logger)
    fasta_file = os.path.join("fasta_converted",
                              "DNAMIX_S95_L001_paired_PEAR.assembled.fasta")
    database = os.path.join("fasta_converted", "database.out")
    out_dedup = os.path.join("fasta_converted", "temp.fasta")
    dedup.run(dedup_prog, fasta_file, database, out_dedup,
              logger)

    # need to trim the left and right assembled seq so they
    # cluster with the database.
    left_trim = 53
    right_trim = 0
    chop_prog = os.path.join("pycits", "trim_fasta_file.py")

    fasta_file = os.path.join("fasta_converted", "temp.fasta")
    ITS_database = os.path.join("data",
                                "ITS_database_NOT_confirmed_correct_" +
                                "last14bases_removed.fasta")
    fasta_out = os.path.join("fasta_converted",
                             "database_assembled_reads.fasta")

    chopper = chop_seq.Chop_seq(chop_prog, logger)
    #        run(exe_path, fasta, database, left, right,
            #fasta_out, barcode="0", logger=False)
    chopper.run(chop_prog, fasta_file, ITS_database, left_trim,
                right_trim, fasta_out, logger)

    # SWARM testing - assemble
    cluster = swarm.Swarm("swarm", logger)
    assembled_fa_reads = os.path.join("fasta_converted",
                                      "temp.fasta")

    logger.info("clustering with Swarm")
    cluster.run(assembled_fa_reads,
                threads, 1, "Swarm_cluster_assembled_reads_only", logger)
    cluster.run(fasta_out,
                threads, 1, "Swarm_cluster", logger)

    # recode cluster output
    #python pycits/parse_clusters_new_to_old_name.py -i
    # -i swarm_tempd1.out -d database.out -o decoded_clusters.out
    logger.info("renaming swarm output")
    rename_prog = os.path.join("pycits",
                               "parse_clusters_new_to_old_name.py")
    rename = rename_clusters_new_to_old.Rename(rename_prog, logger)
    infile = os.path.join("Swarm_cluster", "swarm_clustering_d1",
                          "swarm_clustering_d1")
    outfile = os.path.join("Swarm_cluster", "swarm_clustering_d1",
                           "swarm_clustering_d1_renamed.out")
    rename.run(rename_prog, infile, ITS_database,
               database, outfile, logger)

    # need to summarise the clusters now
    # how? scripts already made, are they good enough?
