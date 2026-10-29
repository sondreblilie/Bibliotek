from datetime import datetime
import csv
from pathlib import Path
import json

BREDDE = 60

ENDRER_BØKER = {1, 2, 3}

FELTER = [
    "tittel",
    "forfattere",
    "utgivelsesår",
    "utgave",
    "eksemplarer_tot",
    "eksemplarer_nå",
]

STANDARD_INNSTILLINGER = {
    "autolast": False,
    "autolagre" : False,
}

FILSTI = Path(__file__).parent / "bøker.csv"

INNSTILLINGER = Path(__file__).parent / "innstillinger.json"


# Hjelpefunksjoner
def overskrift(tekst):
    print(f"{f' {tekst} ':=^{BREDDE}}")


def linje():
    print("=" * BREDDE)


def linje_tynn():
    print("-" * BREDDE)


def melding(tekst):
    linje_tynn()
    print(tekst)
    linje_tynn()


def på_av(verdi):
    return "PÅ" if verdi else "AV"


def spør_ja_nei(spørsmål):
    while True:
        svar = input(f"{spørsmål} (j/n): ").strip().lower()
        if svar in ("ja", "j"):
            return True
        if svar in ("nei", "n"):
            return False
        print("Du må svare ja/j eller nei/n")


def les_heltall(spørsmål, minst, maks=None):
    while True:
        if maks is None:
            tekst = f"{spørsmål} (Minst {minst}): "
        else:
            tekst = f"{spørsmål} ({minst}-{maks}): "

        try:
            valg = int(input(tekst))
        except ValueError:
            print("Du må skrive inn et tall!")
            continue

        if valg >= minst and (maks is None or valg <= maks):
            return valg

        if maks is None:
            print(f"Tallet må være minst {minst}!")
        else:
            print(f"Tallet må være mellom {minst} - {maks}!")


def les_tekst(spørsmål, feilmelding):
    while True:
        tekst = input(f"{spørsmål}: ").strip()
        if not tekst:
            print(feilmelding)
            continue
        return tekst


def skriv_forfattere():
    forfattere = []
    while True:
        forfatter = les_tekst("Forfatter", "Du må skrive inn en forfatter.")
        forfattere.append(forfatter)
        if not spør_ja_nei("Vil du legge til flere forfattere?"):
            return forfattere


def velg_bok(bibliotek):
    if not bibliotek.bøker:
        melding("Biblioteket har ingen bøker")
        return None
    overskrift("Velg bok")
    bibliotek.vis_titler()
    linje_tynn()

    liste_bøker = list(bibliotek.bøker)

    valg = les_heltall("Velg bok", 1, (len(liste_bøker))) - 1
    return liste_bøker[valg]


def lagre_bøker(bibliotek):
    with open(FILSTI, "w", encoding="utf-8-sig", newline="") as f:
        skriver = csv.DictWriter(f, delimiter=";", fieldnames=FELTER)
        skriver.writeheader()
        for bok, beholdning in bibliotek.bøker.items():
            rad = bok.til_dict() | beholdning.til_dict()
            skriver.writerow(rad)


def last_bøker(bibliotek):
    if not FILSTI.exists():
        return False

    bibliotek.tøm_biblioteket()
    with open(FILSTI, "r", encoding="utf-8-sig", newline="") as f:
        leser = csv.DictReader(f, delimiter=";")
        for rad in leser:
            tittel = rad["tittel"]
            forfattere = rad["forfattere"].split("|")
            utgivelsesår = int(rad["utgivelsesår"])
            utgave = int(rad["utgave"])
            eksemplarer_tot = int(rad["eksemplarer_tot"])
            eksemplarer_nå = int(rad["eksemplarer_nå"])

            bok = Bok(tittel, forfattere, utgivelsesår, utgave=utgave)
            bibliotek.legg_til_bok(bok, eksemplarer_tot, eksemplarer_nå)
        return True
    

# Lagrer innstillinger
def lagre_innstillinger(innstillinger):
    with open(INNSTILLINGER, "w", encoding="utf-8-sig") as f:
        json.dump(innstillinger, f, indent=4)


# Leser innstillinger
def les_innstillinger():
    if not INNSTILLINGER.exists():
        return dict(STANDARD_INNSTILLINGER)
    with open(INNSTILLINGER, encoding="utf-8-sig") as f:
        try:
            return STANDARD_INNSTILLINGER | json.load(f)
        except json.JSONDecodeError:
            return dict(STANDARD_INNSTILLINGER)


# Toggler en innstilling av og på
def bytt_innstilling(nøkkel):
    innstillinger = les_innstillinger()
    innstillinger[nøkkel] = not innstillinger[nøkkel]
    lagre_innstillinger(innstillinger)
    return innstillinger[nøkkel]

