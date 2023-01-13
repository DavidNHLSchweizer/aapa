@set starttime=%DATE% %TIME%
@echo Started: %starttime%

python -m nuitka --standalone --onefile --enable-plugin=tk-inter --enable-plugin=numpy --noinclude-unittest-mode=allow --windows-icon-from-ico=aapa_icon.ico aapa.py 
:: unittest-mode is nodig omdat dat gebruikt (?misbruikt) wordt in fpdf voor iets vaags met signing pdfs (wat ik dus niet doe) maar het kan er dus ook niet zomaar uit 

@set endtime=%DATE% %TIME%
@echo Ready: %endtime%
@python batchtimer.py "%starttime%" "%endtime%" "total build time: "

