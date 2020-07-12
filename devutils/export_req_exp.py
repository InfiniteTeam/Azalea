import json

ls = {}
num = 0
print("레벨업 요구 경험치를 입력하세요. 다음 레벨을 입력하려면 줄바꿈하세요. 입력이 완료되었으면 'end' 를 입력하세요.")
while True:
    num += 1
    print(f'레벨 {num}의 요구 경험치 입력')
    ipt = input()
    if ipt == 'end':
        break
    else:
        ls[num] = int(ipt.replace(',', ''))

with open('opt.json', 'w', encoding='utf-8') as f:
    json.dump(ls, f)

print('opt.json 에 저장됨')