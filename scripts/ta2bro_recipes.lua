-- Keep each predicate independent: CookDiary probes ingredient reads in order.
-- Test required ingredients before exclusions so it never tries to satisfy a
-- different flavor first. Cooked ingredients remain valid fillers only.
local tests = {
    spicy = function(_, names, tags)
        return (names.drumstick or 0) >= 1
            and ((names.potato or 0) >= 1 or (names.corn or 0) >= 1)
            and (names.pepper or 0) >= 1
            and (tags.inedible or 0) == 0
            and (tags.sweetener or 0) == 0
    end,
    garlic = function(_, names, tags)
        return (names.drumstick or 0) >= 1
            and ((names.potato or 0) >= 1 or (names.corn or 0) >= 1)
            and (names.garlic or 0) >= 1
            and (names.pepper or 0) == 0
            and (tags.inedible or 0) == 0
            and (tags.sweetener or 0) == 0
    end,
    soy = function(_, names, tags)
        return (names.drumstick or 0) >= 1
            and ((names.potato or 0) >= 1 or (names.corn or 0) >= 1)
            and (names.onion or 0) >= 1
            and (names.pepper or 0) == 0
            and (names.garlic or 0) == 0
            and (tags.inedible or 0) == 0
            and (tags.sweetener or 0) == 0
    end,
}

local variants = {
    { id = "spicy", ingredient = "pepper", sanity = 30,
      displayname = "麻辣炒鸡", description = "辣得暖到心窝里！" },
    { id = "garlic", ingredient = "garlic", sanity = 40,
      displayname = "蒜香炒鸡", description = "蒜香一飘，烦恼全消。" },
    { id = "soy", ingredient = "onion", sanity = 15,
      displayname = "酱香炒鸡", description = "浓浓酱香，还是熟悉的家常味。" },
}

return function(tuning, foodtype, cooker)
    local foods = {}
    -- Stewer multiplies recipe time by both BASE_COOK_TIME and cooker speed.
    local multiplier = cooker == "portablecookpot" and tuning.PORTABLE_COOK_POT_TIME_MULTIPLIER or 1
    local duration = cooker == "portablecookpot" and 10 or 20
    for _, variant in ipairs(variants) do
        local id = variant.id
        local name = "ta2bro_chicken_" .. id
        foods[#foods + 1] = {
            name = name,
            displayname = variant.displayname,
            description = variant.description,
            test = tests[id],
            priority = 100,
            weight = 1,
            foodtype = foodtype.MEAT,
            health = 60,
            hunger = 75,
            sanity = variant.sanity,
            temperature = id == "spicy" and 40 or 0,
            temperatureduration = id == "spicy" and 15 or 0,
            perishtime = 10 * tuning.TOTAL_DAY_TIME,
            cooktime = duration / (tuning.BASE_COOK_TIME * multiplier),
            overridebuild = "ta2bro_chicken",
            overridesymbolname = name .. "_pot",
            cookbook_atlas = "images/cookbook/" .. name .. ".xml",
            cookbook_tex = name .. ".tex",
            card_def = { ingredients = { { "drumstick", 1 }, { "potato", 1 },
                { variant.ingredient, 1 }, { "carrot", 1 } } },
            floater = { "small", 0.05, 0.7 },
        }
    end
    return foods
end
