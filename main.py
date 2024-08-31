import sys
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

    def solve(self):
        # TODO: Add criteria options
        # Currently - least repetitions, then least words
        # NYT itself concerns itself only with the word count

        # Create word graph
        self.word_connect = {
            word: list(filter(lambda x: x[0] == word[-1], self.words)) for word in self.words
        }

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

    # Keep checking sequences for correctness and add next steps to the queue
    def word_worker(self):
        while True:
            item = self.task_queue.get()
            word_list, allowed_repetitions = item

            # Check how many letters current sequence is using
            letters_used = reduce(lambda x, y: x+y, [Counter(word) for word in word_list])
            # We should not count the joint letters twice.
            for word1, word2 in zip(word_list[:-1], word_list[1:]):
                letters_used[word1[-1]] -= 1
            letters_left = self.letter_count.copy()
            letters_left.update({k: -v for k, v in letters_used.items()})

            repetitions = -sum(filter(lambda count: count <= 0, letters_left.values()))

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

    def initialise_word_workers(self):
        self.workers = [Thread(target=self.word_worker, daemon=True).start() for _ in range(self.threads)]


if __name__ == '__main__':
    ls = LetterboxedSolver(
        sides=["EUN", "ROZ", "IMP", "FSY"],
        threads=12
    )
    solutions, repetitions = ls.solve()
    print(f'Solutions requiring at least {repetitions} repetitions:')
    for solution in solutions:
        print(f'  {len(solution)}: {solution}')
