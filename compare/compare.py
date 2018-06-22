import csv
import sys
import re

##README
#Rum program by;
#python compare.py ARGUMENT
#where ARGUMENT is the name of the ratecity header field to be compared i.e. isextrarepaymentallowed

#General sanitisation of csv data input by removing symbols
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

#Sanitisation of Mozo data
def sanitiseMZ(row, beta):
	#Make all ID's unique by appending fixed months
	if row[beta] == str(0):
		row[beta] = row['Product ID']
	else:
		row[beta] = re.sub(r'[A-Za-z\s]', '', row[beta])
	#Sanitisation of True/False columns
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

#Sanitisation of Infochoice Data, creating new True/False fields
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

#setting up dictionary data structures for csv storage - can potentially be improved by using dataframes instead
#csv data is read as dict of dicts with rows using ID as keys	
ratecityList = {}
infochoiceList = {}
mozoList = {}
companies = {}
titles = {}
codeMatch  = {}

#Reading in ratecity csv data -- Input is data dump of HL data from Tableau
with open('ratecity.csv', encoding='utf-8-sig') as ratecity:
	reader = csv.DictReader(ratecity)
	for row in reader:
		row['rate'] = float(row['rate'])
		ratecityList.update({row['variationuuid']:row})

#Reading in infochoice csv data -- Input is from infochoice.py crawl results
with open('infochoice.csv', encoding='utf-8-sig') as infochoice:
	reader = csv.DictReader(infochoice)
	for row in reader:
		#sanitisation
		row = sanitise(row)
		row = sanitiseIF(row)
		row['Rate'] = float(row['Rate'])
		infochoiceList[row['CodeID']] = row

#Reading in mozo csv data -- Input is from mozo.py crawl results
with open('mozo.csv', encoding='utf-8-sig') as mozo:
	reader = csv.DictReader(mozo)
	for row in reader:
		#sanitisation
		row = sanitise(row)
		row = sanitiseMZ(row, "Variation ID")
		row['Interest Rate'] = float(row['Interest Rate'])
		print(float(row['Interest Rate']))
		mozoList[row['Variation ID']] = row

#Reading in companies csv which is used to name-match different spellings of company together -- csv was created manually
with open('companies.csv', encoding='utf-8-sig') as company:
	reader = csv.DictReader(company)
	for row in reader:
		companies[row['ratecity']] = row

#Reading in titles csv which is used to name-match different column heading spellings together -- csv was created manually
with open('titles.csv', encoding='utf-8-sig') as toot:
	reader = csv.DictReader(toot)
	for row in reader:
		titles[row['RC']] = row

#Reading in matched csv which specifies which product ids are confirmed to match between RC/IF/MZ datasets -- csv was created manually
with open('matched.csv', encoding='utf-8-sig') as tootie:
	reader = csv.DictReader(tootie)
	for row in reader:
		row["mz_code"] = re.sub(r'[A-Za-z\s]', '', row["mz_code"])
		codeMatch[row['rc_code']] = row

#Argument parsing
if len(sys.argv) != 2 or sys.argv[1] not in titles.keys():
	print("Invalid arguments. Please give name of ratecityList field as argument.")
else:
	field = sys.argv[1]
	name = field+".csv"
	#opens new csv to write output with input argument as name. Throws permission error if existing file with same name is already open. 	
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
	