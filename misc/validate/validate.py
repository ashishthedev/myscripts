import pandas as pd

GSTIN_COL = 0
INVOICENUMBER_COL = 1
INVOICEDATE_COL = 2
INVOICEVALUE_COL = 3
PLACEOFSUPPLY_COL = 4
REVRESECHARGE_COL = 5
INVOICETYPE_COL = 6
ECOMMERCEGSTIN_COL = 7
RATE_COL = 8
TAXABLE_VALUE_COL = 9
CESSAMOUNT_COL = 10

def ParseArguments():
  import argparse
  parser = argparse.ArgumentParser()

  parser.add_argument("-f", "--file",
      dest='filename', type=str, required=True,
      default="", help="The file to be analysed.")

  return parser.parse_args()

def main():
    args = ParseArguments()
    filename = args.filename

    if not filename:
        raise Exception("Filename not provided.")

    #Compare A5 to L5, B5 to M5, ... K5 to V5
    xl = pd.ExcelFile(filename)
    b2bsheet = xl.parse('b2b')
    
    STARTING_ROW = 3
    OFFSET = 11
    compareColumns = [
        (GSTIN_COL,          GSTIN_COL + OFFSET,          "GSTIN"), 
        (INVOICENUMBER_COL,  INVOICENUMBER_COL + OFFSET,  "InvoiceNumber"),
        (INVOICEDATE_COL,    INVOICEDATE_COL + OFFSET,    "InvoiceDate"),
        (INVOICEVALUE_COL,   INVOICEVALUE_COL + OFFSET,   "InvoiceValue"),
        (PLACEOFSUPPLY_COL,  PLACEOFSUPPLY_COL + OFFSET,  "PlaceofSupply"), 
        (REVRESECHARGE_COL,  REVRESECHARGE_COL + OFFSET,  "ReverseCharge"),
        (INVOICETYPE_COL,    INVOICETYPE_COL + OFFSET,    "InvoiceType"),
        (ECOMMERCEGSTIN_COL, ECOMMERCEGSTIN_COL + OFFSET, "E-CommerceGSTIN"),
        (RATE_COL,           RATE_COL + OFFSET,           "Rate"), 
        (TAXABLE_VALUE_COL,  TAXABLE_VALUE_COL + OFFSET,  "TaxableValue"), 
        (CESSAMOUNT_COL,     CESSAMOUNT_COL + OFFSET,     "CessAmount"),
        ]


    diff = 0

    for r in b2bsheet.values[STARTING_ROW:]:

        for s, d, intent in compareColumns:
            sv = str(r[s])
            dv = str(r[d])

            if intent == "PlaceofSupply":
                if sv[:2] != dv[:2]:
                    diff += 1; print("{}. Difference in inv#{} {} : {} != {}".format(diff, r[1], intent, sv[:2], dv[:2]), s, d); 
                continue

            if intent == "InvoiceNumber":
                if int(sv) != int(dv):
                    diff += 1; print("{}. Difference in inv#{} {} : {} != {}".format(diff, r[1], intent, sv, dv, s, d)); 
                continue

            if intent == "Rate":
                if float(sv) != float(dv):
                    diff += 1; print("{}. Difference in inv#{} {} : {} != {}".format(diff, r[1], intent, sv, dv,s, d)); 
                continue

            if str(sv) != str(dv):
                diff += 1; print("{}. Difference in inv#{} {} : {} != {}".format(diff, r[1], intent, sv, dv, s, d)); 
    invoiceValue_b2b = 0
    for r in b2bsheet.values[STARTING_ROW:]:
        invoiceValue_b2b += r[INVOICEVALUE_COL]

    #HSN SHEET
    HSN_INVOICE_VALUE_COL = 4
    invoiceValue_hsn = 0
    hsnsheet = xl.parse('hsn')
    for r in hsnsheet.values[STARTING_ROW:]:
    	invoiceValue_hsn += r[HSN_INVOICE_VALUE_COL]

    if invoiceValue_b2b != invoiceValue_hsn:
        diff += 1; print("{}. Difference in b2b invoice value total={} and HSN sheet's invoice value total: {} ".format(diff, invoiceValue_b2b, invoiceValue_hsn)); 
    else:
    	print("invoiceValue_b2b = invoiceValue_hsn = {}".format(invoiceValue_hsn))

    	
    if not diff:
        print("Perfect")


if __name__ == '__main__':
    main()
