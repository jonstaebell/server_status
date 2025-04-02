server_addr = ['alpha', 'bravo', 'charlie']
server_name = ['phi', 'beta', 'kappa']
param_dict={}
new_dict = {}

for i in range(0,len(server_addr)):
    new_dict[server_addr[i]] = server_name[i]

print (new_dict)