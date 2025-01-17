import oci
import time

WaitRefresh = 15
MaxIDeleteIteration = 20

##########################################################################
# ListAny
# Lists any OCI Object
##########################################################################
def ListAny(config, signer, Compartments, ServiceClient, ServiceName, ServiceID="", ReturnServiceID="id", ListCommand="", GetCommand="", ObjectNameVar="display_name", Extra="", Filter="", PerAD=False):
    try:
        AllItems = []
        object = eval("oci.{}(config, signer=signer)".format(ServiceClient))
        if not object:
            print(f'Object not defined for {ServiceName}')

        if ServiceID == "":
            ServiceID = ServiceName + "_id"
        if ListCommand == "":
            # If service name ends on 'y', make plural to 'ies', "ss" to "sses", else just add 's'
            if ServiceName[-2:] == "ay":
                ListCommand = "list_" + ServiceName + "s"
            elif ServiceName[-2:] == "ey":
                ListCommand = "list_" + ServiceName + "s"
            elif ServiceName[-1] == "y":
                ListCommand = "list_" + ServiceName[0:-1] + "ies"
            elif ServiceName[-2:] == "ss":
                ListCommand = "list_" + ServiceName + "es"
            else:
                ListCommand = "list_" + ServiceName + "s"
        if GetCommand == "":
            GetCommand = "get_" + ServiceName

        if PerAD:
            identity = oci.identity.IdentityClient(config, signer=signer)

        print("Getting all {} objects                 ".format(ServiceName), end="\r")
        items = []
        for C in Compartments:
            Compartment = C.details
            compartment_name = C.fullpath
            try:
                if PerAD:
                    ads = identity.list_availability_domains(compartment_id=Compartment.id).data
                    for ad in ads:
                        itemstemp = eval("oci.pagination.list_call_get_all_results(object.{}, availability_domain=\"{}\", compartment_id=Compartment.id{}, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY).data".format(ListCommand, ad.name, Extra))
                        for item in itemstemp:
                            items.append(item)
                else:
                    items = eval("oci.pagination.list_call_get_all_results(object.{}, compartment_id=Compartment.id{}, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY).data".format(ListCommand, Extra))
            except oci.exceptions.ServiceError as response:
                if response.code == 404:
                    print("No items found in compartment {}   ".format(Compartment.name), end="\r")
                else:
                    print("error {}-{} trying to list: {}".format(response.code, response.message, ServiceName))

            for item in items:
                if item.lifecycle_state.lower() not in ("deleted","terminated"):
                    print("----------------------------------------------------")
                    print(f'Service: {ServiceName}')
                    # todo add category
                    print(f'Region:', config["region"]) 
                    print(f'Compartment:', compartment_name) 
                    # print(f'Full Item contents for debug:')
                    # print(item) 
                    if hasattr(item, ObjectNameVar):
                        print(f'{ObjectNameVar}: {getattr(item, ObjectNameVar)}')
                    if hasattr(item, "lifecycle_state"):
                        print(f'lifecycle_state: {item.lifecycle_state}')
                    if hasattr(item, "id"):
                        print(f'id: {item.id}')
                    if hasattr(item, "compartment_id"):
                        print(f'compartment_id: {item.compartment_id}')
                # Extract and print tags (with placeholders for missing values)
                    defined_tags = item.defined_tags if hasattr(item, "defined_tags") and item.defined_tags is not None else {}
                    oracle_tags = defined_tags.get("Oracle-Tags", {}) if defined_tags else {}
                    created_by_value = oracle_tags.get("CreatedBy", "MISSING")
                    if created_by_value != "MISSING" and "/" in created_by_value:
                        created_by_value = created_by_value.split("/")[-1]
                    print(f'created_by: {created_by_value}')
                    print(f'created_on: {oracle_tags.get("CreatedOn", "MISSING").split("T")[0] if oracle_tags.get("CreatedOn", "MISSING") != "MISSING" else "MISSING"}') 
                    print(f'EOL: {oracle_tags.get("EOL", "MISSING")}')
                    print(f'LifeTime: {oracle_tags.get("LifeTime", "MISSING")}')
                    # Extract and print time_created
                    if hasattr(item, "time_created"):
                        time_created_str = item.time_created.strftime("%Y-%m-%d")  # Format the date
                        print(f'time_created: {time_created_str}') 
                    else:
                        print('time_created: MISSING')
                    print("----------------------------------------------------")

    except Exception as e:
        print(f'\nError in ListAny, {ServiceClient}:{ServiceName}: {str(e)}')

