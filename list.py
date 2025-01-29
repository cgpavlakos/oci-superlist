#!/usr/bin/env python3

##########################################################################################
# OCI-SuperList                                                                          #
#                                                                                        #
# Use with PYTHON3!                                                                      #
##########################################################################################
# Application Command line parameters
#
#   -cp profile              - profile inside the config file
#   -ip                      - Use Instance Principals for Authentication
#   -dt                      - Use Instance Principals with delegation token for cloud shell
#   -f,  --force             - Force list, skipping confirmation
#   -rg, --regions           - Regions to list comma separated
#   -c,  --compartment       - Top level compartment to list
#   -d,  --debug             - Enable debug
#   -o,  --objects           - Comma-separated list of components to list (e.g., Compute,Database,VbInstance). Default is all.
#   --openscv                - Open csv file when program completes
#   --top5                   - List only the top 5 most pertinent types of objects. Ok... more than 5. 
#
##########################################################################################
# todo:                                                                                  #
#    - add any missing services
#    - add Category to CSV 
#    - refactor to clean up code
#    - add "if verbose" to list out detail items
##########################################################################################

import sys
import time
import oci
import platform
import logging
import os

# import ocimodules
from ocimodules.functions import ( 
    print_header, input_command_line, create_signer, check_oci_version, 
    list_compute_components, list_vb_components, list_di_components,
    list_db_components, list_mysql_components, list_nosql_components, 
    list_oda_components, list_oac_components, list_integ_components, 
    list_devops_components, list_ocvs_components, list_dbmigration_components, 
    list_migration_components, list_gg_components, list_bastion_components,
    list_waf_components, list_cloudguard_components, list_oke_components,
    list_ocir_components, list_ds_components, list_apigw_components, 
    list_datasafe_components, list_datacatalog_components, list_blockchain_components,
    list_rm_components, list_dataflow_components, list_block_components, 
    list_fss_components, list_network_components, list_observability_components, list_iam_components
    # list_os_components, list_email_components, list_fn_components
    # list_dbmanagement_components, list_loganalytics_components, list_anomaly_components
)
from ocimodules.IAM import Login, SubscribedRegions, GetHomeRegion, GetTenantName
from ocimodules.parse import parse_text_to_csv

# Disable OCI CircuitBreaker feature
oci.circuit_breaker.NoCircuitBreakerStrategy()

#################################################
#           Manual Configuration                #
#################################################
# Specify your config file
configfile = "~/.oci/config"  # Linux
# configfile = "/etc/oci/config" # Cloud Shell
# configfile = "\\Users\\username\\.oci\\config"  # Windows

# Specify your config profile
configProfile = "DEFAULT"

# Specify the DEFAULT compartment OCID that you want to delete, Leave Empty for no default
ListCompartmentOCID = ""

# Search for resources in regions, this is an Array, so you can specify multiple regions:
# If no regions specified, it will be all subscribed regions.
# regions = ["eu-frankfurt-1", "us-ashburn-1", "us-chicago-1", "us-phoenix-1", "us-sanjose-1", "ca-toronto-1"]
regions = ["us-ashburn-1", "us-chicago-1", "us-phoenix-1"]

#################################################
#           Application Configuration           #
#################################################
min_version_required = "2.88.0"
application_version = "24.12.01"
debug = False


#############################################
# MyWriter to redirect output
#############################################
class MyWriter:

    filename = "log.txt"

    def __init__(self, stdout, filename):
        self.stdout = stdout
        self.filename = filename
        self.logfile = open(self.filename, "a", encoding="utf-8")

    def write(self, text):
        self.stdout.write(text)
        self.logfile.write(text)

    def close(self):
        self.stdout.close()
        self.logfile.close()

    def flush(self):
        self.logfile.close()
        self.logfile = open(self.filename, "a", encoding="utf-8")

    def clear_buffer(self):
        self.logfile.flush()  # Flush the log file buffer
        os.fsync(self.logfile.fileno())


def CurrentTimeString():
    return time.strftime("%D %H:%M:%S", time.localtime())