# Menyvalg 9: Innstillinger
def meny_innstillinger(bibliotek):
    while True:
        overskrift("Innstillinger")
        print("[1] Auto-last"
              "\n[2] Auto-lagre"
              "\n[0] Tilbake")
        valg = les_heltall("Velg et av alternativene", 0, 2)
        if valg == 1:
            ny_verdi = bytt_innstilling("autolast")
            melding(f"Automatisk innlasting er nå {på_av(ny_verdi)}")
        elif valg == 2:
            ny_verdi = bytt_innstilling("autolagre")
            melding(f"Automatisk lagring er nå {på_av(ny_verdi)}")
        elif valg == 0:
            break





# Menyvalg 1
def meny_legg_til(bibliotek):
    while True:
        overskrift("Legg til bok")
        tittel = les_tekst("Tittel", "Tittelen kan ikke være tom.")
        forfattere = skriv_forfattere()
        utgivelsesår = les_heltall("Utgivelsesår", 0, datetime.now().year)
        utgave = les_heltall("Utgave", 1)
        eksemplarer = les_heltall("Eksemplarer", 1)

        bok = Bok(tittel, forfattere, utgivelsesår, utgave)
        bibliotek.legg_til_bok(bok, eksemplarer)
        melding(f"{bok.tittel} ble lagt til i biblioteket.")

        if not spør_ja_nei("Vil du legge til flere bøker?"):
            return


# Menyvalg 2
def meny_utlån(bibliotek):
    while True:
        bok = velg_bok(bibliotek)
        if bok is None:
            return
        if bibliotek.lån_ut(bok):
            melding(f"Lån registrert: {bok.tittel}")
        else:
            melding(f"Ingen ledige eksemplarer av {bok.tittel}")

        if not spør_ja_nei("Vil du låne flere bøker?"):
            return


# Menyvalg 3
def meny_innlevering(bibliotek):
    while True:
        bok = velg_bok(bibliotek)
        if bok is None:
            return
        try:
            bibliotek.lever_inn(bok)
            melding(f"Innlevering registrert: {bok.tittel}")
        except ValueError as feil:
            melding(f"Feil: {feil}")

        if not spør_ja_nei("Vil du levere flere bøker?"):
            return


# Menyvalg 4
def meny_vis_alle(bibliotek):
    overskrift("Alle bøker i biblioteket")
    bibliotek.vis_alle_bøker()
    linje_tynn()
    input("Trykk 'ENTER' for å gå tilbake: ")


# Menyvalg 5
def meny_lagre_bøker(bibliotek):

    lagre_bøker(bibliotek)
    melding("Bibliotek lagret")


# Menyvalg 6
def meny_last_bøker(bibliotek):
    if not last_bøker(bibliotek):
        melding("Fant ingen fil")
        return
    melding("Suksess: Bøker lastet")
    return True


# Menyvalg 7
def meny_sjekk_bøker(bibliotek):
    utlånt = bibliotek.utlån_teller()
    ord = "bok" if utlånt == 1 else "bøker"
    if utlånt == 0:
        melding(f"Ingen {ord} er utlånt.")
    else:
        melding(f"{utlånt} {ord} er utlånt.")
        bibliotek.vis_alle_lånte_bøker()
    input("Trykk 'ENTER' for å gå tilbake.")


# Menyvalg 8
def meny_søk(bibliotek):
    overskrift("Søk")
    søke_tekst = les_tekst("Søk", "Søk kan ikke være tom.")
    søk = bibliotek.søk(søke_tekst)
    if not søk:
        melding("Ingen bøker funnet")

    else:
        linje_tynn()
        for resultat in søk:
            print(resultat)
        linje_tynn()

    input("Trykk 'ENTER' for å gå tilbake")


# Hovedmeny
def hovedmeny(bibliotek):
    ulagrede_endringer = False
    while True:
        overskrift("Bibliotek")
        print(
            "[1] Legg til bok"
            "\n[2] Lån bok"
            "\n[3] Lever bok"
            "\n[4] Vis alle bøker"
            "\n[5] Last inn bibliotek"
            "\n[6] Lagre biblioteket"
            "\n[7] Sjekk utlånte bøker"
            "\n[8] Søk"
            "\n[9] Innstillinger"
            "\n[0] Avslutt"
        )
        valg = les_heltall("Velg ett av alternativene", 0, 9)
        if valg == 1:
            meny_legg_til(bibliotek)
        elif valg == 2:
            meny_utlån(bibliotek)
        elif valg == 3:
            meny_innlevering(bibliotek)
        elif valg == 4:
            meny_vis_alle(bibliotek)
        elif valg == 5:
            meny_last_bøker(bibliotek)
            ulagrede_endringer = False
        elif valg == 6:
            meny_lagre_bøker(bibliotek)
            ulagrede_endringer = False
        elif valg == 7:
            meny_sjekk_bøker(bibliotek)
        elif valg == 8:
            meny_søk(bibliotek)
        elif valg == 9:
            meny_innstillinger(bibliotek)
        elif valg == 0:
            if ulagrede_endringer and spør_ja_nei(
                "Du har ulagrede endringer. Vil du lagre før du avslutter?"):
                lagre_bøker(bibliotek)
                melding("Endringer lagret")
            melding("Du har avsluttet programmet. Ha det fint!")
            break

        if valg in ENDRER_BØKER:
            if les_innstillinger()["autolagre"]:
                lagre_bøker(bibliotek)
                melding("Endringer lagret automatisk")
            else:
                ulagrede_endringer = True

