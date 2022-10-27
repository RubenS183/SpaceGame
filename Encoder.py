import random

def encode(message):
    code = ''
    hash = random.randint(1,99)
    count = 0
    for i in message:
        code += chr(ord(i) + hash + (count % hash))
        count += 1
        
    code = str(hash//10) + code + str(hash%10)

    return code
    
def decode(code):
    hash = int(code[-1]) + int(code[0]) * 10
    code = code[1:-1]
    message = ''
    count = 0
    for i in code:
        message += chr(ord(i) - hash - (count % hash))
        count += 1

    return message

if __name__ == '__main__':
    while 1:
        print(encode(input('Encode: ')))
        print(decode(input('Decode: ')))
