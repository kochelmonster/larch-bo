from datetime import date
from larch.reactive import Reactive, Cell, rule
from larch.bo.client.wc.vaadin import vbutton, vinput, vcheckbox, vswitch, vdate, vdialog, styles
from larch.bo.client.grid import Grid, splitter
from larch.bo.client.browser import start_main
from larch.bo.client.session import Session
from larch.bo.client.control import register
from larch.bo.client.command import label, icon, command, MixinCommandHandler
from larch.bo.client.animate import animator

# __pragma__("skip")
window = document = console = styles
def require(path): pass
def __pragma__(*args): pass
# __pragma__("noskip")


vdate.register()
vbutton.register()
vinput.register()
vcheckbox.register()
vswitch.register()


class Model(Reactive):
    first = Cell("Jon")
    last = Cell("Doe")
    email = Cell("jon@doe.com")
    birthday = Cell(date(1985, 10, 1))
    password = Cell("")
    accept = Cell(False)


class AllLive:
    def modify_controls(self):
        super().modify_controls()
        self.control("first").live()
        self.control("last").live()
        self.control("email").live()
        self.control("password").live()


@register(Model)
class CheckForm(MixinCommandHandler, AllLive, Grid):
    layout = """
First Name|[first]
Last Name |[last]
Email     |[email]@email
Birthday  |[birthday]
Password  |[password]@password
Accept    |[accept]
          |[.open]
          |<1>
"""

    @command(key="ctrl+o")
    @icon("check")
    @label("Open Dialog")
    def open(self):
        def done():
            console.log("***done dialog")
            window.lbo.state.set("main", "dialog", None)

        dialog = vdialog.Dialog(TimeForPoems(), self.context)
        dialog.modal(done, style="height: 80%")
        window.lbo.state.set("main", "dialog", True)
        console.log("submit")

    @rule
    def _rule_update_state(self):
        if self.element:
            yield
            for state in window.lbo.state.loop("main", "dialog"):
                if state:
                    self.open()


@register(Model, "switch")
class SwitchForm(AllLive, Grid):
    layout = """
[first]
[last]
[email]
[password]
Accept|[accept]@switch
      |<1>
"""

    def modify_controls(self):
        super().modify_controls()
        self.set_input("first", "First Name")
        self.set_input("last", "Last Name")
        self.celement("email").label = "Email"
        self.celement("password").label = "Password"

    def set_input(self, name, label):
        el = self.celement(name)
        el.label = label
        el.style.width = "100%"


class Controller(Grid):
    layout = """
Show Form1   |[.show_form1]@switch
Show Form2   |[.show_form2]@switch
Toggle Forms |[.first_is_switch]@switch
Disable      |[.disabled]@switch
Readonly     |[.readonly]@switch
"""

    show_form1 = Cell(True)
    show_form2 = Cell(True)
    first_is_switch = Cell(False)
    disabled = Cell(False)
    readonly = Cell(False)


class HTMLEditor(splitter.MixinSplitter, Grid):
    layout = """
Editor               |Preview
edit:[.content]@multi|preview:[.content]@html|<1>
<1M>                 |<1M>
"""
    content = Cell("""
<h1>Hello</h1>
World""")

    def modify_controls(self):
        edit = self.control("edit")
        style = edit.element.style
        style.width = "100%"
        style.height = "100%"
        style.boxSizing = "border-box"
        edit.live()


class TimeForPoems(Grid):
    layout = """
[.title]@html
[.poem]@text  |<1>
[.like_it]{c}
"""

    def __init__(self, cv):
        super().__init__(cv)
        self.poem = GLOCKE
        self.title = "<h3>Das Lied von der Glocke</h3>"

    def modify_controls(self):
        self.container("poem").classList.add("scrollable")

    @label("Like it")
    def like_it(self):
        self.context.get("dialog").close()


class Frame(splitter.MixinSplitter, Grid):
    layout = """
f1:[.person]{1}       |[.controller]{3}
f2:[.person]{2}@switch|   "             |<1M>
[.html]{4}                              |<1M>
<1>                   |
"""

    def __init__(self, cv):
        super().__init__(cv)
        self.person = Model()
        self.html = HTMLEditor()
        self.controller = Controller()

    @rule
    def _rule_change_styles(self):
        if self.element:
            controller = self.control("controller")
            if controller.first_is_switch:
                self.contexts["f1"].set("style", "switch")
            else:
                self.contexts["f1"].set("style", "")

    @rule
    def _rule_controller_styles(self):
        if self.element:
            controller = self.control("controller")
            animator.show(self.container("f1"), controller.show_form1)
            animator.show(self.container("f2"), controller.show_form2)

            self.contexts["f1"].set("disabled", controller.disabled)
            self.contexts["f2"].set("disabled", controller.disabled)
            self.contexts["f1"].set("readonly", controller.readonly)
            self.contexts["f2"].set("readonly", controller.readonly)


