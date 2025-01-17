# import only system from os
import argparse
import oci
import os
import sys
from ocimodules.AnyList import ListAny
#from ocimodules.functions import print_header, input_command_line, create_signer, check_oci_version
from ocimodules.IAM import Login, SubscribedRegions, GetHomeRegion, GetTenantName

##########################################################################
# todo: 
#   - add "if verbose" to list out detail items
#   - fix up objects that are not implemented
#   - refactor things out of list.py into here
#   - find a "procedural" approach instead of individual service functions
##########################################################################

##########################################################################
# define our clear function
##########################################################################
def clear():

    # for windows
    if os.name == 'nt':
        _ = os.system('cls')

    # for mac and linux(here, os.name is 'posix')
    else:
        _ = os.system('clear')


##########################################################################
# Print header centered
##########################################################################
def print_header(name, category):
    options = {0: 95, 1: 85, 2: 60}
    chars = int(options[category])
    print("")
    print('#' * chars)
    print("#" + name.center(chars - 2, " ") + "#")
    print('#' * chars)


##########################################################################
# input_command_line
##########################################################################
def input_command_line(help=False):
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=80, width=130))
    parser.add_argument('-cp', default="", dest='config_profile', help='Config Profile inside the config file')
    parser.add_argument('-ip', action='store_true', default=False, dest='is_instance_principals', help='Use Instance Principals for Authentication')
    parser.add_argument('-dt', action='store_true', default=False, dest='is_delegation_token', help='Use Delegation Token for Authentication')
    parser.add_argument('-log', default="log.txt", dest='log_file', help='output log file')
    parser.add_argument("-f", '--force', action='store_true', default=False, dest='force', help='force list without confirmation')
    parser.add_argument('-d', '--debug', action='store_true', default=False, dest='debug', help='Enable debug')
    parser.add_argument("-rg", "--regions", default="", dest='regions', help="Regions to list comma separated")
    parser.add_argument("-c", "--compartment", default="", dest='compartment', help="top level compartment id to dellistete")
    parser.add_argument("-o", "--objects", dest='objects', default="all", help="Comma-separated list of components to list (e.g., compute,visualbuilder). Default is 'all'")
    parser.add_argument('--top5', action='store_true', default=False, dest='top5', help='List only the "top 5" components. Overrides objects. Ok... more than 5.')
    parser.add_argument('--opencsv', action='store_true', default=False, dest='opencsv', help='Open CSV file at end of execution. Default is false')
    cmd = parser.parse_args()
    if help:
        parser.print_help()

    return cmd


##########################################################################
# Create signer for Authentication
# Input - config_profile and is_instance_principals and is_delegation_token
# Output - config and signer objects
##########################################################################
def create_signer(config_profile, is_instance_principals, is_delegation_token):

    # if instance principals authentications
    if is_instance_principals:
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            config = {'region': signer.region, 'tenancy': signer.tenancy_id}
            return config, signer

        except Exception:
            print("Error obtaining instance principals certificate, aborting")
            sys.exit(-1)

    # -----------------------------
    # Delegation Token
    # -----------------------------
    elif is_delegation_token:

        try:
            # check if env variables OCI_CONFIG_FILE, OCI_CONFIG_PROFILE exist and use them
            env_config_file = os.environ.get('OCI_CONFIG_FILE')
            env_config_section = os.environ.get('OCI_CONFIG_PROFILE')

            # check if file exist
            if env_config_file is None or env_config_section is None:
                print("*** OCI_CONFIG_FILE and OCI_CONFIG_PROFILE env variables not found, abort. ***")
                print("")
                sys.exit(-1)

            config = oci.config.from_file(env_config_file, env_config_section)
            delegation_token_location = config["delegation_token_file"]

            with open(delegation_token_location, 'r') as delegation_token_file:
                delegation_token = delegation_token_file.read().strip()
                # get signer from delegation token
                signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(delegation_token=delegation_token)

                return config, signer

        except KeyError:
            print("* Key Error obtaining delegation_token_file")
            sys.exit(-1)

        except Exception:
            raise

    # -----------------------------
    # config file authentication
    # -----------------------------
    else:
        try:
            config = oci.config.from_file(
                oci.config.DEFAULT_LOCATION,
                (config_profile if config_profile else oci.config.DEFAULT_PROFILE)
            )
            signer = oci.signer.Signer(
                tenancy=config["tenancy"],
                user=config["user"],
                fingerprint=config["fingerprint"],
                private_key_file_location=config.get("key_file"),
                pass_phrase=oci.config.get_config_value_or_default(config, "pass_phrase"),
                private_key_content=config.get("key_content")
            )
        except Exception:
            print("Error obtaining authentication, did you configure config file? aborting")
            sys.exit(-1)

        return config, signer


