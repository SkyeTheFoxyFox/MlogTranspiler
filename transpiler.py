import sys
import math 
import random

ENABLE_SCOPE = True
COPY_CODE = False
NO_COPY = False
SOURCE_FILE = ""
OUTPUT_FILE = ""


global_const_list = {}

try:
    import pyperclip
except ImportError:
    NO_COPY = True

class CodeDefinition:
	def __init__(self, name, code, mac_only, fun_only, arg_count):
		self.name = name
		self.code = code
		self.index = 0
		self.mac_only = mac_only
		self.fun_only = fun_only
		self.argument_count = arg_count
		self.argument_out_list = [0 for x in range(arg_count)]

def ERROR(message):
	print("ERROR:", message)
	input_file.close()
	sys.exit()

def WARNING(message):
	print("WARNING:", message)

def arg_len_check(input, length):
	if(len(input) < (length + 1)):
		ERROR("Instruction \"%s\" expected more arguments" % input[0])

def open_file(file_loc):
	try:
		file = open(file_loc, "r")
	except OSError:
		ERROR("Can't find file \"%s\"" % file_loc)
	return(file)

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
	global global_const_list
	text = split_line(input)
	output = []
	for i in text:
		if(i.startswith('#', 0, len(i))):
			break
		output.append(i)
	for i in range(output.count("")):
		output.remove("")
	temp = output
	output = []
	for word in temp:
		if(word in global_const_list):
			for const_word in global_const_list[word]:
				output.append(const_word)
		else:
			output.append(word)
	return(output)

def merge_line(line):
	output = ""
	for word in line:
		output += word + " "
	return(output.strip(" "))

def update_line(line):
	return(merge_line(parse_line(line)))

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

def handle_basic_instructions(input, output, current_file, called_functions_list, def_list):
	for line in input:
		parsed_line = parse_line(line)
		match parsed_line[0]:
			case "fun":
				instruction_fun(parsed_line, output, called_functions_list, def_list)
			case "arr":
				instruction_arr(parsed_line, output)
			case "swrite":
				instruction_swrite(parsed_line, output)
			case "printf":
				instruction_printf(parsed_line, output)
			case _:
				if(parsed_line[0] != "const" and parsed_line[0] != "include"):
					output.append(update_line(line))

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
			for i in range(arr_len):
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

def instruction_printf(line, output):
	arg_len_check(line, 1)
	if(not is_string(line[1])):
		ERROR("Instruction \"printf\" expected string, got \"%s\"" % line[1])
	format_string = line[1][1:len(line[1])-1]
	output_string = ""
	var_list = []
	current_variable_index = 0
	index = 0
	while True:
		char = format_string[index]
		if(char == "{" and format_string[index-1] != "\\"):
			output_string += "{"
			variable_string = ""
			while True:
				index += 1
				var_char = format_string[index]
				if(index >= len(format_string)):
					ERROR("Printf variable not closed")
				elif(var_char == "}"):
					output_string += str(current_variable_index) + "}"
					current_variable_index += 1
					break
				else:
					variable_string += var_char
			if(variable_string == ""):
				ERROR("Variable not included from printf")
			var_list.append(variable_string)
		elif(char != "\\" or (char == "\\" and format_string[index-1] == "\\")):
			output_string += char
		index += 1
		if(index >= len(format_string)):
			break
	output.append(f'print "{output_string}"')
	for variable in var_list:
		output.append(f"format {variable}")	

def is_variable(instruction, value, index):
	return(not is_instruction_value(instruction, index) and not is_number(value) and not is_string(value) and not is_enum(value) and not is_const(value))
	
def is_instruction_value(ins, index):
	match(index):
		case 0:
			return(ins[len(ins)-1] != ':')
		case 1:
			return(ins in ["op","cop","draw","radar","control","lookup","ucontrol","uradar","ulocate","getblock","setblock","status","setrule","message","cutscene","fetch","effect","setmarker","mac"])
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
			elif(value[0] == '%'):
				return(string_contains(value[1:], "0123456789abcdefABCDEF"))
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

