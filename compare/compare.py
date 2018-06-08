import csv
import sys
import re

def sanitise(row):
	for x in row:
		row[x] = str(row[x]).replace('%','')
		row[x] = str(row[x]).replace('$','')
		row[x] = str(row[x]).replace(',','')
		row[x] = str(row[x]).replace('.00','')
		row[x] = str(row[x]).replace('n/a','0')
		row[x] = str(row[x]).replace('N/A','0')
		row[x] = str(row[x]).strip()
	return row

def sanitiseMZ(row, beta):
	#sanitise take id and attach fixed term year bit
	if row[beta] == str(0):
		row[beta] = row['Product ID']
	else:
		row[beta] = re.sub(r'[A-Za-z\s]', '', row[beta])
	if 'yes' in row['Extra repayments']:
		row['Extra Repayments'] = "TRUE"
	else:
		row['Extra Repayments'] = "FALSE"

	if 'yes' in row['Offset account']:
		row['Offset account'] = "TRUE"
	else:
		row['Offset account'] = "FALSE"
	
	if 'yes' in row['Redraw facility']:
		row['Redraw facility'] = "TRUE"
	else:
		row['Redraw facility'] = "FALSE"
	
	return row

def sanitiseIF(row):
	if 'Owner' in row['Availability']:
		row['hasowneroccupied'] = 'True'
	else:
		row['hasowneroccupied'] = 'False'
	if 'Invest' in row['Availability']:
		row['hasinvestment'] = 'True'
	else:
		row['hasinvestment'] = 'False'
	
	if 'Principal' in row['Repayment Options']:
		row['hasprincipal'] = 'True'
	else:
		row['hasprincipal'] = 'False'
	if 'Only' in row['Repayment Options']:
		row['hasinterest'] = 'True'
	else:
		row['hasinterest'] = 'False'

	if 'Week' in row['Repayment Frequency']:
		row['hasweekly'] = 'True'
	else:
		row['hasweekly'] = 'False'
	if 'Fortnight' in row['Repayment Frequency']:
		row['hasfortnightly'] = 'True'
	else:
		row['hasfortnightly'] = 'False'
	if 'Month' in row['Repayment Frequency']:
		row['hasmonthly'] = 'True'
	else:
		row['hasmonthly'] = 'False'

	search = re.match('([0-9]+)', row['Fixed Months'])
	row['Fixed Months'] = int(search.group(1))*12
	return row

def nameBuilder(row):
	name = row['Company']+' - '+row['Product']
	if row['Fixed Months'] != '0':
		name = name+' '+str(row['Fixed Months'])
	if 'Principal' not in row['Product'] and row['Repayment Options'] == 'Principal & Interest':
		name = name+' '+'Principal & Interest'
	if 'Only' not in row['Product'] and row['Repayment Options'] == 'Interest Only':
		name = name+' '+'Interest Only'
	if "Invest" not in name and "Invest" in row['Availability']:
		name = name+' '+'Investment'
	return name

ratecityList = {}
infochoiceList = {}
mozoList = {}
companies = {}
titles = {}
codeMatch  = {}

#builds dict of dicts (required as each row needs a unique identifier)
with open('ratecity.csv', encoding='utf-8-sig') as ratecity:
	reader = csv.DictReader(ratecity)
	for row in reader:
		row['rate'] = float(row['rate'])
		#print(type(row['extrarepaymentsallowed']))
		ratecityList.update({row['variationuuid']:row})

with open('infochoice.csv', encoding='utf-8-sig') as infochoice:
	reader = csv.DictReader(infochoice)
	for row in reader:
		#sanitisation
		row['Name'] = nameBuilder(row)
		row = sanitise(row)
		row = sanitiseIF(row)
		row['Rate'] = float(row['Rate'])
		#print(float(row['Rate']))
		infochoiceList[row['CodeID']] = row

with open('mozo.csv', encoding='utf-8-sig') as mozo:
	reader = csv.DictReader(mozo)
	for row in reader:
		#sanitisation
		row = sanitise(row)
		row = sanitiseMZ(row, "Variation ID")
		row['Interest Rate'] = float(row['Interest Rate'])
		print(float(row['Interest Rate']))
		mozoList[row['Variation ID']] = row

with open('companies.csv', encoding='utf-8-sig') as company:
	reader = csv.DictReader(company)
	for row in reader:
		companies[row['ratecity']] = row

with open('titles.csv', encoding='utf-8-sig') as toot:
	reader = csv.DictReader(toot)
	for row in reader:
		titles[row['RC']] = row

with open('matched.csv', encoding='utf-8-sig') as tootie:
	reader = csv.DictReader(tootie)
	for row in reader:
		row["mz_code"] = re.sub(r'[A-Za-z\s]', '', row["mz_code"])
		codeMatch[row['rc_code']] = row

if len(sys.argv) != 2 or sys.argv[1] not in titles.keys():
	print("Invalid arguments. Please give name of ratecityList field as argument.")
else:
	field = sys.argv[1]
	name = field+".csv"	
	with open(name, 'w+', newline='', encoding='utf-8-sig') as matcher:
		csvwriter = csv.writer(matcher, delimiter=',')
		csvwriter.writerow(['rc_id','if_id','mz_id','company','variationname','rc_value','other_value'])
		for keyRC, row in ratecityList.items():
			if keyRC in codeMatch.keys():	
				keyIF = codeMatch[keyRC]['if_code']
				keyMZ = codeMatch[keyRC]['mz_code']
				if keyIF == "0" or keyMZ == "0":
					continue
				if infochoiceList[keyIF][titles[field]['IF']] == mozoList[keyMZ][titles[field]['MZ']] != row[field]:
					print(row[field])
					print(row['companyname']+" "+row['variationname'])
					line = [keyRC, keyIF, keyMZ, row['companyname'], row['variationname']]
					line.append(row[field])
					line.append(infochoiceList[keyIF][titles[field]['IF']])
					csvwriter.writerow(line)
	print("Success! compare.csv has been generated based on the field: "+field)
	