import requests
from pprint import pprint
from bs4 import BeautifulSoup
from tqdm import tqdm
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select

def getCourses():
    departments = getDepartmentShortNames()
    # oldDepartments = ["AEE", "BUSMGT", "CHBE"]
    page = requests.get("https://osuprofs.com/search/?search=+")
    soup = BeautifulSoup(page.content, 'html.parser')
    all_courses = soup.find_all(name="a", attrs={"class": "list-group-item list-group-item-action"})

    # print(all_courses[0].contents[0].strip()) # how to get class dept + number
    # print(all_courses[0].contents[1].contents[0].strip()) # how to get class official name

    model = "search.course"
    list_of_courses = []

    # name, department, number, description
    counter = 1
    for course in all_courses:
        pk = counter
        department_and_number = course.contents[0].strip()
        if department_and_number == "CSE SP 22":
            continue
        # print(department_and_number)
        if len(course.contents) < 3 or len(course.contents[1].contents) < 1:
            name = department_and_number
        else:
            # print(course.contents[1])
            name = course.contents[1].contents[0].strip()
        dept, number = department_and_number.split(" ")
        if dept not in departments:
            continue
        description = "description"
        fields = {"name": name, "department": [dept], "number": number, "description": description}
        fixture_item = {"model": model, "pk": pk, "fields": fields}
        list_of_courses.append(fixture_item)
        counter += 1

    return list_of_courses

# instructor is a tuple: (first_name, last_name, department)
# list_of_instructors is a list of instructor tuples
def isInstructorUnique(list_of_instructors, instructor):
    for i in list_of_instructors:
        if i[0] == instructor[0] and i[1] == instructor[1] and i[2] == instructor[2]:
            return False
    return True


def getProfessors(limit=10000):
    courses = getCourses()

    base_url = "https://osuprofs.com/courses/"
    
    counter = 0

    # used for isInstructorUnique
    set_of_instructors = set()

    # used to return (list of dictionaries)
    list_of_professors = []
    # make a progress bar for this for loop
    for course in tqdm(courses):
        if counter == limit:
            break
        fields = course["fields"]
        dept = fields["department"][0]
        number = fields["number"]

        url = base_url + dept + "/" + number
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        instructors = soup.find_all(name="div", attrs={"class": "card-body"})
        for instructor in instructors:
            name_element = instructor.find(name="h5", attrs={"class": "card-title"})
            name = name_element.text.strip()
            names = name.split(" ")
            first_name = names[0]
            last_name = names[-1]

            if (first_name, last_name, dept) in set_of_instructors:
                continue
            else:
                set_of_instructors.add((first_name, last_name, dept))

            fields = {"first_name": first_name, "last_name": last_name, "department": [dept]}
            fixture_item = {"model": "search.instructor", "pk": len(list_of_professors) + 1, "fields": fields}
            list_of_professors.append(fixture_item)
        
        counter += 1
            
    return list_of_professors


def getDepartments(term=1242):
    try:
        url = "https://courses.erppub.osu.edu/psc/ps/EMPLOYEE/PUB/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL?PortalActualURL=https%3a%2f%2fcourses.erppub.osu.edu%2fpsc%2fps%2fEMPLOYEE%2fPUB%2fc%2fCOMMUNITY_ACCESS.CLASS_SEARCH.GBL&PortalRegistryName=EMPLOYEE&PortalServletURI=https%3a%2f%2fcourses.erppub.osu.edu%2fpsp%2fps%2f&PortalURI=https%3a%2f%2fcourses.erppub.osu.edu%2fpsc%2fps%2f&PortalHostNode=CAMP&NoCrumbs=yes&PortalKeyStruct=yes"

        # Initialize the browser with headless option
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

        # Navigate to the website
        driver.get(url)
        wait = WebDriverWait(driver, 10) # wait for up to 10 seconds

        toWaitOn = wait.until(
            EC.visibility_of_element_located((By.NAME, "CLASS_SRCH_WRK2_STRM$35$")))
        # toWaitOn = driver.find_element(By.ID, "SSR_CLSRCH_WRK_LAST_NAME$8")

        select = Select(driver.find_element(By.NAME, "CLASS_SRCH_WRK2_STRM$35$"))

        if select.first_selected_option.get_attribute("value") != str(term):
            select.select_by_value(str(term))  # change this value for different semesters
            wait.until(EC.staleness_of(toWaitOn))

        # Wait for the "processing" activity to complete
        wait.until(EC.presence_of_element_located((By.NAME, "SSR_CLSRCH_WRK_SUBJECT_SRCH$1")))

        # Now, you can scrape the content
        page = driver.page_source
    finally:
        # Don't forget to close the browser once done
        # print(driver.page_source)
        driver.quit()

    # page = requests.get(url)
    soup = BeautifulSoup(page, 'html.parser')

    subject_select = soup.find(name="select", attrs={"id": "SSR_CLSRCH_WRK_SUBJECT_SRCH$1"})
    all_departments = subject_select.find_all(name="option") # type: ignore

    model = "search.department"
    list_of_departments = []
    list_of_departments_fields = []

    counter = 1
    for department in all_departments:
        pk = counter
        name = department.contents[0].strip()
        short_name = department['value']
        if name == "" and short_name == "":
            continue

        fields = {"name": name, "short_name": short_name}
        fixture_item = {"model": model, "pk": pk, "fields": fields}
        list_of_departments.append(fixture_item)
        list_of_departments_fields.append(fields)
        counter += 1

    return list_of_departments, list_of_departments_fields

