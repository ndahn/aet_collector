A small convenience tool for souls modding. Pass it a material (.matbin) file and it will collect the AETs referenced by that material. 

If the material resides in the game folder it will locate the AET folder automatically. Otherwise you can select the game folder from a file dialog. This tool also accepts a few command line switches:
- `-g`: specify the game to use. Will use the game's (windows) default path, or a path saved in a soulstruct config which is created on the first run.
- `-p`: provide the path to the game folder manually.
- `-o`: where to store the collected AETs. If not provided the AETs will be stored in a folder called `aet` next to the input material.