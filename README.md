# YU-RIS Decompiler

A decompiler for the YU-RIS visual novel engine.  
(No YPF extraction tool here, you can use others' tool for that)  
compile(decompile(original)) is almost identical to original ysbin's

## Usage

see [example_usage.py](example_usage.py)

## Tested on

not thourougly tested, but I guess it works

- the official example from version 0.488_19, 0.488_20, 0.494_30a
- 夏空あすてりずむ (dlsite RJ367965)  
    I don't know why but in the same run, each time I return to title and start, it begins from a different position in the game

## Limitations

most are due to the compilation process

- no variable names
- no macro
- currently, all globals go into one data/script/global.yst  
    theoretically it is possible to split them into their respective files, but it just works now.

## Thank You

- file format: [arcusmaximus/VNTranslationTools](https://github.com/arcusmaximus/VNTranslationTools/blob/main/VNTextPatch.Shared/Scripts/Yuris/Notes.txt)
- ysvr >v455: [1F1E33-float32/Tools](https://github.com/1F1E33-float32/Tools/blob/main/VisualNovel/Engine/YuRis/decompiler/ysvr.py#L72)
- many others which I don't remember exactly, see my starts maybe
