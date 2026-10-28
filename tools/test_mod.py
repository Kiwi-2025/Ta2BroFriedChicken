"""Lua 5.1 contract tests plus independent packed-resource validation.

Optional --game-dir loads installed, unmodified cooking.lua and recipe predicates
to check actual ingredient tags and conflicts with vanilla dishes. Combine with
--cookdiary-dir to check the installed CookDiary recipe discovery and constraints.
"""
from __future__ import annotations

import argparse
from collections import Counter
import io
from itertools import combinations_with_replacement
from pathlib import Path
import struct
import unittest
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from lupa.lua51 import LuaRuntime
from PIL import Image, ImageChops, ImageOps

ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = None
COOKDIARY_DIR = None


def runtime():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().package.path = str(ROOT / "scripts/?.lua").replace("\\", "/") + ";" + lua.globals().package.path
    lua.execute('''
        TUNING = { BASE_COOK_TIME = 19.998, TOTAL_DAY_TIME = 480,
                   PORTABLE_COOK_POT_TIME_MULTIPLIER = .8, STACK_SIZE_SMALLITEM = 40 }
        FOODTYPE = { MEAT = "MEAT" }
    ''')
    return lua


class Recipes(unittest.TestCase):
    def setUp(self):
        self.lua = runtime()
        self.make = self.lua.eval('require("ta2bro_recipes")')

    def matched(self, names, tags=None):
        counts = Counter(names)
        return [r.name for _, r in self.make(self.lua.globals().TUNING, self.lua.globals().FOODTYPE, "cookpot").items()
                if r.test("cookpot", self.lua.table_from(counts), self.lua.table_from(tags or {}))]

    def test_flavors_bases_fillers(self):
        for base in ("potato", "corn"):
            for spice, flavor in (("pepper", "spicy"), ("garlic", "garlic"), ("onion", "soy")):
                for filler in ("carrot", "ice", "monstermeat", "pepper_cooked", "potato_cooked", "drumstick_cooked"):
                    with self.subTest(base=base, spice=spice, filler=filler):
                        self.assertEqual(self.matched(["drumstick", base, spice, filler]), ["ta2bro_chicken_" + flavor])

    def test_missing_and_cooked_gate_ingredients(self):
        for items in (["meat", "potato", "pepper", "ice"],
                      ["drumstick_cooked", "potato", "pepper", "ice"],
                      ["drumstick", "potato_cooked", "pepper", "ice"],
                      ["drumstick", "corn_cooked", "garlic", "ice"],
                      ["drumstick", "potato", "pepper_cooked", "ice"],
                      ["drumstick", "potato", "garlic_cooked", "onion_cooked"],
                      ["drumstick", "carrot", "onion", "ice"]):
            self.assertEqual(self.matched(items), [], items)

    def test_priority_and_zero_tags(self):
        for a, b, expected in (("pepper", "garlic", "spicy"), ("pepper", "onion", "spicy"), ("garlic", "onion", "garlic")):
            self.assertEqual(self.matched(["drumstick", "potato", a, b]), ["ta2bro_chicken_" + expected])
        items = ["drumstick", "potato", "onion", "ice"]
        for tags in ({"inedible": 1}, {"sweetener": 1}, {"sweetener": .5}):
            self.assertEqual(self.matched(items, tags), [])
        self.assertEqual(self.matched(items, {"inedible": 0, "sweetener": 0, "monster": 1}), ["ta2bro_chicken_soy"])

    def test_metadata_and_exact_duration(self):
        g = self.lua.globals()
        for cooker, speed in (("cookpot", 1), ("portablecookpot", .8)):
            for _, food in self.make(g.TUNING, g.FOODTYPE, cooker).items():
                self.assertAlmostEqual(food.cooktime * g.TUNING.BASE_COOK_TIME * speed,
                                       10 if cooker == "portablecookpot" else 20)
                self.assertEqual((food.health, food.hunger, food.perishtime, food.priority), (60, 75, 4800, 100))
                self.assertEqual(food.overridesymbolname, food.name + "_pot")
                spicy = food.name.endswith("spicy")
                self.assertEqual(food.sanity, {"ta2bro_chicken_spicy": 30, "ta2bro_chicken_garlic": 40, "ta2bro_chicken_soy": 15}[food.name])
                self.assertEqual((food.temperature, food.temperatureduration), (40, 15) if spicy else (0, 0))
                card = []
                for _, ingredient in food.card_def.ingredients.items():
                    card.extend([ingredient[1]] * ingredient[2])
                self.assertEqual(self.matched(card), [food.name])

    def test_modmain_registration_and_lua_syntax(self):
        for path in ROOT.rglob("*.lua"):
            if ".cache" not in path.parts:
                self.lua.execute('assert(loadstring(...))', path.read_text(encoding="utf-8"))
        self.lua.execute('''
            GLOBAL = _G
            STRINGS = { NAMES = {}, CHARACTERS = { GENERIC = { DESCRIBE = {} } } }
            registrations = {}; atlases = {}
            function Asset(kind, path) return {kind, path} end
            function AddCookerRecipe(cooker, food)
                registrations[cooker] = registrations[cooker] or {}
                table.insert(registrations[cooker], food)
            end
            function RegisterInventoryItemAtlas(path, name) atlases[name] = path end
        ''')
        self.lua.execute((ROOT / "modmain.lua").read_text(encoding="utf-8"))
        for cooker in ("cookpot", "portablecookpot"):
            self.assertEqual(len(self.lua.globals().registrations[cooker]), 3)
        self.assertEqual(len(list(self.lua.globals().atlases.items())), 3)
        self.assertEqual(self.lua.globals().STRINGS.NAMES.TA2BRO_CHICKEN_SOY, "酱香炒鸡")

    def installed_cooking(self):
        if GAME_DIR is None:
            self.skipTest("Use --game-dir for installed vanilla cooking integration")
        # Only tuning/effect-display dependencies are stubbed; ingredient tags,
        # recipe predicates and the priority algorithm are installed game code.
        lua = self.lua
        lua.execute('''
            setmetatable(TUNING, {__index = function() return 1 end})
            setmetatable(FOODTYPE, {__index = function(_, k) return k end})
            local function strings() return setmetatable({}, {__index=function(t,k)
                local v = strings(); rawset(t,k,v); return v end}) end
            STRINGS = strings()
            package.loaded.tuning = true
            package.loaded["prefabs/oceanfishdef"] = {fish={}}
            package.loaded.spicedfoods = {}; package.loaded.preparednonfoods = {}
        ''')
        with ZipFile(GAME_DIR / "data/databundles/scripts.zip") as archive:
            for module in ("preparedfoods", "preparedfoods_warly"):
                lua.globals().package.loaded[module] = lua.execute(archive.read("scripts/" + module + ".lua").decode())
            cooking = lua.execute(archive.read("scripts/cooking.lua").decode())
        lua.globals().package.loaded.cooking = cooking
        return cooking

    def test_installed_cooking_integration(self):
        cooking = self.installed_cooking()
        lua = self.lua
        for cooker in ("cookpot", "portablecookpot"):
            for _, food in self.make(lua.globals().TUNING, lua.globals().FOODTYPE, cooker).items():
                lua.globals().AddCookerRecipe(cooker, food, True)
            cases = [(["drumstick", base, spice, filler], "ta2bro_chicken_" + flavor)
                     for base in ("potato", "corn")
                     for spice, flavor in (("pepper", "spicy"), ("garlic", "garlic"), ("onion", "soy"))
                     for filler in ("ice", "monstermeat", "carrot_cooked", "mandrake", "pepper_cooked", "drumstick")]
            cases += [(["drumstick", "potato", "pepper", "garlic"], "ta2bro_chicken_spicy"),
                      (["drumstick", "corn", "onion", "garlic"], "ta2bro_chicken_garlic")]
            for ingredients, expected in cases:
                actual, time = cooking.CalculateRecipe(cooker, lua.table_from(ingredients))
                self.assertEqual(actual, expected, (cooker, ingredients))
            for ingredient in ("twigs", "honey", "honeycomb", "royal_jelly", "nightmarefuel"):
                result = cooking.CalculateRecipe(cooker, lua.table_from(["drumstick", "potato", "pepper", ingredient]))
                self.assertFalse(result[0].startswith("ta2bro_"), ingredient)
        print("Installed vanilla cooking integration: 86 pot/ingredient scenarios passed")

    def test_installed_cookdiary_parser(self):
        if COOKDIARY_DIR is None:
            self.skipTest("Use --cookdiary-dir and --game-dir for CookDiary parser integration")
        cooking = self.installed_cooking()
        lua = self.lua
        # Run the installed parser unchanged. Only unrelated UI dependencies
        # are stubbed; ingredient definitions come from the installed game.
        lua.execute('''
            package.loaded.util = true
            package.loaded.diary_utils = {aliases={}, aliases_reverse={}}
            package.loaded.diary_exception = {}
            package.loaded.diary_tags = {}
            function deepcopy(t)
                if type(t) ~= "table" then return t end
                local copy = {}
                for k,v in pairs(t) do copy[k] = deepcopy(v) end
                return copy
            end
            function upvalue(fn, key)
                for i=1,100 do
                    local name, value = debug.getupvalue(fn, i)
                    if name == key then return value end
                    if name == nil then break end
                end
                error("CookDiary parser changed: missing " .. key)
            end
        ''')
        module = lua.execute((COOKDIARY_DIR / "scripts/diary_preload_fooddetail.lua").read_text(encoding="utf-8"))
        upvalue = lua.globals().upvalue
        ingredient_values = upvalue(cooking.CalculateRecipe, "GetIngredientValues")
        search = upvalue(module.GetFoodDetail, "SmartSearch")
        minimize = upvalue(module.GetFoodDetail, "MinimizeRecipe")
        details = upvalue(module.GetFoodDetail, "diary_food_detail")
        upvalue(module.GetFoodDetail, "GetAllNameTag")()
        ingredients = ("drumstick", "drumstick_cooked", "potato", "potato_cooked",
                       "corn", "corn_cooked", "pepper", "pepper_cooked", "garlic",
                       "garlic_cooked", "onion", "onion_cooked", "ice", "monstermeat",
                       "twigs", "honey", "carrot")
        for cooker in ("cookpot", "portablecookpot"):
            for _, food in self.make(lua.globals().TUNING, lua.globals().FOODTYPE, cooker).items():
                with self.subTest(cooker=cooker, food=food.name):
                    details[food.name] = food
                    parsed = search(food.test)
                    self.assertTrue(parsed, "CookDiary could not discover " + food.name)
                    self.assertTrue(minimize(food.name, parsed))
                    self.assertEqual(len(parsed.minlist), 2, "Both potato and corn must be discovered")
                    # Compare CookDiary's inferred restrictions with actual
                    # predicates, including cooked fillers and mixed flavors.
                    for items in combinations_with_replacement(ingredients, 4):
                        values = ingredient_values(lua.table_from(items))
                        names, tags = values.names, values.tags
                        expected = bool(food.test(cooker, names, tags))
                        allowed = (all((names[k] or 0) <= v for k, v in parsed.maxnames.items())
                                   and all((tags[k] or 0) <= v for k, v in parsed.maxtags.items()))
                        predicted = allowed and any(
                            all((names[k] or 0) >= v for k, v in branch.names.items())
                            and all((tags[k] or 0) >= v for k, v in branch.tags.items())
                            for _, branch in parsed.minlist.items())
                        self.assertEqual(predicted, expected, (cooker, food.name, items))
        print("CookDiary parser integration: 29,070 recipe/pot/ingredient scenarios passed")


