import csv

def parse_text_to_csv(input_file, output_csv_file, debug):
    """
    Parses the input TXT file containing instance details and writes the data to a CSV file.

    Args:
        input_file (str): The path to the input TXT file.
        output_csv_file (str): The name of the output CSV file.
    """

    debug = debug 
    with open(input_file, 'r') as f:
        lines = f.readlines()

    with open(output_csv_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write the header row
        writer.writerow(['Service', 'Region', 'Compartment', 'display_name', 'lifecycle_state', 'id', 'compartment_id', 'created_by', 'created_on', 'EOL', 'LifeTime', 'time_created', 'parent_compartment', 'assigned_to', 'Action', 'Justification'])
        # todo add category

        i = 0
        while i < len(lines):
            if lines[i].startswith("Service:"):
                data = {}
                for j in range(i, i + 12):  # Capture the next 12 lines
                    try:
                        line = lines[j]
                        if debug:
                            print("Line:", line.strip())  # Print the line for debugging
                        if ": " in line:  # Check if the delimiter is present
                            key, value = line.strip().split(": ", 1)
                            data[key] = value
                            compartment = data.get('Compartment', 'N/A')
                            parent_compartment = compartment.split('/')[2] if compartment.startswith('/root/') and len(compartment.split('/')) > 2 else 'N/A'
                        else:
                            print("Skipping line due to missing delimiter:", line.strip())
                    except IndexError:
                        break  # Handle cases with fewer than 12 lines remaining
                    except ValueError:
                        print("Skipping line due to ValueError:", line.strip())  # Error handling
                        continue

                writer.writerow([
                    # print N/A to column if value is not found
                    data.get('Service', 'N/A'), 
                    # todo add category
                    data.get('Region', 'N/A'),
                    data.get('Compartment', 'N/A'),
                    data.get('display_name', 'N/A'),
                    data.get('lifecycle_state', 'N/A'),
                    data.get('id', 'N/A'),
                    data.get('compartment_id', 'N/A'),
                    data.get('created_by', 'N/A'),
                    data.get('created_on', 'N/A'),
                    data.get('EOL', 'N/A'),
                    data.get('LifeTime', 'N/A'),
                    data.get('time_created', 'N/A'),
                    parent_compartment
                ])
                i += 12  # Move to the next potential data block
            else:
                i += 1
