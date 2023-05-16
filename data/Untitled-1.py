
params = [10]
for ft in [11,12,13,14]: 
    params.append(ft)

print(params)

params = list([10]).extend([ft for ft in [11,12,13,14]])

print(params)

