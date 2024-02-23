@echo --verslag=581>killer.txt
@echo --verslag=582>>killer.txt
@echo --verslag=583>>killer.txt
@echo --verslag=584>>killer.txt
py run_plugin.py plugins.remove_verslag -stop --onedrive=d:\onedrive --database=testing123.db @killer.txt -unlink -debug %1 %2 %3 %4 %5 %6
