##
## Copyright (C) 2011 Aldebaran Robotics
##

clean(QXT_CORE)
fpath(QXT_CORE qxtcore.h PATH_SUFFIXES QxtCore qxt/QxtCore)
fpath(QXT_CORE QxtCore PATH_SUFFIXES qxt)
flib(QXT_CORE QxtCore)
export_lib(QXT_CORE)
qi_set_global(QXT_CORE_DEPENDS "QT_QTCORE")