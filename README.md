# YU-RIS Decompiler

A decompiler for the YU-RIS visual novel engine.  
(No YPF extraction tool here, you can use others' tool for that)  
(re)compile(decompile(original)) is almost identical to original  

## Usage

see [example_usage.py](example_usage.py)

## Tested on

- the official example from version 0.488_19
- 夏空あすてりずむ (dlsite RJ367965)  

now, for these two, recompile(decompile(original)) == original  
except yst_list.ybn due to stored modification time.  
you can use diff_official_bin.sh and diff_natsu_bin.sh to test this

## Limitations

most are due to the compilation process

- no variable names
- no macro
- all globals go into the first empty script, or into a created data/script/global.yst
    (mostly eris/global.yst where they most possibly original stayed)

## Thank You

- file format: [arcusmaximus/VNTranslationTools](https://github.com/arcusmaximus/VNTranslationTools/blob/main/VNTextPatch.Shared/Scripts/Yuris/Notes.txt)
- ysvr >v455: [1F1E33-float32/Tools](https://github.com/1F1E33-float32/Tools/blob/main/VisualNovel/Engine/YuRis/decompiler/ysvr.py#L72)
- many others which I don't remember exactly, see my starts maybe
