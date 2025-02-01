import pyodbc
import sys
import re
import csv
from datetime import datetime

CONN_STR = (
    "DRIVER={SQL SERVER};"
    "SERVER=IT-USAMA\\SQLEXPRESS;"  # Change to your actual server name
    "DATABASE=TFSSCHOOLDB;"
    "TRUSTED_CONNECTION=YES;"
)

###############################################################################
# Database connectivity and basic utilities
###############################################################################

def get_connection():
    try:
        conn = pyodbc.connect(CONN_STR)
        return conn
    except pyodbc.Error as e:
        print(f"[ERROR] Could not connect to database: {str(e)}")
        sys.exit(1)

def initialize_database():
    """
    Creates a StudentRegistration table with 62 columns (A..BJ) 
    matching your provided headers exactly.
    Adjust data types and lengths as needed.
    """
    create_stmt = """
    IF NOT EXISTS (
       SELECT * FROM sys.objects
       WHERE object_id = OBJECT_ID(N'[dbo].[StudentRegistration]')
         AND type in (N'U')
    )
    CREATE TABLE [dbo].[StudentRegistration] (
      -- A=0
      FormNo                VARCHAR(50),
      -- B=1
      IssueDate             VARCHAR(50),
      -- C=2
      ValidTill             VARCHAR(50),
      -- D=3
      ChildName             VARCHAR(100),
      -- E=4
      ChildDOB              VARCHAR(50),  -- We'll do a minimal store; could be DATE
      -- F=5
      ChildAge              VARCHAR(50),
      -- G=6
      PlaceOfBirth          VARCHAR(100),
      -- H=7
      Gender                VARCHAR(10),
      -- I=8
      Nationality           VARCHAR(50),
      -- J=9
      Religion              VARCHAR(50),
      -- K=10
      FormB_BirthCertNo     VARCHAR(100),
      -- L=11
      ClassAppliedFor       VARCHAR(50),
      -- M=12
      PresentAddress        VARCHAR(200),
      -- N=13
      PermanentAddress      VARCHAR(200),
      -- O=14
      HomePhone1            VARCHAR(50),
      -- P=15
      HomePhone2            VARCHAR(50),
      -- Q=16
      PreviousSchoolAttended VARCHAR(200),
      -- R=17
      ClassLastAttended     VARCHAR(50),
      -- S=18
      SessionCompleted      VARCHAR(50),
      -- T=19
      ReasonForLeavingLastSchool VARCHAR(200),
      -- U=20
      FatherName            VARCHAR(100),
      -- V=21
      FatherDOB             VARCHAR(50),
      -- W=22
      FatherNationality     VARCHAR(50),
      -- X=23
      FatherReligion        VARCHAR(50),
      -- Y=24
      FatherCNIC            VARCHAR(50),
      -- Z=25
      FatherEmail           VARCHAR(100),
      -- AA=26
      FatherQualification   VARCHAR(100),
      -- AB=27
      FatherJobType         VARCHAR(100),
      -- AC=28
      FatherBusinessType    VARCHAR(100),
      -- AD=29
      FatherOrganization    VARCHAR(200),
      -- AE=30
      FatherOfficeAddress   VARCHAR(200),
      -- AF=31
      FatherOfficePhone     VARCHAR(50),
      -- AG=32
      FatherMobile1         VARCHAR(50),
      -- AH=33
      FatherMobile2         VARCHAR(50),
      -- AI=34
      FatherWhatsApp        VARCHAR(50),
      -- AJ=35
      MotherName            VARCHAR(100),
      -- AK=36
      MotherDOB             VARCHAR(50),
      -- AL=37
      MotherNationality     VARCHAR(50),
      -- AM=38
      MotherReligion        VARCHAR(50),
      -- AN=39
      MotherCNIC            VARCHAR(50),
      -- AO=40
      MotherEmail           VARCHAR(100),
      -- AP=41
      MotherQualification   VARCHAR(100),
      -- AQ=42
      MotherJobType         VARCHAR(100),
      -- AR=43
      MotherBusinessType    VARCHAR(100),
      -- AS=44
      MotherOrganization    VARCHAR(200),
      -- AT=45
      MotherOfficeAddress   VARCHAR(200),
      -- AU=46
      MotherOfficePhone     VARCHAR(50),
      -- AV=47
      MotherMobile1         VARCHAR(50),
      -- AW=48
      MotherMobile2         VARCHAR(50),
      -- AX=49
      MotherWhatsApp        VARCHAR(50),
      -- AY=50
      ParentsMaritalStatus  VARCHAR(50),
      -- AZ=51
      ChildBloodGroup       VARCHAR(50),
      -- BA=52
      ChildMedicalConditions VARCHAR(200),
      -- BB=53
      ChildDisabilities     VARCHAR(200),
      -- BC=54
      EmergencyContactName  VARCHAR(100),
      -- BD=55
      EmergencyContactRelation VARCHAR(50),
      -- BE=56
      EmergencyContactPTCL  VARCHAR(50),
      -- BF=57
      EmergencyContactCell  VARCHAR(50),
      -- BG=58
      OtherChildrenStudyingDetails VARCHAR(200),
      -- BH=59
      SiblingsInSchoolDetails VARCHAR(200),
      -- BI=60
      RelativesInSchoolDetails VARCHAR(200),
      -- BJ=61
      RelativesWorkedInSchoolDetails VARCHAR(200)
    )
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(create_stmt)
    conn.commit()
    conn.close()

###############################################################################
# 2) Minimal Helper Functions (DOB, CNIC, Phone, generate_registration_num)
###############################################################################

def format_dob(raw_dob):
    """
    If you want a strict 8-digit format (DDMMYYYY):
      We'll remove non-digits, check length=8, parse.
    If you want to store as string only, just return raw_dob.
    Here we'll do a minimal parse.
    """
    digits = re.sub(r'\D', '', raw_dob)
    if len(digits) != 8:
        # We'll just return raw_dob unmodified or None
        # For simplicity, let's store as-is if it doesn't match.
        return raw_dob  # or return None if you want to fail
    # Let's attempt to parse to confirm it's valid
    day = digits[:2]
    month = digits[2:4]
    year = digits[4:]
    try:
        dt = datetime.strptime(day+month+year, "%d%m%Y")
        # store in ISO format
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        # invalid date
        return raw_dob

def format_cnic(raw_cnic):
    """
    Remove dashes, check length=13. If not, store as-is or return None.
    We'll just do minimal:
    """
    digits = re.sub(r'\D', '', raw_cnic)
    if len(digits) == 13:
        return digits
    # else store as is or None
    return raw_cnic

def format_phone(raw_phone):
    """
    Minimal approach: remove non-digits, if it starts with '0', remove it, etc.
    We'll store as-is if it doesn't match. 
    """
    digits = re.sub(r'\D', '', raw_phone)
    if not digits:
        return raw_phone
    # example: if starts with 0, remove one
    if digits.startswith('0'):
        digits = digits[1:]
    # if it starts with '3' => +92
    if digits.startswith('3') and len(digits) == 10:
        return f"+92-{digits}"
    # else store as is
    return raw_phone

def generate_registration_number():
    """
    Example function that returns a dummy registration number or 
    you can query the DB for the next available number.
    """
    # In your older code, you used 'academic_year' to generate. 
    # You can adapt that logic. For now, let's just return a placeholder.
    import random
    return f"RN{random.randint(1000,9999)}"

###############################################################################
# Registration Number & GR Number Generation
###############################################################################

def generate_registration_number(academic_year):
    """
    Generate a new registration number (e.g., 20250001) 
    taking into account the year-based logic.
    This is a simplistic approach; you might store the last used index in a table.
    """
    # Suppose academic_year is "2024-2025" or "2025-2026" 
    # Extract the first year or the second:
    # For simplicity, let's assume we take the first 4 digits from "2025-2026" => "2025"
    base_year = academic_year.split('-')[0] if '-' in academic_year else academic_year
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check the maximum RegNo that starts with base_year
    # We'll store RegNo as string, e.g. "20250001"
    query = f"""
        SELECT MAX(RegNo) 
        FROM StudentRegistration
        WHERE RegNo LIKE '{base_year}%'
    """
    cursor.execute(query)
    row = cursor.fetchone()
    
    if row and row[0]:
        last_reg_no = row[0]
        # e.g., last_reg_no = "20250007"
        # Extract the numeric part after the year
        idx_part = last_reg_no[len(base_year):]  # e.g. "0007"
        new_idx = int(idx_part) + 1
    else:
        new_idx = 1
        
    new_reg_no = f"{base_year}{str(new_idx).zfill(4)}"  # e.g. "20250001"
    
    conn.close()
    return new_reg_no

def generate_gr_number():
    """
    Generate a new GR No which is 4 digits, user can define the first GR No.
    We'll keep track in a table or retrieve the last one used.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT MAX(GRNo)
        FROM StudentAdmitted
    """
    cursor.execute(query)
    row = cursor.fetchone()
    
    if row and row[0]:
        # row[0] is something like "1001"
        new_gr = int(row[0]) + 1
    else:
        # If no admissions yet, define your starting GR (e.g. 1000 or 1)
        new_gr = 1000
    
    conn.close()
    return str(new_gr).zfill(4)


###############################################################################
# Main Menu
###############################################################################

def main_menu():
    while True:
        print("\n=== School Management System ===")
        print("1. Student Management")
        print("2. Teacher Management")
        print("3. Fee Management")
        print("4. Reports")
        print("5. Exit")
        
        choice = input("Enter your choice: ").strip()
        
        if choice == "1":
            student_management_menu()
        elif choice == "2":
            teacher_management_menu()
        elif choice == "3":
            fee_management_menu()
        elif choice == "4":
            reports_menu()
        elif choice == "5":
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice. Please try again.")


###############################################################################
# 1. Student Management
###############################################################################

def student_management_menu():
    while True:
        print("\n--- Student Management ---")
        print("1. Register Student")
        print("2. Admission Test Result")
        print("3. Admission Fee")
        print("4. Student Admission")
        print("5. Assigning Classes")
        print("6. Status Of Students")
        print("7. Back To Main Menu")

        choice = input("Enter your choice: ").strip()
        
        if choice == "1":
            register_student_menu()
        elif choice == "2":
            admission_test_result_menu()
        elif choice == "3":
            admission_fee_menu()
        elif choice == "4":
            student_admission_menu()
        elif choice == "5":
            assigning_classes_menu()
        elif choice == "6":
            status_of_students_menu()
        elif choice == "7":
            return  # back to main
        elif choice.lower() == 'esc':
            # As per requirement, pressing ESC goes back one menu 
            return
        else:
            print("Invalid choice. Please try again.")


###############################################################################
# 1.1 Register Student
###############################################################################

def register_student_menu():
    while True:
        print("\n--- Register Student ---")
        print("1. Register New Student (Manual)")
        print("2. Register New Students (CSV)")
        print("3. View Registered Students")
        print("4. Back To Student Management")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            register_new_student_manual()
        elif choice == "2":
            register_new_students_csv()
        elif choice == "3":
            view_registered_students()
        elif choice == "4":
            return
        elif choice.lower() == 'esc':
            return
        else:
            print("Invalid choice. Please try again.")

def register_new_students_csv():
    """
    Reads CSV with columns A..BJ (62 columns).
    Row 1 => sample row (skip)
    Row 2 => header row
    Row 3+ => data
    Minimal validation. Everything is inserted.
    """
    print("\n--- Register New Students (CSV) ---")
    file_path = input("Enter CSV path (or 'esc' to cancel): ").strip()
    if file_path.lower() == 'esc':
        return

    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            # Skip row 1 (sample row)
            _sample = next(reader, None)
            # read row 2 (header)
            header = next(reader, None)
            if not header or len(header) < 62:
                print("[ERROR] No valid header row found. Expected 62 columns.")
                return

            conn = get_connection()
            cursor = conn.cursor()

            success_list = []
            fail_list = []
            row_num = 2  # we ended on row 2, so next is data row 3

            for row in reader:
                row_num += 1
                if len(row) < 62:
                    fail_list.append((row_num, "(Unknown)", f"Not enough columns: {len(row)}/62"))
                    continue

                # Extract columns (0..61)
                # We'll apply minimal transformations on a few fields
                colA  = row[0].strip()   # FormNo
                colB  = row[1].strip()   # IssueDate
                colC  = row[2].strip()   # ValidTill
                colD  = row[3].strip()   # ChildName
                colE  = format_dob(row[4].strip())  # ChildDOB
                colF  = row[5].strip()   # ChildAge
                colG  = row[6].strip()   # PlaceOfBirth
                colH  = row[7].strip()   # Gender
                colI  = row[8].strip()   # Nationality
                colJ  = row[9].strip()   # Religion
                colK  = row[10].strip()  # FormB_BirthCertNo
                colL  = row[11].strip()  # ClassAppliedFor
                colM  = row[12].strip()  # PresentAddress
                colN  = row[13].strip()  # PermanentAddress
                colO  = format_phone(row[14].strip()) # HomePhone1
                colP  = format_phone(row[15].strip()) # HomePhone2
                colQ  = row[16].strip()  # PreviousSchoolAttended
                colR  = row[17].strip()  # ClassLastAttended
                colS  = row[18].strip()  # SessionCompleted
                colT  = row[19].strip()  # ReasonForLeavingLastSchool
                colU  = row[20].strip()  # FatherName
                colV  = format_dob(row[21].strip())  # FatherDOB
                colW  = row[22].strip()  # FatherNationality
                colX  = row[23].strip()  # FatherReligion
                colY  = format_cnic(row[24].strip()) # FatherCNIC
                colZ  = row[25].strip()  # FatherEmail
                colAA = row[26].strip()  # FatherQualification
                colAB = row[27].strip()  # FatherJobType
                colAC = row[28].strip()  # FatherBusinessType
                colAD = row[29].strip()  # FatherOrganization
                colAE = row[30].strip()  # FatherOfficeAddress
                colAF = format_phone(row[31].strip()) # FatherOfficePhone
                colAG = format_phone(row[32].strip()) # FatherMobile1
                colAH = format_phone(row[33].strip()) # FatherMobile2
                colAI = format_phone(row[34].strip()) # FatherWhatsApp
                colAJ = row[35].strip()  # MotherName
                colAK = format_dob(row[36].strip()) # MotherDOB
                colAL = row[37].strip()  # MotherNationality
                colAM = row[38].strip()  # MotherReligion
                colAN = format_cnic(row[39].strip()) # MotherCNIC
                colAO = row[40].strip()  # MotherEmail
                colAP = row[41].strip()  # MotherQualification
                colAQ = row[42].strip()  # MotherJobType
                colAR = row[43].strip()  # MotherBusinessType
                colAS = row[44].strip()  # MotherOrganization
                colAT = row[45].strip()  # MotherOfficeAddress
                colAU = format_phone(row[46].strip()) # MotherOfficePhone
                colAV = format_phone(row[47].strip()) # MotherMobile1
                colAW = format_phone(row[48].strip()) # MotherMobile2
                colAX = format_phone(row[49].strip()) # MotherWhatsApp
                colAY = row[50].strip()  # ParentsMaritalStatus
                colAZ = row[51].strip()  # ChildBloodGroup
                colBA = row[52].strip()  # ChildMedicalConditions
                colBB = row[53].strip()  # ChildDisabilities
                colBC = row[54].strip()  # EmergencyContactName
                colBD = row[55].strip()  # EmergencyContactRelation
                colBE = format_phone(row[56].strip()) # EmergencyContactPTCL
                colBF = format_phone(row[57].strip()) # EmergencyContactCell
                colBG = row[58].strip()  # OtherChildrenStudyingDetails
                colBH = row[59].strip()  # SiblingsInSchoolDetails
                colBI = row[60].strip()  # RelativesInSchoolDetails
                colBJ = row[61].strip()  # RelativesWorkedInSchoolDetails

                # Minimal check: ChildName must not be empty
                if not colD:
                    fail_list.append((row_num, "(No ChildName)", "ChildName is empty (col D)"))
                    continue

                # Attempt insert
                insert_sql = """
                INSERT INTO StudentRegistration (
                  FormNo, IssueDate, ValidTill, ChildName, ChildDOB, ChildAge, PlaceOfBirth, Gender,
                  Nationality, Religion, FormB_BirthCertNo, ClassAppliedFor, PresentAddress, PermanentAddress,
                  HomePhone1, HomePhone2, PreviousSchoolAttended, ClassLastAttended, SessionCompleted, ReasonForLeavingLastSchool,
                  FatherName, FatherDOB, FatherNationality, FatherReligion, FatherCNIC, FatherEmail, FatherQualification,
                  FatherJobType, FatherBusinessType, FatherOrganization, FatherOfficeAddress, FatherOfficePhone, FatherMobile1,
                  FatherMobile2, FatherWhatsApp, MotherName, MotherDOB, MotherNationality, MotherReligion, MotherCNIC, MotherEmail,
                  MotherQualification, MotherJobType, MotherBusinessType, MotherOrganization, MotherOfficeAddress, MotherOfficePhone,
                  MotherMobile1, MotherMobile2, MotherWhatsApp, ParentsMaritalStatus, ChildBloodGroup, ChildMedicalConditions, ChildDisabilities,
                  EmergencyContactName, EmergencyContactRelation, EmergencyContactPTCL, EmergencyContactCell, OtherChildrenStudyingDetails,
                  SiblingsInSchoolDetails, RelativesInSchoolDetails, RelativesWorkedInSchoolDetails
                )
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """

                try:
                    cursor.execute(insert_sql, (
                        colA, colB, colC, colD, colE, colF, colG, colH,
                        colI, colJ, colK, colL, colM, colN,
                        colO, colP, colQ, colR, colS, colT,
                        colU, colV, colW, colX, colY, colZ, colAA,
                        colAB, colAC, colAD, colAE, colAF, colAG,
                        colAH, colAI, colAJ, colAK, colAL, colAM, colAN, colAO,
                        colAP, colAQ, colAR, colAS, colAT, colAU, colAV, colAW,
                        colAX, colAY, colAZ, colBA, colBB,
                        colBC, colBD, colBE, colBF, colBG,
                        colBH, colBI, colBJ
                    ))
                    success_list.append((row_num, colD))
                except Exception as ex:
                    fail_list.append((row_num, colD, f"DB Insert Error: {ex}"))
                    continue

            conn.commit()
            cursor.close()
            conn.close()

            total_rows = row_num - 2  # data rows
            success_count = len(success_list)
            fail_count = len(fail_list)
            print(f"\nCSV Import Complete. Rows read: {total_rows}")
            print(f"Successfully inserted: {success_count}")
            print(f"Failed: {fail_count}")

            if success_count > 0:
                print("\n-- Success List --")
                for (rnum, name) in success_list:
                    print(f"  Spreadsheet Row {rnum}, Child: {name}")

            if fail_count > 0:
                print("\n-- Fail List --")
                for entry in fail_list:
                    if len(entry) == 3:
                        (rnum, name, reason) = entry
                        print(f"  Row {rnum}, Child '{name}' => {reason}")
                    else:
                        (rnum, name) = entry
                        print(f"  Row {rnum}, Child '{name}' => Unknown reason")

    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
    except Exception as e:
        print(f"[ERROR] An error occurred while processing the CSV: {e}")

def register_new_student_manual():
    """
    Prompts user for all 62 columns (A..BJ) and inserts into StudentRegistration.
    Minimal validations. For large production usage, you'd likely do 
    a more user-friendly approach, but here's the direct approach.
    """
    print("\n-- Manual Student Registration (All 62 Fields) --")
    # We'll store them in a list, in order, so we can do a single insert.
    data = []

    # We'll define the prompts in a list of (column, prompt)
    columns_prompts = [
        ("FormNo", "Form No (A)"),
        ("IssueDate", "Issue Date (B)"),
        ("ValidTill", "Valid Till (C)"),
        ("ChildName", "Child Name (D)"),
        ("ChildDOB", "Date of Birth (E) [DDMMYYYY or any?]"),
        ("ChildAge", "Age (F)"),
        ("PlaceOfBirth", "Place of Birth (G)"),
        ("Gender", "Gender (H) [M/F]?"),
        ("Nationality", "Nationality (I)"),
        ("Religion", "Religion (J)"),
        ("FormB_BirthCertNo", "Form B No / Birth Cert No (K)"),
        ("ClassAppliedFor", "Class Applied For (L)"),
        ("PresentAddress", "Present Address (M)"),
        ("PermanentAddress", "Permanent Address (N)"),
        ("HomePhone1", "Home Phone 1 (O)"),
        ("HomePhone2", "Home Phone 2 (P)"),
        ("PreviousSchoolAttended", "Previous School Attended (Q)"),
        ("ClassLastAttended", "Class Last Attended (R)"),
        ("SessionCompleted", "Session Completed (S)"),
        ("ReasonForLeavingLastSchool", "Reason for Leaving (T)"),
        ("FatherName", "Father Name (U)"),
        ("FatherDOB", "Father DOB (V) [DDMMYYYY or any?]"),
        ("FatherNationality", "Father Nationality (W)"),
        ("FatherReligion", "Father Religion (X)"),
        ("FatherCNIC", "Father CNIC (Y)"),
        ("FatherEmail", "Father Email (Z)"),
        ("FatherQualification", "Father Qualification (AA)"),
        ("FatherJobType", "Father Job Type (AB)"),
        ("FatherBusinessType", "Father Business Type (AC)"),
        ("FatherOrganization", "Father Organization (AD)"),
        ("FatherOfficeAddress", "Father Office Address (AE)"),
        ("FatherOfficePhone", "Father Office Phone (AF)"),
        ("FatherMobile1", "Father Mobile 1 (AG)"),
        ("FatherMobile2", "Father Mobile 2 (AH)"),
        ("FatherWhatsApp", "Father WhatsApp (AI)"),
        ("MotherName", "Mother Name (AJ)"),
        ("MotherDOB", "Mother DOB (AK) [DDMMYYYY or any?]"),
        ("MotherNationality", "Mother Nationality (AL)"),
        ("MotherReligion", "Mother Religion (AM)"),
        ("MotherCNIC", "Mother CNIC (AN)"),
        ("MotherEmail", "Mother Email (AO)"),
        ("MotherQualification", "Mother Qualification (AP)"),
        ("MotherJobType", "Mother Job Type (AQ)"),
        ("MotherBusinessType", "Mother Business Type (AR)"),
        ("MotherOrganization", "Mother Organization (AS)"),
        ("MotherOfficeAddress", "Mother Office Address (AT)"),
        ("MotherOfficePhone", "Mother Office Phone (AU)"),
        ("MotherMobile1", "Mother Mobile 1 (AV)"),
        ("MotherMobile2", "Mother Mobile 2 (AW)"),
        ("MotherWhatsApp", "Mother WhatsApp (AX)"),
        ("ParentsMaritalStatus", "Parents Marital Status (AY)"),
        ("ChildBloodGroup", "Child Blood Group (AZ)"),
        ("ChildMedicalConditions", "Child Medical Conditions (BA)"),
        ("ChildDisabilities", "Child Disabilities (BB)"),
        ("EmergencyContactName", "Emergency Contact Name (BC)"),
        ("EmergencyContactRelation", "Emergency Contact Relation (BD)"),
        ("EmergencyContactPTCL", "Emergency Contact PTCL (BE)"),
        ("EmergencyContactCell", "Emergency Contact Cell (BF)"),
        ("OtherChildrenStudyingDetails", "Other Children Studying Details (BG)"),
        ("SiblingsInSchoolDetails", "Siblings in School Details (BH)"),
        ("RelativesInSchoolDetails", "Relatives in School Details (BI)"),
        ("RelativesWorkedInSchoolDetails", "Relatives Worked in School Details (BJ)"),
    ]

    for (col, prompt_str) in columns_prompts:
        val = input(f"Enter {prompt_str}: ").strip()
        # Minimal transformations:
        if col in ("ChildDOB", "FatherDOB", "MotherDOB"):
            val = format_dob(val)
        elif col in ("FatherCNIC", "MotherCNIC"):
            val = format_cnic(val)
        elif col in ("HomePhone1", "HomePhone2", "FatherOfficePhone", 
                     "FatherMobile1", "FatherMobile2", "FatherWhatsApp",
                     "MotherOfficePhone", "MotherMobile1", "MotherMobile2", 
                     "MotherWhatsApp", "EmergencyContactPTCL", "EmergencyContactCell"):
            val = format_phone(val)
        # else store as is
        data.append(val)

    # Now data has 62 items in exact order as columns.
    if not data[3]:
        # data[3] = ChildName
        print("[ERROR] Child Name is required!")
        return

    # Insert into DB
    conn = get_connection()
    cursor = conn.cursor()

    insert_sql = """
    INSERT INTO StudentRegistration (
      FormNo, IssueDate, ValidTill, ChildName, ChildDOB, ChildAge, PlaceOfBirth, Gender,
      Nationality, Religion, FormB_BirthCertNo, ClassAppliedFor, PresentAddress, PermanentAddress,
      HomePhone1, HomePhone2, PreviousSchoolAttended, ClassLastAttended, SessionCompleted, ReasonForLeavingLastSchool,
      FatherName, FatherDOB, FatherNationality, FatherReligion, FatherCNIC, FatherEmail, FatherQualification,
      FatherJobType, FatherBusinessType, FatherOrganization, FatherOfficeAddress, FatherOfficePhone, FatherMobile1,
      FatherMobile2, FatherWhatsApp, MotherName, MotherDOB, MotherNationality, MotherReligion, MotherCNIC, MotherEmail,
      MotherQualification, MotherJobType, MotherBusinessType, MotherOrganization, MotherOfficeAddress, MotherOfficePhone,
      MotherMobile1, MotherMobile2, MotherWhatsApp, ParentsMaritalStatus, ChildBloodGroup, ChildMedicalConditions, ChildDisabilities,
      EmergencyContactName, EmergencyContactRelation, EmergencyContactPTCL, EmergencyContactCell, OtherChildrenStudyingDetails,
      SiblingsInSchoolDetails, RelativesInSchoolDetails, RelativesWorkedInSchoolDetails
    )
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """

    try:
        cursor.execute(insert_sql, tuple(data))
        conn.commit()
        print(f"[INFO] Student '{data[3]}' inserted successfully.")
    except Exception as ex:
        print(f"[ERROR] Could not insert manual student: {ex}")
        conn.rollback()

    cursor.close()
    conn.close()
        
def view_registered_students():
    """
    View all registered students (active or all).
    """
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT RegNo, Name, Gender, DOB, FatherName, FatherCNIC, FatherPhone, IsActive FROM StudentRegistration"
    cursor.execute(query)
    rows = cursor.fetchall()
    if not rows:
        print("No registered students found.")
    else:
        print("\n--- Registered Students ---")
        for row in rows:
            print(f"RegNo: {row[0]}, Name: {row[1]}, Gender: {row[2]}, DOB: {row[3]}, "
                  f"Father: {row[4]}, CNIC: {row[5]}, Phone: {row[6]}, Active: {row[7]}")
    conn.close()



###############################################################################
# 1.2 Admission Test Result
###############################################################################

def admission_test_result_menu():
    while True:
        print("\n--- Admission Test Result ---")
        print("1. Update Admission Test Results (Auto-Generate Fee Voucher If Pass)")
        print("2. Update Admission Test Results In Bulk Using Excel/CSV (Auto-Generate Fee Voucher If Pass)")
        print("3. View Admission Test Results")
        print("4. Back To Student Management")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            update_admission_test_result()
        elif choice == "2":
            update_admission_test_result_bulk()
        elif choice == "3":
            view_admission_test_results()
        elif choice == "4":
            return
        elif choice.lower() == 'esc':
            return
        else:
            print("Invalid choice. Please try again.")

def update_admission_test_result():
    """
    Manually update test results for a single student (RegNo).
    If pass, auto-generate admission fee voucher.
    """
    print("\n[INFO] Update Admission Test Results - NOT IMPLEMENTED (Placeholder)")

def update_admission_test_result_bulk():
    """
    Bulk update from CSV/Excel.
    """
    print("\n[INFO] Update Admission Test Results In Bulk - NOT IMPLEMENTED (Placeholder)")

def view_admission_test_results():
    """
    View results for all or filtered by pass/fail, etc.
    """
    print("\n[INFO] View Admission Test Results - NOT IMPLEMENTED (Placeholder)")


###############################################################################
# 1.3 Admission Fee
###############################################################################

def admission_fee_menu():
    while True:
        print("\n--- Admission Fee ---")
        print("1. Print Admission Fee Voucher")
        print("2. Update Fee Status In Bulk Using Excel/Csv (When Fee Is Paid, Admit Student)")
        print("3. View Fee Status")
        print("4. Back To Student Management")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            print_admission_fee_voucher()
        elif choice == "2":
            update_fee_status_bulk()
        elif choice == "3":
            view_fee_status()
        elif choice == "4":
            return
        elif choice.lower() == 'esc':
            return
        else:
            print("Invalid choice. Please try again.")

def print_admission_fee_voucher():
    """
    Print Admission Fee Voucher for a given RegNo or a range.
    """
    print("\n[INFO] Print Admission Fee Voucher - NOT IMPLEMENTED (Placeholder)")

def update_fee_status_bulk():
    """
    When fee is paid, student becomes eligible for admission.
    """
    print("\n[INFO] Update Fee Status In Bulk - NOT IMPLEMENTED (Placeholder)")

def view_fee_status():
    print("\n[INFO] View Fee Status - NOT IMPLEMENTED (Placeholder)")


###############################################################################
# 1.4 Student Admission
###############################################################################

def student_admission_menu():
    while True:
        print("\n--- Student Admission ---")
        print("1. Admit Student (Manually)")
        print("2. View Admitted Students (Should Give Option To View Admissions Per Year As Well)")
        print("3. Back To Student Management")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            admit_student_manually()
        elif choice == "2":
            view_admitted_students()
        elif choice == "3":
            return
        elif choice.lower() == 'esc':
            return
        else:
            print("Invalid choice. Please try again.")

def admit_student_manually():
    """
    After the admission fee is paid, generate GR No and move from registration to admitted table.
    """
    print("\n[INFO] Admit Student (Manual) - NOT IMPLEMENTED (Placeholder)")

def view_admitted_students():
    print("\n[INFO] View Admitted Students - NOT IMPLEMENTED (Placeholder)")


###############################################################################
# 1.5 Assigning Classes
###############################################################################

def assigning_classes_menu():
    while True:
        print("\n--- Assigning Section For Class ---")
        print("1. Assign Section Manually")
        print("2. Assign Section In Bulk (CSV)")
        print("3. Back To Student Management")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            assign_section_manually()
        elif choice == "2":
            assign_section_bulk()
        elif choice == "3":
            return
        elif choice.lower() == 'esc':
            return
        else:
            print("Invalid choice. Please try again.")

def assign_section_manually():
    print("\n[INFO] Assign Section Manually - NOT IMPLEMENTED (Placeholder)")

def assign_section_bulk():
    print("\n[INFO] Assign Section In Bulk (CSV) - NOT IMPLEMENTED (Placeholder)")


###############################################################################
# 1.6 Status Of Students
###############################################################################

def status_of_students_menu():
    while True:
        print("\n--- Status Of Students ---")
        print("1. Manage Active/Inactive (Single)")
        print("2. Inactivate Students In Bulk (CSV)")
        print("3. Reactivate Inactive Students")
        print("4. View Active Students")
        print("5. View Inactive Students")
        print("6. Back To Student Management")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            manage_active_inactive_single()
        elif choice == "2":
            inactivate_students_bulk()
        elif choice == "3":
            reactivate_inactive_students()
        elif choice == "4":
            view_active_students()
        elif choice == "5":
            view_inactive_students()
        elif choice == "6":
            return
        elif choice.lower() == 'esc':
            return
        else:
            print("Invalid choice. Please try again.")

def manage_active_inactive_single():
    print("\n[INFO] Manage Active/Inactive (Single) - NOT IMPLEMENTED (Placeholder)")

def inactivate_students_bulk():
    print("\n[INFO] Inactivate Students In Bulk (CSV) - NOT IMPLEMENTED (Placeholder)")

def reactivate_inactive_students():
    print("\n[INFO] Reactivate Inactive Students - NOT IMPLEMENTED (Placeholder)")

def view_active_students():
    print("\n[INFO] View Active Students - NOT IMPLEMENTED (Placeholder)")

def view_inactive_students():
    print("\n[INFO] View Inactive Students - NOT IMPLEMENTED (Placeholder)")


###############################################################################
# 2. Teacher Management
###############################################################################

def teacher_management_menu():
    while True:
        print("\n--- Teacher Management ---")
        print("1. View Teachers")
        print("2. Add Teacher (Manual)")
        print("3. Add Teachers (Csv)")
        print("4. Assign Roles To Teachers")
        print("5. Assign Classes To Teachers")
        print("6. Back To Main Menu")
        
        choice = input("Enter your choice: ").strip()
        
        if choice == "1":
            view_teachers_menu()
        elif choice == "2":
            add_teacher_manual()
        elif choice == "3":
            add_teachers_csv()
        elif choice == "4":
            assign_roles_to_teachers()
        elif choice == "5":
            assign_classes_to_teachers()
        elif choice == "6":
            return
        elif choice.lower() == 'esc':
            return
        else:
            print("Invalid choice. Please try again.")

def view_teachers_menu():
    while True:
        print("\n--- View Teachers ---")
        print("1. View All Teachers")
        print("2. View All Class Teachers")
        print("3. View Teachers By Subject")
        print("4. View Teachers By Class")
        print("5. Back To Main Menu")

        choice = input("Enter your choice: ").strip()
        
        if choice == "1":
            view_all_teachers()
        elif choice == "2":
            view_all_class_teachers()
        elif choice == "3":
            view_teachers_by_subject()
        elif choice == "4":
            view_teachers_by_class()
        elif choice == "5":
            return
        elif choice.lower() == 'esc':
            return
        else:
            print("Invalid choice. Please try again.")

def view_all_teachers():
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT ID, Name, CNIC, IsClassTeacher, Subjects FROM Teachers"
    cursor.execute(query)
    rows = cursor.fetchall()
    if not rows:
        print("No teachers found.")
    else:
        print("\n--- All Teachers ---")
        for row in rows:
            teacher_id = row[0]
            name = row[1]
            cnic = row[2]
            is_ct = "Yes" if row[3] else "No"
            subjects = row[4]
            print(f"ID: {teacher_id}, Name: {name}, CNIC: {cnic}, ClassTeacher: {is_ct}, Subjects: {subjects}")
    conn.close()

def view_all_class_teachers():
    """
    Lists all teachers where IsClassTeacher = 1 (i.e., True).
    """
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT ID, Name, CNIC, Subjects
        FROM Teachers
        WHERE IsClassTeacher = 1
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    if not rows:
        print("\nNo class teachers found.\n")
    else:
        print("\n--- All Class Teachers ---")
        for row in rows:
            teacher_id = row[0]
            name = row[1]
            cnic = row[2]
            subjects = row[3]
            print(f"ID: {teacher_id}, Name: {name}, CNIC: {cnic}, Subjects: {subjects}")
    conn.close()

def view_teachers_by_subject():
    """
    Asks user for a subject keyword (e.g., 'Math') and
    lists all teachers whose 'Subjects' column includes that keyword.
    """
    subject_search = input("\nEnter the subject you want to search for: ").strip()
    if not subject_search:
        print("[ERROR] Subject cannot be empty.")
        return

    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT ID, Name, CNIC, IsClassTeacher, Subjects
        FROM Teachers
        WHERE Subjects LIKE ?
    """
    # Use parameter binding for safety, adding wildcards
    cursor.execute(query, f"%{subject_search}%")
    rows = cursor.fetchall()

    if not rows:
        print(f"\nNo teachers found for subject '{subject_search}'.\n")
    else:
        print(f"\n--- Teachers who teach '{subject_search}' ---")
        for row in rows:
            teacher_id = row[0]
            name = row[1]
            cnic = row[2]
            is_ct = "Yes" if row[3] else "No"
            subjects = row[4]
            print(f"ID: {teacher_id}, Name: {name}, CNIC: {cnic}, ClassTeacher: {is_ct}, Subjects: {subjects}")
    conn.close()

