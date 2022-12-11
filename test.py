lorem_ipsum = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Donec imperdiet velit et hendrerit efficitur. Pellentesque tristique lorem et tellus pulvinar, eget volutpat nisi accumsan. Phasellus sagittis varius ipsum id convallis. Nunc et metus quis tortor lacinia posuere eget et dolor. In ligula urna, faucibus ac facilisis eu, consectetur quis nibh. Maecenas euismod mauris eget est lacinia, sit amet interdum diam gravida. Nulla ac ornare dolor, eu rutrum magna."""
short_text = "this is a short line of text"


def split_string(line:str, length:int=70):

    if len(line) <= length:
        tmp_list = [line.strip()]
        return tmp_list

    else:
        all_indexes = [x for x, v in enumerate(line) if v == ' ']
        short_indexes = list(filter(lambda index: index <= length, all_indexes))
        max_space = max(short_indexes)
        short_line = [line[:max_space]]
        remainder = line[max_space:].strip()
        short_line.extend(split_string(remainder))
        return short_line
        

# fmt = split_string(line=lorem_ipsum, length=70)
fmt = split_string(line=short_text, length=70)

print(fmt)
# for line in fmt:
#     print(line)