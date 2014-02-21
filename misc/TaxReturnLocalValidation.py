import xml.dom.minidom, os, unittest
from UtilConfig import GetAppDir
FOLDER_NAME             = "2014-01"
BASEPATH                = os.path.join(GetAppDir(), "SalesTaxReturnFiles", "2013-2014")
ANNEXUREA               = os.path.join(BASEPATH, FOLDER_NAME, "UPVAT", "XML", "Form24AnnexureA.xml")
ANNEXUREB               = os.path.join(BASEPATH, FOLDER_NAME, "UPVAT", "XML", "Form24AnnexureB.xml")
ANNEXUREC               = os.path.join(BASEPATH, FOLDER_NAME, "UPVAT", "XML", "Form24AnnxC.xml")
UPVAT_TAX_DETAIL_SALE   = os.path.join(BASEPATH, FOLDER_NAME, "UPVAT", "XML", "Form24TaxDetailS.xml")
UPVAT_MAINFORM_FILE     = os.path.join(BASEPATH, FOLDER_NAME, "UPVAT", "XML", "Form24MainForm.xml")
UPVAT_BANKDETAIL_FILE   = os.path.join(BASEPATH, FOLDER_NAME, "UPVAT", "XML", "Form24BankDetail.xml")
UPVAT_VAT_NONVAT_FILE   = os.path.join(BASEPATH, FOLDER_NAME, "UPVAT", "XML", "Form24VatNonVat.xml")
CST_MAIN_FORM           = os.path.join(BASEPATH, FOLDER_NAME, "CST",   "XML", "FormCSTMainForm.xml")
CST_TAX_PAID_FORM       = os.path.join(BASEPATH, FOLDER_NAME, "CST",   "XML", "FormCSTTaxPaid.xml")
CST_TURNOVER_FORM       = os.path.join(BASEPATH, FOLDER_NAME, "CST",   "XML", "FormCSTTurnover.xml")
CST_LOISS_FORM          = os.path.join(BASEPATH, FOLDER_NAME, "CST",   "XML", "FormCST_ListofInterstateSales.xml")

PREVALING_VAT_RATE='14'  # in percent
PREVALING_CST_RATE='2'   # in percent
PREVALING_EXPORT_RATE='0'   # in percent
TOLERANCE_IN_RUPEES=1

def SumFloat(fileName, nodeName):
    return sum([float(getText(eachNode.childNodes)) for eachNode in GetAllNodesByNameFromFile(fileName, nodeName)])

def GetAllNodesByNameFromFile(filePath, tagName):
    """
    This helper function will return all the elements in a file with a specific tag.
    """
    dom = xml.dom.minidom.parse(filePath)
    elements = dom.getElementsByTagName(tagName)
    assert (len(elements)> 0), "<" + tagName + "> does not exist in " + filePath
    return elements

def GetCentralSaleByRate(taxRate):
    """
    This function returns the sale amount for a given tax rate from CST Turnover sheet
    """
    recordList = GetAllNodesByNameFromFile(CST_TURNOVER_FORM, "Record")
    for node in recordList:
        taxR= getText(node.getElementsByTagName("tax_rate")[0].childNodes)
        if(taxR == taxRate):
            sale_amount = getText(node.getElementsByTagName("sale_amount")[0].childNodes)
            return float(sale_amount)

    return 0 # If we didn't sell anything at that rate, then sale is 0

def getAmountFromVatNonVatSheet(code, vatNonVat, salePurchase):
    """
    Returns a specific cell value from Vat Non Vat Sheet
    """
    recordList = GetAllNodesByNameFromFile(UPVAT_VAT_NONVAT_FILE, "Record")
    for node in recordList:
        codeValue = getText(node.getElementsByTagName("code")[0].childNodes)
        vatNonVatValue = getText(node.getElementsByTagName("vat_nonvat")[0].childNodes)
        typeValue = getText(node.getElementsByTagName("type")[0].childNodes)
        amountValue = getText(node.getElementsByTagName("amount")[0].childNodes)

        if((code == codeValue)
                and (vatNonVat == vatNonVatValue)
                and (salePurchase == typeValue)):
            return float(amountValue)
    assert("If you have reached here, the combination of code/vatNonVat/salePurchase does not exist. Look carefully in Excel sheet")
    return None

def getFloatValueFromXmlFile(xmlFileName, fieldName):
    value = float(getText(GetAllNodesByNameFromFile(xmlFileName, fieldName)[0].childNodes))
    return value

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def TestSameness(testCaseInstance, fileName_ValueToLookFor_Dict):
    """
    fileName_ValueToLookFor_Dict is a dictonary having following properties
    key: filename of the xml in which to search for
    value: The name of single node. The node may be repeated multiple times in that file. All the values will be checked for sameness
    """
    values = list()
    for fileName, valuesToLookFor in fileName_ValueToLookFor_Dict.items():
        for n in GetAllNodesByNameFromFile(fileName, valuesToLookFor):
            values.append(getText(n.childNodes))

    for x in values:
        if x != values[0]: print("These are not equal: {}".format(values))
        testCaseInstance.assertEqual(values[0], x)


