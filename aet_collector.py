import argparse
from pathlib import Path
import re
import shutil
from crossfiledialog import open_file

from soulstruct.config import (
    GET_CONFIG,
    SET_CONFIG,
    ELDEN_RING_PATH,
    DS3_PATH,
    SEKIRO_PATH,
)
from soulstruct.games import GAMES
from soulstruct.base.models import MATBIN


AET_BASE_DIR = "assets/aet"
NIGHTREIGN_DEFAULT_PATH = Path(
    "C:/Program Files (x86)/Steam/steamapps/common/ELDEN RING NIGHTREIGN"
)


def collect_aets(mat_path: Path, game_path: Path, output_dir: Path = None) -> None:
    aet_base_dir = game_path / AET_BASE_DIR
    if not aet_base_dir.is_dir():
        raise ValueError(f"Could not locate aet folder in {game_path}")

    mat: MATBIN = MATBIN.from_path(mat_path)
    collected: set[str] = set()
    print(f"Collecting AETs for {mat_path.name}")

    for sampler in mat.samplers:
        aet: str = next(re.finditer(r"(?<=/)AET\d\d\d_\d\d\d(?=/)", sampler.path), None)
        if not aet or aet.lower() in collected:
            continue

        print(f" - {aet}")
        group = aet.split("_")[0]

        for suffix in ["", "_l"]:
            aet_dir = aet_base_dir / group.lower()
            name = f"{aet}{suffix}"

            for file in aet_dir.glob("*.tpfbnd.dcx"):
                if (
                    file.stem.lower() == name.lower()
                    and not (output_dir / file.name).is_file()
                ):
                    shutil.copy(file, output_dir)

        collected.add(aet.lower())

    print(f"{mat_path.name}: collected {len(collected)} AETs in {output_dir}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("matbin", type=Path, required=True, help="Path to a matbin file")
    group = p.add_mutually_exclusive_group()
    group.add_argument(
        "-g",
        "--game",
        choices=["NR", "ER", "DS3", "SDT"],
        help="Use this game for locating AETs",
    )
    group.add_argument(
        "-p",
        "--game-path",
        type=Path,
        help="Manually set the game path to locate AETs. If neither game nor game-path are provided the game path is determined from the matbin location if possible.",
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        required=False,
        help="Where to save located AETs. Will default to an 'aet' folder next to the matbin.",
    )

    args = p.parse_args()

    # === game path from game type via config ===
    if args.game:
        game = args.game = args.game.upper()
        if game == "NR":
            cfg = GET_CONFIG()
            if "NIGHTREIGN_PATH" in cfg:
                args.game_path = cfg["NIGHTREIGN_PATH"]
        elif game == "ER":
            args.game_path = ELDEN_RING_PATH
        elif game == "DS3":
            args.game_path = DS3_PATH
        elif game == "SDT":
            args.game_path = SEKIRO_PATH
        else:
            raise ValueError(f"Invalid game {game}")

    # === game path from matbin path ===
    if not args.game_path or not args.game_path.is_dir():
        # Try to determine the game directory from the matbin path first
        parent: Path = args.matbin.parent
        while parent and parent.parent != parent:
            candidate = parent / AET_BASE_DIR
            if candidate.is_dir():
                args.game_path = parent
                break

            parent = parent.parent
        else:
            input(
                "Failed to determine game directory, please press Enter and choose the game's .exe manually..."
            )
            ret = open_file("Locate Game .exe", str(args.matbin.parent), ".exe")
            if ret:
                args.game_path = Path(ret).parent

    if not args.game_path:
        raise ValueError(
            "Could not determine game and neither game nor game-path were provided"
        )

    # Use game folder if the game exe was provided
    if args.game_path.is_file():
        args.game_path = args.game_path.parent

    if not (args.game_path / AET_BASE_DIR).is_dir():
        raise ValueError(f"Game directory does not contain {AET_BASE_DIR} subfolder")

    # === game type from
    if not args.game:
        path = args.game_path

        if (path / "NIGHTREIGN.exe").is_file():
            args.game = "NR"
        else:
            for game in GAMES:
                if (path / game.executable_name).is_file():
                    args.game = game.abbreviated_name.upper()
                    break

    # === save back to config if we managed to locate the game dir ===
    if args.game:
        key = {
            "NR": "NIGHTREIGN_PATH",
            "ER": "ELDEN_RING_PATH",
            "DS3": "DS3_PATH",
            "SDT": "SEKIRO_PATH",
        }[args.game]
        SET_CONFIG(key=str(args.game_path))
    else:
        print("WARNING: could not determine game type, config has not been updated")

    # default output dir
    if not args.output:
        args.output = args.matbin.parent / "aet"
    args.output.mkdir(parents=True, exist_ok=True)

    collect_aets(args.matbin, args.game_path, args.output)