##########################################################################
# Main Program
##########################################################################
check_oci_version(min_version_required)

# Check command line
cmd = input_command_line()

# Redirect output to log.txt
logfile = cmd.log_file
writer = MyWriter(sys.stdout, logfile)
sys.stdout = writer

# configfile = cmd.config_file if cmd.config_file else configfile
configProfile = cmd.config_profile if cmd.config_profile else configProfile
debug = cmd.debug if cmd.debug else debug
force = cmd.force
regions = cmd.regions.split(",") if cmd.regions else regions
ListCompartmentOCID = cmd.compartment if cmd.compartment else ListCompartmentOCID
objects = cmd.objects.split(",") if cmd.objects else ["all"]  # Enforce list
top5 = cmd.top5
if top5:
    objects = ["Top 5"]
opencsv = cmd.opencsv 

if ListCompartmentOCID == "":
    print("No compartment specified \n")
    input_command_line(help=True)
    sys.exit(2)

######################################################
# oci config and debug handle
######################################################
config, signer = create_signer(cmd.config_profile, cmd.is_instance_principals, cmd.is_delegation_token)
tenant_id = config['tenancy']

if debug:
    config['log_requests'] = True
    logging.basicConfig()
    logging.getLogger('oci').setLevel(logging.DEBUG)

######################################################
# Loading Compartments
# Add all active compartments,
# exclude the ManagementCompartmentForPaas (as this is locked compartment)
# Add root compartment to processRootCompartment if specified for root compartment objects
######################################################
print("\nLogin check and loading compartments...\n")
compartments = Login(config, signer, ListCompartmentOCID)
processCompartments = []
processRootCompartment = []
for compartment in compartments:
    if compartment.details.lifecycle_state == "ACTIVE" and compartment.details.name != "ManagedCompartmentForPaaS":
        processCompartments.append(compartment)
    if compartment.details.id == tenant_id:
        processRootCompartment.append(compartment)

# Check if regions specified if not getting all subscribed regions.
if len(regions) == 0:
    regions = SubscribedRegions(config, signer)

homeregion = GetHomeRegion(config, signer)
tenant_name = GetTenantName(config, signer)

######################################################
# Header Print and Confirmation
######################################################
print_header("OCI-SuperList", 0)

print("Date/Time          : " + CurrentTimeString())
print("Command Line       : " + ' '.join(x for x in sys.argv[1:]))
print("App Version        : " + application_version)
print("Machine            : " + platform.node() + " (" + platform.machine() + ")")
print("OCI SDK Version    : " + oci.version.__version__)
print("Python Version     : " + platform.python_version())
print("Config File        : " + configfile)
print("Config Profile     : " + configProfile)
print("Log File           : " + logfile)
print("")
print("Tenant Name        : " + tenant_name)
print("Tenant Id          : " + config['tenancy'])
print("Home Region        : " + homeregion)
print("Regions to Process : " + ','.join(x for x in regions))
print("Components to Process : " + ', '.join(objects))
print("\nCompartments to Process : \n")
for c in processCompartments:
    print("  " + c.fullpath)


#########################################
# Check confirmation for execution
#########################################
confirm = ""
if force:
    confirm = "yes"
else:
    confirm = input("\ntype yes to list contents from these compartments: ")