def view_teachers_by_class():
    """
    Prompts user for a class name (and optionally a section),
    then lists teachers assigned to that class in the TeacherClasses table.
    """
    class_name = input("\nEnter the class name to search (e.g., 'Class 1'): ").strip()
    if not class_name:
        print("[ERROR] Class name cannot be empty.")
        return

    section = input("Enter the section to search (or press Enter to skip): ").strip()

    conn = get_connection()
    cursor = conn.cursor()

    if section:
        query = """
            SELECT T.ID, T.Name, T.CNIC, T.IsClassTeacher, T.Subjects, TC.ClassName, TC.Section
            FROM Teachers T
            JOIN TeacherClasses TC ON T.ID = TC.TeacherID
            WHERE TC.ClassName = ? AND TC.Section = ?
        """
        cursor.execute(query, (class_name, section))
    else:
        query = """
            SELECT T.ID, T.Name, T.CNIC, T.IsClassTeacher, T.Subjects, TC.ClassName, TC.Section
            FROM Teachers T
            JOIN TeacherClasses TC ON T.ID = TC.TeacherID
            WHERE TC.ClassName = ?
        """
        cursor.execute(query, (class_name,))

    rows = cursor.fetchall()
    if not rows:
        msg_sec = f" and section '{section}'" if section else ""
        print(f"\nNo teachers found for class '{class_name}'{msg_sec}.\n")
    else:
        msg_sec = f" Section '{section}'" if section else ""
        print(f"\n--- Teachers for class '{class_name}'{msg_sec} ---")
        for row in rows:
            teacher_id = row[0]
            name = row[1]
            cnic = row[2]
            is_ct = "Yes" if row[3] else "No"
            subjects = row[4]
            class_assigned = row[5]
            sec_assigned = row[6]
            print(
                f"ID: {teacher_id}, Name: {name}, CNIC: {cnic}, "
                f"ClassTeacher: {is_ct}, Subjects: {subjects}, "
                f"Class: {class_assigned}, Section: {sec_assigned}"
            )
    conn.close()

