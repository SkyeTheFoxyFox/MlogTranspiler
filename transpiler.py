import sys

ENABLE_SCOPE = True

def ERROR(message):
	print("ERROR:", message)
	input_code.close()
	sys.exit()

def parse_file(input):
	text = input.read()

	text = text.split("\n", text.count("\n"))
	#print("stripping lines")
	for i in range(len(text)-1):
		text[i] = text[i].strip("\t ")
	#print("clearing lines")
	for i in range(text.count("")):
		text.remove("") 
	for i in range(len(text)-1, 0, -1):
		if(text[i].startswith('#')):
			#print("clearing comment line " + str(i))
			del(text[i])

	return(text)

def parse_line(input):
	text = input.split(" ", input.count(" "))
	in_string = False
	output = []
	for i in text:
		if(i.startswith('#', 0, len(i))):
			break
		start = i.startswith('"', 0, len(i))
		end = i.endswith('"', 0, len(i))
		if(start and not end):
			if(in_string == True):
				ERROR("string not closed")
			in_string = True
		if(end):
			in_string = False

		if(in_string == True and start == False or end == True and start != True):
			output[len(output)-1] = output[len(output)-1] + " " + i
		else:
			output.append(i)

	if(in_string == True):
		ERROR("string not closed")
	return(output)

def instruction_arr(line, output): 
	match line[1]: #arr define UnitArray 32
		case "define":
			output.append(line[2] + "_read_:")
			output.append("op add _" + line[2] + "_jump_pointer_ _" + line[2] + "_jump_pointer_ 1")
			output.append(line[2] + "_write_:")
			output.append("op add @counter _" + line[2] + "_jump_pointer_ @counter")
			for i in range(int(line[3])):
				output.append("set _" + line[2] + "_var" + str(i) + " _" + line[2] + "_input_")
				output.append("set _" + line[2] + "_output_ _" + line[2] + "_var" + str(i))
				output.append("set @counter _" + line[2] + "_return_pointer_")
		case "write":
			output.append("set _" + line[2] + "_input_ @unit ")
			output.append("op mul _" + line[2] + "_jump_pointer_ i 3")
			output.append("op add _" + line[2] + "_return_pointer_ @counter 1")
			output.append("jump " + line[2] + "_write_ always")
		case "read":
			output.append("op mul _" + line[2] + "_jump_pointer_ i 3")
			output.append("op add _" + line[2] + "_return_pointer_ @counter 1")
			output.append("jump " + line[2] + "_read_ always")
			output.append("set unit _" + line[2] + "_output_")
		case _:
			ERROR("unknown instruction \"arr " + line[1] + "\"")

def macro_define_search(input):
	output = []
	can_macro = True
	is_macro = False
	current_macro_data = []
	current_macro = ""
	for line in input:
		parsed_line = parse_line(line)
		if(can_macro == True):
			if(is_macro == True):
				if(parsed_line[0] == "mac" and parsed_line[1] == "define"):
					ERROR("macro \"" + current_macro + "\" not closed")
				elif(parsed_line[0] == "mac" and parsed_line[1] == "end"):
					is_macro = False
					can_macro = False
				else:
					output_line = ""
					if(parsed_line[0] == "mac" and parsed_line[1] == current_macro):
						ERROR("Macro \"" + current_macro + "\" tried to call itself")
					for word in parsed_line:
						if word in arguments:
							output_line = output_line + "_macvar_" + str(arguments.index(word)) + " "
						else:
							output_line = output_line + word + " "

					current_macro_data.append(output_line)
			elif(not (parsed_line[0] == "mac" and parsed_line[1] == "define")):
				output.append(line)
			if(parsed_line[0] == "mac" and parsed_line[1] == "define"):
				current_macro = parsed_line[2]
				arguments = parsed_line[3:]
				is_macro = True
		else:
			output.append(line)
	return(output, current_macro, current_macro_data)

def macro_call_search(input, macro_name, macro_data):
	output = []
	macro_index = 0
	for line in input:
		parsed_line = parse_line(line)
		if(parsed_line[0] == "mac" and parsed_line[1] == macro_name):
			print("found call for macro " + macro_name)
			arguments = parsed_line[2:]
			for macro_line in macro_data:
				parsed_macro_line = parse_line(macro_line)
				output_line = ""
				for index in range(len(parsed_macro_line)):
					word = parsed_macro_line[index]
					if "_macvar_" in word:
						arg_index = int(word[8:])
						if(len(arguments) <= arg_index):
							ERROR("Macro \"" + macro_name + "\" needs " + str(len(arguments)) + " arguments")
						output_line = output_line + arguments[arg_index] + " "
					elif(word.endswith(":")):
						output_line = output_line + "_" + macro_name + "_" + str(macro_index) + "_" + word
					elif(parsed_macro_line[0] == "jump" and index == 1):
						output_line = output_line + "_" + macro_name + "_" + str(macro_index) + "_" + word + " "
					else:
						if(is_variable(parsed_macro_line[0], word, index) and ENABLE_SCOPE):
							output_line = output_line + "_" + macro_name + "_" + str(macro_index) + "_" + word + " "
						else:
							output_line = output_line + word + " "
				output.append(output_line)
			macro_index = macro_index + 1
		else:
			output.append(line)
		
	return(output)

def is_variable(instruction, value, index):
	return(not is_instruction_value(instruction, index) and not is_number(value) and not is_string(value) and not is_enum(value))
	

def is_instruction_value(ins, index):
	match(index):
		case 0:
			return(ins[len(ins)-1] != ':')
		case 1:
			return(ins in ["op","draw","radar","control","lookup","ucontrol","uradar","ulocate","getblock","setblock","status","setrule","message","cutscene","fetch","effect","mac"])
		case 2:
			return(ins in ["jump","radar","uradar","ulocate","status"])
		case 3:
			return(ins in ["radar","uradar"])
		case 4:
			return(ins in ["radar","uradar"])
		case _:
			return(False)


def is_number(value):
	match(value[0:1]):
		case "0x":
			return(string_contains(value[2:], "0123456789abcdefABCDEF"))
		case "0b":
			return(string_contains(value[2:], "01"))
		case _:
			return(string_contains(value, "0123456789.-"))

def string_contains(string, list):
	string_len = len(string)
	count = 0
	for char in list:
		count += string.count(char)
	return(string_len == count)

def is_string(value):
	return(value[0] == '"' and value[len(value)-1] == '"')

def is_enum(value):
	return(value[0] == '@')


input_code = open(sys.argv[1], "r")

output_code = []

for line in parse_file(input_code):
	#print(line)
	parsed_line = parse_line(line)
	match parsed_line[0]:
		case "arr":
			instruction_arr(parsed_line, output_code)
		case _:
			output_code.append(line)

#print("Parsed normal stuff")

while(True):
	output_code, macro_name, macro_data = macro_define_search(output_code)
	if(macro_name == ""):
		break
	print("working on macro " + macro_name)
	output_code = macro_call_search(output_code, macro_name, macro_data)
for line in output_code:
	parsed_line = parse_line(line)
	if(parsed_line[0] == "mac"):
		ERROR("Unknown macro \"" + parsed_line[1] + '"')
file_output = ""
for i in output_code:
	file_output = file_output + i + "\n"



write_code = open(sys.argv[2], "w")
write_code.write(file_output)

print("File transpiled successfully")

input_code.close()
write_code.close()