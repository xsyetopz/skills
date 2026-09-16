set_project("c-optimization-examples")
set_version("0.0.0")
set_languages("c17")
set_warnings("allextra", "error")

option("sanitize")
    set_default(false)
    set_showmenu(true)
    set_description("ASan+UBSan diagnostic build; GCC/Clang only")
option_end()

for _, name in ipairs({"c-pairs"}) do
    target(name)
        set_kind("binary")
        set_targetdir(".build")
        -- 'faster' is the baseline. 'fastest' maps to /fp:fast on MSVC.
        set_optimize("faster")
        set_symbols("debug")
        add_files("c_pairs.c")
        on_load(function (target)
            if has_config("sanitize") then
                if is_plat("windows") then
                    raise("This diagnostic recipe supports GCC/Clang on non-Windows targets only")
                end
                target:add("cxflags", "-fsanitize=address,undefined", "-fno-omit-frame-pointer")
                target:add("ldflags", "-fsanitize=address,undefined")
            end
        end)
    target_end()
end