def add_teacher_manual():
    """
    Prompt user to manually add a teacher to the Teachers table.
    Required fields: Name, CNIC (unique), IsClassTeacher (Y/N), Subjects (comma-separated).
    """
    print("\n--- Add Teacher (Manual) ---")

    name = input("Enter teacher name (type 'esc' to cancel): ").strip()
    if name.lower() == 'esc':
        return

    if not name:
        print("[ERROR] Name cannot be empty.")
        return

    cnic_raw = input("Enter teacher CNIC (13 digits, dashes optional, 'esc' to cancel): ").strip()
    if cnic_raw.lower() == 'esc':
        return
    cnic = format_cnic(cnic_raw)
    if cnic is None:
        print("[ERROR] Invalid CNIC format.")
        return

    # IsClassTeacher
    is_class_teacher_input = input("Is this teacher a Class Teacher? (Y/N): ").strip().upper()
    if is_class_teacher_input.lower() == 'esc':
        return
    if is_class_teacher_input not in ['Y', 'N']:
        print("[ERROR] Invalid input for class teacher. Must be Y or N.")
        return
    is_class_teacher = True if is_class_teacher_input == 'Y' else False

    # Subjects
    # We can accept a comma-separated string
    subjects = input("Enter subjects (comma-separated), or press Enter if none: ").strip()
    if subjects.lower() == 'esc':
        return

    # Insert into database
    conn = get_connection()
    cursor = conn.cursor()

    insert_stmt = """
        INSERT INTO Teachers (Name, CNIC, IsClassTeacher, Subjects)
        VALUES (?, ?, ?, ?)
    """

    try:
        cursor.execute(insert_stmt, (name, cnic, int(is_class_teacher), subjects))
        conn.commit()
        print(f"[INFO] Teacher '{name}' added successfully.")
    except pyodbc.IntegrityError as e:
        # If there's a unique constraint on CNIC, handle it
        print(f"[ERROR] Could not add teacher. Possible duplicate CNIC '{cnic}'. {e}")
        conn.rollback()
    except Exception as e:
        print(f"[ERROR] Could not add teacher: {e}")
        conn.rollback()
    finally:
        conn.close()

