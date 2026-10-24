-- Keep the matching logic shared by both cookers and the food prefabs.
-- Cooked ingredients may fill a slot, but never count toward these gates.
local function count(names, name)
    return names[name] or 0
end

local function flavor(names, tags)
    if count(names, "drumstick") < 1
        or count(names, "potato") + count(names, "corn") < 1
        or (tags.inedible or 0) ~= 0
        or (tags.sweetener or 0) ~= 0 then
        return nil
    end
    if count(names, "pepper") >= 1 then
        return "spicy"
    elseif count(names, "garlic") >= 1 then
        return "garlic"
    elseif count(names, "onion") >= 1 then
        return "soy"
    end
end

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
    for _, variant in ipairs(variants) do
        local id = variant.id
        local name = "ta2bro_chicken_" .. id
        foods[#foods + 1] = {
            name = name,
            displayname = variant.displayname,
            description = variant.description,
            test = function(_, names, tags) return flavor(names, tags) == id end,
            priority = 100,
            weight = 1,
            foodtype = foodtype.MEAT,
            health = 60,
            hunger = 75,
            sanity = variant.sanity,
            temperature = id == "spicy" and 40 or 0,
            temperatureduration = id == "spicy" and 15 or 0,
            perishtime = 10 * tuning.TOTAL_DAY_TIME,
            cooktime = 20 / (tuning.BASE_COOK_TIME * multiplier),
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