def getDepartmentShortNames(term=1248):
    try:
        url = "https://courses.erppub.osu.edu/psc/ps/EMPLOYEE/PUB/c/COMMUNITY_ACCESS.CLASS_SEARCH.GBL?PortalActualURL=https%3a%2f%2fcourses.erppub.osu.edu%2fpsc%2fps%2fEMPLOYEE%2fPUB%2fc%2fCOMMUNITY_ACCESS.CLASS_SEARCH.GBL&PortalRegistryName=EMPLOYEE&PortalServletURI=https%3a%2f%2fcourses.erppub.osu.edu%2fpsp%2fps%2f&PortalURI=https%3a%2f%2fcourses.erppub.osu.edu%2fpsc%2fps%2f&PortalHostNode=CAMP&NoCrumbs=yes&PortalKeyStruct=yes"

        # Initialize the browser with headless option
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

        # Navigate to the website
        driver.get(url)
        wait = WebDriverWait(driver, 10) # wait for up to 10 seconds

        toWaitOn = wait.until(
            EC.visibility_of_element_located((By.NAME, "CLASS_SRCH_WRK2_STRM$35$")))
        # toWaitOn = driver.find_element(By.ID, "SSR_CLSRCH_WRK_LAST_NAME$8")

        select = Select(driver.find_element(By.NAME, "CLASS_SRCH_WRK2_STRM$35$"))

        if select.first_selected_option.get_attribute("value") != str(term):
            select.select_by_value(str(term))  # change this value for different semesters
            wait.until(EC.staleness_of(toWaitOn))

        # Wait for the "processing" activity to complete
        wait.until(EC.presence_of_element_located((By.NAME, "SSR_CLSRCH_WRK_SUBJECT_SRCH$1")))

        # Now, you can scrape the content
        page = driver.page_source
    finally:
        # Don't forget to close the browser once done
        # print(driver.page_source)
        driver.quit()

    # page = requests.get(url)
    soup = BeautifulSoup(page, 'html.parser')

    subject_select = soup.find(name="select", attrs={"id": "SSR_CLSRCH_WRK_SUBJECT_SRCH$1"})
    all_departments = subject_select.find_all(name="option") # type: ignore

    short_names = []
    for department in all_departments:
        name = department.contents[0].strip()
        short_name = department['value']
        if name == "" and short_name == "":
            continue
        short_names.append(short_name)
    
    return short_names
    # returns only the strings of the department short_names

def main():
    all_courses = getCourses()
    # pprint(all_courses)
    with open("search/fixtures/search/courses.json", "w") as f:
        json.dump(all_courses, f)

    all_departments_short_names = set()
    all_departments = []
    counter = 1
    for term in [1242, 1244, 1248]:
        model = "search.department"
        departments, fields = getDepartments(term)
        for field in fields:
            if field["short_name"] not in all_departments_short_names:
                pk = counter
                all_departments_short_names.add(field["short_name"])
                fixture_item = {"model": model, "pk": pk, "fields": field}
                all_departments.append(fixture_item)
                counter += 1
    # pprint(all_departments)
    with open("search/fixtures/search/departments.json", "w") as f:
        json.dump(all_departments, f)

    all_professors = getProfessors()
    # pprint(all_professors)
    with open("search/fixtures/search/professors.json", "w") as f:
        json.dump(all_professors, f)