def add_teachers_csv():
    """
    Bulk add teachers from a CSV file.
    Expected CSV columns (in order):
    Name, CNIC, IsClassTeacher (Y/N), Subjects (comma-separated)
    Example row:
        "Ali Khan","4210112345671","Y","Math,English"
    """
    print("\n--- Add Teachers (CSV) ---")
    file_path = input("Enter the CSV file path (type 'esc' to cancel): ").strip()
    if file_path.lower() == 'esc':
        return

    try:
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # If your CSV has no header, comment this out

            conn = get_connection()
            cursor = conn.cursor()

            success_count = 0
            row_num = 1

            for row in reader:
                row_num += 1
                if len(row) < 4:
                    print(f"[WARNING] Row {row_num} has insufficient columns. Skipping.")
                    continue

                name, cnic_raw, class_teacher_flag, subjects = row

                name = name.strip()
                if not name:
                    print(f"[WARNING] Empty teacher name at row {row_num}. Skipping.")
                    continue

                cnic = format_cnic(cnic_raw.strip())
                if cnic is None:
                    print(f"[WARNING] Invalid CNIC at row {row_num}. Skipping.")
                    continue

                class_teacher_flag = class_teacher_flag.strip().upper()
                if class_teacher_flag not in ['Y','N']:
                    print(f"[WARNING] Invalid IsClassTeacher flag at row {row_num}. Must be Y or N. Skipping.")
                    continue
                is_class_teacher = True if class_teacher_flag == 'Y' else False

                subjects = subjects.strip() if subjects else ""

                insert_stmt = """
                    INSERT INTO Teachers (Name, CNIC, IsClassTeacher, Subjects)
                    VALUES (?, ?, ?, ?)
                """

                try:
                    cursor.execute(insert_stmt, (name, cnic, int(is_class_teacher), subjects))
                    success_count += 1
                except pyodbc.IntegrityError as e:
                    print(f"[ERROR] Duplicate CNIC '{cnic}' at row {row_num}. Skipping. {e}")
                except Exception as e:
                    print(f"[ERROR] Could not insert teacher at row {row_num}: {e}")

            conn.commit()
            cursor.close()
            conn.close()

            print(f"[INFO] CSV Import Complete. Successfully added {success_count} teachers.")

    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
    except Exception as e:
        print(f"[ERROR] An error occurred while processing the CSV file: {e}")


