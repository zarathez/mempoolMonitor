from foundrycli import foundry_cli

def calldata_decoder(byte_series):
    command = f'cast 4byte-decode {byte_series}'
    result = foundry_cli(command)
    return result
def pretty_calldata(byte_series):
    command = f'cast pretty-calldata {byte_series}'
    result = foundry_cli(command)
    return result



if __name__ == "__main__":
    byte_series = "0xf305d7190000000000000000000000009b883483c8a54eb0c3093b330f9b583b1783131d0000000000000000000000000000000000000000033a42f31f3f6bea83e000000000000000000000000000000000000000000000033a42f31f3f6bea83e000000000000000000000000000000000000000000000000000000b1a2bc2ec500000000000000000000000000000b18700fbb9cbd2bebc9c7472bb72cd9c058469670000000000000000000000000000000000000000000000000000000066a4dd37"
    output = calldata_decoder(byte_series)
    print(output)
    print(output['matches'][0]['argument1'])


    