def barrett_test():
    # prev_department_short_names = getDepartmentShortNames(1248)
    prev_department_short_names_SP24 = ['ACADAFF', 'ACCTMIS', 'ACCAD', 'AEROENG', 'AFAMAST', 'AEDECON', 'ACEL', 'AGRCOMM', 'AGSYSMT', 'ASE', 'AIRSCI', 'AMINSTS', 'ASL', 'ANATOMY', 'ANIMSCI', 'ANMLTEC', 'ANTHROP', 'ARABIC', 'ARCH', 'ART', 'ARTEDUC', 'ARTSSCI', 'ASAMSTS', 'ASTRON', 'ATHTRNG', 'ATMOSSC', 'AVIATN', 'BIOCHEM', 'BIOETHC', 'BIOPHRM', 'BIOLOGY', 'BIOMEDE', 'BMI', 'BIOMSCI', 'BSGP', 'BIOPHYS', 'BIOTECH', 'BCS', 'BUSOBA', 'BUSFIN', 'BUSMHR', 'BUSML', 'BUSADM', 'BUSTEC', 'CONSRTM', 'CBG', 'CATALAN', 'CLLC', 'CHEMPHY', 'CBE', 'CHEM', 'CHINESE', 'CRPLAN', 'CIVILEN', 'CLAS', 'MCR', 'COMM', 'COMLDR', 'COMPSTD', 'CSE', 'CONSYSM', 'CSCFFS', 'CSFRST', 'CSHSPMG', 'CONSCI', 'CRPSOIL', 'CSTW', 'CZECH', 'DANCE', 'DENTHYG', 'DENT', 'DESIGN', 'DSABLST', 'DNE', 'EARTHSC', 'EALL', 'EEURLL', 'ECON', 'ESCE', 'ESCFE', 'ESEPSY', 'ESEADM', 'ESEPOL', 'ESHESA', 'ESLTECH', 'ESPHE', 'ESQUAL', 'ESQREM', 'ESSPSY', 'ESSPED', 'ESWDE', 'EHE', 'EDUTL', 'EDUCST', 'ECE', 'ENGR', 'ENGREDU', 'ENGTECH', 'ENGRTEC', 'ENGLISH', 'ENTMLGY', 'ENR', 'ENVENG', 'ENVSCI', 'ETHNSTD', 'EEOB', 'EXP', 'FILMSTD', 'FDSCTE', 'FABENG', 'FAES', 'FRENCH', 'FRIT', 'GENED', 'GENSTDS', 'GENBIOL', 'GENCHEM', 'GENCOMM', 'GENMATH', 'GENSSC', 'GEOSCIM', 'GEOG', 'GERMAN', 'GRADSCH', 'GREEK', 'HCINNOV', 'HIMS', 'HTHRHSC', 'HW', 'HWIH', 'HEBREW', 'HECCREG', 'HINDI', 'HISTORY', 'HISTART', 'HONORS', 'HORTTEC', 'HCS', 'HDFS', 'HUMNNTR', 'ISE', 'INTMED', 'INTSTDS', 'ISLAM', 'ITALIAN', 'JAPANSE', 'JEWSHST', 'KINESIO', 'KNHES', 'KNPE', 'KNSFHP', 'KNSISM', 'KNOW', 'KOREAN', 'LARCH', 'LATIN', 'LAW', 'LING', 'MBA', 'MDN', 'MATSCEN', 'MATH', 'MEATSCI', 'MECHENG', 'MEDDIET', 'MEDLBS', 'MEDCOLL', 'MEDREN', 'MEDMCIM', 'MICRBIO', 'MILSCI', 'MDRNGRK', 'MCDBIO', 'MOLGEN', 'MVNGIMG', 'MUSIC', 'NAVALSC', 'NELC', 'NEURSGY', 'NEURO', 'NEUROSC', 'NEUROGS', 'NUCLREN', 'NURSING', 'NRSADVN', 'NRSPRCT', 'OCCTHER', 'OSBP', 'OPTOM', 'OTOLARN', 'PATHOL', 'PEDS', 'PERSIAN', 'PHR', 'PHILOS', 'PHYSMED', 'PHYSTHR', 'PHYSICS', 'PHYSIO', 'PLNTPTH', 'POLISH', 'POLITSC', 'PORTGSE', 'PSYBHLH', 'PSYCH', 'PUBHBIO', 'PUBHEHS', 'PUBHEPI', 'PUBHHBP', 'PUBHHMP', 'PUBAFRS', 'PUBHLTH', 'QUECHUA', 'ROOM', 'RADONC', 'RADSCI', 'RADIOLG', 'RELSTDS', 'RESPTHR', 'ROMLING', 'ROMANIA', 'RURLSOC', 'RUSSIAN', 'SANSKRT', 'SCANDVN', 'SLAVIC', 'SOCWORK', 'SOCIOL', 'SOMALI', 'SASIA', 'SPANISH', 'SPHHRNG', 'STAT', 'SURGERY', 'SWAHILI', 'SWEDISH', 'TECPHYS', 'THEATRE', 'GRADTDA', 'TURKISH', 'URDU', 'UROLOGY', 'UZBEK', 'VETBIOS', 'VETCLIN', 'VMCOLL', 'VETPREV', 'VISSCI', 'WELDENG', 'WGSST', 'YIDDISH']
    prev_department_short_names_AU24 = ['ACADAFF', 'ACCTMIS', 'ACCAD', 'AEROENG', 'AFAMAST', 'AEDECON', 'ACEL', 'AGRCOMM', 'AGSYSMT', 'ASE', 'AIRSCI', 'AMINSTS', 'ASL', 'ANATOMY', 'ANIMSCI', 'ANMLTEC', 'ANTHROP', 'ARABIC', 'ARCH', 'ART', 'ARTEDUC', 'ARTSSCI', 'ASAMSTS', 'ASTRON', 'ATHTRNG', 'ATMOSSC', 'AVIATN', 'BIOCHEM', 'BIOETHC', 'BIOPHRM', 'BIOLOGY', 'BMEA', 'BIOMEDE', 'BMI', 'BIOMSCI', 'BSGP', 'BIOPHYS', 'BIOTECH', 'BCS', 'BUSOBA', 'BUSFIN', 'BUSMHR', 'BUSML', 'BUSADM', 'BUSTEC', 'CONSRTM', 'CBG', 'CATALAN', 'CLLC', 'CHEMPHY', 'CBE', 'CHEM', 'CHINESE', 'CRPLAN', 'CIVILEN', 'CLAS', 'MCR', 'COMM', 'COMLDR', 'COMPSTD', 'CSE', 'CONSYSM', 'CSCFFS', 'CSFRST', 'CSHSPMG', 'CONSCI', 'CRPSOIL', 'CZECH', 'DANCE', 'DENTHYG', 'DENT', 'DESIGN', 'DSABLST', 'DNE', 'EARTHSC', 'EALL', 'ECON', 'ESCPSY', 'ESCE', 'ESCFE', 'ESEPSY', 'ESEADM', 'ESEPOL', 'ESHESA', 'ESLTECH', 'ESPHE', 'ESQUAL', 'ESQREM', 'ESSPSY', 'ESSPED', 'ESWDE', 'EHE', 'EDUTL', 'EDUCST', 'ECE', 'ENGR', 'ENGREDU', 'ENGTECH', 'ENGRTEC', 'ENGLISH', 'ENTMLGY', 'ENR', 'ENVENG', 'ENVSCI', 'ENVSCT', 'ETHNSTD', 'EEOB', 'EXP', 'FILMSTD', 'FDSCTE', 'FABENG', 'FAES', 'FRENCH', 'FRIT', 'GENED', 'GENSTDS', 'GENBIOL', 'GENCHEM', 'GENCOMM', 'GENMATH', 'GENSSC', 'GEOSCIM', 'GEOG', 'GERMAN', 'GRADSCH', 'GREEK', 'HCINNOV', 'HIMS', 'HTHRHSC', 'HW', 'HEBREW', 'HECCREG', 'HINDI', 'HISTORY', 'HISTART', 'HONORS', 'HORTTEC', 'HCS', 'HDFS', 'HUMNNTR', 'ISE', 'INTMED', 'INTSTDS', 'ISLAM', 'ITALIAN', 'JAPANSE', 'JEWSHST', 'KINESIO', 'KNHES', 'KNPE', 'KNSFHP', 'KNSISM', 'KNOW', 'KOREAN', 'LARCH', 'LATIN', 'LAW', 'LING', 'MBA', 'MDN', 'MATSCEN', 'MATH', 'MEATSCI', 'MECHENG', 'MEDDIET', 'MEDLBS', 'MEDCOLL', 'MEDREN', 'MEDMCIM', 'MICRBIO', 'MILSCI', 'MDRNGRK', 'MCDBIO', 'MOLGEN', 'MVNGIMG', 'MUSIC', 'NAVALSC', 'NELC', 'NEURSGY', 'NEURO', 'NEUROSC', 'NEUROGS', 'NUCLREN', 'NURSING', 'NRSADVN', 'NRSPRCT', 'OCCTHER', 'OSBP', 'OPTOM', 'OTOLARN', 'PATHOL', 'PEDS', 'PERSIAN', 'PHR', 'PHILOS', 'PHYSTHR', 'PHYSICS', 'PHYSIO', 'PLNTPTH', 'POLISH', 'POLITSC', 'PORTGSE', 'PSYBHLH', 'PSYCH', 'PUBHBIO', 'PUBHEHS', 'PUBHEPI', 'PUBHHBP', 'PUBHHMP', 'PUBAFRS', 'PUBHLTH', 'QUECHUA', 'ROOM', 'RADONC', 'RADSCI', 'RADIOLG', 'RELSTDS', 'RESPTHR', 'ROMANIA', 'RURLSOC', 'RUSSIAN', 'SANSKRT', 'SCANDVN', 'SCHOLAR', 'SLAVIC', 'SOCWORK', 'SOCIOL', 'SOMALI', 'SASIA', 'SPANISH', 'SPHHRNG', 'STAT', 'SURGERY', 'SWAHILI', 'SWEDISH', 'THEATRE', 'GRADTDA', 'TURKISH', 'URDU', 'UROLOGY', 'UZBEK', 'VETBIOS', 'VETCLIN', 'VMCOLL', 'VETPREV', 'VISSCI', 'WELDENG', 'WGSST', 'YIDDISH']
    prev_department_short_names_SU24 = ['ACCTMIS', 'ACCAD', 'AEROENG', 'AFAMAST', 'AEDECON', 'ACEL', 'AGRCOMM', 'AGSYSMT', 'ASE', 'AMINSTS', 'ASL', 'ANATOMY', 'ANIMSCI', 'ANMLTEC', 'ANTHROP', 'ARABIC', 'ARCH', 'ART', 'ARTEDUC', 'ARTSSCI', 'ASAMSTS', 'ASTRON', 'ATHTRNG', 'ATMOSSC', 'AVIATN', 'BIOCHEM', 'BIOETHC', 'BIOPHRM', 'BIOLOGY', 'BIOMEDE', 'BMI', 'BSGP', 'BIOPHYS', 'BUSOBA', 'BUSFIN', 'BUSMHR', 'BUSML', 'BUSADM', 'BUSTEC', 'CONSRTM', 'CBG', 'CLLC', 'CHEMPHY', 'CBE', 'CHEM', 'CHINESE', 'CRPLAN', 'CIVILEN', 'CLAS', 'MCR', 'COMM', 'COMLDR', 'COMPSTD', 'CSE', 'CONSYSM', 'CSCFFS', 'CSFRST', 'CSHSPMG', 'CONSCI', 'CRPSOIL', 'DANCE', 'DENTHYG', 'DENT', 'DESIGN', 'DSABLST', 'DNE', 'EARTHSC', 'EALL', 'ECON', 'ESCE', 'ESEPSY', 'ESEADM', 'ESEPOL', 'ESHESA', 'ESLTECH', 'ESPHE', 'ESQUAL', 'ESQREM', 'ESSPSY', 'ESSPED', 'ESWDE', 'EHE', 'EDUTL', 'EDUCST', 'ECE', 'ENGR', 'ENGREDU', 'ENGTECH', 'ENGLISH', 'ENTMLGY', 'ENR', 'ENVENG', 'EEOB', 'EXP', 'FILMSTD', 'FDSCTE', 'FABENG', 'FAES', 'FRENCH', 'FRIT', 'GENED', 'GEOSCIM', 'GEOG', 'GERMAN', 'GRADSCH', 'GREEK', 'HCINNOV', 'HIMS', 'HTHRHSC', 'HW', 'HISTORY', 'HISTART', 'HORTTEC', 'HCS', 'HDFS', 'HUMNNTR', 'ISE', 'INTMED', 'INTSTDS', 'ITALIAN', 'JAPANSE', 'KINESIO', 'KNHES', 'KNPE', 'KNSFHP', 'KNSISM', 'KNOW', 'KOREAN', 'LARCH', 'LATIN', 'LAW', 'LING', 'MBA', 'MDN', 'MATSCEN', 'MATH', 'MEATSCI', 'MECHENG', 'MEDDIET', 'MEDLBS', 'MEDCOLL', 'MEDREN', 'MEDMCIM', 'MICRBIO', 'MCDBIO', 'MOLGEN', 'MVNGIMG', 'MUSIC', 'NELC', 'NEURSGY', 'NEURO', 'NEUROSC', 'NUCLREN', 'NURSING', 'NRSADVN', 'NRSPRCT', 'ORIENTAT', 'OCCTHER', 'OSBP', 'OPTOM', 'OTOLARN', 'PATHOL', 'PEDS', 'PERSIAN', 'PHR', 'PHILOS', 'PHYSTHR', 'PHYSICS', 'PHYSIO', 'PLNTPTH', 'POLITSC', 'PORTGSE', 'PSYBHLH', 'PSYCH', 'PUBHBIO', 'PUBHEHS', 'PUBHEPI', 'PUBHHBP', 'PUBHHMP', 'PUBAFRS', 'PUBHLTH', 'RADONC', 'RADSCI', 'RESPTHR', 'RURLSOC', 'RUSSIAN', 'SLAVIC', 'SOCWORK', 'SOCIOL', 'SPANISH', 'SPHHRNG', 'STAT', 'SURGERY', 'SWAHILI', 'THEATRE', 'GRADTDA', 'VETBIOS', 'VETCLIN', 'VMCOLL', 'VETPREV', 'VISSCI', 'WELDENG', 'WGSST']
    prev_department_short_names_combined = set(prev_department_short_names_SP24 + prev_department_short_names_AU24 + prev_department_short_names_SU24)
    new_department_short_names = []

    url = "https://www.asc.ohio-state.edu/barrett.3/schedule/"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    # get each <td></td> element
    tds = soup.find_all(name="td")

    # get the department short names from the <td></td> elements by getting the text
    for td in tds:
        new_department_short_names.append(td.text.strip())
    
    # print the department short names in prev_department_short_names that are not in new_department_short_names
    # print(set(prev_department_short_names) - set(new_department_short_names))

    # print the department short names in new_department_short_names that are not in prev_department_short_names
    # print(set(new_department_short_names) - set(prev_department_short_names))

    barret_departments_unique = sorted(list(set(new_department_short_names) - set(prev_department_short_names_combined)))
    print(barret_departments_unique)

    def verify_department_short_names(department_short_names):
        max_hrefs = {}
        for dept in department_short_names:
            url = "https://www.asc.ohio-state.edu/barrett.3/schedule/" + dept
            page = requests.get(url)
            soup = BeautifulSoup(page.content, 'html.parser')
            
            tds = soup.find_all(name="td")
            hrefs = []
            for td in tds:
                a = td.find(name="a")
                if a is not None and a['href'][-4:] == ".txt":
                    # print(a)
                    # add the href value to the list, cutting off the .txt at the end
                    hrefs.append(int(a['href'][:-4]))
            
            try:
                max_href = max(hrefs)
            except ValueError:
                max_href = None
            max_hrefs[dept] = max_href
        
        return max_hrefs
    
    # print(verify_department_short_names(barret_departments_unique))
    # print values of verify_department_short_names(barret_departments_unique) if the value is None (i.e. no .txt file) or if > 1232
    # print({k: v for k, v in verify_department_short_names(barret_departments_unique).items() if v is None or v > 1232})

    # scrape through https://www.asc.ohio-state.edu/barrett.3/schedule/{department_short_name}/{term}.txt
    dept_term_url = "https://www.asc.ohio-state.edu/barrett.3/schedule/{}/{}.txt"

    test_dept = ["CSE"] # replace later with prev_department_short_names_combined
    test_term = ["1248"] # replace later with [1242, 1244, 1248]

    for dept in test_dept:
        for term in test_term:
            url = dept_term_url.format(dept, term)
            page = requests.get(url)
            print(page.text)





    

if __name__ == "__main__":
    # main()
    # print(getDepartmentShortNames(1244))
    barrett_test()