An mlog transpiler with support for macros and simple counter arrays.

The program takes 2 arguments, the file to tranpiler, and the file to write it out to.

macro example
```
set a 25
mac TestMacro 67 a out
print out
printflush message1

mac define TestMacro a b c
  op add c a b
mac end
```

array example
```
arr write TestArray @copper 0 # writes @copper to the array at 0
arr write TestArray @lead 1
arr read TestArray output 0 # reads the value from the array at 0 to output
print output
printflush message1

end

arr define TestArray 25 # 25 is the size of the array
```
