@rem set preview=-preview
@set preview=-preview
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 1" --migrate="data\migrate\m119" > detect.out
@copy logs\aapa_debug.log sherlock.log >NUL
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 1B" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2020-2021\Semester 2" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 1" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 2" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 3" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2021-2022\Periode 4" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 1" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 2" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 3" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2022-2023\Periode 4" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024 Oud" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
py aapa.py -debug %PREVIEW% --detect=":ONEDRIVE:\NHL Stenden\HBO-ICT Afstuderen - Software Engineering\2023-2024 Nieuw" --migrate="data\migrate\m119" >> detect.out
@copy sherlock.log+logs\aapa_debug.log sherlock.log>NUL