def assign_roles_to_teachers():
    """
    Prompts user to search a teacher by ID or CNIC, then sets their role.
    Because "all class teachers are also subject teachers," 
    setting IsClassTeacher = 1 means they're also subject teachers.
    """
    print("\n--- Assign Roles To Teachers ---")
    teacher_id_or_cnic = input("Enter Teacher ID or CNIC (type 'esc' to cancel): ").strip()
    if teacher_id_or_cnic.lower() == 'esc':
        return

    conn = get_connection()
    cursor = conn.cursor()

    # Try searching by numeric ID first
    teacher = None
    try:
        teacher_id_int = int(teacher_id_or_cnic)
        cursor.execute("SELECT ID, Name, CNIC, IsClassTeacher, Subjects FROM Teachers WHERE ID = ?", teacher_id_int)
        teacher = cursor.fetchone()
    except ValueError:
        # If not an integer, assume it's a CNIC
        pass

    if not teacher:
        # If teacher not found by ID, try searching by CNIC
        cursor.execute("SELECT ID, Name, CNIC, IsClassTeacher, Subjects FROM Teachers WHERE CNIC = ?", teacher_id_or_cnic)
        teacher = cursor.fetchone()

    if not teacher:
        print("[ERROR] Teacher not found.")
        conn.close()
        return

    teacher_id = teacher[0]
    teacher_name = teacher[1]
    teacher_cnic = teacher[2]
    is_class_teacher = teacher[3]
    subjects = teacher[4]
    print(f"\nFound Teacher => ID: {teacher_id}, Name: {teacher_name}, CNIC: {teacher_cnic},")
    print(f"   IsClassTeacher: {is_class_teacher}, Subjects: {subjects}\n")

    # Prompt new role
    new_role = input("Assign role: (C)lass Teacher or (S)ubject Teacher? (type 'esc' to cancel) ").strip().upper()
    if new_role.lower() == 'esc':
        conn.close()
        return
    if new_role not in ['C','S']:
        print("[ERROR] Invalid choice. Must be 'C' or 'S'.")
        conn.close()
        return

    if new_role == 'C':
        # "All class teachers are also subject teachers"
        update_sql = "UPDATE Teachers SET IsClassTeacher = 1 WHERE ID = ?"
    else:
        # Subject teacher only
        update_sql = "UPDATE Teachers SET IsClassTeacher = 0 WHERE ID = ?"

    try:
        cursor.execute(update_sql, teacher_id)
        conn.commit()
        print(f"[INFO] Role updated successfully for teacher ID {teacher_id}. IsClassTeacher={new_role=='C'}")
    except Exception as e:
        print(f"[ERROR] Could not update role: {e}")
        conn.rollback()

    conn.close()


