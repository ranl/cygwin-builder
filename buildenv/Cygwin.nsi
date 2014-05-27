!define PRODUCT_NAME "MyCygwin"
!define PRODUCT_VERSION "TMPL_MyCygwinVersion"

CRCCheck On 
Name "${PRODUCT_NAME}"
OutFile "MyCygwin-${PRODUCT_VERSION}.exe"
ShowInstDetails "nevershow"
ShowUninstDetails "nevershow"
InstallDir "C:\${PRODUCT_NAME}"
LicenseData "license.txt"

!define MUI_WELCOMEPAGE  
!define MUI_LICENSEPAGE
!define MUI_DIRECTORYPAGE
!define MUI_ABORTWARNING
!define MUI_UNINSTALLER
!define MUI_UNCONFIRMPAGE
!define MUI_FINISHPAGE  

Section "install"

  ExecWait "net stop sshd"
  SetOutPath "$INSTDIR" 
  SetOverwrite try

  File "cygwin.zip"
  File /r "7z"
  File "mycygwin_post_install.sh"

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}" "DisplayIcon" "$INSTDIR\Cygwin.ico"

  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\bin\mintty.exe" "-i /Cygwin-Terminal.ico -" "$INSTDIR\Cygwin-Terminal.ico" 0 SW_SHOWNORMAL "" "MyCygwin"
  
  ExecWait "$INSTDIR\7z\7z.exe x -y cygwin.zip"
  ExecWait "$INSTDIR\bin\bash.exe -c /mycygwin_post_install.sh"
SectionEnd


Section "Uninstall"
  ExecWait "net stop sshd"
  ExecWait "$INSTDIR\bin\cygrunsrv.exe -R sshd"
  ExecWait "net user sshd /delete /y"
  ExecWait "net user cyg_server /delete /y"
  RMDir /r "$INSTDIR\*.*"    
  RMDir "$INSTDIR"
  DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\${PRODUCT_NAME}"
  DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
SectionEnd


Function .onInstSuccess
  ;post install script
FunctionEnd


Function un.onUninstSuccess
  ;post uninstall script
FunctionEnd
 