##########################################################################
# Checking SDK Version
# Minimum version requirements for OCI SDK
##########################################################################
def check_oci_version(min_oci_version_required):
    outdated = False

    for i, rl in zip(oci.__version__.split("."), min_oci_version_required.split(".")):
        if int(i) > int(rl):
            break
        if int(i) < int(rl):
            outdated = True
            break

    if outdated:
        print("Your version of the OCI SDK is out-of-date. Please first upgrade your OCI SDK Library bu running the command:")
        print("OCI SDK Version : {}".format(oci.__version__))
        print("Min SDK required: {}".format(min_oci_version_required))
        print("pip install --upgrade oci")
        quit()

##########################################################################
# Add functionality to only output the components that the user wants
##########################################################################

def list_compute_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "core.ComputeClient", "instance")
    # ListAny(config, signer, processCompartments, "core.ComputeClient", "image")
    # ListAny(config, signer, processCompartments, "core.ComputeClient", "dedicated_vm_host")
    # ListAny(config, signer, processCompartments, "core.ComputeManagementClient", "instance_pool")
    # ListAny(config, signer, processCompartments, "core.ComputeManagementClient", "instance_configuration")
    # ListAny(config, signer, processCompartments, "autoscaling.AutoScalingClient", "auto_scaling_configuration")
    # ListAny(config, signer, processCompartments, "os_management.OsManagementClient", "managed_instance_group")
    # ListAny(config, signer, processCompartments, "os_management.OsManagementClient", "scheduled_job")
    # ListAny(config, signer, processCompartments, "os_management.OsManagementClient", "software_source")
    # ListAny(config, signer, processCompartments, "management_agent.ManagementAgentClient", "management_agent")
    # # ListAny(config, signer, processCompartments, "management_agent.ManagementAgentClient", "management_agent_install_key")

def list_vb_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "visual_builder.VbInstanceClient", "vb_instance")

def list_di_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "data_integration.DataIntegrationClient", "workspace")

def list_db_components(config, signer, processCompartments):
    #Oracle DB
    ListAny(config, signer, processCompartments, "database.DatabaseClient", "db_system")
    ListAny(config, signer, processCompartments, "database.DatabaseClient", "autonomous_database")
    #ListAny(config, signer, processCompartments, "database.DatabaseClient", "backup")

def list_mysql_components(config, signer, processCompartments):
    #MySQL
    ListAny(config, signer, processCompartments, "mysql.DbSystemClient", "db_system")

def list_nosql_components(config, signer, processCompartments):
    #NoSQL
    ListAny(config, signer, processCompartments, "nosql.NosqlClient", "table", ServiceID="table_name_or_id")

def list_oda_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "oda.OdaClient", "oda_instance")

def list_oac_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "analytics.AnalyticsClient", "analytics_instance", ObjectNameVar="name")
    # ListAny(config, signer, processCompartments, "streaming.StreamAdminClient", "stream", ObjectNameVar="name")
    # ListAny(config, signer, processCompartments, "streaming.StreamAdminClient", "stream_pool", ObjectNameVar="name")
    # ListAny(config, signer, processCompartments, "streaming.StreamAdminClient", "connect_harness", ObjectNameVar="name")
    # ListAny(config, signer, processCompartments, "sch.ServiceConnectorClient", "service_connector")

def list_integ_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "integration.IntegrationInstanceClient", "integration_instance")
 
def list_devops_components(config, signer, processCompartments):
    elements = ["deploy_stage", "deploy_artifact", "deploy_environment", "deploy_pipeline", "build_pipeline"]
    for element in elements:
        ListAny(config, signer, processCompartments, "devops.DevopsClient", element)
        ListAny(config, signer, processCompartments, "devops.DevopsClient", "repository", ObjectNameVar="name")
        ListAny(config, signer, processCompartments, "devops.DevopsClient", "project", ObjectNameVar="name")

