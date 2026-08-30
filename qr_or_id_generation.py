from turtle import fillcolor

import qrcode
import os

prefix = 'AAK'

def code_string(prefix,number):
    return f"{prefix}{number:03d}"

def create_qr(data_string):
    try:

        output_folder = "qr_codes"

        os.makedirs(output_folder,exist_ok=True)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(data_string)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black",back_color="white")

        filename = os.path.join(output_folder,f"{data_string}.png")
        img.save(filename)
        print(f"qr code is generated: {data_string} for {filename}")

    except Exception as e:
        print(f"error is occured {e}")
        return False

def student_id_generation(prefix,start_num):
    try:
        unique_code = code_string(prefix,start_num)
        create_qr(unique_code)
    except Exception as e:
        print(f"error is occured {e}")
    return unique_code