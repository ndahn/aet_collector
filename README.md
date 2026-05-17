A small convenience tool for souls modding. Simply drag and drop one or more material (.matbin) files on it and it will collect the AETs referenced by that material in a folder *next to the .exe*.

If the material resides in its game folder the tool will locate the AET folder automatically. Otherwise you can select the game folder from a file dialog. This tool also accepts a few command line switches:

- `-g`: specify the game to use. Will use the game's (windows) default path, or a path saved in a soulstruct config which is created on the first run.
- `-p`: provide the path to the game folder manually.
- `-o`: where to store the collected AETs.