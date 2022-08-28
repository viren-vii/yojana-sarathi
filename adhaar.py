# from PIL import Image
# from pyzbar.pyzbar import decode
import xmltodict
import json
# # data = decode(Image.open('./uploads/adhaarTest.jpeg'))


# def getQrData(path_to_qr='./uploads/919423587762/6.jpg'):
#     data = decode(Image.open(path_to_qr))
#     print(data)
#     # data = xmltodict.parse(data[0].data.decode())['PrintLetterBarcodeData']
#     return data


# getQrData()

import cv2
from pyzbar.pyzbar import decode
from pyaadhaar.utils import isSecureQr
from pyaadhaar.decode import AadhaarSecureQr
from datetime import date
# testAdhaarSakshi.jpg
# 6


def getAdhaarData(path_to_img='./uploads/919423587762/sakshiTest.jpg'):
    img = cv2.imread(path_to_img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    code = decode(gray)
    # print(code)
    if len(code):
        print(len(code))
        qrData = code[0].data
    else:
        print("JUGAD")
        return None

    isSecureQR = (isSecureQr(qrData))
    if isSecureQR:
        secure_qr = AadhaarSecureQr(int(qrData))
        QRDATA = secure_qr.decodeddata()
        # return decoded_secure_qr_data
    else:
        QRDATA = xmltodict.parse(qrData.decode())['PrintLetterBarcodeData']

    ret = {}
    year = date.today().year

    for k in QRDATA.keys():
        if 'name' in k:
            ret['name'] = QRDATA[k]
        elif 'dob' in k:
            ret['age'] = year - int(QRDATA[k].split('-')[2])
        elif 'yob' in k:
            ret['age'] = year - int(QRDATA[k])
        elif 'gender' in k:
            ret['gender'] = QRDATA[k]
        elif 'pc' in k or 'pincode' in k:
            ret['pincode'] = QRDATA[k]
        elif 'state' in k:
            ret['state'] = QRDATA[k].lower()

    print(ret)
    return ret


# print(getAdhaarData())

"""
{
    'email_mobile_status': '3', 
    'referenceid': '738320220321221610588', 
    'name': 'Sakshi Nitin Kulkarni', 
    'dob': '19-06-2001', 
    'gender': 'F', 
    'careof': 'D/O: Nitin Kulkarni', 
    'district': 'Aurangabad', 
    'landmark': 'Near Nutan kanya Vidyalay,', 
    'house': 'H.No. 5-9-104/2 Ramai,', 
    'location': 'Raj Nagar Pagaria Colony,', 
    'pincode': '431005', 
    'postoffice': 'Kranti Chowk', 
    'state': 'Maharashtra', 
    'street': 'Station Road,', 
    'subdistrict': 'Aurangabad', 
    'vtc': 'Aurangabad', 
    'adhaar_last_4_digit': '7383', 
    'adhaar_last_digit': '3', 
    'email': 'yes', 
    'mobile': 'yes'
}

{
    '@uid': '754698818034', 
    '@name': 'Viren Rahul Bhosale', 
    '@gender': 'M', 
    '@yob': '2001', 
    '@house': 'Flat No-2, Building- D, Nyayadhish Niwas', 
    '@street': 'Alpabachat Bhavan Road', 
    '@lm': 'Near Council Hall', 
    '@loc': 'Camp', 
    '@vtc': 'Pune City',
    '@po': 'Pune', 
    '@dist': 'Pune', 
    '@subdist': 'Pune City', 
    '@state': 'Maharashtra',
    '@pc': '411001'
}
"""
