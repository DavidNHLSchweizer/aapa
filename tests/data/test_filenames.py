
from data.general.const import FileType, MijlpaalType
from process.input.importing.filename_parser import AanvraagDetector, EindBeoordelingDetector, EindVerslagDetector, FileTypeDetector, FilenameDetector, OnderzoeksVerslagDetector, PlanVanAanpakDetector, PresentatieBeoordelingDetector, ProductBeoordelingDetector, TechnischVerslagDetector

# deze testcases komen allemaal voor in de huidige directories
testcases = { MijlpaalType.AANVRAAG: 
             [                 
                {'filename': r'Beoordeling aanvraag Mimi Hoeksema.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.AANVRAAG)},
                {'filename': r'Beoordeling aanvraag Mimi Hoeksema.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.AANVRAAG)},
                {'filename': r'1. Aanvraag toelating afstuderen.docx', 'expected': (FileType.INVALID_DOCX, MijlpaalType.AANVRAAG)},
                {'filename': r'1. Aanvraag toelating afstuderen.pdf', 'expected': (FileType.INVALID_PDF, MijlpaalType.AANVRAAG)},
                {'filename': r'1. Aanvraag toelating afstuderen (2).docx', 'expected': (FileType.INVALID_DOCX, MijlpaalType.AANVRAAG)},
                {'filename': r'1. Aanvraag toelating afstuderen.pdf Mimi Hoeksema', 'expected': (FileType.INVALID_PDF, MijlpaalType.AANVRAAG)},
                {'filename': r'2. Beoordeling afstudeeropdracht - Erica Plantenga.docx', 'expected': (FileType.AANVRAAG_OTHER, MijlpaalType.AANVRAAG)},
                {'filename': r'2. Beoordeling afstudeeropdracht - Erica Plantenga.pdf', 'expected': (FileType.AANVRAAG_PDF, MijlpaalType.AANVRAAG)},
                {'filename': r'2. Beoordeling afstudeeropdracht - Erica Plantenga.docx', 'expected': (FileType.AANVRAAG_OTHER, MijlpaalType.AANVRAAG)},

              ],
              MijlpaalType.PVA: 
             [                 
                {'filename': r'3. Beoordeling plan van aanpak.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.PVA)},
                {'filename': r'3. Beoordeling plan van aanpak.docx.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.PVA)},
                {'filename': r'3. Beoordeling plan van aanpak gezamenlijk.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.PVA)},
                {'filename': r'3. Beoordeling plan van aanpak ex1.docx', 'expected': (FileType.GRADE_FORM_EX1_DOCX, MijlpaalType.PVA)},
                {'filename': r'3. Beoordeling plan van aanpak ex1 copy.docx', 'expected': (FileType.GRADE_FORM_EX1_DOCX, MijlpaalType.PVA)},
                {'filename': r'3. Beoordeling plan van aanpak ex2.docx', 'expected': (FileType.GRADE_FORM_EX2_DOCX, MijlpaalType.PVA)},
                {'filename': r'3. Beoordeling plan van aanpak - onvoldoende.docx', 'expected': (FileType.GRADE_FORM_DOCX,MijlpaalType.PVA)},     
                {'filename': r'3. Beoordeling plan van aanpak - voldoende.docx', 'expected': (FileType.GRADE_FORM_DOCX,MijlpaalType.PVA)},     
                {'filename': r'3. Beoordeling plan van aanpak 1e keer.docx', 'expected': (FileType.GRADE_FORM_DOCX,MijlpaalType.PVA)},     
                {'filename': r'3. Beoordeling plan van aanpak 2e keer.docx', 'expected': (FileType.GRADE_FORM_DOCX,MijlpaalType.PVA)},     
                {'filename': r'3. Beoordeling plan van aanpak 2e versie.docx', 'expected': (FileType.GRADE_FORM_DOCX,MijlpaalType.PVA)},     
                {'filename': r'3. Beoordeling plan van aanpak Erica Hoeksema.docx', 'expected': (FileType.GRADE_FORM_DOCX,MijlpaalType.PVA)},     
                {'filename': r'3. Beoordeling plan van aanpak ex1 copy.docx', 'expected': (FileType.GRADE_FORM_EX1_DOCX, MijlpaalType.PVA)},
                {'filename': r'3. Beoordeling plan van aanpak ex2 - Erica Hoeksema.docx', 'expected': (FileType.GRADE_FORM_EX2_DOCX, MijlpaalType.PVA)},
                {'filename': r'3. Beoordeling plan van aanpak.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.PVA)},
                {'filename': r'3. Beoordeling plan van aanpak gezamenlijk.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.PVA)},
              ],
              MijlpaalType.ONDERZOEKS_VERSLAG: 
              [                 
                {'filename': r'4. Beoordeling onderzoeksverslag gezamenlijk.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.ONDERZOEKS_VERSLAG)},
                {'filename': r'4. Beoordeling onderzoeksverslag ex1.docx', 'expected': (FileType.GRADE_FORM_EX1_DOCX, MijlpaalType.ONDERZOEKS_VERSLAG)},
                {'filename': r'4. Beoordeling onderzoeksverslag ex2.docx', 'expected': (FileType.GRADE_FORM_EX2_DOCX, MijlpaalType.ONDERZOEKS_VERSLAG)},
                {'filename': r'4. Beoordeling onderzoeksverslag ex3.docx', 'expected': (FileType.GRADE_FORM_EX3_DOCX, MijlpaalType.ONDERZOEKS_VERSLAG)},
                {'filename': r'4. Beoordeling onderzoeksverslag gezamenlijk.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.ONDERZOEKS_VERSLAG)},
                {'filename': r'4. Beoordeling onderzoeksverslag ex1.PDF', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.ONDERZOEKS_VERSLAG)},
                {'filename': r'4. Beoordeling onderzoeksverslag ex2.PDF', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.ONDERZOEKS_VERSLAG)},
                {'filename': r'4. Beoordeling onderzoeksverslag ex1 (1).docx', 'expected': (FileType.GRADE_FORM_EX1_DOCX, MijlpaalType.ONDERZOEKS_VERSLAG)},
                {'filename': r'4. Beoordeling onderzoeksverslag ex1 Erica Hoeksema.docx', 'expected': (FileType.GRADE_FORM_EX1_DOCX, MijlpaalType.ONDERZOEKS_VERSLAG)},
                {'filename': r'4. Beoordeling onderzoeksverslag ex2 (MiMi).docx', 'expected': (FileType.GRADE_FORM_EX2_DOCX, MijlpaalType.ONDERZOEKS_VERSLAG)},
                {'filename': r'4. Beoordeling onderzoeksverslag - gezamenlijk.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.ONDERZOEKS_VERSLAG)},
                {'filename': r'4. Beoordeling onderzoeksverslag - gezamenlijk.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.ONDERZOEKS_VERSLAG)},
                {'filename': r'4. Beoordeling onderzoeksverslag gezamelijk.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.ONDERZOEKS_VERSLAG)},
                {'filename': r'4. Beoordeling onderzoeksverslag Gezamelijk.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.ONDERZOEKS_VERSLAG)},
                {'filename': r'4. Beoordeling onderzoeksverslag.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.ONDERZOEKS_VERSLAG)},
              ],
              MijlpaalType.TECHNISCH_VERSLAG: 
              [                 
                {'filename': r'5. Beoordeling technisch verslag gezamenlijk.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag ex1.docx', 'expected': (FileType.GRADE_FORM_EX1_DOCX, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag ex2.docx', 'expected': (FileType.GRADE_FORM_EX2_DOCX, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag ex3.docx', 'expected': (FileType.GRADE_FORM_EX3_DOCX, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag gezamenlijk.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag ex1.PDF', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag ex2.PDF', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag ex1 (1).docx', 'expected': (FileType.GRADE_FORM_EX1_DOCX, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag ex1 Erica Hoeksema.docx', 'expected': (FileType.GRADE_FORM_EX1_DOCX, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag ex2 (MiMi).docx', 'expected': (FileType.GRADE_FORM_EX2_DOCX, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag - gezamenlijk.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag - gezamenlijk.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag gezamelijk.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag Gezamelijk.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag Mimi ex2x1.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag ex2-macbookair.docx', 'expected': (FileType.GRADE_FORM_EX2_DOCX, MijlpaalType.TECHNISCH_VERSLAG)},
                {'filename': r'5. Beoordeling technisch verslag.ex2.docx', 'expected': (FileType.GRADE_FORM_EX2_DOCX, MijlpaalType.TECHNISCH_VERSLAG)},

              ],
              MijlpaalType.EIND_VERSLAG: 
              #hier zijn nog geen voorbeelden van
              [                 
                {'filename': r'5. Beoordeling eindverslag gezamenlijk.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.EIND_VERSLAG)},
                {'filename': r'5. Beoordeling eindverslag ex1.docx', 'expected': (FileType.GRADE_FORM_EX1_DOCX, MijlpaalType.EIND_VERSLAG)},
                {'filename': r'5. Beoordeling eindverslag ex2.docx', 'expected': (FileType.GRADE_FORM_EX2_DOCX, MijlpaalType.EIND_VERSLAG)},
                {'filename': r'5. Beoordeling eindverslag ex3.docx', 'expected': (FileType.GRADE_FORM_EX3_DOCX, MijlpaalType.EIND_VERSLAG)},
                {'filename': r'5. Beoordeling eindverslag gezamenlijk.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.EIND_VERSLAG)},
                {'filename': r'5. Beoordeling eindverslag ex1.PDF', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.EIND_VERSLAG)},
                {'filename': r'5. Beoordeling eindverslag ex2.PDF', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.EIND_VERSLAG)},
              ],
              MijlpaalType.PRODUCT_BEOORDELING: 
              [                 
                {'filename': r'6. Beoordeling product.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.PRODUCT_BEOORDELING)},
                {'filename': r'6. Beoordeling product ingevuld-bedrijfsbegeleider.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.PRODUCT_BEOORDELING)},
                {'filename': r'6. Beoordeling product ingevuld-bedrijfsbegeleider.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.PRODUCT_BEOORDELING)},
                {'filename': r'6. Beoordeling product Ludo Sanders[5].docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.PRODUCT_BEOORDELING)},
                {'filename': r'6. Beoordeling product - Henry, Niels, Thomas 20210625 - met handtekening.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.PRODUCT_BEOORDELING)},
                {'filename': r'6._Beoordeling product.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.PRODUCT_BEOORDELING)},
                {'filename': r'6._Beoordeling product.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.PRODUCT_BEOORDELING)},
                {'filename': r'6._Beoordeling product_Mimi_ingevuld.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.PRODUCT_BEOORDELING)},
                {'filename': r'6.+Beoordeling+product.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.PRODUCT_BEOORDELING)},
                {'filename': r'6.+Beoordeling+product+SINUS_COSINUS.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.PRODUCT_BEOORDELING)},
              ],
              MijlpaalType.PRESENTATIE: 
              [                 
                {'filename': r'7. Beoordeling presentatie.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.PRESENTATIE)},
                {'filename': r'7. Beoordeling presentatie.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.PRESENTATIE)},
                {'filename': r'7. Beoordeling presentatie-macbook-pro.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.PRESENTATIE)},
              ],
              MijlpaalType.EINDBEOORDELING: 
              [                 
                {'filename': r'8. Eindbeoordeling afstuderen.docx', 'expected': (FileType.GRADE_FORM_DOCX, MijlpaalType.EINDBEOORDELING)},
                {'filename': r'8. Eindbeoordeling afstuderen.pdf', 'expected': (FileType.GRADE_FORM_PDF, MijlpaalType.EINDBEOORDELING)},
              ],
             }

def _test_positive(detector: FilenameDetector):
    for testcase in testcases[detector.mijlpaal_type]:
        filetype,detected_mijlpaal_type = detector.detect(testcase['filename'])
        expected_filetype, expected_mijlpaal_type = testcase['expected']
        assert filetype == expected_filetype
        assert detected_mijlpaal_type == expected_mijlpaal_type

def _test_negative(detector: FilenameDetector):
    for mijlpaal_type in MijlpaalType:
        if detector.mijlpaal_type == mijlpaal_type:
            continue
        for testcase in testcases.get(mijlpaal_type, []):                  
            filetype,detected_mijlpaal_type = detector.detect(testcase['filename'])
            expected_filetype, expected_mijlpaal_type = FileType.UNKNOWN, MijlpaalType.UNKNOWN
            assert filetype == expected_filetype
            assert detected_mijlpaal_type == expected_mijlpaal_type

def test_Aanvraag_positive():
    _test_positive(AanvraagDetector())
def test_Aanvraag_negative():
    _test_negative(AanvraagDetector())

def test_PVA_positive():
    _test_positive(PlanVanAanpakDetector())
def test_PVA_negative():
    _test_negative(PlanVanAanpakDetector())

def test_OnderzoeksVerslag_positive():
    _test_positive(OnderzoeksVerslagDetector())
def test_OnderzoeksVerslag_negative():
    _test_negative(OnderzoeksVerslagDetector())

def test_TechnischVerslag_positive():
    _test_positive(TechnischVerslagDetector())
def test_TechnischVerslag_negative():
    _test_negative(TechnischVerslagDetector())

def test_EindVerslag_positive():
    _test_positive(EindVerslagDetector())
def test_EindVerslag_negative():
    _test_negative(EindVerslagDetector())

def test_Product_positive():
    _test_positive(ProductBeoordelingDetector())
def test_Product_negative():
    _test_negative(ProductBeoordelingDetector())

def test_Presentatie_positive():
    _test_positive(PresentatieBeoordelingDetector())
def test_Presentatie_negative():
    _test_negative(PresentatieBeoordelingDetector())

def test_Eindbeoordeling_positive():
    _test_positive(EindBeoordelingDetector())
def test_Eindbeoordeling_negative():
    _test_negative(EindBeoordelingDetector())

def test_FileTypeDetector():
    FTD = FileTypeDetector()
    for mijlpaal_type in MijlpaalType:
        mijlpaal_cases = testcases.get(mijlpaal_type, [])
        for testcase in mijlpaal_cases:
            file_type,detected_mijlpaal_type = FTD.detect(testcase['filename'])
            expected_filetype,expected_mijlpaal_type = testcase['expected']
            assert file_type == expected_filetype        
            assert detected_mijlpaal_type == expected_mijlpaal_type