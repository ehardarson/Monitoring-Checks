#!/usr/bin/env python
# Check to probe name server for percentile response time.
# Code ->> Ellert Hardarson <-> ehardarson.com
# https://github.com/ehardarson/Monitoring-Checks
#
# !! NO WARANTY - home made checks - use at own risk.

import dns.resolver
import time, sys, getopt, urllib
from operator import itemgetter

# define script name.
scriptName=sys.argv[0] 

# define script version.
scriptVersion = "v0.1"

# Nagios plugin exit codes
STATE_OK       = 0
STATE_WARNING  = 1
STATE_CRITICAL = 2
STATE_UNKNOWN  = 3

###  << -- >> ###

class Usage(Exception):
    def __init__(self, err):
        self.msg = err

def usage():
    print "Usage: check_dns_probe.py -s dns_server -U url -P persentile -w warn_ms -c crit_ms -f max_failed"
    print "       check_dns_probe.py -h for detailed help"
    print "       check_dns_probe.py -V for version information"

def detailedUsage():
    print "Plugin to probe dns server with persentile"
    print 
    usage()
    print 
    print "Options:"
    print "  -h"
    print "     Print this help message."
    print "  -V"
    print "     Print version information then exit."
    print "  -s"
    print "     DNS server you want to use for the lookup"
    print "  -U"
    print "     Url list of records to probe"
    print "     Examples in helper-files folder"
    print "  -P"
    print "     Percentile example: 95"
    print "  -w warn_ms" 
    print "     Warning threshold avrage threshold in ms."
    print "  -c crit_ms"
    print "     Critical threshold avrage threshold in ms."
    print 

# parse the command line switches and arguments
try:
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hVH:f:s:U:P:w:c:v", ["help", "output="])
    except getopt.GetoptError, err:
        # print help information and exit:
        raise Usage(err)
except Usage, err:
    print >>sys.stderr, err.msg
    usage()
    sys.exit(STATE_UNKNOWN)

# gather values from given parameter switches
for o, a in opts:
        if o == "-w":
            avtimeWARNING = float(a)
        elif o == "-c":
            avtimeCRITICAL = float(a)
        elif o == "-f":
            failedCritical = int(a)    
        elif o in ("-s", "--server"):
            dns_server = a
        elif o in ("-P", "--percentile"):
            persentile = float(a)
        elif o in ("-U", "--url"):
            url = a
        elif o in ("-V","-v","--version"):
            print scriptName + " " + scriptVersion
            usage()
            sys.exit()
        elif o in ("-h", "--help"):
            detailedUsage()
            sys.exit()
        else:
            assert False, "unhandled option"

# Check to see if specified, throw an error if not.
try:
    avtimeWARNING
except NameError:
    print "Error: no WARNING threshhold specified."
    usage()
    sys.exit(3)
try: 
    avtimeCRITICAL
except NameError:
    print "Error: no CRITICAL threshhold specified."
    usage()
    sys.exit(3)
try:
    dns_server
except NameError:
    print "Error: no DNS server specified."
    usage()
    sys.exit(3)
try:
    persentile
except NameError:
    print "Error: no Persentile specified."
    usage()
    sys.exit(3)    
try:
    url
except NameError:
    print "Error: no URL specified."
    usage()
    sys.exit(3)    
try:
    failedCritical
except NameError:
    print "Error: no max failed specified."
    usage()
    sys.exit(3)

# DNS server
try:
    dns_resolver = dns.resolver.Resolver()
    dns_resolver.nameservers = [dns_server]
except Exception as e:
    print("UNKNOWN : %s " % (e))
    sys.exit(3)

# Open given url text file. # TODO other input options.
try:
    # Open record list.
    records = urllib.urlopen(url)
except Exception as e:
    print("UNKNOWN : %s " % (e))
    sys.exit(3)

try:
    # Convert record_list object to list.
    record_list = []
    for record in records:
        record_list.append(record.rstrip('\r\n'))
except Exception as e:
    print("UNKNOWN : %s " % (e))
    sys.exit(3)    

# Query each record TODO other that just A records.
try:
    lookup_result = []
    failed_counter = 0
    for i in range(1, len(record_list)):
        try:
            result = dns.resolver.query(record_list[i], 'A')
            lookup_result.append({'record': record_list[i], 'query_time': result.response.time * 1000 })
        except Exception:
            failed_counter =+ 1           
except Exception as e:
    print("UNKNOWN : %s " % (e)) 
    sys.exit(3)

# Sort dict by query_time
try:
    # sort lookup 
    lrsorted = sorted(lookup_result, key=itemgetter('query_time'))
except Exception as e:
    print("UNKNOWN : %s " % (e)) 
    sys.exit(3)

# calculate percentile
try:
    perc = float(persentile / 100.0)
    perc_index = int(perc * len(record_list))
    avr_resp_perc_time = (lrsorted[perc_index].get('query_time'))
except Exception as e:
    print("UNKNOWN : %s " % (e)) 
    sys.exit(3)

# check thresholds.
if float(avr_resp_perc_time) >= avtimeCRITICAL:
    checkResult="CRITICAL"
    nagiosState=STATE_CRITICAL
elif float(avr_resp_perc_time) >= avtimeWARNING:
    checkResult="WARNING"
    nagiosState=STATE_WARNING
elif failed_counter >= failedCritical:
    checkResult="CRITICAL"
    nagiosState=STATE_CRITICAL
else:
    # otherwise it's ok
    checkResult="OK"
    nagiosState=STATE_OK

# display output.
print "%s; %s records probed %s failed; average %s percentile response time : %s ms" % (checkResult, len(record_list), failed_counter, int(persentile), round(avr_resp_perc_time, 4))
sys.exit(nagiosState)