def read_texture(data):
    assert data[:4] == b"KTEX"
    header, = struct.unpack_from("<I", data, 4)
    assert header & 15 == 0, "Use default platform, matching shipped game textures"
    assert (header >> 4) & 31 == 2, "Windows ANGLE needs DXT5 rather than raw RGBA"
    assert (header >> 9) & 15 == 1
    count = (header >> 13) & 31
    offset = 8 + count * 10
    levels = []
    for i in range(count):
        w, h, pitch, size = struct.unpack_from("<HHHI", data, 8 + i * 10)
        assert pitch == max(1, (w + 3) // 4) * 16
        assert size == pitch * max(1, (h + 3) // 4)
        levels.append(ImageOps.flip(Image.frombytes("RGBA", (w, h), data[offset:offset + size], "bcn", (3,))))
        offset += size
    assert offset == len(data) and levels[-1].size == (1, 1)
    return levels[0]


class Resources(unittest.TestCase):
    def test_reject_texture_headers_that_crashed_mod_menu(self):
        original = (ROOT / "modicon.tex").read_bytes()
        header, = struct.unpack_from("<I", original, 4)
        for bad_header in ((header & ~15) | 12, (header & ~(31 << 4)) | (4 << 4)):
            with self.assertRaises(AssertionError):
                read_texture(original[:4] + struct.pack("<I", bad_header) + original[8:])

    def test_atlas_textures_and_alpha(self):
        for xml in [ROOT / "modicon.xml", *ROOT.glob("images/inventoryimages/*.xml"), *ROOT.glob("images/cookbook/*.xml")]:
            atlas = ET.parse(xml).getroot()
            tex = xml.parent / atlas.find("Texture").get("filename")
            image = read_texture(tex.read_bytes())
            self.assertEqual(image.size, (64, 64) if xml.parent.name == "inventoryimages" else (256, 256))
            self.assertEqual(image.getchannel("A").getextrema(), (0, 255))
            self.assertEqual(atlas.find("Elements/Element").get("name"), tex.name)

    def test_build_symbols_and_uvs(self):
        with ZipFile(ROOT / "anim/ta2bro_chicken.zip") as archive:
            data = io.BytesIO(archive.read("build.bin"))
            atlas = read_texture(archive.read("atlas-0.tex"))
        def unpack(fmt): return struct.unpack(fmt, data.read(struct.calcsize(fmt)))
        def string(): return data.read(unpack("<I")[0]).decode("ascii")
        self.assertEqual(data.read(4), b"BILD")
        self.assertEqual(unpack("<III"), (6, 6, 6))
        self.assertEqual(string(), "ta2bro_chicken")
        self.assertEqual(unpack("<I"), (1,))
        self.assertEqual(string(), "atlas-0.tex")
        symbols = []
        for _ in range(6):
            hashed, frames = unpack("<II")
            self.assertEqual(frames, 1)
            frame, duration, x, y, w, h, start, count = unpack("<IIffffII")
            self.assertEqual((frame, duration, count), (0, 1, 6))
            self.assertEqual(w, h)
            symbols.append((hashed, start, count, w))
        self.assertEqual([x[0] for x in symbols], sorted(x[0] for x in symbols))
        vertices = [unpack("<6f") for _ in range(unpack("<I")[0])]
        strings = {}
        for _ in range(unpack("<I")[0]):
            hashed, = unpack("<I"); strings[hashed] = string()
        self.assertEqual(data.read(), b"")
        for hashed, start, count, width in symbols:
            vs = vertices[start:start + count]
            self.assertEqual(len(vs), 6)
            self.assertTrue(all(0 <= v[3] <= 1 and 0 <= v[4] <= 1 and v[5] == 0 for v in vs))
            self.assertAlmostEqual(width, 220 if strings[hashed].endswith("_pot") else 200)
            basename = strings[hashed].removesuffix("_pot")
            index = ("spicy", "garlic", "soy").index(basename.removeprefix("ta2bro_chicken_"))
            region = atlas.crop((index * 256, 0, (index + 1) * 256, 256))
            cookbook = read_texture((ROOT / f"images/cookbook/{basename}.tex").read_bytes())
            self.assertIsNone(ImageChops.difference(region, cookbook).getbbox())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-dir", type=Path)
    parser.add_argument("--cookdiary-dir", type=Path)
    args, remaining = parser.parse_known_args()
    GAME_DIR = args.game_dir
    COOKDIARY_DIR = args.cookdiary_dir
    unittest.main(argv=[__file__, *remaining], verbosity=2)
