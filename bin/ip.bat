::For Easy accessibility of professional website
IF "%1". EQU "".  (
start /w "C:\Users\Ichigo\AppData\Local\Google\Chrome\Application\chrome.exe" "http://addgadgets.com/ipaddress/"
) ELSE (
start /w "C:\Users\Ichigo\AppData\Local\Google\Chrome\Application\chrome.exe" "http://addgadgets.com/ipaddress/index.php?ipaddr=%1%"
)