def list_ocvs_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "ocvp.SddcClient", "sddc")

def list_dbmigration_components(config, signer, processCompartments):
    elements = ["migration", "connection"]
    for element in elements:
        ListAny(config, signer, processCompartments, "database_migration.DatabaseMigrationClient", element)

def list_migration_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "cloud_migrations.MigrationClient", "migration_plan")
    ListAny(config, signer, processCompartments, "cloud_migrations.MigrationClient", "migration")
    ListAny(config, signer, processCompartments, "cloud_migrations.MigrationClient", "replication_schedule")
    ListAny(config, signer, processCompartments, "cloud_bridge.OcbAgentSvcClient", "environment")
    ListAny(config, signer, processCompartments, "cloud_bridge.OcbAgentSvcClient", "agent_dependency")
    ListAny(config, signer, processCompartments, "cloud_bridge.DiscoveryClient", "asset_source")
    ListAny(config, signer, processCompartments, "cloud_bridge.DiscoveryClient", "discovery_schedule")
    ListAny(config, signer, processCompartments, "cloud_bridge.InventoryClient", "asset")
    ListAny(config, signer, processCompartments, "cloud_bridge.InventoryClient", "inventory")

def list_gg_components(config, signer, processCompartments):
    elements = ["database_registration", "deployment", "deployment_backup"]
    for element in elements:
        ListAny(config, signer, processCompartments, "golden_gate.GoldenGateClient", element)

def list_bastion_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "bastion.BastionClient", "bastion", ObjectNameVar="name")

def list_waf_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "waf.WafClient", "web_app_firewall")
    # ListAny(config, signer, processCompartments, "waf.WafClient", "web_app_firewall_policy")

#def list_os_components(config, signer, processCompartments):
    ## todo object storage
    # ListAny(config, signer, processCompartments, "data_integration.DataIntegrationClient", "workspace")

def list_cloudguard_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "cloud_guard.CloudGuardClient", "target")
    ListAny(config, signer, processCompartments, "cloud_guard.CloudGuardClient", "detector_recipe")
    ListAny(config, signer, processCompartments, "cloud_guard.CloudGuardClient", "responder_recipe")
    ListAny(config, signer, processCompartments, "cloud_guard.CloudGuardClient", "managed_list")

# def list_email_components(config, signer, processCompartments):
#     ListAny(config, signer, processCompartments, "email.EmailClient", "sender", ObjectNameVar="email_address")
#     if processRootCompartment:
#         ListAny(config, signer, processRootCompartment, "email.EmailClient", "suppression", ObjectNameVar="email_address")
#     ListAny(config, signer, processCompartments, "email.EmailClient", "email_domain", ObjectNameVar="name")

def list_oke_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "container_engine.ContainerEngineClient", "cluster", ObjectNameVar="name")

def list_ocir_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "artifacts.ArtifactsClient", "container_repository", ServiceID="repository_id")
    ListAny(config, signer, processCompartments, "artifacts.ArtifactsClient", "repository")

def list_ds_components(config, signer, processCompartments):
    # ListAny(config, signer, processCompartments, "data_science.DataScienceClient", "notebook_session")
    ListAny(config, signer, processCompartments, "data_science.DataScienceClient", "model_deployment")
    ListAny(config, signer, processCompartments, "data_science.DataScienceClient", "model")
    ListAny(config, signer, processCompartments, "data_science.DataScienceClient", "project")

# def list_fn_components(config, signer, processCompartments):
#     ## todo functions service
#     ListAny(config, signer, processCompartments, "data_integration.DataIntegrationClient", "workspace")

def list_apigw_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "apigateway.DeploymentClient", "deployment")
    ListAny(config, signer, processCompartments, "apigateway.GatewayClient", "gateway")
    ListAny(config, signer, processCompartments, "apigateway.ApiGatewayClient", "api")
    ListAny(config, signer, processCompartments, "apigateway.ApiGatewayClient", "certificate")

def list_datasafe_components(config, signer, processCompartments):
    # ListAny(config, signer, processCompartments, "data_safe.DataSafeClient", "user_assessment")
    # ListAny(config, signer, processCompartments, "data_safe.DataSafeClient", "security_assessment")
    ListAny(config, signer, processCompartments, "data_safe.DataSafeClient", "target_database")
    ListAny(config, signer, processCompartments, "data_safe.DataSafeClient", "on_prem_connector")
    ListAny(config, signer, processCompartments, "data_safe.DataSafeClient", "data_safe_private_endpoint")