if confirm == "yes":

    ######################################################
    # Loop on Regions
    ######################################################
    for region in regions:

        print_header("Listing resources in region " + region, 0)
        config["region"] = region

        if "compute" in objects or "all" in objects or top5:
            print_header("Listing Compute Instances at " + CurrentTimeString() + "@ " + region, 1)
            list_compute_components(config, signer, processCompartments)

        if "vbinstance" in objects or "all" in objects or top5:
            print_header("Listing Visual Builder Components at " + CurrentTimeString() + "@ " + region, 1)
            list_vb_components(config, signer, processCompartments)  # Call the function from functions.py

        if "dataintegration" in objects or "all" in objects:
            print_header("Listing Data Integratation services at " + CurrentTimeString() + "@ " + region, 1)
            list_di_components(config, signer, processCompartments)

        if "database" in objects or "all" in objects or top5:
            print_header("Listing Oracle Databases at " + CurrentTimeString() + "@ " + region, 1)
            list_db_components(config, signer, processCompartments) 

        if "database" in objects or "all" in objects or top5:
            print_header("Listing MySQL Database Instances at " + CurrentTimeString() + "@ " + region, 1)
            list_mysql_components(config, signer, processCompartments)

        if "database" in objects or "all" in objects or top5:
            print_header("Listing Nosql tables at " + CurrentTimeString() + "@ " + region, 1)
            list_nosql_components(config, signer, processCompartments)

        if "oda" in objects or "all" in objects or top5:
            print_header("Listing Digital Assistants at " + CurrentTimeString() + "@ " + region, 1)
            list_oda_components(config, signer, processCompartments)

        if "analytics" in objects or "all" in objects or top5:
            print_header("Listing Analytics at " + CurrentTimeString() + "@ " + region, 1)
            list_oac_components(config, signer, processCompartments)

        if "integration" in objects or "all" in objects:
            print_header("Listing Integration at " + CurrentTimeString() + "@ " + region, 1)
            list_integ_components(config, signer, processCompartments)

        if "devops" in objects or "all" in objects:
            print_header("Listing DevOps Projects at " + CurrentTimeString() + "@ " + region, 1)
            list_devops_components(config, signer, processCompartments)

        if "ocvs" in objects or "all" in objects or top5:
            print_header("Listing Oracle Cloud VMware solution at " + CurrentTimeString() + "@ " + region, 1)
            list_ocvs_components(config, signer, processCompartments)

        if "dbmigration" in objects or "all" in objects:
            print_header("Listing Database Migrations at " + CurrentTimeString() + "@ " + region, 1)
            list_dbmigration_components(config, signer, processCompartments)

        if "migration" in objects or "all" in objects:
            print_header("Listing Migrations at " + CurrentTimeString() + "@ " + region, 1)
            list_migration_components(config, signer, processCompartments)

        if "goldengate" in objects or "all" in objects:
            print_header("Listing GoldenGate at " + CurrentTimeString() + "@ " + region, 1)
            list_gg_components(config, signer, processCompartments)

        if "bastion" in objects or "all" in objects:
            print_header("Listing Bastion Services at " + CurrentTimeString() + "@ " + region, 1)
            list_bastion_components(config, signer, processCompartments)

        if "waf" in objects or "all" in objects:
            print_header("Listing Web Application Firewall at " + CurrentTimeString() + "@ " + region, 1)
            list_waf_components(config, signer, processCompartments)

        # if "objectstorage" in objects or "all" in objects:
        #     print_header("Listing Object Storage at " + CurrentTimeString() + "@ " + region, 1)
        #     list_os_components(config, signer, processCompartments)

        if "cloudguard" in objects or "all" in objects:
            print_header("Listing Cloud Guard Servcies at " + CurrentTimeString() + "@ " + region, 1)
            list_cloudguard_components(config, signer, processCompartments)

        # if "email" in objects or "all" in objects:
        #     print_header("Listing Email Service at " + CurrentTimeString() + "@ " + region, 1)
        #     list_email_components(config, signer, processCompartments)

        if "oke" in objects or "all" in objects:
            print_header("Listing OKE Clusters at " + CurrentTimeString() + "@ " + region, 1)
            list_oke_components(config, signer, processCompartments)

        if "ocir" in objects or "all" in objects:
            print_header("Listing Repositories at " + CurrentTimeString() + "@ " + region, 1)
            list_ocir_components(config, signer, processCompartments)

        if "datascience" in objects or "all" in objects:
            print_header("Listing DataScience Components at " + CurrentTimeString() + "@ " + region, 1)
            list_ds_components(config, signer, processCompartments)

        # if "functions" in objects or "all" in objects:
        #     print_header("Listing Functions (Fn) at " + CurrentTimeString() + "@ " + region, 1)
        #     list_fn_components(config, signer, processCompartments)

        if "apigateway" in objects or "all" in objects:
            print_header("Listing API Gateway Service at " + CurrentTimeString() + "@ " + region, 1)
            list_apigw_components(config, signer, processCompartments)

        if "datasafe" in objects or "all" in objects:
            print_header("Listing Datasafe services at " + CurrentTimeString() + "@ " + region, 1)
            list_datasafe_components(config, signer, processCompartments)

        # if "dbmanagement" in objects or "all" in objects:
        #     print_header("Listing Database Management services at " + CurrentTimeString() + "@ " + region, 1)
        #     list_dbmanagement_components(config, signer, processCompartments)

        # if "loganalytics" in objects or "all" in objects:
        #     print_header("Listing Log Analytics services at " + CurrentTimeString() + "@ " + region, 1)1)
        #     list_loganalytics_components(config, signer, processCompartments)

        if "datacatalog" in objects or "all" in objects:
            print_header("Listing Data Catalog services at " + CurrentTimeString() + "@ " + region, 1)
            list_datacatalog_components(config, signer, processCompartments)

        if "blockchain" in objects or "all" in objects:
            print_header("Listing Blockchain at " + CurrentTimeString() + "@ " + region, 1)
            list_blockchain_components(config, signer, processCompartments)

        if "rm" in objects or "all" in objects:
            print_header("Listing Resource Manager Stacks at " + CurrentTimeString() + "@ " + region, 1)
            list_rm_components(config, signer, processCompartments)

        # if "anomaly" in objects or "all" in objects:
        #     print_header("Listing Anomaly Detection Services at " + CurrentTimeString() + "@ " + region, 1)
        #     list_anomaly_components(config, signer, processCompartments)

        if "dataflow" in objects or "all" in objects:
            print_header("Listing Data Flow Services at " + CurrentTimeString() + "@ " + region, 1)
            list_dataflow_components(config, signer, processCompartments)

        if "block" in objects or "all" in objects or top5:
            print_header("Listing Block Volumes at " + CurrentTimeString() + "@ " + region, 1)
            list_block_components(config, signer, processCompartments)

        if "fss" in objects or "all" in objects or top5:
            print_header("Listing FileSystem and Mount Targets at " + CurrentTimeString() + "@ " + region, 1)
            list_fss_components(config, signer, processCompartments)

        if "network" in objects or "all" in objects:
            print_header("Listing Network Components at " + CurrentTimeString() + "@ " + region, 1)
            list_network_components(config, signer, processCompartments)

        if "observability" in objects or "all" in objects:
            print_header("Listing Database Migrations at " + CurrentTimeString() + "@ " + region, 1)
            list_observability_components(config, signer, processCompartments)

        if "iam" in objects or "all" in objects:
            if region == homeregion:
                print_header("Listing IAM Components at " + CurrentTimeString() + "@ " + region, 1)
                list_iam_components(config, signer, processCompartments)


    print_header("SUCCESS! Listing complete at " + CurrentTimeString(), 0)
    print("Tenant Name          : " + tenant_name)
    print("Tenant Id            : " + config['tenancy'])
    print("Home Region          : " + homeregion)
    print("Regions processed    : " + ','.join(x for x in regions))
    print("Objects              : " + ', '.join(objects))
    for c in processCompartments:
        print("Compartment          : " + c.fullpath)
    csv_file = logfile + ".csv" 
    print_header("Waiting for log file to fully flush before writing csv...", 0) 
    writer.flush() 
    time.sleep(3)
    print_header("Writing csv file...", 2)
    parse_text_to_csv(logfile, csv_file, debug)
    print("CSV file is ready at: "+ csv_file + "\n")
    # Open the CSV file
    if opencsv:
        print("Opening" + csv_file + "\n")
        if os.name == 'nt':  # Windows
            os.startfile(csv_file)
        elif os.name == 'posix':  # macOS or Linux
            if sys.platform == 'darwin':  # macOS
                os.system(f'open {csv_file}')
            else:  # Linux
                os.system(f'xdg-open {csv_file}')
else:
    print("ok, doing nothing")
