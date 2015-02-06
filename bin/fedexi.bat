::For Easy accessibility of professional website
IF "%1". EQU "".  (

start /w "C:\Users\Ichigo\AppData\Local\Google\Chrome\Application\chrome.exe" "https://www.fedex.com/in"
) ELSE (
start /w "C:\Users\Ichigo\AppData\Local\Google\Chrome\Application\chrome.exe" "https://www.fedex.com/apps/fedextrack/?tracknumbers=%1&cntry_code=in" )
