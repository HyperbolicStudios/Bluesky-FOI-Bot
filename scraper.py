import cloudscraper
import json

url_search_paths = [
    "https://www2.gov.bc.ca/gov/search?id=9199E7BC9682482EB9EA0B6D6B8D386C&q=ALL%2Binmeta%3Adc.contributor%3DTransportation+and+Transit&tab=1&page=1",
    "https://www2.gov.bc.ca/gov/search?id=9199E7BC9682482EB9EA0B6D6B8D386C&q=ALL%2Binmeta%3Adc.contributor%3DTransportation+and+Infrastructure&tab=1&page=1"]

def scrape():
    foi_objects = []
    scraper = cloudscraper.create_scraper()
    for url_search_path in url_search_paths:
        for depth in range(1, 2):
            url_search_path = url_search_path[:-1] + str(depth)
            response = scraper.get(url_search_path).text

            #extract everything after the last <script> tag
            response = response.split("<script")[-1]

            #delete everything before, and including, the first ">" char
            response = response[response.find(">")+1:]

            #delete everything after the last "}" char
            response = response[:response.rfind("}")+1]

            #convert response to a dictionary
            #if this fails, no more pages to scrape - break loop and move on to next url_search_path
            try:
                response = json.loads(response)
            except:
                break

            # Function to recursively search for any objects containing a fields sub-object
            def find_foi_requests(obj, key="fields"):
                results = []
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if k == key:
                            results.append(obj)  # Store the entire object containing the match
                        else:
                            results.extend(find_foi_requests(v, key))  # Recurse into the value
                elif isinstance(obj, list):
                    for item in obj:
                        results.extend(find_foi_requests(item, key))  # Recurse into each list item
                return results
            
            has_fields = find_foi_requests(response)
            
            is_FOI = []
            for i in has_fields:
                try:
                    if i['fields'][0]['name'] == 'recordUid':
                        is_FOI.append(i['fields'])
                except:
                    pass
            
            #clean FOI objects, append to main list to be returned
            for i in is_FOI:
                foi_objects.append({
                    "Record_UID": i[0]['value'],
                    "search_ID": i[1]['value'],
                    "perm_URL": i[3]['value'],
                    "Name": i[4]['value'],
                    "Description": i[5]['value'],
                    "starred": False
                })
            
    return foi_objects