# A script to, with some user help and knowledge of boto3 (or at least its documentation), derive Terraform import blocks from bulk AWS resources
import boto3
from botocore.exceptions import ClientError
import re
import os
import sys

sys.path.append(os.path.realpath("."))
import inquirer

output_sent = False
while not output_sent:
    output_mode_question = [
        inquirer.List(
            "mode",
            message="Do you want to output to a file or to stdout?",
            choices=["import.tf file", "standard output"],
        ),
    ]

    output_mode_answer = inquirer.prompt(output_mode_question)

    method_input_answer = inquirer.text(
        message="Enter boto3 client or resource method i.e. boto3.client('s3')"
    )

    method_code = compile(method_input_answer, "<string>", "eval")

    try:
        boto3_resource_method = eval(method_code)
        print(f"boto3 client or resource method successfully registered!")
    except Exception as error:
        print("An exception occurred: ", error)
        print("Returning to output location selection...")
        continue

    try:
        # resource list method setup
        resource_listing_answer = inquirer.text(
            message="Enter resource listing method for your client or resource method i.e. list_buckets()"
        )

        try:
            resource_listing_code = compile(
                f"{method_input_answer}.{resource_listing_answer}",
                "<string>",
                "eval",
            )
            resource_listing_output = eval(resource_listing_code)
            print(f"Resource listing method successfully registered!")
        except Exception as error:
            print("An exception occurred: ", error)
            print("Returning to output location selection...")
            continue
    except ClientError as e:
        print(e)
        print("Returning to output location selection...")
        continue

    top_level_key_answer = inquirer.text(
        message=f"Enter the top-level key with the resource's id without quotes. Output keys for your listing method are {[key for key in resource_listing_output.keys()]}"
    )

    print("Resource list successful!")

    # this is a decent assumption that record 0 will have the appropriate ID key along with the rest of the records, but it's an assumption
    resource_id_answer = inquirer.text(
        message=f"Enter the Terraform import id key underneath the key {top_level_key_answer}, without quotes. Keys for the top-level key you selected are {[key for key in resource_listing_output[top_level_key_answer][0].keys()]}"
    )
    print("Import id key selected!")

    # can probably just hardcode in the "aws_"?
    resource_type_answer = inquirer.text(
        message="Input your Terraform resource type here, such as aws_instance"
    )
    print("Generating Terraform import blocks... \n____________________________\n")

    import_blocks = []

    for resource in resource_listing_output[top_level_key_answer]:
        import_id = resource[resource_id_answer]

        import_id_str = "import {\n  id = " + '"' + import_id + '"'

        # just a regex to convert dots to underscore for now, other parsing may be necessary (such as removing spaces for underscores from some ids, any other illegal tf characters there
        import_to_str = (
            "\n  to = "
            + resource_type_answer
            + "."
            + re.sub("\.", "_", import_id)
            + "\n  }"
        )
        # create and append resource's import block to blocks
        import_blocks.append(import_id_str + import_to_str)

    if output_mode_answer["mode"] == "import.tf file":
        # create import file
        with open("import.tf", "w") as f:
            print("Terraform import blocks written to import.tf!")
            for line in import_blocks:
                f.write(f"{line}\n\n")
            output_sent = True
    elif output_mode_answer["mode"] == "standard output":
        print("Printing Terraform import blocks to standard output:\n")
        # output to terminal
        for line in import_blocks:
            print(f"{line}\n\n")
        output_sent = True
    else:
        raise Exception("Something went wrong, likely with the execution mode dialog!")
        print("Returning to output location selection...")
        continue