def is_const(value):
	return(value in ["true", "false", "null"])

def is_output(ins, subins, index):
	match(index):
		case 0:
			return(False)
		case 1:
			return(ins in ["read", "getlink", "sensor", "set", "packcolor", "getblock", "spawn", "getflag"])
		case 2:
			return(ins in ["op", "lookup", "fetch"])
		case 3:
			return(ins in ["message"])
		case 5:
			return(ins in ["ulocate"])
		case 6:
			return(ins in ["uradar", "ulocate"])
		case 7:
			return(ins in ["radar", "ulocate"])
		case 8:
			return(ins in ["ulocate"])
		case _:
			if(ins == "ucontrol"):
				if(subins == "getBlock"):
					return(index >= 4 and index <= 6)
				elif(subins == "within"):
					return(index == 5)
				else:
					return(False)
			else:
				return(False)

def def_get(input, defs):
	is_def = False
	mac_only = False
	fun_only = False
	current_def = ""
	arguments = []
	for line in input:
		parsed_line = parse_line(line)

		if(parsed_line[0] == "def" and parsed_line[1] == "end"):
			is_def = False

		elif(is_def):
			output_line = ""
			for word in parsed_line:
				if word in arguments:
					output_line = output_line + "_defvar_" + str(arguments.index(word)) + " "
				else:
					output_line = output_line + word + " "
			defs[current_def].code.append(output_line)

		elif(parsed_line[0] == "def"):
			if(parsed_line[1] == "mac"):
				if(parsed_line[2] in defs):
					ERROR("Definition \"" + parsed_line[1] + "\" already defined")
				mac_only = True
				current_def = parsed_line[2]
				arguments = parsed_line[3:]
			elif(parsed_line[1] == "fun"):
				if(parsed_line[2] in defs):
					ERROR("Definition \"" + parsed_line[1] + "\" already defined")
				fun_only = True
				current_def = parsed_line[2]
				arguments = parsed_line[3:]
			elif(parsed_line[1] in defs):
				ERROR("Definition \"" + parsed_line[1] + "\" already defined")
			else:
				current_def = parsed_line[1]
				arguments = parsed_line[2:]
			is_def = True
			defs[current_def] = CodeDefinition(current_def, [], mac_only, fun_only, len(arguments))

def def_split(input, defs, output):
	is_def = False
	mac_only = False
	fun_only = False
	current_def = ""
	arguments = []
	for line in input:
		parsed_line = parse_line(line)

		if(parsed_line[0] == "def" and parsed_line[1] == "end"):
			is_def = False

		elif(is_def):
			output_line = ""
			for word in parsed_line:
				if word in arguments:
					output_line = output_line + "_defvar_" + str(arguments.index(word)) + " "
				else:
					output_line = output_line + word + " "
			defs[current_def].code.append(output_line)

		elif(parsed_line[0] == "def"):
			if(parsed_line[1] == "mac"):
				if(parsed_line[2] in defs):
					ERROR("Definition \"" + parsed_line[1] + "\" already defined")
				mac_only = True
				current_def = parsed_line[2]
				arguments = parsed_line[3:]
			elif(parsed_line[1] == "fun"):
				if(parsed_line[2] in defs):
					ERROR("Definition \"" + parsed_line[1] + "\" already defined")
				fun_only = True
				current_def = parsed_line[2]
				arguments = parsed_line[3:]
			elif(parsed_line[1] in defs):
				ERROR("Definition \"" + parsed_line[1] + "\" already defined")
			else:
				current_def = parsed_line[1]
				arguments = parsed_line[2:]
			is_def = True
			defs[current_def] = CodeDefinition(current_def, [], mac_only, fun_only, len(arguments))

		else:
			output.append(update_line(line))