def assign_classes_to_teachers():
    """
    Prompts user for a teacher (by ID or CNIC), then assigns a class + section to them
    by inserting into the TeacherClasses table.
    """
    print("\n--- Assign Classes To Teachers ---")
    teacher_id_or_cnic = input("Enter Teacher ID or CNIC (type 'esc' to cancel): ").strip()
    if teacher_id_or_cnic.lower() == 'esc':
        return

    conn = get_connection()
    cursor = conn.cursor()

    # Try searching by numeric ID first
    teacher = None
    try:
        teacher_id_int = int(teacher_id_or_cnic)
        cursor.execute("SELECT ID, Name, CNIC FROM Teachers WHERE ID = ?", teacher_id_int)
        teacher = cursor.fetchone()
    except ValueError:
        # Not an integer, assume CNIC
        pass

    if not teacher:
        # If teacher not found by ID, try CNIC
        cursor.execute("SELECT ID, Name, CNIC FROM Teachers WHERE CNIC = ?", teacher_id_or_cnic)
        teacher = cursor.fetchone()

    if not teacher:
        print("[ERROR] Teacher not found.")
        conn.close()
        return

    teacher_id = teacher[0]
    teacher_name = teacher[1]
    teacher_cnic = teacher[2]
    print(f"\nFound Teacher => ID: {teacher_id}, Name: {teacher_name}, CNIC: {teacher_cnic}")

    class_name = input("Enter Class Name (e.g., 'Class 1'): ").strip()
    if not class_name:
        print("[ERROR] Class name cannot be empty.")
        conn.close()
        return

    section = input("Enter Section (e.g., 'A'): ").strip()
    if not section:
        print("[ERROR] Section cannot be empty.")
        conn.close()
        return

    # Insert into TeacherClasses
    insert_sql = """
        INSERT INTO TeacherClasses (TeacherID, ClassName, Section)
        VALUES (?, ?, ?)
    """
    try:
        cursor.execute(insert_sql, (teacher_id, class_name, section))
        conn.commit()
        print(f"[INFO] Class '{class_name}' Section '{section}' assigned to teacher ID {teacher_id} successfully.")
    except Exception as e:
        print(f"[ERROR] Could not assign class: {e}")
        conn.rollback()

    conn.close()

