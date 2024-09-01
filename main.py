import sys
from abc import abstractmethod
from time import sleep
from collections import Counter
from queue import Queue
from threading import Lock, Thread
from functools import reduce


class Wordlist:
    # TODO: Get NYT Letteboxed wordlist
    words = []


class LetterboxedSolver:
    def __init__(self, sides, threads=12):
        self.sides = sides
        self.letter_list = [letter for side in self.sides for letter in side]
        self.letter_count = Counter(self.letter_list)
        self.words = Wordlist.words

        # word -> list_of_possible_next_words
        self.word_connect = {}
        # sequence -> repetitions
        self.failed_sequences = {}
        self.solutions = []

        self.task_queue = Queue()
        self.threads = 12
        self.workers = []
        self.lock = Lock()
        self.progress_lock = Lock()
        self.progress_end = False
        self.initialise_word_workers()

        self.cut_down_words()
        self.create_word_graph()

    # A possible word uses only available letters and doesn't use the same side twice in a row
    def is_word_possible_for_given_sides(self, word):
        last_side_index = -1
        for letter in word:
            side_index = last_side_index
            for index, letters in enumerate(self.sides):
                if letter in letters and index != last_side_index:
                    side_index = index
            if side_index != last_side_index:
                last_side_index = side_index
            else:
                break
        else:
            return True
        return False

    def cut_down_words(self):
        self.words = list(filter(self.is_word_possible_for_given_sides, Wordlist.words))

        # As long as I do not have the wordlist, I can insert given day's available word set
        # It is provided in NYT Letterboxed window.gameData
        # 31.08.2024 data
        self.words = ["EON", "EONS", "NOIRE", "FRISE", "FIRMUS", "FER", "MEIN", "MER", "NON", "MON", "EMS", "EMERSE", "EMERSION", "EMERY", "EMESIS", "EMO", "EMOS", "EMU", "EMUS", "MERE", "EOSIN", "EPONYM", "EPONYMS", "EPONYMY", "EPONYMOUS", "ERE", "ERF", "ESE", "ESES", "ESPOUSE", "ESPOUSES", "ESPOUSER", "ESPOUSERS", "ESPY", "EYE", "EYES", "EYRE", "EYRES", "EYRIE", "EYRIES", "EYRIR", "FEIS", "FEME", "FEM", "FEMS", "FEMUR", "FEMURS", "FERN", "FERNS", "FERNY", "FEY", "FEYER", "FEZ", "FIE", "FIEF", "FIERI", "FIERY", "FIERIER", "FIFE", "FIFES", "FIFER", "FIFERS", "FIN", "FINS", "FINIS", "FINO", "FINOS", "FIR", "FIRS", "FIRE", "FIRES", "FIRER", "FIRERS", "FIRIE", "FIRIES", "FIRM", "FIRMER", "FIRMS", "FIRN", "FIRNI", "FOE", "FOES", "FOEFIE", "FOIE", "FONS", "FOP", "FOPS", "FOU", "FOUR", "FOURS", "FOURSOME", "FOURSOMES", "FOYER", "FOYERS", "FREON", "FRIEZE", "FRIEZES", "FRY", "FRIES", "FRYER", "FRIER", "FRYERS", "FRIERS", "FUFU", "FUME", "FUMES", "FUMY", "FUR", "FURS", "FURIOSO", "FURIOUS", "FURY", "FURIES", "FUSE", "FUSES", "FUZE", "FUZES", "FUSION", "FUSIONS", "FUSIONISM", "INS", "INFER", "INFERS", "INFERNO", "INFERNOS", "INFIRM", "INFO", "INFUSE", "INFUSES", "INFUSER", "INFUSERS", "INFUSION", "INFUSIONS", "INION", "INIONS", "INSPO", "INSPOS", "INSURE", "INSURES", "INSURER", "INSURERS", "ION", "IONS", "IONIZE", "IONISE", "IONIZES", "IONISES", "IONIZER", "IONISER", "IONIZERS", "IONISERS", "IONOMER", "IONOMERS", "IRE", "IRIE", "IRIS", "IRISES", "ISM", "ISMS", "ISOMER", "ISOMERS", "ISOMERISM", "ISOMERIZE", "ISOMERISE", "ISOMERIZES", "ISOMERISES", "PYE", "REO", "OUR", "MEIOSIS", "MEIOSES", "MEME", "MEMES", "MEMO", "MEMOS", "MEMOIR", "MEMOIRS", "MERES", "MERINO", "MERINOS", "MESMERISM", "MESMERIZE", "MESMERISE", "MESMERIZES", "MESMERISES", "MESMERIZER", "MESMERISER", "MESMERIZERS", "MESMERISERS", "MESOMERISM", "MESON", "MESONS", "MEZE", "MEZES", "MEZEREON", "MEZEREONS", "MYOSIS", "MOE", "MOFO", "MOFOS", "MOI", "MOIRE", "MOIRES", "MOM", "MOMS", "MOMO", "MOMOS", "MONIES", "MONISM", "MONISMS", "MONO", "MONOS", "MONOMER", "MONOMERS", "MONONYM", "MONONYMS", "MONONYMOUS", "MONOPSONY", "MONOPSONIES", "MONOSEMY", "MONOSEMOUS", "MONOSOME", "MONOSOMES", "MONOSOMY", "MONS", "MOP", "MOPS", "MOPE", "MOPES", "MOPER", "MOPERS", "MOPEY", "MOPY", "MOPERY", "MOSEY", "MOURN", "MOURNS", "MOUSE", "MOUSES", "MOUSER", "MOUSERS", "MOUSEY", "MOUSIER", "MUS", "MUM", "MUMS", "MUMSIES", "MUON", "MUONS", "MURE", "MURES", "MURMUR", "MURMURS", "MURMURER", "MURMURERS", "MURU", "MUSE", "MUSES", "MUSO", "MUSOS", "MYOMERE", "MYOMERES", "MYOPE", "MYOPES", "MYOSIN", "NINON", "NISEI", "NISEIS", "NISI", "NISIN", "NOES", "NOIR", "NOIRS", "NOISE", "NOISES", "NOISOME", "NOISIER", "NOM", "NOMS", "NOME", "NOMES", "NONI", "NONIS", "NONPERSON", "NONPERSONS", "NONPOISONOUS", "NONRESPONSE", "NONRESPONSES", "NONSERIOUS", "NOPE", "NOSE", "NOSES", "NOSEY", "NOSIER", "NOSIES", "NOUS", "OER", "OMS", "OMER", "OMERS", "OMNIUM", "OMNIUMS", "ONION", "ONIONS", "ONIONY", "ONYMOUS", "OPS", "OPE", "OPES", "OPEPE", "OPEPES", "OPSIN", "OPSONIN", "OPSONINS", "OPSONIZE", "OPSONISE", "OPSONIZES", "OPSONISES", "OPUS", "OPUSES", "OSIER", "OSIERS", "OSMOSE", "OSMOSES", "OSMOSIS", "OSPREY", "OUS", "OURS", "OYER", "OYEZ", "OYES", "PRIS", "SOIE", "PEIN", "PEINS", "PEON", "PEONS", "PEONY", "PEONIES", "PEP", "PEPS", "PEPERINO", "PEPERINOS", "PEPO", "PEPOS", "PEPSIN", "PER", "PERE", "PERES", "PERF", "PERFIN", "PERFINS", "PERFUME", "PERFUMES", "PERFUMY", "PERFUMER", "PERFUMERS", "PERFUMERY", "PERFUMERIES", "PERFUSE", "PERFUSES", "PERFUSION", "PERFUSIONS", "PERI", "PERIS", "PERISPERM", "PERISPERMS", "PERM", "PERMS", "PERP", "PERPS", "PERSE", "PERSON", "PERSONS", "PERSONIFIES", "PERSONIFIER", "PERSONIFIERS", "PERUSE", "PERUSES", "PERUSER", "PERUSERS", "PES", "PESO", "PESOS", "PFUI", "POS", "POEM", "POEMS", "POI", "POIS", "POISE", "POISES", "POISON", "POISONS", "POISONOUS", "POME", "POMES", "POMO", "PONS", "PONY", "PONIES", "PONZU", "POUF", "POUFIER", "POP", "POPS", "POPE", "POPES", "POPERY", "POPO", "POPOS", "POPSIE", "POPSIES", "POPUP", "POPUPS", "POSE", "POSES", "POSER", "POSERS", "POSEY", "POSIER", "POSIES", "POUI", "POUIS", "POUR", "POURS", "POURER", "POURERS", "PRE", "PREFER", "PREFERS", "PREM", "PREMS", "PREP", "PREPS", "PREPOSE", "PREPOSES", "PRESUME", "PRESUMES", "PREY", "PREYER", "PREYERS", "PREZ", "UOMO", "PRION", "PRIONS", "PRISE", "PRIZE", "PRISES", "PRIZES", "PRISM", "PRISMS", "PRISON", "PRISONS", "PRUINOSE", "PRY", "PRIES", "PSI", "PSIS", "PUP", "PUPS", "PURE", "PURER", "PURI", "PURIS", "PURIFIES", "PURIFIER", "PURIFIERS", "PURISM", "PURPOSE", "PURPOSES", "PURPURE", "PURPURIN", "PURSE", "PURSES", "PURSER", "PURSERS", "PUS", "PUY", "PYRE", "PYRES", "REF", "REFER", "REFERS", "REFUSE", "REFUSES", "REFUSER", "REFUSERS", "REIFIES", "REIN", "REINS", "REINSURE", "REINSURES", "REINSURER", "REINSURERS", "REM", "REP", "REPS", "REPERFUSION", "REPO", "REPOS", "REPOSE", "REPOSES", "REPRISE", "REPRISES", "REPURIFIES", "REPURPOSE", "REPURPOSES", "RESIN", "RESINS", "RESINOUS", "RESIZE", "RESIZES", "RESPONSE", "RESPONSES", "RESPONSUM", "RESUME", "RESUMES", "REZ", "RES", "RIEM", "RIEMS", "RIFE", "RINSE", "RINSES", "RINSER", "RINSERS", "RISE", "RISES", "RISER", "RISERS", "RUFOUS", "RUIN", "RUINS", "RUINOUS", "RUM", "RUMS", "RUMOUR", "RUMOURS", "RUSE", "RUSES", "RUS", "RYE", "RYES", "RYU", "RYUS", "SES", "SERE", "SEI", "SEIS", "SEIF", "SEISIN", "SEIZIN", "SEISINS", "SEIZINS", "SEIZE", "SEIZES", "SEISE", "SEISES", "SEIZER", "SEIZERS", "SEIZURE", "SEIZURES", "SEME", "SEMES", "SEMEME", "SEMEMES", "SEPOY", "SEPS", "SEPSES", "SEPSIS", "SERES", "SERF", "SERIES", "SERIF", "SERIN", "SERINS", "SERIOUS", "SERMON", "SERMONS", "SERMONIZE", "SERMONISE", "SERMONIZES", "SERMONISES", "SERMONIZER", "SERMONISER", "SERMONIZERS", "SERMONISERS", "SERUM", "SERUMS", "SEZ", "SEZES", "SIN", "SINS", "SIR", "SIRS", "SIRE", "SIRES", "SIS", "SIZE", "SIZES", "SIZER", "SIZERS", "SIZEISM", "SOS", "SOM", "SOME", "SOMONI", "SOMONIS", "SON", "SONS", "SONSIE", "SONSIER", "SOP", "SOPS", "SOU", "SOUS", "SOUP", "SOUPS", "SOUPY", "SOUR", "SOURER", "SOURS", "SOURSOP", "SOURSOPS", "SOUSE", "SOUSES", "SOY", "SPERM", "SPERMS", "SPONSON", "SPONSONS", "SPOUSE", "SPOUSES", "SPRY", "SPRYER", "SPUME", "SPUMES", "SPUMOUS", "SPUMY", "SPUMONI", "SPUR", "SPURS", "SPURIOUS", "SPURN", "SPURNS", "SPY", "SUI", "SUM", "SUMS", "SUMO", "SUMOS", "SUP", "SUPS", "SUPER", "SUPERS", "SUPERFUSION", "SUPERIUS", "SUPERMUM", "SUPERMUMS", "SUPERMOM", "SUPERMOMS", "SUPERPOSE", "SUPERPOSES", "SUPERSIZE", "SUPERSIZES", "SUPERUSER", "SUPERUSERS", "SUPREME", "SUPREMES", "SUPREMO", "SUPREMOS", "SUPREMUM", "SUPREMUMS", "SURE", "SURER", "SUREFIRE", "SURF", "SURFER", "SURFERS", "SURFIE", "SURFIES", "SURPRISE", "SURPRISES", "SUS", "SIRUP", "SIRUPS", "SIRUPY", "UME", "UMU", "UMUS", "UPS", "UPON", "UPRISE", "UPRISES", "UPSIZE", "UPSIZES", "URN", "URNS", "URUS", "URUSES", "USE", "USES", "USER", "USERS", "USURER", "USURERS", "USURIOUS", "USURP", "USURPS", "USURPER", "USURPERS", "USURY", "YEP", "YER", "YES", "YESES", "YEZ", "YIZ", "YIN", "YINZ", "YINZER", "YINZERS", "YON", "YONI", "YONIS", "YOU", "YOUR", "YOURN", "YOURS", "YOUSE", "YOUS", "YOYO", "YOYOS", "YOYOES", "YUM", "YUP", "YUPS", "YUS", "YUZU", "YUZUS", "ZES", "ZEIN", "ZIN", "ZINS", "NONISM", "OIS", "REFI", "REFIES", "SIZISM", "SPRIER", "EYER", "EYERS", "EYESOME", "FONIO", "FONIOS", "FRUM", "FUSIONY", "IONIUM", "MEINIE", "MEINIES", "MEISIE", "MEISIES", "MEISM", "MERESE", "MERESES", "MERISE", "MERISES", "MERISIS", "MERISISES", "MERISM", "MERISMS", "MERISMUS", "MERISMUSES", "MERSE", "MERSES", "MESE", "MESES", "MESEM", "MESEMS", "MESOMERE", "MESOMERES", "MESOSOME", "MESOSOMES", "MOME", "MOMES", "MONPE", "MOMSEY", "MONION", "MONIONS", "MONOMERIZE", "MONOMERISE", "MONOMERIZES", "MONOPS", "MONOSE", "MONOSES", "MONOSPERM", "MONOSPERMOUS", "MONOSPERMY", "MOEY", "MUI", "MOY", "MUIRY", "MOPSIES", "MOPUS", "MOPUSES", "MOSIES", "MOU", "MOUS", "MOUF", "MOURNSOME", "MOUSERY", "MOUSERIES", "MOUSME", "MOUSMES", "MUONIUM", "MUONIUMS", "MUREIN", "MUREINS", "MURUMURU", "MUSER", "MUSERS", "MUSION", "MUSIONS", "MYON", "MYONS", "MYOPS", "MYOPSES", "MYOPY", "NIEF", "NIF", "NIFE", "NIOPO", "NOPO", "NIS", "NISUS", "NISUSES", "NIU", "NIUS", "NOEME", "NOEMES", "NOESIS", "NOESISES", "NOISER", "NOISERS", "NOISESOME", "NOMOS", "NOMOSES", "NONIUS", "NONIUSES", "NONOSE", "NONOSES", "NOI", "NOY", "NOUP", "NOSER", "NOSERS", "NOSISM", "NOSIR", "NOUPS", "NYUSE", "NYUZE", "NYE", "NIE", "NYES", "ONIUM", "OURIE", "OUREY", "OUZE", "OPRY", "OPERY", "OPRIES", "OSEY", "OUI", "OURN", "OURSIN", "OURSINS", "OUZERI", "OUZERY", "OUZERIS", "PEONIN", "PEISE", "PEISES", "PEPON", "PEPONS", "PEREION", "PEREON", "PEREIONS", "PERIFUSE", "PERIFUSES", "PERIFUSION", "PERIFUSIONS", "PERMY", "PERN", "PERNS", "PERNIO", "PERNIOS", "PERNIOSIS", "PERNIOSES", "PERSP", "PYNSON", "POESIS", "POESISES", "POIESIS", "POIESISES", "POIRE", "POIRES", "POISER", "POYZER", "POISERS", "POISONY", "POMEIS", "POMEISES", "POMERIUM", "POMOERIUM", "POMERIUMS", "POPEISM", "POU", "POUS", "POUPOU", "POUPOUS", "POURIE", "POURIES", "PRESES", "PREFERER", "PREFIRE", "PREFIRES", "PREON", "PREONS", "PRESEPE", "PRESUMER", "PRESUMERS", "PREMSIE", "PRISERE", "PRISERES", "PRISMY", "PRISONIZE", "PRISONISE", "PRISONIZES", "PRISONOUS", "PRIUS", "PRIUSES", "PRIZER", "PRIZERS", "PRUINOUS", "PRYER", "PRIER", "PRYERS", "PUPSIE", "PUPSIES", "PUPU", "PUPUS", "PURIRI", "PURIRIS", "PURP", "PURPS", "PURPY", "PURPOSER", "PURPOSERS", "PURPUREIN", "PURPUREINS", "PURPUREOUS", "PYOSIS", "PYOSES", "PYRUS", "PYRUSES", "PYU", "REFIRE", "REFIRES", "REFRY", "REFRIES", "REIF", "RIEF", "REINFUSE", "REINFUSES", "REINFUSION", "REINFUSIONS", "REIONIZE", "REIONISE", "REIONIZES", "REIS", "REISES", "REMF", "REMOU", "REMOUS", "REMURMUR", "REMURMURS", "REPERFUME", "REPERFUMES", "REPERUSE", "REPERUSES", "REPOSER", "REPOSERS", "REPOSURE", "REPOSURES", "REPOUR", "REPOURS", "REPRISER", "REPRISERS", "RESEIZE", "RESEIZES", "RESEIZURE", "RESEIZURES", "RESINIFIES", "RESINOSIS", "RESINOSES", "RESINY", "RESIZER", "RESIZERS", "RESPONSER", "RESPONSERS", "RESUMER", "RESUMERS", "RESURPRISE", "RESURPRISES", "RIN", "RINS", "RISP", "RESP", "RISPS", "RUFUS", "RUFUSES", "RUMOURER", "RUMOURERS", "RURP", "RURPS", "RURU", "RURUS", "RYMER", "RYMERS", "RYO", "RIO", "RIYO", "RYOS", "SINSI", "SERIR", "SERIRS", "SONOFER", "SONSE", "SONSES", "SPOSO", "SPOSOS", "SPOUSIE", "SPOUSIES", "SPURION", "SPURIONS", "SUPE", "SUPES", "SUPERFUSE", "SUPERFUSES", "SUPERINFUSE", "SUPERINFUSES", "SUPERINFUSION", "SUPERINFUSIONS", "SUPERN", "SUPERPERSON", "SURFUSION", "SURFUSIONS", "YOPO", "YOPOS", "ZEF", "ZINO", "ZINOS"]
        # 01.09.2024 data
        self.words = ["ACACIA", "ACAI", "ACARA", "AKARA", "ACH", "ACHE", "ACHENE", "ACHIEVE", "ACHIEVER", "ACHKAN", "ACHIER", "ACID", "ACIDIC", "ACK", "ACNE", "ACRE", "ACT", "ACTANT", "ACTIVE", "ADHERE", "ADHERENT", "ADIEU", "ADIT", "ADNATE", "ADRET", "ADVENT", "ADVENTITIA", "ADVERT", "ADVT", "AERATE", "AID", "AIDA", "AIT", "AITCH", "AKRATIC", "ACRATIC", "VERA", "ANA", "ANANDA", "ANARCH", "ANARCHIC", "ANCIEN", "ANCIENT", "AND", "ANDANTE", "ANDRADITE", "ANENT", "ANKH", "ANT", "ANTACID", "ANTE", "ANTEATER", "ANTHER", "ANTHRACITE", "ANTHRACITIC", "ANTI", "ANTIC", "ANTIDIURETIC", "ANTITANK", "ANTITHETIC", "ANTIVENENE", "ANTRA", "ANURA", "ANURAN", "VITAE", "ARANEID", "ARC", "ARCANA", "ARCANE", "ARCH", "ARCHER", "ARCHIVE", "ARCTIC", "ARCUATE", "ARE", "AREA", "ARENA", "ARETE", "ARK", "ARAK", "ART", "ARTIC", "ARTIER", "ATACTIC", "ATARACTIC", "ATE", "AUDIT", "AUDITIVE", "AUNT", "AUNTIE", "AURA", "AURAE", "AURAR", "AUREATE", "AUREI", "VIVEUR", "CACA", "CACHE", "CACHET", "CACK", "CACTI", "CAD", "CADRE", "CAKE", "CAN", "CANARD", "CANCAN", "CANDID", "CANDIDA", "CANDIDATE", "CANE", "CANER", "CANKER", "CANT", "CANTATA", "CANTER", "CANTHI", "CANTHIC", "CANTI", "CAR", "CARACARA", "CARAT", "KARAT", "CARCANET", "CARD", "CARDAN", "CARDIA", "CARDIAC", "CARDIE", "CARDI", "CARE", "CARER", "CARET", "CARETAKE", "CARETAKEN", "CARETAKER", "CARK", "KARK", "CART", "CARTER", "CARVE", "CARVEN", "CARVER", "CAT", "CATANANCHE", "CATARACT", "CATCH", "CATCHER", "CATCHIER", "CATE", "CATENA", "CATENAE", "CATENANE", "CATENATIVE", "CATER", "CATERAN", "CATERER", "TREAD", "CATHEAD", "CATHETER", "CAUDA", "CAUDAE", "CAUDATE", "CHEAT", "CHEATER", "CHERT", "CHEVET", "CHEVRE", "CHI", "CHIACK", "CHIC", "CHICA", "CHICANE", "CHICHI", "CHICK", "CHICKEN", "CHID", "CHIKAN", "CHENAR", "CHIT", "CHIVE", "CHUCK", "CHUCKER", "CHUNK", "CHUNKIER", "CHUNTER", "CHURCH", "CHURCHIER", "CICADA", "CICHETI", "CITE", "CITRATE", "CIVET", "CIVIC", "ARTE", "RENDU", "ETAT", "THEATRE", "CRACK", "CRAIC", "CRACKER", "CRACKHEAD", "CRAKE", "CRAN", "CRANE", "CRANK", "CRANKIER", "CRATCH", "CRATE", "CRATER", "CREAK", "CREAKIER", "CREATE", "CREATIVE", "CRENATE", "CRETIC", "CRU", "CRUCIAN", "CRUCIATE", "CRUCK", "CRUD", "CRUET", "CRUNCH", "CRUNCHER", "CRUNCHIER", "CRUNK", "CRURA", "CUCK", "CUD", "CUE", "CUI", "CUNEATE", "CUR", "CURARE", "CURATE", "CURATIVE", "CURD", "CURE", "CURER", "CURT", "CURTANA", "CURVE", "CURVET", "CURVIER", "DACITE", "DACITIC", "DAD", "DADA", "DAI", "DAK", "DAN", "DANAID", "DANDA", "DANDIER", "DANK", "DANKER", "DARE", "DARER", "DARK", "DARKER", "DARKEN", "DARKENER", "DARKNET", "DART", "DARTER", "DAT", "DATA", "DATE", "DATER", "DATIVE", "DAUNT", "DHIKR", "DIANA", "DIARCHIC", "DICIER", "DICK", "DICKER", "DICKERER", "DICTA", "DICTATE", "DID", "DIDACTIC", "DIDI", "DIE", "DIENE", "DIET", "DIETER", "DIETETIC", "DIETICIAN", "DIETITIAN", "DIKDIK", "DIKE", "DIT", "DITCH", "DITCHER", "DITHER", "DITHERER", "DIURETIC", "DIV", "DIVE", "DIVER", "DIVERT", "DIVERTER", "DIVIER", "DIVI", "ENTENDRE", "VIVRE", "DRACAENA", "DRACK", "DRAKE", "NACH", "DRANK", "DRAT", "DREAD", "DREAR", "DREK", "DREICH", "DRENCH", "DRUNK", "DRUNKER", "DRUNKARD", "DRUNKEN", "DUAD", "DUCAT", "DUCK", "DUCKER", "DUCT", "DUCTI", "DUD", "DUE", "DUET", "DUH", "DUIKER", "DUN", "DUNE", "DUNK", "DUNKER", "DUNT", "DUR", "DURA", "DURATIVE", "DUVET", "EACH", "EAR", "EARACHE", "EARTH", "EARTHEN", "EARTHIER", "EAT", "EATEN", "EATER", "EITHER", "EKE", "ENACT", "ENACTIVE", "END", "ENDIAN", "ENDITE", "ENDIVE", "ENDUE", "ENDURE", "ENDURER", "ENTENTE", "ENTER", "ENTITATIVE", "ENTRACTE", "ENTRANT", "ENTREAT", "ENTRENCH", "ENTRE", "ENUNCIATE", "ENUNCIATIVE", "ENURE", "ENURETIC", "VENTRE", "ENVIER", "ERA", "ERADICATE", "ERADICANT", "ERE", "ERVEN", "ERHU", "ERK", "ERUCIC", "ERUCT", "ERUCTATE", "ERUDITE", "ERUV", "ETA", "ETCH", "ETCHER", "ETH", "ETHENE", "ETHER", "AETHER", "ETHIC", "ETHNARCH", "ETIC", "EUCHRE", "EUNUCH", "EUREKA", "EVE", "EVEN", "EVENER", "EVENT", "EVENTER", "EVENTIVE", "EVER", "EVERT", "EVICT", "EVITE", "HEHE", "HEAD", "HEADACHE", "HEADHUNT", "HEADHUNTER", "HEADTEACHER", "HEADTIE", "HEADIER", "HEAR", "HEARD", "HEARER", "HEARKEN", "HEART", "HEARTACHE", "HEARTEN", "HEARTH", "HEARTRATE", "HEARTIER", "HEAT", "HEATER", "HEATH", "HEATHEN", "HEATHER", "HEIAU", "HEN", "HENCH", "HENTAI", "HER", "HERD", "HERE", "HEREAT", "HERETIC", "HET", "HETAERA", "HETAERAE", "HEUCHERA", "HEUCH", "HEVEA", "HIC", "HICK", "HID", "HIE", "HIERARCH", "HIERARCHIC", "HIERATIC", "HIKE", "HIKER", "HIT", "HITCH", "HITCHER", "HITHE", "HITHER", "HIVE", "HUARACHE", "HUCHEN", "HUCK", "HUE", "HUH", "HUI", "HUIA", "HUN", "HUNCH", "HUNK", "HUNKER", "HUNKIER", "HUNT", "HUNTER", "HURT", "HURTIER", "ICK", "ICKIER", "ICIER", "IKAT", "ITCH", "ITCHIER", "ITERATE", "ITERATIVE", "KAI", "KAIKAI", "KAITIAKI", "KAKA", "KAKI", "KANA", "KANAKA", "KARA", "KADAI", "KARAI", "KARAKA", "KARAKIA", "KARATE", "KARATEKA", "KART", "KATA", "KATAKANA", "KATANA", "KEA", "KEAKI", "KIEVE", "KEITAI", "KEN", "KENT", "KENTE", "KENTIA", "KERERU", "KET", "KETCH", "KETE", "KETENE", "KHUD", "KIA", "KICK", "KICKER", "KICKIER", "KID", "KIDVID", "KIEKIE", "KIER", "KIT", "KITCHEN", "KITCHENER", "KITE", "KITH", "KNACK", "KNACKER", "KNAR", "KNUR", "KNEAD", "KRAI", "KRAIT", "KRAKEN", "KVETCH", "THE", "REA", "VIVENDI", "NACARAT", "NACRE", "NADA", "NAD", "NAE", "NAEVI", "NEVI", "NAI", "NAIAD", "NAIANT", "NAIVE", "NAIVER", "NAIVETE", "NAKER", "NAN", "NANA", "NARC", "NARK", "NARD", "NARKIER", "NATAK", "NATANT", "NATCH", "NATE", "NATIVE", "NEAR", "NEARER", "NEAT", "NEATER", "NEATEN", "NEATH", "NEITHER", "NEK", "NENE", "NERD", "NURD", "NERDIER", "NURDIER", "NEREID", "NERK", "NERVE", "NERVURE", "NERVIER", "NET", "NETA", "NETHEAD", "NETHER", "NETI", "NEVE", "NEVER", "NTH", "NUDIE", "NUIT", "NUN", "NUNATAK", "NUNU", "EARTHER", "CIT", "DURE", "CADI", "KADI", "KANAT", "CARTE", "VIVE", "ERAT", "RACHITIC", "RACK", "RACKET", "RACIER", "RAD", "RADAR", "RADIAN", "RADIANT", "RADIATE", "RADIATIVE", "RAI", "RAID", "ETRE", "RAITA", "RAKE", "RAKER", "RAKHI", "RAKI", "RAN", "RANCH", "RANCHER", "RANCHERA", "RANCID", "RAND", "RANDAN", "RANDIER", "RANK", "RANKER", "RANT", "RANTER", "RARA", "RARE", "RARER", "RARK", "RAT", "RATA", "RATATAT", "RATCATCHER", "RATCHET", "RATE", "RATH", "RATHE", "RATHER", "RATITE", "RATRUN", "RAUNCH", "RAUNCHIER", "REACH", "REACHER", "REACT", "REACTANT", "REACTIVE", "READ", "READIER", "REAR", "REARER", "REHEAR", "REHEARD", "REHEAT", "REHEATER", "REIKI", "REITERATE", "REITERATIVE", "REIVE", "REIVER", "REND", "RENT", "RENTER", "RENTIER", "RENUNCIANT", "RENUNCIATIVE", "RERAN", "RERATE", "REREAD", "RERUN", "RET", "RETAKE", "RETAKEN", "RETARD", "RETARDATIVE", "RETARDANT", "RETARDATE", "RETCH", "RETE", "RETIA", "RETEACH", "RETENTIVE", "RETIE", "RETRACT", "RETRACTIVE", "RETREAD", "RETREAT", "RETRENCH", "REV", "REVENANT", "REVENUE", "REVERE", "REVEREND", "REVERENT", "REVERT", "REVERTANT", "REVERTER", "REVET", "REVIVE", "REVIVER", "REVUE", "RHEA", "RUA", "RUCHE", "RUCK", "RUE", "RUN", "RUNE", "RUNT", "RUNTIER", "DHU", "UND", "TACAN", "TACH", "TACHI", "TACIT", "TACK", "TACKER", "TACKIE", "TACKIER", "TACT", "TACTIC", "TACTICIAN", "TAD", "TADA", "TAE", "TAI", "TAKA", "TAKE", "TAKEN", "TAKER", "TAKHT", "TAN", "TANK", "TANKA", "TANKARD", "TANKER", "TANTE", "TANT", "TANTRA", "TAR", "TARA", "TARAKIHI", "TARATA", "TARD", "TARDIVE", "TARDIER", "TARE", "TARKA", "TART", "TARTER", "TARTAN", "TARTAR", "TARTARE", "TARTE", "TARTRATE", "TARTIER", "TACHE", "TAT", "TATA", "TATAKI", "TATER", "TATIE", "TAU", "TAUA", "TAUNT", "TAUNTER", "TCH", "TEA", "TEACAKE", "TEACH", "TEACHER", "TEAK", "TEAR", "TEARER", "TEAT", "TEN", "TENANT", "TENCH", "TEND", "TENDRE", "TENDU", "TENET", "TENT", "TENTATIVE", "TENTER", "TENTH", "TENURE", "TERAI", "TERETE", "VERTE", "TERTIAN", "TETCHIER", "TETE", "TETHER", "TETRA", "TETRAD", "TETRARCH", "THEATER", "THIKADAR", "THEN", "THENAR", "THENARDITE", "THERE", "THEREANENT", "THEREAT", "THETA", "THICK", "THICKER", "THICKEN", "THICKENER", "THICKET", "THICKHEAD", "THIEVE", "THITHER", "THREAD", "THREADIER", "THREAT", "THREATEN", "THREATENER", "THRU", "THUD", "THUNK", "TIAN", "TIARA", "TIARE", "TIC", "TICK", "TICKER", "TICKET", "TIDIER", "TIE", "TIENDA", "TIER", "TIK", "TIKA", "TIKI", "TIKIA", "TIKITAKA", "TIT", "TITAN", "TITANATE", "TITCH", "TICH", "TITCHIER", "TITHE", "TITI", "TITRATE", "TITRE", "TITER", "TRACHEA", "TRACHEAE", "TRACHEATE", "TRACHEID", "TRACK", "TRACKER", "TRACKIE", "TRACT", "TRACTATE", "TRACTIVE", "TRAD", "TRADIE", "TRAIK", "TRAIT", "TRAITEUR", "TRA", "TRANCHE", "TRANK", "TREAT", "TREATER", "TREK", "TRENCH", "TRENCHER", "TREND", "TRENDIER", "TRENTE", "TRET", "TRUANT", "TRUCK", "TRUCKER", "TRUCKIE", "TRUE", "TRUER", "TRUNCATE", "TRUNK", "TIKE", "UHUH", "UNCANDID", "UNCHURCH", "UNCRATE", "UNCREATE", "UNCREATIVE", "UNDID", "UNDRUNK", "UNDUE", "UNEARTH", "UNEATEN", "UNEVEN", "UNHEARD", "UNHITCH", "UNHURT", "UNTACK", "UNTAKEN", "UNTEACH", "UNTETHER", "UNTHREAD", "UNTICK", "UNTIDIER", "UNTIE", "UNTRUE", "URAEI", "URATE", "UREA", "UREID", "URETER", "URETHRA", "URETHRAE", "URTICATE", "UVEA", "VENA", "VEND", "VENDUE", "VENERATE", "VENERER", "VENETIAN", "VENT", "VENTER", "VENTI", "VENTIDUCT", "VENUE", "VERANDA", "VERDANT", "VERDICT", "VERDITER", "VERDURE", "VERT", "VERVE", "VERVET", "VET", "VETCH", "VETERAN", "VETIVER", "VETIVERT", "VIA", "VIADUCT", "VIAND", "VIATICA", "VICAR", "VICUNA", "VICI", "VID", "VIE", "VITA", "VITIATE", "VIVID", "CHUN", "ACIDHEAD", "CHIA", "CHIANTI", "ACANTH", "ACANTHITE", "ACARDIA", "ACARDIAC", "ACATER", "ACAUDATE", "ACHER", "ACIDANTHERA", "ACKER", "ACTA", "ACUATE", "ADAT", "ADHEREND", "ADHERER", "ADIATE", "ADIENT", "ADIKAR", "ADITHER", "ADRENARCHE", "ADUNCATE", "ADVEHENT", "ADVENE", "ADVENTIVE", "ADVERTENT", "AETITE", "AIE", "AKAKIA", "AKE", "AKEAKE", "AKHUND", "ANDIC", "ANTA", "ANTEVERT", "ANTHRACIC", "ANTRE", "ARCTICIAN", "ARENE", "ARTER", "ARTIAD", "ATER", "AUCHT", "AUDIENCIER", "AUDIENT", "AUH", "AUNE", "CHURCHITE", "CITATE", "CITATIVE", "CITER", "CITHER", "CITRENE", "CTENE", "DATHER", "DADTHER", "DADI", "DAUD", "DICTATIVE", "DIDACHE", "DIDACT", "DIDACTICIAN", "DIDACTIVE", "DURENE", "ENT", "ETHERATE", "ETHEREAN", "ETHICIAN", "EVICTER", "HEARTENER", "HEURETIC", "EURETIC", "IDANT", "CHITI", "KIAKI", "NACKET", "NAID", "NAIDID", "NAIK", "NAKA", "NAKERER", "NAKHUDA", "NANDU", "NANT", "NANTE", "NANTI", "NANTEN", "NAR", "NARA", "NATICID", "NEANT", "NERAND", "NEATHERD", "NEICHER", "NENADKEVICHITE", "NENADKEVITE", "NENTA", "NERKA", "NETE", "NEU", "NUH", "NUNCHUCK", "NUNCIATE", "NUNK", "NUNKIE", "UNT", "KENA", "RACHE", "RATCH", "RACHIDIAN", "RACKER", "RACKETER", "RANKET", "RACKIE", "RADIATA", "RADICAND", "RADICANT", "RADICATE", "RAIK", "RAIKE", "RAITH", "RAKIA", "RANA", "RANCIEITE", "RANE", "RAEN", "REN", "RAUN", "RATANHIA", "RAITCH", "RATER", "RATHITE", "RATI", "RAUREKAU", "RAURAKAU", "RAUREKA", "RDV", "READHERE", "REAK", "REAN", "REHEARTEN", "REARD", "REITERANT", "RENARDITE", "RENERVE", "RENK", "RENTE", "RENTIERE", "RENUNCIATE", "RERADIATE", "RETACK", "RETAKER", "RETARDIVE", "RETENANT", "RETENE", "RETENTATE", "RETENUE", "RETHREAD", "RETRACK", "RETRACTATIVE", "RETRAITE", "RETREATANT", "RETREATER", "RETREATIVE", "RETRENCHER", "REUNE", "REVEHENT", "REVEND", "REVENDICATE", "REVENT", "REVENTA", "REVENUER", "REVERDIE", "REVERER", "REVERTIVE", "REVIVICATE", "RHE", "RHEID", "RHENATE", "RHETIC", "REATA", "RUACH", "RUANA", "RUD", "RUDIE", "RUDITE", "RUNCH", "RUNCHICK", "RUNCHIE", "RUND", "RUNER", "RURU", "RUVID", "TITAR", "TITA", "TITE", "TITHER", "TITHI", "THITHI", "TRADIT", "TRADITIVE", "TRADUCIAN", "TRADUCT", "TRADUCTIVE", "UNKET", "UNKERT", "UNKENT", "UNKETH", "URANATE", "VETERATE", "VETITIVE", "VEUVE", "VEVE"]

    def create_word_graph(self):
        self.word_connect = {
            word: list(filter(lambda x: x[0] == word[-1], self.words)) for word in self.words
        }

    @abstractmethod
    def solve(self):
        pass

    # Print out how many words are currently in the queue
    def progress_worker(self):
        last_amount = 0
        while True:
            tasks = self.task_queue.unfinished_tasks
            if last_amount != 0:
                sys.stdout.write('\r' + ' ' * 100)
            if tasks:
                trend_sign = '↗' if tasks > last_amount else '↘' if tasks < last_amount else '→'
                amount_text = trend_sign + ' ' + str(tasks) + ' ' + trend_sign
                sys.stdout.write(f'\rStill considering {amount_text:^20} word sequences')
                last_amount = tasks
            sys.stdout.flush()

            with self.progress_lock:
                if self.progress_end:
                    sys.stdout.write(f'\rAll word sequences considered!\n')
                    sys.stdout.flush()
                    break

            sleep(0.2)

    @abstractmethod
    def word_worker(self):
        pass

    def initialise_word_workers(self):
        self.workers = [Thread(target=self.word_worker, daemon=True).start() for _ in range(self.threads)]

    def count_repetitions(self, word_list):
        # Check how many letters current sequence is using
        letters_used = reduce(lambda x, y: x + y, [Counter(word) for word in word_list])
        # We should not count the joint letters twice.
        for word1, word2 in zip(word_list[:-1], word_list[1:]):
            letters_used[word1[-1]] -= 1
        letters_left = self.letter_count.copy()
        letters_left.update({k: -v for k, v in letters_used.items()})

        repetitions = -sum(filter(lambda count: count <= 0, letters_left.values()))

        return repetitions, letters_left


