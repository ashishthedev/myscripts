::For Easy accessibility of trackon website
IF "%1". EQU "".  (
start /w "C:\Users\Ichigo\AppData\Local\Google\Chrome\Application\chrome.exe" "http://www.tpcindia.com/track-trace.aspx"
) ELSE (
start /w "C:\Users\Ichigo\AppData\Local\Google\Chrome\Application\chrome.exe" "http://www.tpcindia.com/trackone.aspx?id=%1%"
)