# def list_dbmanagement_components(config, signer, processCompartments):
#     DisableDatabaseManagement(config, signer, processCompartments)
#     ListAny(config, signer, processCompartments, "database_management.DbManagementClient", "db_management_private_endpoint", ObjectNameVar="name")
#     ListAny(config, signer, processCompartments, "database_management.DbManagementClient", "managed_database_group", ObjectNameVar="name", DelState="", DelingSate="")

# def list_loganalytics_components(config, signer, processCompartments):
#     ListAny(config, signer, processCompartments, "log_analytics.LogAnalyticsClient", "log_analytics_entity", ObjectNameVar="name", Extra=", namespace_name=\"{}\"".format(tenant_name))

def list_datacatalog_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "data_catalog.DataCatalogClient", "catalog")
    ListAny(config, signer, processCompartments, "data_catalog.DataCatalogClient", "catalog_private_endpoint")
    ListAny(config, signer, processCompartments, "data_catalog.DataCatalogClient", "metastore")

def list_blockchain_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "blockchain.BlockchainPlatformClient", "blockchain_platform")

def list_rm_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "resource_manager.ResourceManagerClient", "stack")
    ListAny(config, signer, processCompartments, "resource_manager.ResourceManagerClient", "configuration_source_provider")

# def list_anomaly_components(config, signer, processCompartments):
    # ListAny(config, signer, processCompartments, "ai_anomaly_detection.AnomalyDetectionClient", "data_asset")
    # ListAny(config, signer, processCompartments, "ai_anomaly_detection.AnomalyDetectionClient", "model")
    # ListAny(config, signer, processCompartments, "ai_anomaly_detection.AnomalyDetectionClient", "project")

def list_dataflow_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "data_flow.DataFlowClient", "private_endpoint")
    ListAny(config, signer, processCompartments, "data_flow.DataFlowClient", "application")
    ListAny(config, signer, processCompartments, "data_flow.DataFlowClient", "run")

def list_block_components(config, signer, processCompartments):
    # ListAny(config, signer, processCompartments, "core.BlockstorageClient", "volume_group")
    # ListAny(config, signer, processCompartments, "core.BlockstorageClient", "volume_group_backup")
    ListAny(config, signer, processCompartments, "core.BlockstorageClient", "volume")
    ListAny(config, signer, processCompartments, "core.BlockstorageClient", "volume_backup")
    ListAny(config, signer, processCompartments, "core.BlockstorageClient", "boot_volume")
    ListAny(config, signer, processCompartments, "core.BlockstorageClient", "boot_volume_backup")
    # ListAny(config, signer, processCompartments, "core.BlockstorageClient", "volume_backup_policy", ServiceID="policy_id")

def list_fss_components(config, signer, processCompartments):
    # ListAny(config, signer, processCompartments, "file_storage.FileStorageClient", "mount_target", PerAD=True)
    ListAny(config, signer, processCompartments, "file_storage.FileStorageClient", "file_system", PerAD=True)

def list_network_components(config, signer, processCompartments):
    #DeleteVCN(config, signer, processCompartments)
    ListAny(config, signer, processCompartments, "core.VirtualNetworkClient", "local_peering_gateway")
    ListAny(config, signer, processCompartments, "core.VirtualNetworkClient", "remote_peering_connection")
    ListAny(config, signer, processCompartments, "core.VirtualNetworkClient", "drg")

def list_observability_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "monitoring.MonitoringClient", "alarm")
    ListAny(config, signer, processCompartments, "ons.NotificationControlPlaneClient", "topic", ObjectNameVar="name", ServiceID="topic_id", ReturnServiceID="topic_id")
    ListAny(config, signer, processCompartments, "events.EventsClient", "rule")
    #DeleteLogGroups(config, signer, processCompartments)
    #DeleteAPM(config, signer, processCompartments)

def list_iam_components(config, signer, processCompartments):
    ListAny(config, signer, processCompartments, "identity.IdentityClient", "policy", ObjectNameVar="name")
    ListAny(config, signer, processCompartments, "identity.IdentityClient", "dynamic_group", ObjectNameVar="name")
    ## todo add users and groups
