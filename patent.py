import requests
import random
import sys

BICYCLE_SUBSECTION = "B62"

# Get a random patent in the given subsection. Returns a string of the patent's number.
def getPatent(subsection): 
    # First try with a random result number between 1 and 1,000,000.
    address = assembleQueryAddress(subsection, random.randint(1,1000000))

    # Assuming the presence of certain fields, which are looked for in the sendRequest function.
    # If there are no patents, try again using the patent count as the upper bound on page number.
    ok_response = sendRequest(address)
    if ok_response['patents'] is None: 
        print("no luck on the first pass")
        patent_count = ok_response['total_patent_count']
        if patent_count < 1: 
            print("total patent count is too low: " + str(patent_count))
            print("exiting")
            sys.exit()
        address = assembleQueryAddress(subsection, random.randint(1, patent_count))
        print("retrying with informed random page number")
        ok_response = sendRequest(address)
        if ok_response['patents'] is None:
            print("No luck the second time, exiting")
            sys.exit()
    
    return extractPatentNumberString(ok_response['patents'])

def extractPatentNumberString(patents_list):
    # expecting this to have length 1
    if len(patents_list) < 1:
        print("patents list has length 0, unexpectedly - exiting")
        sys.exit()
    patent = patents_list[0]
    if 'patent_number' not in patent.keys():
        print("can't find patent_number field, exiting")
        sys.exit()
    return patent['patent_number']


def sendRequest(address):
    response = requests.get(address)
    if response.status_code != 200:
        print("Response code is not 200!")
        print("status code: " + str(response.status_code))
        print("text: " + response.text)
        print("exiting")
        sys.exit()

    response_json = response.json()
    if 'patents' not in response_json.keys() or 'total_patent_count' not in response_json.keys():
        print("Unexpected response format!")
        print("exiting")
        sys.exit()
    return response_json

def assembleQueryAddress(subsection, page_number):
    base = "http://www.patentsview.org/api/patents/query?"
    query = "q={\"cpc_subsection_id\":\"" + subsection + "\"}"
    return_fields = "f=[\"patent_number\"]"
    
    # Use the passed-in page number with a per_page count of 1.
    # We can't request all on 1 page and pick randomly from whole
    # set of responses because there seems to be an upper limit of 
    # 10,000 on the per_page value.
    options = "o={\"page\":" + str(page_number) + ",\"per_page\":1}"

    return base + query + "&" + return_fields + "&" + options

def assemblePdfUrl(patent_number_string, patent_page_number):
    num_len = len(patent_number_string) 
    if num_len < 6:
        print("patent number is less than 6 digits, doesn't fit the expected pattern - exiting")
        sys.exit()

    base = "http://pdfpiw.uspto.gov/"
    first = patent_number_string[-2:] 
    second = patent_number_string[-5:-2]
    third = ''.join(["0" for i in range(8-num_len)]) + patent_number_string[-num_len:-5]
    
    url = base + "/".join([first, second, third, str(patent_page_number)]) + ".pdf"
    print("assembled pdf url: " + url)
    return url

def downloadPdf(url, file_name):
    print("attempting to dowload pdf")
    response = requests.get(url)
    if response.status_code != 200:
        print("Response code is not 200!")
        print("status code: " + str(response.status_code))
        print("text: " + response.text)
        print("exiting")
        sys.exit()
    print("response code is 200")

    # should maybe validate file name, and/or specify full path
    fp = open(file_name, 'wb')
    fp.write(response.content)
    fp.close()
    
    print("wrote pdf to file: " + file_name)

if __name__ == '__main__':
    patent_number = getPatent(BICYCLE_SUBSECTION)

    # 2 seems to usually work as the first image page of the patent document,
    # though sometimes it's just text.
    page_number = 2
    file_names = sys.argv[1:]
    for name in file_names:
        pdf_url = assemblePdfUrl(patent_number, page_number)
        downloadPdf(pdf_url, name)
        page_number += 1