class LeastRepetitionsLeastWordsSolver(LetterboxedSolver):
    def __init__(self, sides, threads=12):
        super().__init__(sides, threads=threads)

    def solve(self):
        # Caching
        if self.solutions:
            return self.solutions

        progress_t = Thread(target=self.progress_worker, daemon=True)
        progress_t.start()

        allowed_repetitions = 0

        while True:
            for word in self.word_connect:
                self.task_queue.put(([word], allowed_repetitions))

            # Block until all paths analysed
            self.task_queue.join()

            if self.solutions:
                break

            print(f'I have not found any solutions for {allowed_repetitions} repetitions.')
            allowed_repetitions += 1

        self.solutions.sort(key=lambda x: len(x))

        # Allow the progress thread to finish gracefully
        with self.progress_lock:
            self.progress_end = True
        progress_t.join()

        return self.solutions, allowed_repetitions

    # Keep checking sequences for correctness and add next steps to the queue
    def word_worker(self):
        while True:
            item = self.task_queue.get()
            word_list, allowed_repetitions = item

            repetitions, letters_left = self.count_repetitions(word_list)

            if repetitions <= allowed_repetitions:
                # Solution found!
                if all([letter_no <= 0 for letter_no in letters_left.values()]):
                    self.solutions.append(word_list)
                    # Could in theory test further, but I don't want to
                # We can test the next step
                else:
                    # Discard all possible next words that would go over the letter limit
                    possible_next_words = list(filter(
                        lambda next_word: -sum(filter(
                            lambda count: count <= 0,
                            dict({k: -v for k, v in Counter(next_word).items()}, **letters_left).values()
                        )) <= allowed_repetitions,
                        self.word_connect[word_list[-1]]
                    ))

                    # Add following sequences to the consideration queue
                    for word in possible_next_words:
                        possible_sequence = [*word_list, word]

                        with self.lock:
                            # Check if this sequence or its subsequence was previously checked in the cache
                            for ignored_length in range(len(possible_sequence)):
                                sub_sequence = ', '.join(possible_sequence[ignored_length:])
                                if sub_sequence in self.failed_sequences:
                                    if self.failed_sequences[sub_sequence] >= allowed_repetitions:
                                        break
                            else:
                                self.task_queue.put((possible_sequence, allowed_repetitions))
            else:
                # This is over the limit, save the sequence in our failure cache
                with self.lock:
                    self.failed_sequences[', '.join(word_list)] = repetitions

            self.task_queue.task_done()


