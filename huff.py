def main():
    again = "y"
    while again in "yY":
        mode = "s"
        while mode not in "cCdD":
            mode = input("Would you like to (c)ompress or (d)ecompress? ")
        if mode in "cC":
            huffman_encode()
        else:
            huffman_decode()
        again = input("Would you like to go again? (y/n) ")

def huffman_encode():
    in_file = get_file()
    freqs = cnt_freq(in_file)
    out_file = input("Enter the output file: ")
    if len(freqs) == 0:
        open(out_file, "w")
    else:
        root = create_huff_tree(freqs)
        codes = root.get_tree_codes()
        bits = get_bits(in_file, codes)
        group_bits = group_by(bits)
        padded_bits = pad_bits(group_bits)
        byte_list = [int(bit, 2) for bit in padded_bits]
        header = root.tree_preord()
        write_encoded_file(header, byte_list, out_file) 

def huffman_decode():
    in_file = get_file()
    data = open(in_file, "rb").readlines()
    out_file = input("Enter the output file: ")
    if len(data) == 0:
        open(out_file, "w")
    else:
        (header, byte_list) = split_header(data)
        bit_str = make_bit_str(byte_list)
        root = tree_from_header(header)
        codes = root.get_tree_codes()
        translate_codes = invert(codes)
        write_decoded_file(bit_str, translate_codes, out_file)

def get_file():
    filename = input("Enter the input file: ")
    try:
        open(filename, "r")
        return filename
    except FileNotFoundError:
        print("ERROR: File not found")
        return get_file()

def cnt_freq(filename):
    in_file = open(filename, "r")
    count = {}
    for line in in_file:
        for char in line:
            char_code = ord(char)
            if char_code not in count:
                count[char_code] = 1
                last = char_code
            else:
                count[char_code] += 1
    in_file.close()
    if len(count) == 1 and ord("\n") in count:
        count = {}
    return count

def create_huff_tree(freqs):
    list_nodes = []
    for char_ascii in freqs:
        newnode = HuffmanNode(char_ascii, freqs[char_ascii])
        list_nodes = newnode.insert_sorted(list_nodes)
    while len(list_nodes) > 1:
        node1 = list_nodes.pop(0)
        node2 = list_nodes.pop(0)
        newnode = HuffmanNode(min(node1.char, node2.char), 
                              node1.occur + node2.occur, node1, node2)
        node1.parent = node2.parent = newnode
        list_nodes = newnode.insert_sorted(list_nodes)
    if len(list_nodes) == 1:
        return list_nodes.pop()
    return HuffmanNode()

def get_bits(filename, codes):
    in_file = open(filename, "r")
    bits = ""
    for line in in_file:
        for char in line:
            bits += codes[ord(char)]
    in_file.close()
    return bits

def group_by(string, every = 8):
    out = []
    tempstr = ""
    for bit in string:
        tempstr += bit
        if len(tempstr) == 8:
            out.append(tempstr)
            tempstr = ""
    out.append(tempstr)     
    return out

def pad_bits(bits):
    pad = 8 - len(bits[-1])
    bits[-1] += "0" * pad
    return ["{0:08b}".format(pad)] + bits

def get_header(freqs):
    header = ""
    for ascii_char in freqs:
        header += chr(ascii_char) + str(freqs[ascii_char])
    return header

def write_encoded_file(header, bits, filename):
    with open(filename, "w") as out_ascii:
        out_ascii.write(header)
        out_ascii.write("\n")
    with open(filename, "ab") as out_binary:
        out_binary.write(bytes(bits))

def split_header(file_data):
    header = []
    done = False
    idx = 0
    while not done and idx < len(file_data):
        line = file_data[idx]
        try:
            header.append(line.decode())
            idx += 1
        except UnicodeDecodeError:
            done = True
    if header[-1] == "\n":
        header.pop()
    else:
        header[-1] = header[-1][ : len(header[-1]) - 1]
    return ("".join(header), file_data[idx : ])

def make_bit_str(byte_list):
    decoded = [byte for line in byte_list for byte in line]
    pad = decoded.pop(0)
    bit_list = [int_to_bit(byte) for byte in decoded]
    bit_str = "".join(bit_list)
    return bit_str[ : len(bit_str) - pad]

def int_to_bit(base_10, new_base = 2):
    bits = ""
    while base_10 > 0:
        bits += str(base_10 % new_base)
        base_10 //= new_base
    return "0" * (8 - len(bits)) + bits[ : : -1]

def tree_from_header(header):
    idx = 1
    root = HuffmanNode()
    current = root
    while idx < len(header):
        if current.right and current.left:
            current = current.parent
        elif current.has_no_children():
            current.left = HuffmanNode(parent = current)
            if header[idx] == "0":
                current = current.left
            elif header[idx] == "1":
                idx += 1
                current.left.char = ord(header[idx])
            idx += 1
        else:
            current.right = HuffmanNode(parent = current)
            if header[idx] == "0":
                current = current.right
            elif header[idx] == "1":
                idx += 1
                current.right.char = ord(header[idx])
            idx += 1
    return root

def invert(dictionary):
    inverted = {}
    for ascii_code in dictionary:
        inverted[dictionary[ascii_code]] = chr(ascii_code)
    return inverted

def write_decoded_file(bits, codes, filename):
    with open(filename, "w") as out:
        temp = ""
        for bit in bits:
            temp += bit
            if temp in codes:
                out.write(codes[temp])
                temp = ""


class HuffmanNode:

    def __init__(self, char = None, occur = None, left = None, right = None, parent = None):
        self.char = char
        self.occur = occur
        self.left = left
        self.right = right
        self.parent = parent

    def insert_sorted(self, tlist):
        idx = 0
        before = False
        while idx < len(tlist) and not before:
            node = tlist[idx]
            if self.comes_before(node):
                before = True
            else:
                idx += 1
        tlist.insert(idx, self)
        return tlist

    def comes_before(self, other):
        if self.occur == other.occur:
            return self.char < other.char
        else:
            return self.occur < other.occur
    
    def get_tree_codes(self):
        codes = {}
        path = []
        checked = []
        current = self
        done = False
        while not done:
            checked.append(current)
            if current != self and current.has_no_children():
                codes[current.char] = "".join(path)
                current = current.parent
                path.pop()
            else:
                if current.left and current.left not in checked:
                    current = current.left
                    path.append("0")
                elif current.right and current.right not in checked:
                    current = current.right
                    path.append("1")
                else:
                    if current.parent:
                        current = current.parent
                        path.pop()
                    else:
                        done = True
        return codes

    def tree_preord(self):
        header = ""
        checked = []
        current = self
        done = False
        while not done:
            checked.append(current)
            if current != self and current.has_no_children():
                header += "1" + chr(current.char)
                current = current.parent
            else:
                if current.left and current.left not in checked:
                    current = current.left
                    header += "0"
                elif current.right and current.right not in checked:
                    current = current.right
                else:
                    if current.parent:
                        current = current.parent
                    else:
                        done = True
        return header

    def has_no_children(self):
        return not self.right and not self.left


if __name__ == "__main__":
    main()