def macro_insert(macro, arguments, macro_list, chain_list, output):
	if(macro_list[macro].fun_only == True):
		ERROR(f"Definition \"{macro}\" can't be called as a macro")
	chain_list.append(macro)
	if(macro not in macro_list):
		ERROR("Macro \"" + macro + "\" undefined")
	for line in macro_list[macro].code:
		parsed_line = parse_line(line)
		output_line = ""
		for index in range(len(parsed_line)):
			word = parsed_line[index]
			if "_defvar_" in word:
				arg_index = int(word[8:])
				if(len(arguments) <= arg_index):
					ERROR("Macro \"" + macro + "\" needs more arguments")
				output_line += arguments[arg_index] + " "
			elif(word.endswith(":")):
				output_line += "_%s_%d_%s" % (macro, macro_list[macro].index, word)
			elif(parsed_line[0] == "jump" and index == 1):
				output_line += "_%s_%d_%s " % (macro, macro_list[macro].index, word)
			else:
				if(word.startswith("$")):
					output_line += word[1:] + " "
				elif(is_variable(parsed_line[0], word, index) and ENABLE_SCOPE):
					output_line += "_%s_%d_%s " % (macro, macro_list[macro].index, word)
				else:
					output_line += word + " "
		parsed_line = parse_line(output_line.strip("\t "))
		if(parsed_line[0] == "mac"):
			if(parsed_line[1] not in chain_list):
				macro_insert(parsed_line[1], parsed_line[2:], macro_list, chain_list, output)
			else:
				WARNING("macro \"" + parsed_line[1] + "\" tried to call itself... skipping")
		else:
			output.append(update_line(output_line))

	macro_list[macro].index += 1
	chain_list.pop()

def handle_macros(input, def_list, output):
	chain_list = []

	for line in input:
		parsed_line = parse_line(line)
		if(parsed_line[0] == "mac"):
			macro_insert(parsed_line[1], parsed_line[2:], def_list, chain_list, output)
		else:
			output.append(update_line(line))

def instruction_fun(parsed_line, output, called_functions_list, def_list):
	if(parsed_line[1] not in called_functions_list):
		called_functions_list.append(parsed_line[1])
	call_function(parsed_line[1], parsed_line[2:], output, def_list)

def function_get_io(def_list):
	for function in def_list:
		for line in def_list[function].code:
			parsed_line = parse_line(line)
			for i in range(len(parsed_line)):
				word = parsed_line[i]
				if "_defvar_" in word:
					arg_index = int(word[8:])
					def_list[function].argument_out_list[arg_index] = is_output(parsed_line[0], parsed_line[1], i)

def handle_functions(code, def_list, called_functions_list):
	code.append("end")
	for function in called_functions_list:
		add_function(function, def_list, code)

def call_function(function, arguments, output, def_list):
	if(function not in def_list):
		ERROR(f"Function \"{function}\" undefined")
	if(def_list[function].mac_only):
		ERROR(f"Definition \"{function}\" can't be called as a function")
	for i in range(len(arguments)):
		if(def_list[function].argument_out_list[i] == False):
			output.append(f"set $_fun_{function}_arg{i} {arguments[i]}")
	output.append(f"op add $_fun_{function}_callback @counter 1")
	output.append(f"jump $_fun_{function} always")
	for i in range(len(arguments)):
		if(def_list[function].argument_out_list[i] == True and not (is_number(arguments[i]) or is_string(arguments[i]) or is_enum(arguments[i]) or is_const(arguments[i]))):
			output.append(f"set {arguments[i]} $_fun_{function}_arg{i}")

