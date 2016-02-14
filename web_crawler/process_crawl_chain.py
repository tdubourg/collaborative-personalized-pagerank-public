#!/usr/bin/python

"""
    This file, as its name suggest, is going to chain all crawl-post-processing scripts into one blow.
    The input parameters are as follows:

    gathered_data_folder: the folder where the files you are going to describe with fname_base, number_of_parts and 
        optionnaly part_pattern are going to be located. They all need to be in the same folder. 
    fname_base: this is the name without the "_partX"
    number_of_parts: the number of parts the crawl results are divided in (typically 3-4 crawlers are run in parallel)
    [optional] part_pattern: if the naming pattern of the files is not "_partX" then provide this parameter
                example of pattern: "_%s" if your pattern is just "result_X.json.gz" (with fname_base = "result")
    [optional] tmp_folder: specific temporary folder instead of /tmp
"""

import sys
from subprocess import Popen, PIPE
from os.path import join as pjoin
from time import time

def exec_and_output(shell_command, args_list):
    print "Executing:", shell_command, '\\\n', '\\\n'.join([str(_) for _ in args_list])
    command = ["time", shell_command]  # TIME ALL THE THINGS!
    command.extend([str(_) for _ in args_list])
    # There is a known deadlock bug with PIPE in case output is more than 64k
    # It will likely be here, but as I am printing stdout on the spot, hopefully the bug won't trigger
    # as I should be emptying the bugger.
    # As for stderr, there should not be any info there, hopefully everything'll be fine
    Popen(command, stdout=sys.stdout, stderr=sys.stderr).communicate()

def shell(shell_command, args_list):
    command = [shell_command]
    command.extend(args_list)
    return Popen(command, stdout=PIPE, stderr=PIPE).communicate()[0] # [0] is stdout, [1] is stderr

CLI_ARGS = ["gathered_data_folder", "fname_base.json.gz", "number_of_parts"]
OPTIONAL_ARGS = ["part_pattern", "tmp_folder"]
def main():
    t0 = time()

    argc = len(sys.argv)
    if argc < (len(CLI_ARGS)+1):
        print "Usage:", sys.argv[0], " ".join(CLI_ARGS), "[" + "][".join(OPTIONAL_ARGS) + "]"
        exit()

    gathered_data_folder        = sys.argv[1]
    fname_base                  = sys.argv[2].strip()
    number_of_parts             = int(sys.argv[3])

    if argc > len(CLI_ARGS) + 1:
        part_pattern            = sys.argv[len(CLI_ARGS) + 1]
    else:
        part_pattern            = "_part%s"
    
    if argc > len(CLI_ARGS) + 2:
        tmp_path                = sys.argv[len(CLI_ARGS) + 2]
    else:
        tmp_path                = "/tmp"
    
    fname_base_pattern          = fname_base.replace(".json.gz", "") + "%s.json.gz" % part_pattern
    # orig = shell("pwd", []).strip()
    t_dir = pjoin(tmp_path, "cppr_tmp")

    # Setup
    fnames       = [fname_base_pattern % i for i in range(1, number_of_parts+1)]
    fnames_graph = [fname_base_pattern % ("%d_graph" % i) for i in range(1, number_of_parts+1)]
    shell("mkdir", ["-p", t_dir])
    args = ["-v"]
    args.extend([pjoin(gathered_data_folder, f) for f in fnames])
    args.extend([pjoin(gathered_data_folder, f) for f in fnames_graph])
    args.append(t_dir)
    exec_and_output("cp", args)
    fnames       = [pjoin(t_dir, f) for f in fnames]
    fnames_graph = [pjoin(t_dir, f) for f in fnames_graph]

    # Generating unique IDs for URLs
    print "Generating unique IDs for URLs"
    ids_dict = pjoin(t_dir, "ids_to_urls.json.gz")
    ids_dict_lst = pjoin(t_dir, "ids_to_urls.lst.gz")
    args = [ids_dict, ids_dict_lst]
    args.extend(fnames_graph)
    exec_and_output("./generate_ids_from_crawl_graph.py", args)

    # Rewriting the crawl information using those IDs
    print "Rewriting the crawl information using those IDs"
    args = [ids_dict]
    args.extend(fnames_graph)
    exec_and_output("./web_crawl_graph_rewrite_with_ids.py", args)
    
    # We now have converted files
    fnames_graph_converted = [f.replace('.json.gz', '.converted.json.gz') for f in fnames_graph]
    
    # And, btw, we do not need the former ones anymore, just remove them:
    print "Memory cleanup..."
    args = ["-vf"]
    args.extend(fnames_graph)
    exec_and_output("rm", args)

    # Now, merge everything
    print "Merging things..."
    merged_graph_converted = pjoin(t_dir, "graph_merged.converted.json.gz")
    args = [number_of_parts, pjoin(t_dir, fname_base), merged_graph_converted, part_pattern]
    exec_and_output("./graph_crawl_parts_merging.py", args)

    # Memory cleanup
    print "Memory cleanup..."
    args = ["-v"]
    args.extend(fnames_graph_converted)
    args.append(gathered_data_folder + "/")  # Trailing slash just to be sure `mv` understands correctly to move several files to a given folder
    exec_and_output("mv", args)

    # Now, we do not need the crawling information anymore, remove it:
    args = ["-vf"]
    args.extend(fnames)
    exec_and_output("rm", args)

    # Now, do a 1st pass of dangling nodes removal. Because loading the graph without those nodes will be so much faster!
    print "1st pass of dangling nodes removal..."
    merged_graph_converted_no_dangling = merged_graph_converted.replace(".json.gz", "_no_dangling.json.gz")
    args = [merged_graph_converted, merged_graph_converted_no_dangling]
    exec_and_output("./remove_dangling_links.py", args)

    # Memory cleanup
    print "Saving everything back to the gathered_data_folder (", gathered_data_folder, ")"
    args = ["-v", merged_graph_converted, merged_graph_converted_no_dangling, ids_dict, gathered_data_folder + "/"]
    exec_and_output("mv", args)

    print "Remove temp dir [Y/n]", t_dir, "?"
    inp = raw_input().strip().lower()
    if inp != "n" and inp != "no":
        exec_and_output("rm", ["-rv", t_dir])
    
    print "Graph-Tool graph generation is not handled by the web crawl process chain. Please run it separately."

    print "Clean"

    print "Done, total running time:", time()-t0

if __name__ == '__main__':
    main()