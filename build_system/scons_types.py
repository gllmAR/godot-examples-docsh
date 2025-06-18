"""
Type stubs for SCons functions used in SConstruct files.
This helps IDEs understand SCons-specific functions.
"""

from typing import Any, Dict, List, Optional, Union

def AddOption(dest: str, type: str = "string", nargs: int = 1, 
              action: str = "store", metavar: str = "", default: Any = None,
              help: str = "") -> None: ...

def GetOption(name: str) -> Any: ...

def SetOption(name: str, value: Any) -> None: ...

def Environment(**kwargs: Any) -> Any: ...

def CacheDir(dir: str) -> None: ...

def Default(*targets: Any) -> None: ...

def Exit(value: int = 0) -> None: ...

def Mkdir(dir: str) -> Any: ...

# Global variables available in SCons
ARGUMENTS: Dict[str, str]