def main():
    print("start main")
    Session(Frame()).boot()


start_main(main)

GLOCKE = """
Fest gemauert in der Erden
Steht die Form aus Lehm gebrannt.
Heute mu?? die Glocke werden!
Frisch, Gesellen, seid zur Hand!
Von der Stirne hei??
Rinnen mu?? der Schwei??,
Soll das Werk den Meister loben!
Doch der Segen kommt von oben.

Zum Werke, das wir ernst bereiten,
Geziemt sich wohl ein ernstes Wort;
Wenn gute Reden sie begleiten,
Dann flie??t die Arbeit munter fort.
So la??t uns jetzt mit Flei?? betrachten,
Was durch schwache Kraft entspringt;
Den schlechten Mann mu?? man verachten,
Der nie bedacht, was er vollbringt.
Das ist's ja, was den Menschen zieret,
Und dazu ward ihm der Verstand,
Da?? er im Herzen sp??ret,
Was er erschaffen mit seiner Hand.

Nehmt Holz vom Fichtenstamme
Doch recht trocken la??t es sein,
Da?? die eingepre??te Flamme
Schlage zu dem Schwalch hinein!
Kocht des Kupfers Brei!
Schnell das Zinn herbei,
Da?? die z??he Glockenspeise
Flie??e nach der rechten Weise!

Was in des Dammes tiefer Grube
Die Hand mit Feuers Hilfe baut,
Hoch auf des Turmes Glockenstube,
Da wird es von uns zeugen laut.
Noch dauern wird's in sp??ten Tagen
Und r??hren vieler Menschen Ohr,
Und wird mit dem Betr??bten klagen
Und stimmen zu der Andacht Chor.
Was unten tief dem Erdensohne
Das wechselnde Verh??ngnis bringt,
Das schl??gt an die metallne Krone,
Die es erbaulich weiter klingt.

Wei??e Blasen seh' ich springen;
Wohl! die Massen sind im Flu??.
La??t's mit Aschensalz durchdringen,
Das bef??rdert schnell den Gu??.
Auch vom Schaume rein
Mu?? die Mischung sein,
Da?? vom reinlichen Metalle
Rein und voll die stimme schalle.

Denn mit der Freude Feierklange
Begr????t sie das geliebte Kind
Auf seines Lebens ersten Gange,
Den es in des Schlafes Arm beginnt.
Ihm ruhen noch im Zeitenscho??e
Die schwarzen und die heitern Lose;
Der Mutterliebe zarte Sorgen
Bewachen seinen goldnen Morgen.
Die Jahre fliehen pfeilgeschwind.
Vom M??dchen rei??t sich stolz der Knabe,
Er st??rmt ins Leben wild hinaus,
Durchmi??t die Welt am Wanderstabe,
Fremd kehrt er heim ins Vaterhaus.
Und herrlich in der Jugend Prangen,
Wie ein Gebild aus Himmelsh??hn,
Mit z??chtigen, versch??mten Wangen,
Sieht er die Jungfrau vor sich stehn.
Da fa??t ein namenloses Sehnen
Des J??nglings Herz, er irrt allein,
Aus seinen Augen brechen Tr??nen,
Er flieht der Br??der wilden Reihn.
Err??tend folgt er ihren Spuren
Und ist von ihrem Gru?? begl??ckt,
Das Sch??nste sucht er auf den Fluren,
Womit er seine Liebe schm??ckt.
O zarte Sehnsucht, s????es Hoffen,
Der ersten Liebe goldne Zeit,
Das Auge sieht den Himmel offen,
Es schwelgt das Herz in Seligkeit;
O da?? sie ewig gr??nen bliebe,
Die sch??ne Zeit der jungen Liebe!

Wie sich schon die Pfeifen br??unen!
Dieses St??bchen tauch' ich ein:
Sehn wir's ??berglast erscheinen,
Wird's zum Gusse zeitig sein.
Jetzt, Gesellen, frisch!
Pr??ft mir das Gemisch,
Ob das Spr??de mit dem Weichen
Sich vereint zum guten Zeichen.

Denn wo das Strenge mit dem Zarten,
Wo Starkes sich und Mildes paarten,
Da gibt es einen guten Klang.
Drum pr??fe, wer sich ewig bindet,
Ob sich das Herz zum Herzen findet!
Der Wahn ist kurz, die Reu' ist lang.
Lieblich in der Br??ute Locken
Spielt der jungfr??uliche Kranz,
Wenn die hellen Kirchenglocken
Laden zu des Festes Glanz.
Ach! des Lebens sch??nste Feier
Endigt auch den Lebensmai:
Mit dem G??rtel, mit dem Schleier
Rei??t der sch??ne Wahn entzwei.
Die Leidenschaft flieht,
Die Liebe mu?? bleiben;
Die Blume verbl??ht,
Die fruchtmu?? treiben.
Der Mann mu?? hinaus
In's feindliche Leben,
Mu?? wirken und streben
Und pflanzen und schaffen,
Erlisten, erraffen,
Mu?? wetten und wagen,
Das Gl??ck zu erjagen.
Da str??met herbei die unendliche Gabe,
Es f??llt sich der Speicher mit k??stlicher Habe,
Die R??ume wachsen, es dehnt sich das Haus.
Und drinnen waltet
Die z??chtige Hausfrau,
Die Mutter der Kinder,
Und herrschet weise
Im h??uslichen Kreise,
Und lehret die M??dchen
Und wehret den Knaben,
Und reget ohn' Ende
Die flei??igen H??nde,
Und mehrt den Gewinn
Mit ordnendem Sinn,
Und f??llet mit Sch??tzen die duftenden Laden,
Und dreht um die schnurrende Spindel den Faden,
Und sammelt im reinlich gegl??tteten Schrein
Die schimmernde Wolle, den schneeigen Lein,
Und f??get zum Guten den Glanz und den Schimmer,
Und ruhet nimmer.

Und der Vater mit frohem Blick
Von des Hauses weitschauendem Giebel
??berz??hlt sein bl??hendes Gl??ck,
Siehet der Pfosten ragende B??ume,
Und der Scheunen gef??llte R??ume,
Und die Speicher, vom Segen gebogen,
Und des Kornes bewegte Wogen,
R??hmt sich mit stolzem Mund:
Fest, wie der Erde Grund,
Gegen des Ungl??cks Macht
Steht mir des Hauses Pracht!
Doch mit des Geschickes M??chten
Ist kein ew'ger Bund zu flechten,
Und das Ungl??ck schreitet schnell.

Wohl! nun kann der Gu?? beginnen,
Sch??n gezacket ist der Bruch,
Doch bevor wir's lassen rinnen,
Betet einen frommen Spruch!
Sto??t den Zapfen aus!
Gott bewahr' das Haus!
Rauschend in des Henkels Bogen
Schie??t's mit feuerbraunen Wogen.

Wohlt??tig ist des Feuers Macht,
Wenn sie der Mensch bez??hmt, bewacht,
Und was er bildet, was er schafft,
Das dankt er dieser Himmelskraft,
Wenn sie der Fessel sich entrafft,
Einhertritt auf der eignen Spur,
Die freie Tochter der Natur.
Wehe, wenn sie losgelassen,
Wachsend ohne Widerstand,
Durch die volkbelebten Gassen
W??lzt den ungeheuren Brand!
Denn die Elemente hassen
Das Gebild der Menschenhand.
Aus der Wolke
Quillt der Segen,
Str??mt der Regen;
Aus der Wolke, ohne Wahl,
Zuckt der Strahl.
H??rt ihr's wimmern hoch im Turm?
Das ist Sturm!
Rot, wie Blut,
Ist der Himmel;
Das ist nicht des Tages Glut!
Welch Get??mmel
Stra??en auf!
Dampf wallt auf!
Flackernd steigt die Feuers??ule;
Durch der Stra??e lange Zeile
W??chst es fort mit Windeseile;
Kochend, wie aus Ofens Rachen,
Gl??hn die L??fte, Balken krachen,
Pfosten st??rzen, Fenster klirren,
Kinder jammern, M??tter irren,
Tiere wimmern
Unter Tr??mmern;
Alles rennet, rettet, fl??chtet,
Taghell ist die Nacht gelichtet.
Durch die H??nde lange Kette
Um die Wette
Fliegt der Eimer; hoch im Bogen
Spritzen Quellen Wasserwogen.
Heulend kommt der Sturm geflogen,
Der die Flamme brausend sucht;
Prasselnd in die d??rre Frucht
F??llt sie, in des Speichers R??ume,
In der Sparren d??rre B??ume, Und als wollte sie im Wehen
Mit sich fort der Erde Wucht
Rei??en in gewalt'ger Flucht,
W??chst sie in des Himmels H??hen
Riesengro??.
Hoffnungslos
Weicht der Mensch der G??tterst??rke:
M????ig sieht er seine Werke
Und bewundernd untergehn.

Leergebrannt
Ist die St??tte,
Wilder St??rme rauhes Bette
In den ??den Fensterh??hlen
Wohnt das Grauen,
Und des Himmels Wolken schauen
Hoch hinein.

Einen Blick
Nach dem Grabe
Seiner Habe
Sendet noch der Mensch zur??ck ??
Greift fr??hlich dann zum Wanderstabe.
Was des Feuers Wut ihm auch geraubt,
Ein s????er Trost ist ihm geblieben:
Er z??hlt die H??upter seiner Lieben,
Und sieh! ihm fehlt kein teures Haupt.

In die Erd' ist's aufgenommen,
Gl??cklich ist die Form gef??llt;
Wird's auch sch??n zu Tage kommen,
Da?? es Flei?? und Kunst vergilt?
Wenn der Gu?? mi??lang?
Wenn die Form zersprang?
Ach! vielleicht, indem wir hoffen,
Hat uns Unheil schon getroffen.

Dem dunklen Scho?? der heil'gen Erde
Vertrauen wir der H??nde Tat,
Vertraut der S??mann seine Saat
Und hofft, da?? sie entkeimen werde
Zum Segen, nach des Himmels Rat.
Noch k??stlicheren Samen bergen
Wir trauernd in der Erde Scho??
Und hoffen, da?? er aus den S??rgen
Erbl??hen soll zu sch??nerm Los.

Von dem Dome,
Schwer und bang,
T??nt die Glocke
Grabgesang.
Ernst begleiten ihre Trauerschl??ge
Einen Wanderer auf dem letzten Wege.

Ach! die Gattin ist's, die teure,
Ach! es ist die treue Mutter,
Die der schwarze F??rst der Schatten
Wegf??hrt aus dem Arm des Gatten,
Aus der zarten Kinder Schar,
Die sie bl??hend ihm gebar,
Die sie an der treuen Brust
Wachsen sah mit Mutterlust ??
Ach! des Hauses zarte Bande
Sind gel??st auf immerdar;
Denn sie wohnt im Schattenlande,
Die des Hauses Mutter war;
Denn es fehlt ihr treues Walten,
Ihre Sorge wacht nicht mehr;
An verwaister St??tte schalten
Wird die Fremde, liebeleer.

Bis die Glocke sich verk??hlet,
La??t die strenge Arbeit ruhn!
Wie im Laub der Vogel spielet,
Mag sich jeder g??tlich tun.
Winkt der Sterne Licht,
Ledig aller Pflicht,
H??rt der Bursch die Vesper schlagen;
Meister mu?? sich immer plagen.

Munter f??rdert seine Schritte
Fern im wilden Forst der Wanderer
Nach der lieben Heimath??tte.
Bl??kend ziehen heim die Schafe,
Und der Rinder
Breitgestirnte, glatte Scharen
Kommen br??llend,
Die gewohnten St??lle f??llend.
Schwer herein
Schwankt der Wagen
Kornbeladen;
Bunt von Farben,
Auf den Garben
Liegt der Kranz,
Und das junge Volk der Schnitter
Fliegt im Tanz.
Markt und Stra??e werden stiller;
Um des Lichts gesell'ge Flamme
Sammeln sich die Hausbewohner,
Und das Stadttor schlie??t sich knarrend.
Schwarz bedecket
Sich die Erde;
Doch den sichern B??rger schrecket
Nicht die Nacht,
Die den B??sen gr????lich wecket;
Denn das Auge des Gesetzes wacht.

Heil'ge Ordnung, segensreiche
Himmelstochter, die das Gleiche
Frei und leicht und freudig bindet,
Die der St??dte Bau gegr??ndet,
Die herein von den Gefilden
Rief den ungesell'gen Wilden,
Eintrat in der Menschen H??tten,
Sie gew??hnt zu sanften Sitten,
Und das teuerste der Bande
Wob, den Trieb zum Vaterlande!

Tausend flei??'ge H??nde regen,
Helfen sich in munterm Bund,
Und in feurigem Bewegen
Werden alle Kr??fte kund.
Meister r??hrt sich und Geselle
In der Freiheit heil'gem Schutz;
Jeder freut sich seiner Stelle,
Bietet dem Ver??chter Trutz.
Arbeit ist des B??rgers Zierde,
Segen ist der M??he Preis:
Ehrt den K??nig seine W??rde,
Ehret uns der H??nde Flei??.

Holder Friede,
S????e Eintracht,
Weilet, eilet
Freundlich ??ber dieser Stadt!
M??ge nie der Tag erscheinen,
Wo des rauhen Krieges Horden
Dieses stille Tal durchtoben;
Wo der Himmel,
Den des Abends sanfte R??te
Lieblich malt,
Von der D??rfer, von der St??dte
Wildem Brande schrecklich strahlt!

Nun zerbrecht mir das Geb??ude,
Seine Absicht hat's erf??llt,
Da?? sich Herz und Auge weide
An dem wohlgelungnen Bild.
Schwingt den Hammer, schwingt,
Bis der Mantel springt!
Wenn die Glock' soll auferstehen,
Mu?? die Form in St??cken gehen.

Der Meister kann die Form zerbrechen
Mit weiser Hand, zur rechten Zeit;
Doch wehe, wenn in Flammenb??chen
Das gl??h'nde Erz sich selbst befreit!
Blindw??tend mit des Donners Krachen
Zersprengt es das geborstne Haus,
Und wie aus offnem H??llenrachen
Speit es Verderben z??ndend aus.
Wo rohe Kr??fte sinnlos walten,
Da kann sich kein Gebild gestalten;
Wenn sich die V??lker selbst befrein,
Da kann die Wohlfahrt nicht gedeihn.

Weh, wenn sich in dem Scho?? der St??dte
Der Feuerzunder still geh??uft,
Das Volk, zerrei??end seine Kette,
Zur Eigenhilfe schrecklich greift!
Da zerret an der Glocke Str??ngen
Der Aufruhr, da?? sie heulend schallt,
Und, nur geweiht zu Friedenskl??ngen,
Die Losung anstimmt zur Gewalt.

Freiheit und Gleichheit! h??rt man schallen;
Der ruh'ge B??rger greift zur Wehr,
Die Stra??en f??llen sich, die Hallen,
Und W??rgerbanden ziehn umher.
Da werden Weiber zu Hy??nen
Und treiben mit Entsetzen Scherz:
Noch zuckend, mit des Panthers Z??hnen,
Zerrei??en sie des Feindes Herz.
Nichts Heiliges ist mehr, es l??sen
Sich alle Bande frommer scheu;
Der Gute r??umt den Platz dem B??sen,
Und alle Laster walten frei.
Gef??hrlich ist's, den Leu zu wecken,
Verderblich ist des Tigers Zahn,
Jedoch der schrecklichste der Schrecken,
Das ist der Mensch in seinem Wahn.
Weh denen, die dem Ewigblinden
Des Lichtes Himmelsfackel leihn!
Sie strahlt ihm nicht, sie kann nur z??nden,
Und ??schert St??dt' und L??nder ein.

Freude hat mit Gott gegeben!
Sehet! wie ein gold'ner Stern
Aus der H??lse, blank und eben,
Sch??lt sich der metallne Kern.
Von dem Helm zum Kranz
Spielt's wie Sonnenglanz.
Auch des Wappens nette Schilder
Loben den erfahrnen Bilder.

Herein! herein,
Gesellen alle, schlie??t den Reihen,
Da?? wir die Glocke taufend weihen!
Concordia soll ihr Name sein.
Zur Eintracht, zu herzinnigem Vereine
Versammle sie die liebende Gemeine.

Und dies sei fortan ihr Beruf,
Wozu der Meister sie erschuf:
Hoch ??ber'm niedern Erdenleben
Soll sie im blauen Himmelszelt,
Die Nachbarin des Domes, schweben
Und grenzen an die Sternenwelt,
Soll eine Stimme sein von oben,
Wie der Gestirne helle Schar,
Die ihren Sch??pfer wandelnd loben
Und f??hren das bekr??nzte Jahr.
Nur ewigen und ernsten Dingen
Sei ihr metallner Mund geweiht,
Und st??ndlich mit den schnellen Schwingen
Ber??hr' im Fluge sie die Zeit.
Dem Schicksal leihe sie die Zunge;
Selbst herzlos, ohne Mitgef??hl,
Begleite sie mit ihrem Schwunge
Des Lebens wechselvolles Spiel.
Und wie der Klang im Ohr vergehet,
Der m??chtig t??nend ihr entschallt,
So lehre sie, da?? nichts bestehet,
Da?? alles Irdische verhallt.

Jetzo mit der Kraft des Stranges
Wiegt die Glock' mir aus der Gruft,
Da?? sie in das Reich des Klanges
Steige, in die Himmelsluft!
Ziehet, ziehet, hebt!
Sie bewegt sich, schwebt!
Freude dieser Stadt bedeute,
Friede sei ihr erst Gel??ute.
"""
