# Warning

This transpiler is not fully functional: functions do not play well with macros. I'll be able to rewrite it once I can find the time and motivation.

# Explanation

A mlog transpiler with support for macros, functions, and simple counter arrays, as well as a bunch of smaller things.

The program takes some arguments, `-src` for the input file, `-out` for the output file, `-copy` to enable copying to clipboard, and `-no_scope` to disable scope. Everything but the input file is optional.

You can define a function/macro using `def Name arg1 ...` then your code, then a `def end`. If you wish to limit it to only being used as one type, you can use `def mac Name` or `def fun Name`.

You can call functions with `fun Name arg1 ...`, and macros with `mac Name arg1 ...`

Functions will generally take less instructions if called a bunch, but macros maintain better performance, especially if you have a whole lot of arguments. Both of them have individual scope, to interact with variables outside the macro use `$` before the variable, such as `$variable`.

`const` will allow you to define words to other things, any instance of the word in the code will be replaced by the defined replacement.

`cop` behaves like `op` but is eveluated at transpile time

The `include` instruction allows you to include another file, and use it's macros. included macros will also apply their own includes. To include a file use `include filePath`, the file path is relative to the directory of the initial file.

Arrays are an easy way to utilize counter arrays, and can be defined with `arr define Name size`. They can be read with `arr read Name output index`, and written to with `arr write Name input index` 

It also adds a few smaller instructions:

`swrite` writes a constant string to a memcell as ascii values.
`printf` converts a formatted string (ex. "var: {var}") into a `print` with a series of `format`s.
