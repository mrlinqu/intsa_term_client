pyinstaller --noconfirm^
    --onefile --noconsole ^
    --name="insta_term" ^
    --add-binary="nxproxy;nxproxy" ^
    --add-binary="vcxsrv;vcxsrv" ^
    --add-binary="gsview;gsview" ^
    --version-file="versionfile.txt" ^
    main.py

rem    --add-data="README;." ^
rem    --add-data="image1.png;img" ^
rem    
rem    --hidden-import=secret1 ^
rem    --hidden-import=secret2 ^
rem    --icon=..\MLNMFLCN.ICO ^