from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import convert_pdf_to_csv
from .models import ReceiptFile
import tabula
import tempfile
import os
import re

def check_file_type(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.pdf':
        return "PDF"
    elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
        return "IMAGE"
    else:
        return "UNKNOWN"

def generate_csv(processed_data, fieldnames):
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w+', newline='', encoding='utf-8')
    writer = csv.DictWriter(temp_file, fieldnames=fieldnames)

    # Write the header
    writer.writeheader()

    # Write the rows
    for row in processed_data:
        writer.writerow(row)

    # The temporary file is not closed so that the caller can continue using it
    return temp_file



@receiver(post_save, sender=ReceiptFile)
def convert_pdf_to_csv(sender, instance, created, **kwargs):
    file_type = check_file_type(instance.file.path)
    if created:
        if file_type == "PDF":
            import tempfile
            import re, csv
            tabula.convert_into(instance.file, instance.file.name, output_format="csv", pages=1)
            data = open(instance.file.name, 'r').read()
            
            def parse_row(row):
                product_name_pattern = r".+?(?=\d{8})"
                code_pattern = r"\d{8}"
                cat_pattern = r"(DN|DS)([A-Z0-9]+)"
                batch_pattern = r"([A-Z0-9]+)(?=[A-Z-]+\d{2}\.\d{4})"
                mfg_name_pattern = r"(?:DN|DS)[A-Za-z0-9]{9}([A-Za-z\s]+)\b"
                date_pattern = r"\d{2}\.\d{4}"
                numeric_pattern = r"(?!\d{2}\.\d{4})\d+\.\d{2}|\d+,\d+\.\d{2}|-?\d+\.\d{2}"
                print(row, "rows")
                # Extracting data
                product_name = re.search(product_name_pattern, row)
                code = re.search(code_pattern, row)
                cat = re.search(cat_pattern, row)
                print(cat, cat.group() if cat else None, "cat")
                batch = re.search(batch_pattern, row)
                print(batch, batch.group() if batch else None, "batch")
                mfg_name = re.search(mfg_name_pattern, row)
                print(mfg_name, mfg_name.group() if mfg_name else None, "mfg_name")
                dates = re.findall(date_pattern, row)
                print(dates, "dates")
                numerics = re.findall(numeric_pattern, row)
                sub_mfg_name = re.search(mfg_name_pattern, batch.group()) if batch else None
                print(sub_mfg_name, "sub_mfg_name")
                print(numerics, "numerics")
                print(cat.group() if cat else None, "cat.group()[2:8]")
                print(mfg_name.group() if mfg_name else None, "mfg_name.group()")
                print(numerics[5] if numerics else None, "numerics[5]")
                PTR = numerics[5] if numerics else None
                print(PTR, "PTR")
                # Constructing result
                result = {
                    "Plant": None,
                    "Order Type": None,
                    "Price grp": "",
                    "Customer": "",
                    "Customer Name": "",
                    "City/Destination":"",
                    "Invoice No":"",
                    "Invoice Date":"",
                    "Product Name": product_name.group() if product_name else None,
                    "HSN/SAC Code": code.group() if code else None,
                    "CAT": cat.group()[:2] if cat else None,
                    "BATCH": cat.group()[2:8] if cat else None,
                    "MFG.NAME": mfg_name.group()[9:] if mfg_name else sub_mfg_name.group()[9:17] if sub_mfg_name else None,
                    "MFG.DT": dates[0] if dates else None,
                    "EXP.DT": dates[1] if dates else None,
                    "GST Rate (%)": numerics[2][2:] if numerics else None,
                    "BILLED QTY": f"{numerics[3]} {numerics[4][:2]}"  if numerics else None,
                    "FREE QTY": 0,
                    "MRP": numerics[4] if numerics else None,
                    "PTR": PTR if PTR else None,
                    "Rate": numerics[6] if numerics else None,
                    "DISC%": numerics[7] if numerics else None,
                    "Invoice Amount": numerics[8] if numerics else None,
                    "Net Value": numerics[8] if numerics else None,
                    "Plant Name": "",
                    "Dist. channel" :"",
                    "Customer State": "",
                    "Customer p0 Number": "Nil",
                    "PO date": "",
                    "System Order No.": "",
                    "Order Date": "",
                    "Product type": "ZFGS",
                    "Local Sales Tax NO.": "",
                    "Central Sales Tax NO.":"",
                    "Material Group 3": "",
                    "Division":"",
                    "Mfg. Plant": "",	
                    "Mfg. Date": "",	
                    "Exp. Date": "",	
                    "Free Quantity": "",	
                    "Disc.": "",	
                    "Cash Disc.": "",	
                    "Tax Type": "",	
                    "Tax %": "",	
                    "Tax Amt.": "",	
                    "Add. Tax": "",	
                    "Surcharge": "",	
                    "Total Tax": "",	
                    "LBT	Ref.": "", "Invoice No.(Returns)": "",	
                    "Ref. Inv. Dt.": "",	
                    "Exc. Inv. No.": "",	
                    "Exc. Inv. Dt.": "",	
                    "Exc. Duty %": "",	
                    "Exc. Inv. Amt": "",	
                    "Product Status": "",	
                    "Reason For Return": "",	
                    "Reason For Rejection": "",	
                    "Str. Loc.": "",	
                    "Sales District": "",	
                    "Sales Group": "",	
                    "Customer Group": "",	
                    "Emp. Code": "",	
                    "Employee Name": "",	
                    "C Form No.": "",	
                    "HSN Code": "",	
                    "Business Place": "",	
                    "JOCG": "",	
                    "JOSG": "",	
                    "JOIG": "",	
                    "JOUG": "",	
                    "PTR_01": "",	
                    "PTS": "",	
                    "Disc. %": "",	
                    "Prod. Category": "",	
                    "Prod. Category Description": "",	
                    "GSTIN No. of Customer": "",	
                    "GST Inv. No.": "",   
                }
                return result
            # Extracting the product data section
            product_data_section = re.search(r'PRODUCT NAME,[^*]*', data, re.DOTALL)
            if product_data_section:
                product_lines = product_data_section.group().split('\n')[1:]  # Skip the header line

            # Process each product line and store in a list
            processed_data = [parse_row(line) for line in product_lines if parse_row(line)]
            csv_file_name = 'processed_data1.csv'

            # Define the field names (columns) based on the keys of the first dictionary in the list
            fieldnames = processed_data[0].keys() if processed_data else []
            # Writing to CSV
            with tempfile.NamedTemporaryFile(delete=False, mode='w+', newline='', encoding='utf-8') as temp_file:
                writer = csv.DictWriter(temp_file, fieldnames=fieldnames)

                # Write the header
                writer.writeheader()

                # Write the rows
                for row in processed_data:
                    writer.writerow(row)

            try:
                with open(temp_file.name, 'rb') as csv_file:
                    from django.core.files import File

                    # Save the CSV file to the converted_csv field
                    instance.converted_csv.save(f'{instance.file.name}.csv', File(csv_file), save=True)
                    instance.status = "Successfully converted"
                    instance.save()
            except Exception as e:
                print(e)
                
        
        elif file_type == "IMAGE":
            import ssl
            from urllib.request import urlopen

            ssl._create_default_https_context = ssl._create_unverified_context

            API_KEY = 'cKwrEpae4Xru7gMG1LKqmNTQmBuAgAstKFd0J1L5'
            EXTRACT_TABLE_URL = "https://trigger.extracttable.com"
            import requests, os
            
            def upload(path):
                import requests

                url = "https://trigger.extracttable.com"

                payload = {}
                files=[
                ('input',('WhatsApp Image 2023-12-29 at 12.03.33 (1).jpeg',open(path,'rb'),'image/jpeg'))
                ]
                headers = {
                'x-api-key': 'D9T9obWxL72YJt2AeHO2MRXppZzTAk6Y1UujFaOP'
                }

                response = requests.request("POST", url, headers=headers, data=payload, files=files)

                print(response.text)
                return response
            res = upload(instance.file.path)
            # print(res.json(), ".DS_Store")
            import tempfile, csv
            response = res.json()
            if(response['JobStatus'] == "Success"):
                # instance.status = "Success"
                # Function to flatten the nested JSON table structure
                def flatten_table(table_json):
                    flat_table = []
                    for row_key, row_data in table_json.items():
                        flat_row = [row_key] + [str(value) for value in row_data.values()]
                        flat_table.append(flat_row)
                    return flat_table

                # Create a temporary file
                with tempfile.NamedTemporaryFile(mode='w+', delete=False, newline='') as temp_file:
                    temp_file_path = temp_file.name

                    # Write CSV file
                    writer = csv.writer(temp_file)
                    for table_entry in response['Tables']:
                        table_json = table_entry['TableJson']
                        flat_table = flatten_table(table_json)

                        # Write table data
                        writer.writerows(flat_table)   
            
            
                # def convert_table_to_csv(table_entry):
                #     import tempfile, csv
                #     # Extract table information from the JSON data
                #     table_number = table_entry.get("Page", 0)  # You can adjust this based on your data
                #     table_json = table_entry.get("TableJson", {})
                    
                #     # Flatten the nested JSON structure into rows
                #     rows = []
                #     for row_key, row_data in table_json.items():
                #         row = [row_key] + [str(value) for value in row_data.values()]
                #         rows.append(row)

                #     # Create a temporary CSV file
                #     with tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', suffix='.csv') as temp_csv_file:
                #         csv_file_path = temp_csv_file.name
                #         writer = csv.writer(temp_csv_file)

                #         # Write table header
                #         writer.writerow(rows[0])

                #         # Write table data
                #         writer.writerows(rows[1:])

                #     print(f"CSV file for Table {table_number} has been created: {csv_file_path}")
                    
                #     # Return the path to the temporary CSV file
                #     return csv_file_path
                
                # converted_file_path = None
                # for i, table_entry in enumerate(response['Tables']):
                #     print(i, table_entry['TableJson'])
                #     if i==1:
                #         converted_file_path = convert_table_to_csv(table_entry)
                #         break

                try:
                    with open(temp_file_path, 'rb') as csv_file:
                        from django.core.files import File

                        # Save the CSV file to the converted_csv field
                        instance.converted_csv.save(f'{instance.file.name}.csv', File(csv_file), save=True)
                        instance.status = "Successfully converted"
                        instance.save()
                except Exception as e:
                    print(e)