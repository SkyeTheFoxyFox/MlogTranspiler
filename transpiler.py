import sys

ENABLE_SCOPE = True
COPY_CODE = False
NO_COPY = False
SOURCE_FILE = ""
OUTPUT_FILE = ""

try:
    import pyperclip
except ImportError:
    NO_COPY = True

def ERROR(message):
	print("ERROR:", message)
	input_file.close()
	sys.exit()

def WARNING(message):
	print("WARNING:", message)

def arg_len_check(input, length):
	if(len(input) < (length + 1)):
		ERROR("Instruction \"%s\" expected more arguments" % input[0])

def handle_args(args):
	i = 0
	while(i < len(args)):
		arg = args[i]
		match arg:
			case "-src":
				global SOURCE_FILE
				i += 1
				SOURCE_FILE = args[i]
			case "-out":
				global OUTPUT_FILE
				i += 1
				OUTPUT_FILE = args[i]
			case "-copy":
				if(NO_COPY == False):
					global COPY_CODE
					COPY_CODE = True
				else:
					WARNING("Install pyperclip to use -copy")
			case "-no_scope":
				global ENABLE_SCOPE
				ENABLE_SCOPE = False
		i += 1

def parse_file(input):
	text = input.read()

	text = text.split("\n", text.count("\n"))
	for i in range(len(text)-1):
		text[i] = text[i].strip("\t ")
	for i in range(len(text)-1, -1, -1):
		if(text[i].startswith('#')):
			del(text[i])
	for i in range(len(text)-1, -1, -1):
		if(text[i] == ""):
			del(text[i])
	return(text)

def parse_line(input):
	text = split_line(input)
	output = []
	for i in text:
		if(i.startswith('#', 0, len(i))):
			break
		output.append(i)
	return(output)

def split_line(line):
	is_string = False
	line_out = []
	word_output = ""
	for char in line:
		if(char == '"' and is_string == False):
			is_string = True
			word_output += char
		elif(char == '"' and is_string == True):
			is_string = False
			word_output += char
		elif(char == ' ' and is_string == False):
			line_out.append(word_output)
			word_output = ""
		else:
			word_output += char
	if(is_string == True):
		ERROR("string not closed")
	line_out.append(word_output)
	return(line_out)

def handle_basic_instructions(input, output, include_list, const_list, current_file):
	for line in input:
		parsed_line = parse_line(line)
		match parsed_line[0]:
			case "arr":
				instruction_arr(parsed_line, output)
			case "include":
				instruction_include(parsed_line, include_list, current_file)
			case "swrite":
				instruction_swrite(parsed_line, output)
			case "const":
				instruction_const(parsed_line, output, const_list)
			case "printf":
				instruction_printf(parsed_line, output)
			case _:
				output.append(line)

def instruction_arr(line, output): 
	arg_len_check(line, 3)
	match line[1]: #arr define UnitArray 32
		case "define":
			output.append(line[2] + "_read_:")
			output.append("op add _" + line[2] + "_jump_pointer_ _" + line[2] + "_jump_pointer_ 1")
			output.append(line[2] + "_write_:")
			output.append("op add @counter _" + line[2] + "_jump_pointer_ @counter")
			try:
				arr_len = int(line[3])
			except ValueError:
				ERROR("Instruction \"arr define\" expected integer length, got \"%s\"" % line[3])
			for i in range():
				output.append("set _" + line[2] + "_var" + str(i) + " _" + line[2] + "_input_")
				output.append("set _" + line[2] + "_output_ _" + line[2] + "_var" + str(i))
				output.append("set @counter _" + line[2] + "_return_pointer_")
		case "write":
			arg_len_check(line, 4)
			output.append("set _" + line[2] + "_input_ " + line[3])
			output.append("op mul _" + line[2] + "_jump_pointer_ " + line[4] + " 3")
			output.append("op add _" + line[2] + "_return_pointer_ @counter 1")
			output.append("jump " + line[2] + "_write_ always")
		case "read":
			arg_len_check(line, 4)
			output.append("op mul _" + line[2] + "_jump_pointer_ " + line[4] + " 3")
			output.append("op add _" + line[2] + "_return_pointer_ @counter 1")
			output.append("jump " + line[2] + "_read_ always")
			output.append("set " + line[3] + " _" + line[2] + "_output_")
		case _:
			ERROR("unknown instruction \"arr " + line[1] + "\"")