###############################################################################
# 3. Fee Management
###############################################################################

def fee_management_menu():
    while True:
        print("\n--- Fee Management ---")
        print("1. Add/Update Fee Policy")
        print("2. View Fee Policy")
        print("3. Generate Monthly Fee Vouchers")
        print("4. Back To Main Menu")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            add_update_fee_policy_menu()
        elif choice == "2":
            view_fee_policy()
        elif choice == "3":
            generate_monthly_fee_vouchers_menu()
        elif choice == "4" or choice.lower() == 'esc':
            return
        else:
            print("Invalid choice. Please try again.")

def add_update_fee_policy_menu():
    while True:
        print("\n-- Add/Update Fee Policy --")
        print("1. Update/Modify Policy")
        print("2. Add Policy")
        print("3. Back To Fee Management")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            update_modify_policy()
        elif choice == "2":
            add_policy_menu()
        elif choice == "3" or choice.lower() == 'esc':
            return
        else:
            print("Invalid choice. Please try again.")

def update_modify_policy():
    print("\n[INFO] Update/Modify Policy")
    print("1. Registration Policy")
    print("2. Admission Policy")
    print("3. General Policy (Class Wise)")
    
    choice = input("Select Policy to Modify (1-3): ").strip()

    if choice == "1":
        add_registration_policy()
    elif choice == "2":
        add_admission_policy()
    elif choice == "3":
        add_general_policy()
    else:
        print("\n[ERROR] Invalid Choice")

def add_policy_menu():
    while True:
        print("\n-- Add Policy --")
        print("1. Registration Policy")
        print("2. Admission Policy")
        print("3. General Policy (Class Wise)")
        print("4. Back To Fee Management")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            add_registration_policy()
        elif choice == "2":
            add_admission_policy()
        elif choice == "3":
            add_general_policy()
        elif choice == "4" or choice.lower() == 'esc':
            return
        else:
            print("Invalid choice. Please try again.")

def add_registration_policy():
    print("\n-- Add Registration Policy --")
    registration_fee = input("Enter Registration Fee: ").strip()
    print(f"[INFO] Registration policy added with fee: {registration_fee}")