class LeastWordsLeastRepetitionsSolver(LetterboxedSolver):
    def __init__(self, sides, threads=12):
        super().__init__(sides, threads=threads)

    def solve(self):
        # Caching
        if self.solutions:
            return self.solutions

        progress_t = Thread(target=self.progress_worker, daemon=True)
        progress_t.start()

        while True:
            for word in self.word_connect:
                self.task_queue.put([word])

            # Block until all paths analysed
            self.task_queue.join()

            if self.solutions:
                break

        self.solutions.sort(key=lambda x: (x[1], x[0]))

        # Allow the progress thread to finish gracefully
        with self.progress_lock:
            self.progress_end = True
        progress_t.join()

        return self.solutions

    # Keep checking sequences for correctness and add next steps to the queue
    def word_worker(self):
        while True:
            item = self.task_queue.get()
            word_list = item

            with self.lock:
                if self.solutions:
                    if len(self.solutions[0][0]) < len(word_list):
                        self.task_queue.task_done()
                        continue

            repetitions, letters_left = self.count_repetitions(word_list)

            # Solution found!
            if all([letter_no <= 0 for letter_no in letters_left.values()]):
                with self.lock:
                    self.solutions.append((word_list, repetitions))
                # Could in theory test further, but I don't want to
            # We can test the next step
            else:
                for word in self.word_connect[word_list[-1]]:
                    self.task_queue.put([*word_list, word])

            self.task_queue.task_done()


if __name__ == '__main__':
    ls = LeastRepetitionsLeastWordsSolver(
        # sides=["EUN", "ROZ", "IMP", "FSY"],  # 31.08.2024
        sides=["CED", "INR", "HVA", "KTU"],  # 01.09.2024
        threads=12
    )
    solutions, repetitions = ls.solve()
    print(f'Solutions requiring at least {repetitions} repetitions:')
    for solution in solutions:
        print(f'  {len(solution)}: {solution}')

    ls = LeastWordsLeastRepetitionsSolver(
        # sides=["EUN", "ROZ", "IMP", "FSY"],  # 31.08.2024
        sides=["CED", "INR", "HVA", "KTU"],  # 01.09.2024
        threads=12
    )
    solutions2 = ls.solve()
    if solutions2:
        print(f'Solutions of length {len(solutions2[0][0])}:')
        for solution, repetitions in solutions2:
            print(f'  {repetitions}: {solution}')
