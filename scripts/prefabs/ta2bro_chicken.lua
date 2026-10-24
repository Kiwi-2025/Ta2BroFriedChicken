local foods = require("ta2bro_recipes")(TUNING, FOODTYPE, "cookpot")
local dependencies = { "spoiled_food" }

local function MakeChicken(food)
    local atlas = "images/inventoryimages/" .. food.name .. ".xml"
    local assets = {
        Asset("ANIM", "anim/cook_pot_food.zip"),
        Asset("ANIM", "anim/ta2bro_chicken.zip"),
        Asset("ATLAS", atlas),
        Asset("IMAGE", "images/inventoryimages/" .. food.name .. ".tex"),
    }

    local function fn()
        local inst = CreateEntity()
        inst.entity:AddTransform()
        inst.entity:AddAnimState()
        inst.entity:AddNetwork()
        MakeInventoryPhysics(inst)

        inst.AnimState:SetBank("cook_pot_food")
        inst.AnimState:SetBuild("ta2bro_chicken")
        inst.AnimState:PlayAnimation("idle")
        inst.AnimState:OverrideSymbol("swap_food", "ta2bro_chicken", food.name)
        inst.scrapbook_overridedata = { "swap_food", "ta2bro_chicken", food.name }
        inst:AddTag("preparedfood")
        MakeInventoryFloatable(inst, food.floater[1], food.floater[2], food.floater[3])

        inst.entity:SetPristine()
        if not TheWorld.ismastersim then
            return inst
        end

        -- Used by food displays such as the original prepared-food prefabs.
        inst.food_symbol_build = "ta2bro_chicken"
        inst:AddComponent("edible")
        inst.components.edible.foodtype = food.foodtype
        inst.components.edible.healthvalue = food.health
        inst.components.edible.hungervalue = food.hunger
        inst.components.edible.sanityvalue = food.sanity
        inst.components.edible.temperaturedelta = food.temperature
        inst.components.edible.temperatureduration = food.temperatureduration

        inst:AddComponent("inspectable")
        inst:AddComponent("inventoryitem")
        inst.components.inventoryitem.atlasname = atlas
        inst.components.inventoryitem:ChangeImageName(food.name)

        inst:AddComponent("stackable")
        inst.components.stackable.maxsize = TUNING.STACK_SIZE_SMALLITEM
        inst:AddComponent("perishable")
        inst.components.perishable:SetPerishTime(food.perishtime)
        inst.components.perishable.onperishreplacement = "spoiled_food"
        inst.components.perishable:StartPerishing()

        MakeSmallBurnable(inst)
        MakeSmallPropagator(inst)
        MakeHauntableLaunchAndPerish(inst)
        inst:AddComponent("bait")
        inst:AddComponent("tradable")
        return inst
    end

    return Prefab(food.name, fn, assets, dependencies)
end

local prefabs = {}
for _, food in ipairs(foods) do
    prefabs[#prefabs + 1] = MakeChicken(food)
end
return unpack(prefabs)