class Bok:
    def __init__(self, tittel, forfattere, utgivelsesår, utgave=1):
        self.tittel = tittel
        self.forfattere = forfattere
        self.utgivelsesår = utgivelsesår
        self.utgave = utgave

    def __str__(self):
        if len(self.forfattere) == 1:
            forfatter_tekst = self.forfattere[0]
        else:
            forfatter_tekst = " og ".join([", ".join(self.forfattere[:-1]), self.forfattere[-1]])
        return f"{self.tittel}, {self.utgave}. utgave, av {forfatter_tekst} ({self.utgivelsesår})"

    def til_dict(self):
        return {
            "tittel": self.tittel,
            "forfattere": "|".join(self.forfattere),
            "utgivelsesår": self.utgivelsesår,
            "utgave": self.utgave,
        }


class Beholdning:
    def __init__(self, eksemplarer_tot=1, eksemplarer_nå=None):
        self.eksemplarer_tot = eksemplarer_tot
        self.eksemplarer_nå = (
            eksemplarer_nå if eksemplarer_nå is not None else eksemplarer_tot
        )

    def __str__(self):
        return f"{self.eksemplarer_nå}/{self.eksemplarer_tot}"

    def lån_ut(self):
        if self.eksemplarer_nå > 0:
            self.eksemplarer_nå -= 1
            return True
        return False

    def lever_inn(self):
        if self.eksemplarer_nå >= self.eksemplarer_tot:
            raise ValueError("Maks antall av denne boken er allerede levert inn")
        self.eksemplarer_nå += 1
        return True

    def til_dict(self):
        return {
            "eksemplarer_nå": self.eksemplarer_nå,
            "eksemplarer_tot": self.eksemplarer_tot,
        }

    def antall_utlånt(self):
        return self.eksemplarer_tot - self.eksemplarer_nå


class Bibliotek:
    def __init__(self):
        self.bøker = {}

    def lån_ut(self, bok):
        return self.bøker[bok].lån_ut()

    def lever_inn(self, bok):
        return self.bøker[bok].lever_inn()

    def legg_til_bok(self, bok, eksemplarer_tot=1, eksemplarer_nå=None):
        beholdning = Beholdning(eksemplarer_tot, eksemplarer_nå)
        self.bøker[bok] = beholdning

    def vis_alle_bøker(self):
        for bok, beholdning in self.bøker.items():
            ord = "eksemplar" if beholdning.eksemplarer_nå == 1 else "eksemplarer"
            status = (
                f"{beholdning.eksemplarer_nå} {ord}"
                if beholdning.eksemplarer_nå > 0
                else f"Ingen ledige {ord}"
            )
            print(f"{bok} - {status}")

    def vis_alle_lånte_bøker(self):
        for bok, beholdning in self.bøker.items():
            if beholdning.antall_utlånt() > 0:
                antall_lånte = beholdning.antall_utlånt()
                ord = "eksemplar" if antall_lånte == 1 else "eksemplarer"
                print(f"{bok} - {antall_lånte} {ord} utlånt")


    def vis_titler(self):
        for nr, bok in enumerate(self.bøker, start=1):
            print(f"{nr}. {bok}")

    def tøm_biblioteket(self):
        self.bøker.clear()

    def utlån_teller(self):
        utlånt = 0
        for beholdning in self.bøker.values():
            utlånt += beholdning.antall_utlånt()
        return utlånt

    def søk(self, søke_streng):
        søke_liste = søke_streng.lower().split()
        resultat = []
        for bok in self.bøker:
            for ord in søke_liste:
                if ord not in bok.tittel.lower():
                    break
            else:
                resultat.append(bok)
        return resultat
            





                    


# Oppretter noen bokobjekter
bok1 = Bok("Starting out with Python", ["Tony Gaddis"], 2001, 6)
bok2 = Bok("Python for realfag", ["Finn Aakre Hugen", "Marius Lysaker"], 1995, 3)
bok3 = Bok(
    "Objektorientert programmering med Python", ["Henrik Hillestad Løvold"], 2025
)

# Skriver ut informasjon om bøkene
bibliotek = Bibliotek()
innstillinger = les_innstillinger()
if innstillinger["autolast"] and last_bøker(bibliotek):
    melding("Biblioteket ble lastet automatisk")

else:
    bibliotek.legg_til_bok(bok1)
    bibliotek.legg_til_bok(bok2)
    bibliotek.legg_til_bok(bok3)

hovedmeny(bibliotek)

