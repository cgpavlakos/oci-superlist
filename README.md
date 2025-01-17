# OCI-SuperList
List all Oracle Cloud resources in a compartment, and export to CSV. 

## Inspired by:
- [OCI-SuperDelete](https://github.com/AnykeyNL/OCI-SuperDelete)
  - Almost evertyhing in OCI-SuperList is a modification of the SUPERB work done by that team
  - I highly recommend OCI-SuperDelete for all your nuking needs!
- [CD3](https://github.com/oracle-devrel/cd3-automation-toolkit)
  - The excel export was essentially what I need, but CD3 is overkill here
- [ociextirpate](https://github.com/therealcmj/ociextirpater)
  - Has the very good idea (and with a much better implementation than me!) to work on "object categories"  

## Why does this exist? 
I was charged with reducing consumption on an Oracle Cloud tenancy by 90% because things had spiralled out of control with folks just spinning things up and never coming back to turn them off. However, there are a few critical things running so running something like [OCI-SuperDelete](https://github.com/AnykeyNL/OCI-SuperDelete) at the root compartment would be too disruptive. I have used [CD3](https://github.com/oracle-devrel/cd3-automation-toolkit) in the past and it gives a very nice detailed export, but it's overkill for my scenario and I wanted the export formatted completely differently. 

So I did my normal thing... spend the better part of few days writing up a program to do something I could do manually in a few hours at most. Enjoy! 

I used this tool to get a list of the resources that were burning a hole in my pocket along with metadata like when they were created, by who, and what compartment tree (business unit) they fall under. This made it easy for me to see things that can be terminated, and follow up with folks (and their managers) for anything I was unsure about. Consumption in the tenancy I administer is down to under $800 per day from a peak of $3,400 per day. Only 76% of my 90% goal, but that's because of politics, not tooling! I know exactly what resources I need to terminate to hit 90% - but I don't want to shoot something that needs saving, to paraphrase Dutch van der Linde.  

## Getting Started:
I assume that if you are using this, you already have your oci cli configured and ready to go. If you need help with that, google is your friend. 

The basic command to run it is `python3 list.py -c ocid1.compartment.oc1..abcd1234` 

This will give you:
- A list of all supported objects and their details in log.txt
- A csv table of the same objects and details in log.txt.csv

I usually run it like `python3 list.py -c ocid1.compartment.oc1..abcd1234 -log export-20250116.txt --top5 -f --opencsv`

This gives me:
- A list of "top 5" supported objects (--top5) and their details in export-20250116.txt (-log)
- A csv table of the same objects and details in export-20250116.txt.csv 
- Automatically opens the csv for me to filter and mark up with actions for each resource
- Skips the confirmation prompt (-f)

It's self-documenting:
```
mandatory arguments:
  -c, --compartment COMPARTMENT              top level compartment id to list

optional arguments:
  -h, --help                                 show this help message and exit
  -cp CONFIG_PROFILE                         Config Profile inside the config file
  -ip                                        Use Instance Principals for Authentication
  -dt                                        Use Delegation Token for Authentication
  -log LOG_FILE                              output log file
  -f, --force                                force list without confirmation
  -d, --debug                                Enable debug
  -rg REGIONS, --regions REGIONS             Regions to list comma separated
  -o OBJECTS, --objects OBJECTS              Comma-separated list of components to list (e.g., compute,visualbuilder). Default is 'all'
  --top5                                     List only the "top 5" components. Overrides objects. Ok... more than 5.
  --opencsv                                  Open CSV file at end of execution. Default is false
```
## Work In Progress:
You will see throughout the code things labeled as #todo or maybe even notice entire families of services are missing. I will update to fix over time, and maybe (probably not) refactor to make the code cleaner. 

Currently on my list:
- Add a Category column to the CSV
- Fix up missing/incomplete services
- Add "if verbose" to optionally list out "detail items" that I have commented out for now
  - maybe this is more intuitive as a "detail level 1, 2, 3" structure
- Refactor and clean up code (not likely!)

Future Plans (OCI-TargetedDelete):
- Read input from a CSV and terminate resources based on some structure
- Check if resources have been tagged properly and terminate them if not
  - or add to a "cull list" csv for review before action
- Check EOL tag and terminate if in the past
  - or add to a "cull list" csv for review before action

## How Does It Work?
If you want to dig in and understand or modify the code, the important things to look at are:
- `list.py` inside of the Regions loop for the main flow
- `functions.py` and `anylist.py` for details of how the details are gathered
- `parse.py` for how the csv is generated

## Legalese:
This is a personal repository. Any code, views or opinions represented here are personal and belong solely to me and do not represent those of people, institutions or organizations that I may or may not be associated with in professional or personal capacity, unless explicitly stated. If you choose to run this tool, you are responsible for understanding what it does and release me from any liability. 
