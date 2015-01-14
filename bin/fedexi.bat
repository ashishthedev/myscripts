::For Easy accessibility of professional website
IF "%1". EQU "".  (

start /w "C:\Users\Ichigo\AppData\Local\Google\Chrome\Application\chrome.exe" "https://www.fedex.com/fedextrack/WTRK/index.html?action=track&action=track&cntry_code=in&lid=/Track/Track_Number&fdx=1490"
) ELSE (
start /w "C:\Users\Ichigo\AppData\Local\Google\Chrome\Application\chrome.exe" "https://www.fedex.com/fedextrack/WTRK/index.html?action=track&tracknumbers=%1&locale=en_IN&cntry_code=in"
)
