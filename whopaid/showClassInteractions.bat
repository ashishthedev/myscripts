del *.png
del *.dot
pyreverse -f ALL -ASmy -p whopaid -o png AddressSlip.py CustomersInfo.py DepricatedWhoPaid.py  FormCRequest.py LatePayments.py MarkBillsAsPaid.py OutstandingPmtJsonDBGeneration.py PaymentReminderForGroups.py RoadPermitRequest.py SanityChecks.py Shipments.py Statement.py TotalCompanyList.py UtilWhoPaid.py WhoPaidInstantFindOut.py whopaidInstantDBGenerate.py
REM pyreverse -f ALL -ASmy -p whopaid -o png whopaid.py UtilWhoPaid.py CustomerTableConsistency.py EmailReminders.py FormCRequest.py LatePayments.py
classes_whopaid.png
