PrefabFiles = { "ta2bro_chicken" }

Assets = {
    GLOBAL.Asset("ANIM", "anim/ta2bro_chicken.zip"),
}

local recipes = require("ta2bro_recipes")
local cookers = { "cookpot", "portablecookpot" }

for _, cooker in ipairs(cookers) do
    for _, food in ipairs(recipes(GLOBAL.TUNING, GLOBAL.FOODTYPE, cooker)) do
        AddCookerRecipe(cooker, food)
    end
end

for _, food in ipairs(recipes(GLOBAL.TUNING, GLOBAL.FOODTYPE, "cookpot")) do
    local atlas = "images/inventoryimages/" .. food.name .. ".xml"
    table.insert(Assets, GLOBAL.Asset("ATLAS", atlas))
    table.insert(Assets, GLOBAL.Asset("IMAGE", "images/inventoryimages/" .. food.name .. ".tex"))
    table.insert(Assets, GLOBAL.Asset("ATLAS", food.cookbook_atlas))
    table.insert(Assets, GLOBAL.Asset("IMAGE", "images/cookbook/" .. food.name .. ".tex"))
    RegisterInventoryItemAtlas(atlas, food.name .. ".tex")
    GLOBAL.STRINGS.NAMES[string.upper(food.name)] = food.displayname
    GLOBAL.STRINGS.CHARACTERS.GENERIC.DESCRIBE[string.upper(food.name)] = food.description
end