def instruction_swrite(line, output):
	arg_len_check(line, 3)
	if(not is_string(line[1])):
		ERROR("Instruction \"swrite\" expected string")
	string = string_esc_parse(line[1])
	if(is_number(line[3])):
		try:
			i = int(line[3])
		except ValueError:
			ERROR("Instruction \"swrite\" expected integer index, got \"%s\"" % line[3])
		if(not is_string(string)):
			ERROR("Instruction \"swrite\" expected string")
		for char in string[1:(len(string)-1)]:
			output.append("write " + str(ord(char)) + " " + line[2] + " " + str(i))
			i += 1
		output.append("write 0 " + line[2] + " " + str(i))
	else:
		output.append("write " + str(ord(string[1])) + " " + line[2] + " " + str(line[3]))
		output.append("op add _swrite_index " + str(line[3]) + " 1")
		for char in string[2:(len(string)-1)]:
			output.append("write " + str(ord(char)) + " " + line[2] + " _swrite_index")
			output.append("op add _swrite_index _swrite_index 1")
		output.append("write 0 " + line[2] + " _swrite_index")

def string_esc_parse(string):
	output = ""
	i = 0
	while True:
		char = string[i]
		if(char == '\\' and i+1 < len(string)):
			match string[i+1]:
				case 'n':
					output += '\n'
				case '\\':
					output += '\\'
				case _:
					ERROR("Invalid escape sequence \"\\%c\"" % string[i+1])
			i += 1
		else:
			output += char
		i += 1
		if(i >= len(string)):
			break
	return(output)

def instruction_const(line, output, const_list):
	arg_len_check(line, 1)
	var = line[1]
	if(is_string(var) or is_enum(var) or is_number(var)):
		ERROR("Invalid constant '%s'" % var)
	if(is_const(var, const_list)):
		ERROR("Attempted to redefine constant \"%s\"" % var)
	const_list.append(line[1])
	if(len(line) > 2):
		output.append("set " + line[1] + " " + line[2])

def instruction_printf(line, output):
	arg_len_check(line, 1)
	if(not is_string(line[1])):
		ERROR("Instruction \"printf\" expected string, got \"%s\"" % line[1])
	format_string = line[1][1:len(line[1])-1]
	current_var = 2
	temp_string = ""
	i = 0
	while(True):
		char = format_string[i]
		if(char == '%' and format_string[i+1] in "dsfc"):
			if(current_var >= len(line)):
				ERROR("Instruction \"printf\" expected more variables")
			if(temp_string != ""):
				output.append('print "%s"' % temp_string)
			temp_string = ""
			output.append("print %s" % line[current_var])
			current_var += 1
			i += 1
		else:
			temp_string += char
		i += 1
		if(i >= len(format_string)):
			break
	if(temp_string != ""):
		output.append('print "%s"' % temp_string)

def is_variable(instruction, value, index, const_list):
	return(not is_instruction_value(instruction, index) and not is_number(value) and not is_string(value) and not is_enum(value) and not is_const(value, const_list))
	
def is_instruction_value(ins, index):
	match(index):
		case 0:
			return(ins[len(ins)-1] != ':')
		case 1:
			return(ins in ["op","draw","radar","control","lookup","ucontrol","uradar","ulocate","getblock","setblock","status","setrule","message","cutscene","fetch","effect","setmarker","mac"])
		case 2:
			return(ins in ["jump","radar","uradar","ulocate","status","makemarker"])
		case 3:
			return(ins in ["radar","uradar"])
		case 4:
			return(ins in ["radar","uradar"])
		case _:
			return(False)

def is_number(value):
	match(value[0:2]):
		case "0x":
			return(string_contains(value[2:], "0123456789abcdefABCDEF"))
		case "0b":
			return(string_contains(value[2:], "01"))
		case _:
			if(value.count("e") == 1):
				return(string_contains(value, "0123456789-e"))
			else:
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

def is_const(value, const_list):
	return(value in const_list)

def macro_split(input, macros, macro_indices, output):
	is_macro = False
	current_macro = ""
	for line in input:
		parsed_line = parse_line(line)

		if(parsed_line[0] == "mac" and parsed_line[1] == "end"):
			is_macro = False

		elif(is_macro):
			output_line = ""
			for word in parsed_line:
				if word in arguments:
					output_line = output_line + "_macvar_" + str(arguments.index(word)) + " "
				else:
					output_line = output_line + word + " "
			macros[current_macro].append(output_line)

		elif(parsed_line[0] == "mac" and parsed_line[1] == "define"):
			if(parsed_line[2] in macros):
				ERROR("Macro \"" + parsed_line[2] + "\" already defined")

			is_macro = True
			current_macro = parsed_line[2]
			macros[current_macro] = []
			macro_indices[current_macro] = 0
			arguments = parsed_line[3:]

		else:
			output.append(line)

