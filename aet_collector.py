import sys
import argparse
from pathlib import Path
import re
import shutil
import json
from crossfiledialog import open_file

from soulstruct.config import (
    GET_CONFIG,
    ELDEN_RING_PATH,
    DS3_PATH,
    SEKIRO_PATH,
    _DEFAULT_STEAM_PATH,
    _SOULSTRUCT_APPDATA,
)
from soulstruct.games import GAMES
from soulstruct.base.models import MATBIN


AET_BASE_DIR = "asset/aet"
DEFAULT_NIGHTREIGN_PATH = _DEFAULT_STEAM_PATH / "ELDEN RING NIGHTREIGN/Game"


def collect_aets(mat_path: Path, game_path: Path, output_dir: Path = None) -> None:
    aet_base_dir = game_path / AET_BASE_DIR
    if not aet_base_dir.is_dir():
        raise ValueError(f"Could not locate aet folder in {game_path}")

    mat: MATBIN = MATBIN.from_path(mat_path)
    collected: set[str] = set()
    print(f"Collecting AETs for {mat_path.name} ({mat.shader_path})")

    for sampler in mat.samplers:
        match = next(re.finditer(r"AET\d\d\d_\d\d\d", sampler.path), None)
        if not match or match.group(0).lower() in collected:
            continue

        aet = match.group(0)
        print(f" - {aet}")
        group = aet.split("_")[0].lower()

        for suffix in ["", "_l"]:
            aet_dir = aet_base_dir / group
            name = f"{aet.lower()}{suffix}"
            aet_dcx = aet_dir / f"{name}.tpf.dcx"

            if aet_dcx.is_file():
                if not (output_dir / aet_dcx.name).is_file():
                    shutil.copy(aet_dcx, output_dir)
            else:
                print(f"Could not locate {aet_dcx}")

        collected.add(aet.lower())

    print(f"{mat_path.name}: collected {len(collected)} AETs in {output_dir}")


def save_config(config: dict = None, **overrides) -> None:
    # Soulstruct is too limiting here
    if config is None:
        config = GET_CONFIG()

    if overrides:
        config.update(overrides)

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        config_path = Path(sys.executable).parent / "soulstruct_config.json"
    else:
        config_path = _SOULSTRUCT_APPDATA / "soulstruct_config.json"

    config_json = {
        k: str(v) if isinstance(v, Path) else v for k, v in config.items()
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w") as f:
        json.dump(config_json, f, indent=4)


if __name__ == "__main__":
    try:
        p = argparse.ArgumentParser()
        p.add_argument("matbins", nargs="+", type=Path, help="Paths to one or more matbin files")
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
                else:
                    args.game_path = DEFAULT_NIGHTREIGN_PATH
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
            parent: Path = args.matbins[0].parent
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
                ret = open_file("Locate Game .exe", str(args.matbins[0].parent), ".exe")
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

            if (path / "nightreign.exe").is_file():
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
            
            cfg = GET_CONFIG()
            cfg[key] = str(args.game_path)
            save_config(cfg)

            print(f"Game is {args.game}")
        else:
            print("WARNING: could not determine game type, config has not been updated")

        # default output dir
        if not args.output:
            args.output = Path(sys.executable).parent / "aet"
        args.output.mkdir(parents=True, exist_ok=True)

        for mat in args.matbins:
            collect_aets(mat, args.game_path, args.output)
            print()
    finally:
        input("Press enter to exit...")