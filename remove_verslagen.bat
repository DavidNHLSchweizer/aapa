@echo --verslag=569>killer.txt
@echo --verslag=570>>killer.txt
@echo --verslag=568>>killer.txt
@echo --verslag=96>>killer.txt
py run_plugin.py plugins.remove_verslag -stop --onedrive=d:\onedrive --database=testing123.db @killer.txt -unlink -debug %1 %2 %3 %4 %5 %6