def macro_insert(macro, arguments, macro_indices, macro_list, chain_list, output, const_list):
	chain_list.append(macro)
	if(macro not in macro_list):
		ERROR("macro \"" + macro + "\" undefined")
	for line in macro_list[macro]:
		parsed_line = parse_line(line)
		output_line = ""
		for index in range(len(parsed_line)):
			word = parsed_line[index]
			if "_macvar_" in word:
				arg_index = int(word[8:])
				if(len(arguments) <= arg_index):
					ERROR("Macro \"" + macro + "\" needs more arguments")
				output_line += arguments[arg_index] + " "
			elif(word.endswith(":")):
				output_line += "_%s_%d_%s" % (macro, macro_indices[macro], word)
			elif(parsed_line[0] == "jump" and index == 1):
				output_line += "_%s_%d_%s " % (macro, macro_indices[macro], word)
			else:
				if(word.startswith("$")):
					output_line += word[1:] + " "
				elif(is_variable(parsed_line[0], word, index, const_list) and ENABLE_SCOPE):
					output_line += "_%s_%d_%s " % (macro, macro_indices[macro], word)
				else:
					output_line += word + " "
		parsed_line = parse_line(output_line.strip("\t "))
		if(parsed_line[0] == "mac"):
			if(parsed_line[1] not in chain_list):
				macro_insert(parsed_line[1], parsed_line[2:], macro_indices, macro_list, chain_list, output, const_list)
			else:
				WARNING("macro \"" + parsed_line[1] + "\" tried to call itself... skipping")
		else:
			output.append(output_line)

	macro_indices[macro] = macro_indices[macro] + 1
	chain_list.pop()

def handle_macros(input, macro_indices, macro_list, output, const_list):
	chain_list = []

	for line in input:
		parsed_line = parse_line(line)
		if(parsed_line[0] == "mac"):
			macro_insert(parsed_line[1], parsed_line[2:], macro_indices, macro_list, chain_list, output, const_list)
		else:
			output.append(line)

def instruction_include(line, include_list, current_file):
	arg_len_check(line, 1)
	file_loc = current_file[:current_file.rfind("/")+1] + line[1]
	if(file_loc in include_list):
		WARNING("File \"" + file_loc + "\" already included... skipping")
	else:
		include_list.append(file_loc)

def include_file(file_loc, macro_list, macro_indices, include_list, const_list):
	try:
		file = open(file_loc, "r")
	except OSError:
		ERROR("Can't find file \"%s\"" % file_loc)
	output_code = []

	handle_basic_instructions(parse_file(file), output_code, include_list, const_list, file_loc)
	input_code = output_code
	output_code = []
	macro_split(input_code, macro_list, macro_indices, output_code)

def handle_includes(include_list, macro_list, macro_indices, const_list):
	file_index = 1
	while(True):
		if(file_index >= len(include_list)):
			return
		file = include_list[file_index]
		include_file(file, macro_list, macro_indices, const_list, include_list)
		file_index += 1



handle_args(sys.argv[1:])
try:
	input_file = open(SOURCE_FILE, "r")
except OSError:
	ERROR("Can't find file \"%s\"" % SOURCE_FILE)

output_code = []
include_list = [SOURCE_FILE]
const_list = ["true", "false", "null"]



handle_basic_instructions(parse_file(input_file), output_code, include_list, const_list, SOURCE_FILE)

input_code = output_code
output_code = []
macro_list = {}
macro_indices = {}

macro_split(input_code, macro_list, macro_indices, output_code)

handle_includes(include_list, macro_list, macro_indices, const_list)

input_code = output_code
output_code = []

handle_macros(input_code, macro_indices, macro_list, output_code, const_list)


file_output = ""
for i in output_code:
	file_output = file_output + i.strip("\t ") + "\n"

if(OUTPUT_FILE != ""):
	try:
		output_file = open(OUTPUT_FILE, "w")
		output_file.write(file_output)
		output_file.close()
	except OSError:
		ERROR("Can't find file \"%s\"" % OUTPUT_FILE)
if(COPY_CODE == True):
	pyperclip.copy(file_output)

print("File transpiled successfully")

input_file.close()
