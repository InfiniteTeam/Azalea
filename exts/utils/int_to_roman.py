def int_to_Roman(num):
   val = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
   syb = ('Ⅿ',  'ⅭⅯ', 'Ⅾ', 'ⅭⅮ','Ⅽ', 'ⅩⅭ','Ⅼ','ⅩⅬ','Ⅹ','ⅠⅩ','Ⅴ','ⅠⅤ','Ⅰ')
   roman_num = ""
   for i in range(len(val)):
      count = int(num / val[i])
      roman_num += syb[i] * count
      num -= val[i] * count
   return roman_num

#다쿤 바보
