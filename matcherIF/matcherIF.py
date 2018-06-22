import csv
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import sys
import re

def sanitise(row):
	for x in row:
		row[x] = str(row[x]).replace('%','')
		row[x] = str(row[x]).replace('$','')
		row[x] = str(row[x]).replace(',','')
		row[x] = str(row[x]).replace('.00','')
		row[x] = str(row[x]).strip()
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
companies = {}
titles = {}

#builds dict of dicts (required as each row needs a unique identifier)
with open('ratecity.csv', encoding='utf-8-sig') as ratecity:
	reader = csv.DictReader(ratecity)
	for row in reader:
		ratecityList.update({row['variationuuid']:row})

with open('infochoice.csv', encoding='utf-8-sig') as infochoice:
	reader = csv.DictReader(infochoice)
	for row in reader:
		#sanitisation
		row['Name'] = nameBuilder(row)
		row = sanitise(row)
		infochoiceList[row['CodeID']] = row

with open('companies.csv', encoding='utf-8-sig') as company:
	reader = csv.DictReader(company)
	for row in reader:
		companies.update({row['infochoice']:row['ratecity']})

with open('titles.csv', encoding='utf-8-sig') as toot:
	reader = csv.DictReader(toot)
	for row in reader:
		titles.update({row['RC']:row['IF']})

#if matched csv is prepped
if len(sys.argv) > 1:
	if sys.argv[1] == "matched.csv":
		matchedList = {}
		with open('matched.csv', encoding='utf-8-sig') as matched:
			reader = csv.DictReader(matched)
			for row in reader:
				matchedList.update({row['rc_code']:row['if_code']})

		with open('fullmatch.csv', 'w+', newline='', encoding='utf-8-sig') as matcher:
			csvwriter = csv.writer(matcher, delimiter=',')
			headings = list(titles.keys())
			headings.append("IF Code")
			headings.append("IF Product")
			print(headings)
			csvwriter.writerow(headings)
			for key, varRC in ratecityList.items():	
				if key in matchedList.keys() and matchedList[key] != '0':
					line = []
					for titleRC, titleIF in titles.items():
						if titleRC == 'companyname' or titleRC == 'variationname' or titleRC == 'variationuuid':
							line.append(varRC[titleRC])
						else:
							if str(ratecityList[key][titleRC]).lower() == str(infochoiceList[matchedList[key]][titleIF]).lower():
								line.append('MATCH')
							else:
								line.append(str(ratecityList[key][titleRC])+' vs '+str(infochoiceList[matchedList[key]][titleIF]))
					line.append(matchedList[key])
					line.append(infochoiceList[matchedList[key]]["Name"])
					#print(line)
					csvwriter.writerow(line)
	else:
		print("invalid argument")

#first time string matching
else:	
	for varRC in ratecityList.values():
		oldFuzz = 0
		varRC['fuzzToken'] = 0
		varRC['matchIF'] = 0
		varRC['codeIF'] = 0
		for varIF in infochoiceList.values():
			if varIF['Company'] in companies.keys():
				if (varRC['companyname'] == companies[varIF['Company']]
				and varRC['homeloantype'] == varIF['Home Loan Type']
				and ((varRC['hasowneroccupiedpurpose'] == varIF['hasowneroccupied']) or (varRC['hasinvestmentpurpose'] == varIF['hasinvestment']))):	
					fuzzToken = fuzz.token_sort_ratio(varRC['variationname'], varIF['Name'])
					if fuzzToken > 0 and fuzzToken > oldFuzz:
						varRC['fuzzToken'] = fuzzToken
						varRC['matchIF'] = varIF['Name']
						varRC['codeIF'] = varIF['CodeID']
						oldFuzz = fuzzToken
						#print(varRC['matchIF'])

	with open('matcher.csv', 'w+', newline='', encoding='utf-8-sig') as matcher:
		csvwriter = csv.writer(matcher, delimiter=',')
		csvwriter.writerow(["RC Code", "Ratecity", "IF Code", "Infochoice"])
		for key, varRC in ratecityList.items():
			csvwriter.writerow([key, varRC['Company Name + Variation Name'], varRC['codeIF'], varRC['matchIF']])
