#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
#Warn  ; Recommended for catching common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.
#SingleInstance force  ; Forces the script to reload on further execution
; Usage
; Windows = #
; Alt = !
; Ctrl = ^
; Shift = +

;TODO: Hardcoding appdir is a hack. Find an elegant solution
ENVGET, WINDIR_ENV, WINDIR
ENVGET, APPDIR_ENV, APPDIR
IF APPDIR_ENV =
 {
    APPDIR_ENV:="c:\users\ichigo\dropbox\SDATDocs"
 }
ENVGET, PROGRAMFILES_ENV, PROGRAMFILES
GVIM = %WINDIR_ENV%\gvim.bat

::sdatdesc::Standard Dies And Tools manufactures wire drawing dies. Our product range includes wire drawing dies for MIG wire, MS wire, HC Wire, LC wire, flux coating TC dies, diamond dies, diamond powder, diamond paste.
::btw::by the way
::;br::;<br> 
::f501::501, Old Arya Nagar, Ghaziabad, UP
::fkil::Kennametal India Limited
::fkmil::Kennametal India Limited
::fkma::8/9th mile, Tumkur Road, Bangalore - 560073
::fkms::Bangalore
::fkmt::29790058796
::fkm1::Blue Dart
::fkm2::
::fkm3::HR55R6142
::fkm4::Satyajeet
::fkm5::9475
::faeh::Ahuja Exim House
::faea::2, Vasanat Vihar Enclave, Midford House, Dehradun PIN-248006(UA)
::faet::05005934970
::faes::Uttaranchal
::fnki::New Kanwal Industries
::fnka::Sector 5, Pocket NO. E356, Bawana Industrial Area, Delhi-39
::fnkt::07250250255
::fnks::Delhi
::fkvc::KVC Enterprises
::fkvca::F-163, Sector 1, Bawana Industrial Area, New Delhi
::fkvct::07600328972
::fkvcs::New Delhi


::pansdat::ABTPA7224J

::bodat::Omega Dies And Tools{enter}ICICI Ac No: 125605500120{enter}RTGS/NEFT Code: ICIC0001256{enter}Branch: Plot No-270, Ambedkar Road, Choudhary More, Ghaziabad
::bsdat::HDFC A/c No: 05732560000238{enter}RTGS No: HDFC0000573{enter}Branch: 35 Ambedkar Road, Gandhinagar, Ghaziabad.

::b178::ICICI A/c No: 125605500178{enter}Name: Vishal Anand{enter}Branch: Razzapur, Ghaziabad.{enter}IFSC Code: ICIC0001256
::buco::UCO A/c No: 08500100002243{enter}Name: Ashok Anand{enter}Branch: Rakesh Marg, Ghaziabad.


::sdatinfo::Standard Dies And Tools{enter}501, Old Arya Nagar, Ghaziabad.{enter}TIN No: 09990700496{enter}anand.dies@gmail.com{enter}HDFC Ac No: 05732560000238{enter}RTGS/NEFT Code: HDFC0000573{enter}Branch: 35 Ambedkar Road, Gandhinagar, Ghaziabad.
::odatinfo::Omega Dies And Tools{enter}KH-178, Kavinagar, Ghaziabad.{enter}TIN No: 09388823011C{enter}omegadiesandtools@gmail.com{enter}ICICI Ac No: 125605500120{enter}RTGS/NEFT Code: ICIC0001256

;______________________________
;Omega official bank ID - ICICI
;ICICI corp account
::id120::521679990
;______________________________

;______________________________
;ICICI Normal Account - closed
::id1830::520340490
;______________________________
;ICICI Corp Acc
::id178::521680106
;______________________________


;______________________________
;Windows Only Shortcut
;______________________________

StartMailServer()
{
    global APPDIR_ENV
    ;Run "b:\\python27\\python.exe" %APPDIR_ENV%\myscripts\misc\SMTPDebugginsServer.py
    ;Run %APPDIR_ENV%\myscripts\misc\SMTPDebugginsServer.py
    cmd = %ComSpec% /k %APPDIR_ENV%\myscripts\misc\SMTPDebugginsServer.py
    Run %cmd%
    return
}

RunAppserverForPath(path)
{
    global PROGRAMFILES_ENV
    skip = ""
    skip = --skip_sdk_update_check True
    clearDS = --clear_datastore True
    mailSettings = --enable_sendmail
    mailSettings = --smtp_host=localhost --smtp_port=8025
    DEV_APPSERVER = "%PROGRAMFILES_ENV%\Google\google_appengine\dev_appserver.py"
    cmd = %ComSpec% /k %DEV_APPSERVER% %mailSettings% %clearDS% %skip% %path%
    ;MsgBox %cmd%
    run %cmd%
    return
}
#F1::
{
    path = %APPDIR_ENV%\..\website
    RunAppserverForPath(path)
    return
}

#!C::
{
    filePath = %APPDIR_ENV%\Bills\Cust.xlsx
    OpenExistingFileIfPossible("Microsoft Excel - Cust.xlsx", filePath)
    return
}