def add_admission_policy():
    print("\n-- Add Admission Policy --")
    admission_fee = input("Enter Admission Fee: ").strip()
    security_deposit = input("Enter Security Deposit: ").strip()
    print(f"[INFO] Admission policy added with Admission Fee: {admission_fee} and Security Deposit: {security_deposit}")

def add_general_policy():
    print("\n-- Add General Policy (Class Wise) --")
    
    # Input for class name
    class_name = input("Enter Class Name (e.g., Class 1): ").strip()
    
    # Input for monthly fee
    monthly_fee = input("Enter Monthly Fee: ").strip()
    
    # Input for annual charges (charged once a year)
    annual_charges = input("Enter Annual Charges: ").strip()
    
    # Input for other annual charges (charged once a year)
    other_charges = input("Enter Other Annual Charges: ").strip()
    
    # Input for computer lab charges (charged monthly)
    computer_lab_charges = input("Enter Monthly Computer Lab Charges: ").strip()
    
    # Input for lab charges (charged monthly)
    lab_charges = input("Enter Monthly Lab Charges: ").strip()
    
    # Displaying the general policy summary
    print(f"[INFO] General policy added for {class_name} with the following details:")
    print(f"  - Monthly Fee: {monthly_fee}")
    print(f"  - Annual Charges (once a year): {annual_charges}")
    print(f"  - Other Annual Charges (once a year): {other_charges}")
    print(f"  - Monthly Computer Lab Charges: {computer_lab_charges}")
    print(f"  - Monthly Lab Charges: {lab_charges}")

def view_fee_policy():
    print("\n[INFO] Displaying all Fee Policies (Details will be fetched from the database)")

def generate_monthly_fee_vouchers_menu():
    while True:
        print("\n--- Generate Monthly Fee Vouchers ---")
        print("1. Generate Fee Voucher")
        print("2. View Fee Voucher (Print Option Available)")
        print("3. Back To Fee Management")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            generate_fee_voucher()
        elif choice == "2":
            view_fee_voucher()
        elif choice == "3" or choice.lower() == 'esc':
            return
        else:
            print("Invalid choice. Please try again.")

# Global storage for fee policies
fee_policies = {
    "registration": None,  # Stores registration fee
    "admission": {"fee": None, "security_deposit": None},  # Stores admission fee and security deposit
    "general": []  # Stores a list of class-wise general policies
}

def view_fee_policy():
    print("\n[INFO] Displaying all Fee Policies:")
    
    # Display Registration Policy
    if fee_policies["registration"]:
        print(f"\nRegistration Policy:")
        print(f"  - Registration Fee: {fee_policies['registration']}")
    else:
        print("\nRegistration Policy: Not Defined")

    # Display Admission Policy
    if fee_policies["admission"]["fee"] or fee_policies["admission"]["security_deposit"]:
        print(f"\nAdmission Policy:")
        print(f"  - Admission Fee: {fee_policies['admission']['fee'] or 'Not Defined'}")
        print(f"  - Security Deposit: {fee_policies['admission']['security_deposit'] or 'Not Defined'}")
    else:
        print("\nAdmission Policy: Not Defined")

    # Display General Policies
    if fee_policies["general"]:
        print("\nGeneral Policies (Class Wise):")
        for policy in fee_policies["general"]:
            print(f"  - Class: {policy['class_name']}")
            print(f"    * Monthly Fee: {policy['monthly_fee']}")
            print(f"    * Annual Charges: {policy['annual_charges']}")
            print(f"    * Other Charges: {policy['other_charges']}")
            print(f"    * Computer Lab Charges: {policy['computer_lab_charges']}")
            print(f"    * Lab Charges: {policy['lab_charges']}")
    else:
        print("\nGeneral Policies: Not Defined")

def add_registration_policy():
    global fee_policies
    registration_fee = input("Enter Registration Fee: ").strip()
    fee_policies["registration"] = registration_fee
    print(f"[INFO] Registration policy updated with Registration Fee: {registration_fee}")

def add_admission_policy():
    global fee_policies
    admission_fee = input("Enter Admission Fee: ").strip()
    security_deposit = input("Enter Security Deposit: ").strip()
    fee_policies["admission"]["fee"] = admission_fee
    fee_policies["admission"]["security_deposit"] = security_deposit
    print(f"[INFO] Admission policy updated with Admission Fee: {admission_fee} and Security Deposit: {security_deposit}")

def add_general_policy():
    global fee_policies
    print("\n-- Add General Policy (Class Wise) --")
    class_name = input("Enter Class Name (e.g., Class 1): ").strip()
    monthly_fee = input("Enter Monthly Fee: ").strip()
    annual_charges = input("Enter Annual Charges: ").strip()
    other_charges = input("Enter Other Annual Charges: ").strip()
    computer_lab_charges = input("Enter Monthly Computer Lab Charges: ").strip()
    lab_charges = input("Enter Monthly Lab Charges: ").strip()

    policy = {
        "class_name": class_name,
        "monthly_fee": monthly_fee,
        "annual_charges": annual_charges,
        "other_charges": other_charges,
        "computer_lab_charges": computer_lab_charges,
        "lab_charges": lab_charges,
    }
    fee_policies["general"].append(policy)
    print(f"[INFO] General policy added for {class_name}.")

# Updated fee_management_menu() to use these functions 
def generate_fee_voucher():
    print("\n[INFO] Generate Fee Voucher functionality will process fee details and generate vouchers.")

def view_fee_voucher():
    print("\n[INFO] View Fee Voucher functionality will display generated vouchers with print options.")


###############################################################################
# 4. Reports
###############################################################################

def reports_menu():
    while True:
        print("\n--- Reports ---")
        print("1. Class List")
        print("2. Marks Sheet")
        print("3. Tabulation Sheet")
        print("4. Individual report cards")
        print("5. Back To Main Menu")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            report_class_list()
        elif choice == "2":
            report_marks_sheet()
        elif choice == "3":
            report_tabulation_sheet()
        elif choice == "4":
            report_individual_cards()
        elif choice == "5":
            return
        elif choice.lower() == 'esc':
            return
        else:
            print("Invalid choice. Please try again.")

def report_class_list():
    """
    Required Format: 
    Class ________  Sec ________
    Display class teacher/subject teacher, then all students with GRNo, Student Name, Remarks column
    """
    print("\n[INFO] Class List Report - NOT IMPLEMENTED (Placeholder)")

def report_marks_sheet():
    """
    Required Format: 
    Class ________  Sec ________
    Contain the same info as class list but with marks, percentage, grade, etc.
    """
    print("\n[INFO] Marks Sheet Report - NOT IMPLEMENTED (Placeholder)")

def report_tabulation_sheet():
    """
    For class teachers/management only. 
    Consolidates all subjects in one sheet.
    """
    print("\n[INFO] Tabulation Sheet Report - NOT IMPLEMENTED (Placeholder)")

def report_individual_cards():
    """
    For individual student(s) by GRNo or by name
    """
    print("\n[INFO] Individual Report Cards - NOT IMPLEMENTED (Placeholder)")


###############################################################################
# Main entry point
###############################################################################

def main():
    initialize_database()  # Ensure tables exist
    main_menu()

if __name__ == "__main__":
    main()