def add_function(function, def_list, output):
	output.append(f"_fun_{function}:")
	for line in def_list[function].code:
		parsed_line = parse_line(line)
		output_line = ""
		for index in range(len(parsed_line)):
			word = parsed_line[index]
			if "_defvar_" in word:
				arg_index = int(word[8:])
				output_line += f"_fun_{function}_arg{arg_index} "
			elif(word.endswith(":")):
				output_line += f"_{function}_{word} "
			elif(parsed_line[0] == "jump" and index == 1):
				output_line += f"_{function}_{word} "
			else:
				if(word.startswith("$")):
					output_line += word[1:] + " "
				elif(is_variable(parsed_line[0], word, index) and ENABLE_SCOPE):
					output_line += f"_{function}_{word} "
				else:
					output_line += word + " "
		if(parsed_line[0] == "mac"):
			chain_list = []
			macro_insert(parsed_line[1], parsed_line[2:], def_list, chain_list, output)
		else:
			output.append(update_line(output_line))
	output.append(f"set @counter _fun_{function}_callback")

def find_includes(input, include_list):
	global SOURCE_FILE
	found_include_list = [SOURCE_FILE]
	include_index = 1
	find_includes_in_file(input, include_list, SOURCE_FILE, found_include_list)
	if(len(include_list) <= 1):
		return
	while True:
		file = open_file(include_list[include_index])
		find_includes_in_file(parse_file(file), include_list, include_list[include_index], found_include_list)
		if(len(include_list) == len(found_include_list)):
			break
		include_index += 1

def find_includes_in_file(file, include_list, current_file, found_include_list):
	for line in file:
		parsed_line = parse_line(line)
		if(parsed_line[0] == "include"):
			arg_len_check(parsed_line, 1)
			file_loc = current_file[:current_file.rfind("/")+1] + parsed_line[1]
			if(file_loc not in include_list):
				include_list.append(file_loc)
				found_include_list.append(current_file)

def find_consts(include_list, const_list):
	for file in include_list:
		for line in parse_file(open_file(file)):
			parsed_line = parse_line(line)
			if(parsed_line[0] == "const"):
				instruction_const(parsed_line, const_list)

def instruction_const(line, const_list):
	arg_len_check(line, 2)
	if(is_string(line[1]) or is_enum(line[1]) or is_number(line[1])):
		ERROR("Invalid constant '%s'" % line[1])
	if(line[1] in const_list):
		ERROR("Attempted to redefine constant \"%s\"" % line[1])
	const_list[line[1]] = line[2:]

def include_files(file_loc, def_list, include_list):
	global SOURCE_FILE
	for file_loc in include_list:
		if(file_loc != SOURCE_FILE):
			file = open_file(file_loc)
			output_code = []
			handle_basic_instructions(parse_file(file), output_code, file_loc)
			input_code = output_code
			output_code = []
			def_split(input_code, def_list, output_code)

def handle_const_op(input, output, const_var_list):
	for line in input:
		parsed_line = parse_line(line)
		output_line = ""
		if(parsed_line[0] == "cop"):
			arg_len_check(parsed_line, 3)
			if(len(parsed_line) >= 5):
				input1 = str(const_op_replace(parsed_line[3], const_var_list, parsed_line[0], 3))
				input2 = str(const_op_replace(parsed_line[4], const_var_list, parsed_line[0], 4))
				input1 = input1 if (input1 != "true") else "1"
				input1 = input1 if (input1 != "false") else "0"
				input2 = input2 if (input2 != "true") else "1"
				input2 = input2 if (input2 != "false") else "0"
				if(is_number(input1) and is_number(input2)):
					const_var_list[parsed_line[2]] = float(process_const_op(parsed_line[1], float(input1), float(input2)))
				else:
					WARNING("Attempted to use undefined input for 'cop', reverting to 'op'")
					output.append(line[1:])
			else:
				input1 = str(const_op_replace(parsed_line[3], const_var_list, parsed_line[0], 3))
				input1 = input1 if (input1 != "true") else 1
				input1 = input1 if (input1 != "false") else 0
				if(is_number(input1)):
					const_var_list[parsed_line[2]] = float(process_const_op(parsed_line[1], float(input1), 0))
				else:
					WARNING("Attempted to use undefined input for 'cop', reverting to 'op'")
					output.append(line[1:])
		else:
			i = 0
			while True:
				word = parsed_line[i]
				output_line += str(const_op_replace(word, const_var_list, parsed_line[0], i)) + " "
				i += 1
				if(i >= len(parsed_line)):
					output.append(output_line)
					break

