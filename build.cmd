REM pyinstaller ams.py --icon=ams.ico --noconfirm
copy d:\Python38\Scripts\AMS\ams.cfg d:\Python38\Scripts\AMS\dist\ams\ams.cfg 
mkdir d:\Python38\Scripts\AMS\dist\ams\images
copy d:\Python38\Scripts\AMS\images d:\Python38\Scripts\AMS\dist\ams\images 
mkdir d:\Python38\Scripts\AMS\dist\ams\html
copy d:\Python38\Scripts\AMS\html d:\Python38\Scripts\AMS\dist\ams\html
mkdir d:\Python38\Scripts\AMS\dist\ams\data
copy "d:\Python38\Scripts\AMS\data\ASSEMBLY Model.mdl" d:\Python38\Scripts\AMS\dist\ams\data
copy d:\Python38\Scripts\AMS\LICENSE d:\Python38\Scripts\AMS\dist\ams
d:\Program Files\7-Zip\7z.exe a -sfx d:\ams_dist\ams_inst.exe dist\* -r