#!P::
{
    path = %APPDIR_ENV%\..\phungsuk_jibabo\detect_change_app
    RunAppserverForPath(path)
    return
}

#!s::
{
    StartMailServer()


    path = %APPDIR_ENV%\..\phungsuk_jibabo\detect_change_app
    RunAppserverForPath(path)


    Run %ComSpec% /k b:\bottleServer\scripts\activate.bat && python b:\bottleServer\app\todo5656.py
    Run %ComSpec% /k b:\bottleServer\scripts\activate.bat && python b:\bottleServer\app\todo5454.py
    ;Run %GVIM% b:\bottleServer\app\todo5656.py


    Run "C:\Program Files\Google\Chrome\Application\chrome.exe"  --app=http://localhost:8080/
    return
}

#w:: Run %GVIM% b:\bottleServer\app\todo5656.py

#u:: Run "B:\Tools\VirtualBoxPortable4.2.12-84980\VirtualBoxPortable.exe"
; Windows k for bills.xlsx
OpenExistingFileIfPossible(windowDispName, filePath)
{
  IfWinExist, %windowDispName%
  {
    WinActivate, %windowDispName%, , , ;
    WinMaximize, %windowDispName%, , , ;
  }
  else
  {
    global PROGRAMFILES_ENV
    ;Run %PROGRAMFILES_ENV%\Microsoft Office\Office12\EXCEL.EXE %filePath%
    Run explorer %filePath%
  }
  return
}

#o::
{
    filePath = %APPDIR_ENV%\..\ODATDocs\Bills\OdatBills.xlsx
    OpenExistingFileIfPossible("Microsoft Excel - ODATBills.xlsx", filePath)
    return
}
#k::
{
    filePath = %APPDIR_ENV%\Bills\Bills.xlsx
    OpenExistingFileIfPossible("Microsoft Excel - Bills.xlsx", filePath)
    return
}

#!d::
{
    filePath = %APPDIR_ENV%\..\personal\misc\DataMining.xlsx
    OpenExistingFileIfPossible("Microsoft Excel - DataMining.xlsx", filePath)
    return
}


; Windows Y for youtube download
#Y:: Run %APPDIR_ENV%\Myscripts\misc\ydl.py

;Windows Aly Y for rate limited youtube downloads
#!Y:: Run %APPDIR_ENV%\Myscripts\misc\ydl.py -r30k

; Windows g for gvim
#g:: Run %GVIM%

; Windows a for actions
#a:: Run %GVIM% %APPDIR_ENV%\FrequentFliers\actions.txt

; Start Tor Browser

#q::
{
PrivDir:= "B:\Tools\Tor\PrivoxyInstalled"
PrivExe = %PrivDir%\privoxy.exe
Run %PrivExe% %PrivDir%"\config.txt

TorDir:="b:\tools\Tor\"

SetWorkingDir, %TorDir%\App\
Vidalia = %TorDir%\App\Vidalia.exe
Run %Vidalia%

Run %TorDir%\TorChrome.exe.lnk

return
}
#t::
{
TorDir:="b:\tools\TorL\"
SetWorkingDir, %TorDir%
Run %TorDir%\Start Tor Browser.exe
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.
return
}

;______________________________
;Ctrl Alt Shortcuts
;______________________________

; Windows Alt R for Reloading this script again
#!r:: Reload

;______________________________
;Windows Alt Shortcuts
;______________________________

; Windows Alt B for Bank reconciliation
#!b::
{
  filePath = %APPDIR_ENV%\FrequentFliers\BankReconcilation.xlsx
  OpenExistingFileIfPossible("Microsoft Excel - BankReconcilation.xlsx", filePath)
  return
}

; Windows alt o for explorer
#!o:: Run explorer %APPDIR_ENV%

; Windows alt f for template of form 38
#!f:: Run %PROGRAMFILES_ENV%\Microsoft Office\Office12\EXCEL.EXE %APPDIR_ENV%\Form38Actual\Receipt\Template-Form38.xlsx

; Windows alt e for eretinfo.txt
#!e:: Run %GVIM% %APPDIR_ENV%\SalesTaxReturnFiles\ereturnInfo.txt

; Windows alt i for info.txt
#!i:: Run %GVIM% %APPDIR_ENV%\FrequentFliers\Info.txt



; Windows h for copy paste through clipboard while preparing sales tax
#h::
{
    clipboard = ;Empty the clipboard
        Send ^+{Down} ; Slect the entire column. Make sure the cursor is on the first row.
        Sleep, 250
        Send ^c ; copy whats selected
        Sleep, 250
        ;Clipwait ; Wait for clipboard to contain text.
        Run Notepad
        Sleep, 250
        Send ^v
        ;Clipwait ; Wait for clipboard to contain text.
        Sleep, 250
        Send ^a
        Sleep, 250
        Send ^c
        Sleep, 250
        IfWinExist, Untitled - Notepad
        WinClose ; use the window found above
        Sleep, 250
        Send n
        Sleep, 250
        Send !{tab}
        Sleep, 250
        ;Clipwait ; Wait for clipboard to contain text.
        return
}