def const_op_replace(input, const_var_list, instruction, index):
	if(is_variable(instruction, input, index)):
		if input in const_var_list:
			return(const_var_list[input])
		else:
			return(input)
	else:
		return(input)

def process_const_op(operation, a, b):
	match operation:
		case "add":
			return(a + b)
		case "sub":
			return(a - b)
		case "mul":
			return(a * b)
		case "div":
			return(a / b)
		case "idiv":
			return(a // b)
		case "mod":
			return(a % b)
		case "pow":
			return(pow(a,b))
		case "equal":
			return(a == b)
		case "notEqual":
			return(a != b)
		case "land":
			return(a and b)
		case "lessThan":
			return(a < b)
		case "lessThanEq":
			return(a <= b)
		case "greaterThan":
			return(a > b)
		case "greaterThanEq":
			return(a >= b)
		case "strictEqual":
			return(a == b)
		case "shl":
			return(int(a) << int(b))
		case "shr":
			return(int(a) >> int(b))
		case "or":
			return(int(a) | int(b))
		case "and":
			return(int(a) & int(b))
		case "xor":
			return(int(a) ^ int(b))
		case "not":
			return(~int(a))
		case "max":
			return(max(a, b))
		case "min":
			return(min(a, b))
		case "angle":
			return(math.degrees(math.atan2(a, b)))
		case "angleDiff":
			a = ((a % 360) + 360) % 360
			b = ((b % 360) + 360) % 360
			return(min(a - b + 360 if (a - b) < 0 else a - b, b - a + 360 if (b - a) < 0 else b - a))
		case "len":
			return(math.hypot(a, b))
		case "noise":
			WARNING("No noise idiot")
			return(0)
		case "abs":
			return(abs(a))
		case "log":
			return(math.log(a))
		case "log10":
			return(math.log10(a))
		case "floor":
			return(math.floor(a))
		case "ceil":
			return(math.ceil(a))
		case "sqrt":
			return(math.sqrt(a))
		case "rand":
			return(random.uniform(0,a))
		case "sin":
			return(math.sin(a))
		case "cos":
			return(math.cos(a))
		case "tan":
			return(math.tan(a))
		case "asin":
			return(math.asin(a))
		case "acos":
			return(math.acos(a))
		case "atan":
			return(math.atan(a))
		case _:
			ERROR("Unknown operation " + operation)

handle_args(sys.argv[1:])
try:
	input_file = open(SOURCE_FILE, "r")
except OSError:
	ERROR("Can't find file \"%s\"" % SOURCE_FILE)

output_code = []
include_list = [SOURCE_FILE]
const_list = {}

input_code = parse_file(input_file)

find_includes(input_code, include_list)

find_consts(include_list, const_list)

global_const_list = const_list
called_functions_list = []

temp_def_list = {}
def_get(input_code, temp_def_list)
function_get_io(temp_def_list)

handle_basic_instructions(input_code, output_code, SOURCE_FILE, called_functions_list, temp_def_list)



input_code = output_code
output_code = []
def_list = {}

def_split(input_code, def_list, output_code)
function_get_io(def_list)

include_files(include_list, def_list, include_list)

input_code = output_code
output_code = []

handle_macros(input_code, def_list, output_code)

input_code = output_code
output_code = []

handle_functions(input_code, def_list, called_functions_list)

const_var_list = {}

handle_const_op(input_code, output_code, const_var_list)

input_code = output_code
output_code = []

for line in input_code:
	line_output = ""
	for word in parse_line(line):
		line_output += word.lstrip("$") + " "
	output_code.append(line_output)


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
