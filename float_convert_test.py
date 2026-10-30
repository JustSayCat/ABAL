# 8 digits max, that is including a decimal point
# if it is negative an A will be used at the start
# if there is a decimal a D will represent the dot where it should go

# Display steps:
# 1. truncate the float to get the whole part
# 2. using the truncation subtract from the original float to get the fractional part
# 3. Determin if the float is negative, if so output the negative character
# 4. using mod 10, div 10 output the whole part
# 5. reverse the whole part
# 6. output a period
# 7. using mul 10, mod 10, output the fractional part (no need to reverse it)
# Checks:
# At each out, check if we are at 8 digits, if we are stop
# when doing the mod 10, div 10 or mul 10, mod 10 methods if the number is zero stop there (obv)
# When starting 3 if the number is 0, output 0
# When starting 6, if the number is 0 just stop

# This will require, mod with floats, div with floats and mul with floats, fun...

def trunc_float(value):
    sign = (value&(1<<31))>>31
    exponent = (value&(0b11111111<<23))>>23
    mantissa = value&(0b11111111111111111111111)|(1<<23)
    true_exponent = exponent-127
    if true_exponent <= 0:
        return 0
    if true_exponent-23 >= 0:
        return value
    shift_amount = 23-true_exponent
    mantissa = (mantissa>>shift_amount)<<shift_amount
    return (sign<<31)|(exponent<<23)|(mantissa&0b11111111111111111111111)

def bit32(value):
    current = str(value)[2:]
    if len(current) == 32:
        return current
    else:
        padding = 32-len(current)
        return "0"*padding+current

def add_float(value1, value2):
    f1_sign = (value1&(1<<31))>>31
    f1_exponent = (value1&(0b11111111<<23))>>23
    f1_mantissa = value1&(0b11111111111111111111111)|(1<<23)
    f2_sign = (value2&(1<<31))>>31
    f2_exponent = (value2&(0b11111111<<23))>>23
    f2_mantissa = value2&(0b11111111111111111111111)|(1<<23)
    if f1_exponent < f2_exponent:
        difference = f2_exponent-f1_exponent
        f1_exponent = f2_exponent
        f1_mantissa = f1_mantissa>>difference
    else:
        difference = f1_exponent-f2_exponent
        f2_exponent = f1_exponent
        f2_mantissa = f2_mantissa>>difference
    if f1_sign > 0:
        f1_mantissa = -f1_mantissa
    if f2_sign > 0:
        f2_mantissa = -f2_mantissa
    num = f1_mantissa+f2_mantissa
    if num == 0:
        return 0
    num, f1_exponent = shift_mantissa(num, f1_exponent)
    num_sign = 1<<31 if num < 0 else 0
    return num_sign|f1_exponent<<23|(num&0b11111111111111111111111)

def shift_mantissa(mantissa, exponent):
    num = mantissa
    f1_exponent = exponent
    while num-0b11111111111111111111111 > 0:
        num = num>>1
        f1_exponent = f1_exponent+1
    while num&0b1_00000000000000000000000 == 0:
        num = num<<1
        f1_exponent = f1_exponent-1
    return num, f1_exponent

def sub_float(value1, value2):
    neg_v2 = value2^(1<<31)
    return add_float(value1, neg_v2)

# We have already made int division before, but we need a modified version of it to work, but that is easy to make
def div_float(value1, value2):
    f1_sign = (value1&(1<<31))>>31
    f1_exponent = (value1&(0b11111111<<23))>>23
    f1_mantissa = value1&(0b11111111111111111111111)|(1<<23)
    f2_sign = (value2&(1<<31))>>31
    f2_exponent = (value2&(0b11111111<<23))>>23
    f2_mantissa = value2&(0b11111111111111111111111)|(1<<23)
    out_sign = f1_sign^f2_sign
    out_mantissa = float_int_div(f1_mantissa, f2_mantissa)
    out_exponent = f1_exponent-f2_exponent+127
    return out_sign<<31|out_exponent<<23|out_mantissa&(0b11111111111111111111111)

def float_int_div(mantissa1, mantissa2):
    operated = mantissa1
    divisor = mantissa2
    quotient = 0
    for _ in range(23):
        if operated > divisor:
            operated -= divisor
            quotient += 1
        operated = operated<<1
        quotient = quotient<<1
    return quotient

def mul_float(value1, value2):
    f1_sign = (value1&(1<<31))>>31
    f1_exponent = (value1&(0b11111111<<23))>>23
    f1_mantissa = value1&(0b11111111111111111111111)|(1<<23)
    f2_sign = (value2&(1<<31))>>31
    f2_exponent = (value2&(0b11111111<<23))>>23
    f2_mantissa = value2&(0b11111111111111111111111)|(1<<23)
    out_sign = f1_sign^f2_sign
    out_mantissa = float_int_mul(f1_mantissa, f2_mantissa)
    out_exponent = f1_exponent+f2_exponent-127
    out_mantissa, out_exponent = shift_mantissa(out_mantissa, out_exponent)
    return out_sign<<31|out_exponent<<23|out_mantissa&(0b11111111111111111111111)

def float_int_mul(mantissa1, mantissa2):
    output = 0
    for i in range(32):
        if mantissa2&(1<<i) != 0:
            output += mantissa1<<i
    return output>>23

def eq_float(value, compare):
    if sub_float(value, compare) == 0:
        return True
    return False

def float_to_int(value):
    sign = (value&(1<<31))>>31
    exponent = (value&(0b11111111<<23))>>23
    mantissa = value&(0b11111111111111111111111)|(1<<23)
    if sign == 1:
        shift = exponent-127-23
        if shift < 0:
            return -(mantissa>>(abs(shift)))
        return -(mantissa<<(abs(shift)))
    else:
        shift = exponent-127-23
        if shift < 0:
            return mantissa>>(abs(shift))
        return mantissa<<(abs(shift))

def float_to_str(value):
    sign = (value&(1<<31))>>31
    value = value&~(1<<31)
    whole_part = trunc_float(value)
    fract_part = sub_float(value, whole_part)
    out_str = ""
    while not eq_float(whole_part, 0):
        next_num = trunc_float(div_float(whole_part, 0b01000001001000000000000000000000)) # 10
        next_digit = sub_float(whole_part, mul_float(next_num, 0b01000001001000000000000000000000)) # 10
        whole_part = next_num
        out_str += str(float_to_int(next_digit))
    out_str = out_str[::-1]
    if sign > 0:
        out_str = "-" + out_str
    if eq_float(fract_part, 0):
        return out_str
    out_str += "."
    while not eq_float(fract_part, 0) and len(out_str) < 8:
        fract_part = mul_float(fract_part, 0b01000001001000000000000000000000) # 10
        next_whole = trunc_float(fract_part)
        fract_part = sub_float(fract_part, next_whole)
        out_str += str(float_to_int(next_whole))
    return out_str


float_value = 0b01000000110011000101001001010001 
# 6.385048389434814453125
# 6.38504838943480144530125
print(float_to_str(float_value))
    
    