class TestFunctions(unittest.TestCase):

    def test_UPVATInputTaxCrossCheck(self):
        #This test asserts that the sum value as defined in Annexure A is equal to the value defined in MainForm
        #TODO: What if Annexure A is not present? Check for file presence maybe?
        UPVATInputInMainForm = getFloatValueFromXmlFile(UPVAT_MAINFORM_FILE, "P_OwnAc")
        if UPVATInputInMainForm == 0:
            return

        totalInputTaxAnnxA = SumFloat(ANNEXUREA, "TaxCharged") + SumFloat(ANNEXUREA, "SatCharged")

        self.assertTrue(abs(totalInputTaxAnnxA-UPVATInputInMainForm)<TOLERANCE_IN_RUPEES,
                "Total UPVAT Input is different in UPVATMainForm and Annexure A")
        return

    def test_AllMonths(self):
        """
        This test will check whether all months are consistent among themselves.
        TODO: Use AI to detect if the consistent months are themselves correct.
        """
        TestSameness( self,
                {
                CST_MAIN_FORM:"month1",
                CST_TAX_PAID_FORM: "month1",
                CST_TURNOVER_FORM: "Month",
                CST_LOISS_FORM: "Month",
                ANNEXUREA: "Month",
                ANNEXUREB: "Month",
                ANNEXUREC: "Month",
                UPVAT_BANKDETAIL_FILE: "month1",
                UPVAT_MAINFORM_FILE: "month1",
                UPVAT_VAT_NONVAT_FILE: "month1",
                UPVAT_TAX_DETAIL_SALE: "Month",
                })
        return
    def test_AnnexureBChecks(self):
        """
        Tests whether ANNEXUREB values(summation) is properly cross referenced in various places
        """
        totalOutputTaxAnnxB = SumFloat(ANNEXUREB, "TaxCharged") + SumFloat(ANNEXUREB, "SatCharged")

        self.assertEqual(
                totalOutputTaxAnnxB,
                getFloatValueFromXmlFile(UPVAT_MAINFORM_FILE, "totaltax"),
                "Payble UP VAT Tax is not same in UPVAT Main Form and ANNEXUREB")

        self.assertEqual(
                getFloatValueFromXmlFile(UPVAT_MAINFORM_FILE, "tot_tax_on_sale"),
                getFloatValueFromXmlFile(UPVAT_MAINFORM_FILE, "totaltax"),
                "Payble UP VAT Tax is not consistent in UPVAT Main Form")

        totalTaxableGoodsSoldinAnnexB = SumFloat(ANNEXUREB, "TaxGood")

        self.assertEqual(totalTaxableGoodsSoldinAnnexB, getAmountFromVatNonVatSheet('1', 'v', 's'), "UP Sale in Annexure B is different from UP Sale in Form24 VAT_NON_VAT sheet")
        self.assertEqual(totalTaxableGoodsSoldinAnnexB, getFloatValueFromXmlFile(UPVAT_TAX_DETAIL_SALE, "SaleAmount"), "UP Sale in Annexure B is different from UP Sale in Form24 Sale sheet.")
        self.assertEqual(getAmountFromVatNonVatSheet('1', 'v', 's'), getFloatValueFromXmlFile(UPVAT_TAX_DETAIL_SALE, "SaleAmount"), "UPSale in VAT_NON_VAT sheet is different from UP Sale in Annexure B")
        return

    def test_UPVAT_Same_MainForm_TaxPaidBankForm(self):
        #This test will check that upvat  amount is same on two pages or not
        self.assertEqual(
                getFloatValueFromXmlFile(UPVAT_MAINFORM_FILE, "net_tax"),
                getFloatValueFromXmlFile(UPVAT_BANKDETAIL_FILE, "tax_amount"))

        return

    def test_Check_Form38_Numbers_length(self):
        """
        This test will check if the number of digits in Form38 are 14 or not.
        """
        REQUIRED_LENGTH_OF_FORM38_NUMBERS = 14

        form38Numbers = GetAllNodesByNameFromFile(ANNEXUREC, "F_38No")
        for eachNumber in form38Numbers:
            number = getText(eachNumber.childNodes)
            self.assertEqual(len(number), REQUIRED_LENGTH_OF_FORM38_NUMBERS, "There is some problem in length of Form38 numbers")

        return
    def test_AnnexureA_Part1_Values(self):
        """
        Tests whether sum of purchase mentioned in Annexure A Part 1 matches the value mentioned in Vat_non_vat sheet
        """
        totalTaxableGoodsPurchased = SumFloat(ANNEXUREA, "TaxGood")

        self.assertEqual(getAmountFromVatNonVatSheet('1', 'v', 'p'), totalTaxableGoodsPurchased, "UP purchase in Annexure A Part 1 is different from UP Purchase in Vat-Non-Vat sheet in Form24")
        return

    def test_purchaseAgainstFORMC_crossCheck_in_VATNONVAT(self):
        """
        Tests whether sum of purchase mentioned in Annexure C matches the value mentioned in VAT_NON_VAT sheet
        """
        VNV_FormCPurchase = getAmountFromVatNonVatSheet('7a', 'os', 'p')
        totalPurchaseAgstFORMC = SumFloat(ANNEXUREC, "Tot_Inv")

        TOLERANCE_IN_RUPEES=1
        isDifferenceTolerable = (abs(VNV_FormCPurchase - totalPurchaseAgstFORMC)<TOLERANCE_IN_RUPEES)
        if not isDifferenceTolerable:
            print("\n_________________________________________________")
            print("FORMC Purchase in VNV is: " + str(VNV_FormCPurchase))
            print("FORMC purchase in Annexure C is: " + str(totalPurchaseAgstFORMC))
            print("The difference is greater than Rs."+str(TOLERANCE_IN_RUPEES))
            print("\n_________________________________________________")
            self.assertTrue(isDifferenceTolerable, "Centre purchase declared in Annexure C does not matches with value mentioned in Form24 VAT-NON-VAT sheet")
        return


    def test_CST_Tax_At_Various_Locations_in_FORM1(self):
        """
        This test will check for CST tax paid and payble consitency in FORM 1 at all the places it is mentioned.
        """
        totalCSTTax = SumFloat(CST_TURNOVER_FORM, "sale_tax_amount")

        itcAdjustment = getFloatValueFromXmlFile(CST_MAIN_FORM, "itc_adjustment")

        values = [
            totalCSTTax-itcAdjustment,
            getFloatValueFromXmlFile(CST_TAX_PAID_FORM, "amount"),
            getFloatValueFromXmlFile(CST_MAIN_FORM, "tax_payable"),
            abs(SumFloat(CST_LOISS_FORM, "AmmountOfTaxCharged")-itcAdjustment),
            ]

        for x in values:
            self.assertEqual(x, values[0])


    def test_NoErrorFilesArePresent(self):
        """
        Tests whether any errors reported by offline tools are still present at the time of filing the return.
        """
        dirPath1 = os.path.join(os.path.dirname(ANNEXUREA), "..", "Form24Errors")
        if os.path.exists(dirPath1):
            self.assertTrue(len(os.listdir(dirPath1)) == 0, "Form24Errors directory still has some error files. Are you sure you fixed them all?")
        dirPath2 = os.path.join(os.path.dirname(CST_MAIN_FORM), "..", "FormCSTErrors")
        if os.path.exists(dirPath2):
            self.assertTrue(len(os.listdir(dirPath2)) == 0, "FormCSTErrors directory still has some error files. Are you sure you fixed them all?")
        return


    def test_SameAssessmentYearEverywhere(self):
        TestSameness( self,
                {
                CST_MAIN_FORM:"assessment_year",
                CST_TAX_PAID_FORM: "assessment_year",
                CST_TURNOVER_FORM: "AssYear",
                CST_LOISS_FORM: "AssYear",
                ANNEXUREA: "AssYear",
                ANNEXUREB: "AssYear",
                ANNEXUREC: "AssYear",
                UPVAT_BANKDETAIL_FILE: "assessment_year",
                UPVAT_MAINFORM_FILE: "assessment_year",
                UPVAT_VAT_NONVAT_FILE: "assessment_year",
                UPVAT_TAX_DETAIL_SALE: "AssYear",
                })
        return

    def test_InterstateSale_CrossCheck_in_UPVAT_And_CST(self):
        """
        Tests whether interstate sale mentioned in VAT_NON_VAT_Sheet is same as in CST Sale Details sheet.
        """
        self.assertEqual(getAmountFromVatNonVatSheet('4', 'v', 's'), GetCentralSaleByRate(PREVALING_CST_RATE))
        self.assertEqual(getAmountFromVatNonVatSheet('5', 'v', 's'),
                GetCentralSaleByRate(PREVALING_VAT_RATE),
                "Central sale without FORM-C is different in VAT_NON_VAT_Sheet and CSTTurnOver sheet.\nIf this is some previous years report then this might be a false negative as VAT rate might have been different at that time.")

        cstAndVatAndExport = GetCentralSaleByRate(PREVALING_CST_RATE) + GetCentralSaleByRate(PREVALING_VAT_RATE) + GetCentralSaleByRate(PREVALING_EXPORT_RATE)
        l = [
            cstAndVatAndExport,
            getFloatValueFromXmlFile(CST_MAIN_FORM, "giss"),
            getFloatValueFromXmlFile(CST_MAIN_FORM, "net_inter_state_sale"),
            SumFloat(CST_LOISS_FORM, "SalesValueOfGoods"),
            ]
        for x in l:
          if x != l[0]:
            print("This values are different: {}".format(l))

        return

if __name__=="__main__":

    from datetime import datetime
    if(5 == datetime.today().month):
        raw_input("Have you made sure that you have changed fincial year while filing April's return")

    print("Folder Name = "+ FOLDER_NAME)
    absoluteFolder = os.path.join(BASEPATH, FOLDER_NAME)
    assert (os.path.exists(absoluteFolder)), "{}: No such path exists".format(absoluteFolder)
    raw_input("Press any key to continue...")

    suite = unittest.TestLoader().loadTestsFromTestCase(TestFunctions)
    unittest.TextTestRunner(verbosity=2).run(suite)
