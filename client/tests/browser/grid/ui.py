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
Heute muß die Glocke werden!
Frisch, Gesellen, seid zur Hand!
Von der Stirne heiß
Rinnen muß der Schweiß,
Soll das Werk den Meister loben!
Doch der Segen kommt von oben.

Zum Werke, das wir ernst bereiten,
Geziemt sich wohl ein ernstes Wort;
Wenn gute Reden sie begleiten,
Dann fließt die Arbeit munter fort.
So laßt uns jetzt mit Fleiß betrachten,
Was durch schwache Kraft entspringt;
Den schlechten Mann muß man verachten,
Der nie bedacht, was er vollbringt.
Das ist's ja, was den Menschen zieret,
Und dazu ward ihm der Verstand,
Daß er im Herzen spüret,
Was er erschaffen mit seiner Hand.

Nehmt Holz vom Fichtenstamme
Doch recht trocken laßt es sein,
Daß die eingepreßte Flamme
Schlage zu dem Schwalch hinein!
Kocht des Kupfers Brei!
Schnell das Zinn herbei,
Daß die zähe Glockenspeise
Fließe nach der rechten Weise!

Was in des Dammes tiefer Grube
Die Hand mit Feuers Hilfe baut,
Hoch auf des Turmes Glockenstube,
Da wird es von uns zeugen laut.
Noch dauern wird's in späten Tagen
Und rühren vieler Menschen Ohr,
Und wird mit dem Betrübten klagen
Und stimmen zu der Andacht Chor.
Was unten tief dem Erdensohne
Das wechselnde Verhängnis bringt,
Das schlägt an die metallne Krone,
Die es erbaulich weiter klingt.

Weiße Blasen seh' ich springen;
Wohl! die Massen sind im Fluß.
Laßt's mit Aschensalz durchdringen,
Das befördert schnell den Guß.
Auch vom Schaume rein
Muß die Mischung sein,
Daß vom reinlichen Metalle
Rein und voll die stimme schalle.

Denn mit der Freude Feierklange
Begrüßt sie das geliebte Kind
Auf seines Lebens ersten Gange,
Den es in des Schlafes Arm beginnt.
Ihm ruhen noch im Zeitenschoße
Die schwarzen und die heitern Lose;
Der Mutterliebe zarte Sorgen
Bewachen seinen goldnen Morgen.
Die Jahre fliehen pfeilgeschwind.
Vom Mädchen reißt sich stolz der Knabe,
Er stürmt ins Leben wild hinaus,
Durchmißt die Welt am Wanderstabe,
Fremd kehrt er heim ins Vaterhaus.
Und herrlich in der Jugend Prangen,
Wie ein Gebild aus Himmelshöhn,
Mit züchtigen, verschämten Wangen,
Sieht er die Jungfrau vor sich stehn.
Da faßt ein namenloses Sehnen
Des Jünglings Herz, er irrt allein,
Aus seinen Augen brechen Tränen,
Er flieht der Brüder wilden Reihn.
Errötend folgt er ihren Spuren
Und ist von ihrem Gruß beglückt,
Das Schönste sucht er auf den Fluren,
Womit er seine Liebe schmückt.
O zarte Sehnsucht, süßes Hoffen,
Der ersten Liebe goldne Zeit,
Das Auge sieht den Himmel offen,
Es schwelgt das Herz in Seligkeit;
O daß sie ewig grünen bliebe,
Die schöne Zeit der jungen Liebe!

Wie sich schon die Pfeifen bräunen!
Dieses Stäbchen tauch' ich ein:
Sehn wir's überglast erscheinen,
Wird's zum Gusse zeitig sein.
Jetzt, Gesellen, frisch!
Prüft mir das Gemisch,
Ob das Spröde mit dem Weichen
Sich vereint zum guten Zeichen.

Denn wo das Strenge mit dem Zarten,
Wo Starkes sich und Mildes paarten,
Da gibt es einen guten Klang.
Drum prüfe, wer sich ewig bindet,
Ob sich das Herz zum Herzen findet!
Der Wahn ist kurz, die Reu' ist lang.
Lieblich in der Bräute Locken
Spielt der jungfräuliche Kranz,
Wenn die hellen Kirchenglocken
Laden zu des Festes Glanz.
Ach! des Lebens schönste Feier
Endigt auch den Lebensmai:
Mit dem Gürtel, mit dem Schleier
Reißt der schöne Wahn entzwei.
Die Leidenschaft flieht,
Die Liebe muß bleiben;
Die Blume verblüht,
Die fruchtmuß treiben.
Der Mann muß hinaus
In's feindliche Leben,
Muß wirken und streben
Und pflanzen und schaffen,
Erlisten, erraffen,
Muß wetten und wagen,
Das Glück zu erjagen.
Da strömet herbei die unendliche Gabe,
Es füllt sich der Speicher mit köstlicher Habe,
Die Räume wachsen, es dehnt sich das Haus.
Und drinnen waltet
Die züchtige Hausfrau,
Die Mutter der Kinder,
Und herrschet weise
Im häuslichen Kreise,
Und lehret die Mädchen
Und wehret den Knaben,
Und reget ohn' Ende
Die fleißigen Hände,
Und mehrt den Gewinn
Mit ordnendem Sinn,
Und füllet mit Schätzen die duftenden Laden,
Und dreht um die schnurrende Spindel den Faden,
Und sammelt im reinlich geglätteten Schrein
Die schimmernde Wolle, den schneeigen Lein,
Und füget zum Guten den Glanz und den Schimmer,
Und ruhet nimmer.

Und der Vater mit frohem Blick
Von des Hauses weitschauendem Giebel
Überzählt sein blühendes Glück,
Siehet der Pfosten ragende Bäume,
Und der Scheunen gefüllte Räume,
Und die Speicher, vom Segen gebogen,
Und des Kornes bewegte Wogen,
Rühmt sich mit stolzem Mund:
Fest, wie der Erde Grund,
Gegen des Unglücks Macht
Steht mir des Hauses Pracht!
Doch mit des Geschickes Mächten
Ist kein ew'ger Bund zu flechten,
Und das Unglück schreitet schnell.

Wohl! nun kann der Guß beginnen,
Schön gezacket ist der Bruch,
Doch bevor wir's lassen rinnen,
Betet einen frommen Spruch!
Stoßt den Zapfen aus!
Gott bewahr' das Haus!
Rauschend in des Henkels Bogen
Schießt's mit feuerbraunen Wogen.

Wohltätig ist des Feuers Macht,
Wenn sie der Mensch bezähmt, bewacht,
Und was er bildet, was er schafft,
Das dankt er dieser Himmelskraft,
Wenn sie der Fessel sich entrafft,
Einhertritt auf der eignen Spur,
Die freie Tochter der Natur.
Wehe, wenn sie losgelassen,
Wachsend ohne Widerstand,
Durch die volkbelebten Gassen
Wälzt den ungeheuren Brand!
Denn die Elemente hassen
Das Gebild der Menschenhand.
Aus der Wolke
Quillt der Segen,
Strömt der Regen;
Aus der Wolke, ohne Wahl,
Zuckt der Strahl.
Hört ihr's wimmern hoch im Turm?
Das ist Sturm!
Rot, wie Blut,
Ist der Himmel;
Das ist nicht des Tages Glut!
Welch Getümmel
Straßen auf!
Dampf wallt auf!
Flackernd steigt die Feuersäule;
Durch der Straße lange Zeile
Wächst es fort mit Windeseile;
Kochend, wie aus Ofens Rachen,
Glühn die Lüfte, Balken krachen,
Pfosten stürzen, Fenster klirren,
Kinder jammern, Mütter irren,
Tiere wimmern
Unter Trümmern;
Alles rennet, rettet, flüchtet,
Taghell ist die Nacht gelichtet.
Durch die Hände lange Kette
Um die Wette
Fliegt der Eimer; hoch im Bogen
Spritzen Quellen Wasserwogen.
Heulend kommt der Sturm geflogen,
Der die Flamme brausend sucht;
Prasselnd in die dürre Frucht
Fällt sie, in des Speichers Räume,
In der Sparren dürre Bäume, Und als wollte sie im Wehen
Mit sich fort der Erde Wucht
Reißen in gewalt'ger Flucht,
Wächst sie in des Himmels Höhen
Riesengroß.
Hoffnungslos
Weicht der Mensch der Götterstärke:
Müßig sieht er seine Werke
Und bewundernd untergehn.

Leergebrannt
Ist die Stätte,
Wilder Stürme rauhes Bette
In den öden Fensterhöhlen
Wohnt das Grauen,
Und des Himmels Wolken schauen
Hoch hinein.

Einen Blick
Nach dem Grabe
Seiner Habe
Sendet noch der Mensch zurück ۃ
Greift fröhlich dann zum Wanderstabe.
Was des Feuers Wut ihm auch geraubt,
Ein süßer Trost ist ihm geblieben:
Er zählt die Häupter seiner Lieben,
Und sieh! ihm fehlt kein teures Haupt.

In die Erd' ist's aufgenommen,
Glücklich ist die Form gefüllt;
Wird's auch schön zu Tage kommen,
Daß es Fleiß und Kunst vergilt?
Wenn der Guß mißlang?
Wenn die Form zersprang?
Ach! vielleicht, indem wir hoffen,
Hat uns Unheil schon getroffen.

Dem dunklen Schoß der heil'gen Erde
Vertrauen wir der Hände Tat,
Vertraut der Sämann seine Saat
Und hofft, daß sie entkeimen werde
Zum Segen, nach des Himmels Rat.
Noch köstlicheren Samen bergen
Wir trauernd in der Erde Schoß
Und hoffen, daß er aus den Särgen
Erblühen soll zu schönerm Los.

Von dem Dome,
Schwer und bang,
Tönt die Glocke
Grabgesang.
Ernst begleiten ihre Trauerschläge
Einen Wanderer auf dem letzten Wege.

Ach! die Gattin ist's, die teure,
Ach! es ist die treue Mutter,
Die der schwarze Fürst der Schatten
Wegführt aus dem Arm des Gatten,
Aus der zarten Kinder Schar,
Die sie blühend ihm gebar,
Die sie an der treuen Brust
Wachsen sah mit Mutterlust ۃ
Ach! des Hauses zarte Bande
Sind gelöst auf immerdar;
Denn sie wohnt im Schattenlande,
Die des Hauses Mutter war;
Denn es fehlt ihr treues Walten,
Ihre Sorge wacht nicht mehr;
An verwaister Stätte schalten
Wird die Fremde, liebeleer.

Bis die Glocke sich verkühlet,
Laßt die strenge Arbeit ruhn!
Wie im Laub der Vogel spielet,
Mag sich jeder gütlich tun.
Winkt der Sterne Licht,
Ledig aller Pflicht,
Hört der Bursch die Vesper schlagen;
Meister muß sich immer plagen.

Munter fördert seine Schritte
Fern im wilden Forst der Wanderer
Nach der lieben Heimathütte.
Blökend ziehen heim die Schafe,
Und der Rinder
Breitgestirnte, glatte Scharen
Kommen brüllend,
Die gewohnten Ställe füllend.
Schwer herein
Schwankt der Wagen
Kornbeladen;
Bunt von Farben,
Auf den Garben
Liegt der Kranz,
Und das junge Volk der Schnitter
Fliegt im Tanz.
Markt und Straße werden stiller;
Um des Lichts gesell'ge Flamme
Sammeln sich die Hausbewohner,
Und das Stadttor schließt sich knarrend.
Schwarz bedecket
Sich die Erde;
Doch den sichern Bürger schrecket
Nicht die Nacht,
Die den Bösen gräßlich wecket;
Denn das Auge des Gesetzes wacht.

Heil'ge Ordnung, segensreiche
Himmelstochter, die das Gleiche
Frei und leicht und freudig bindet,
Die der Städte Bau gegründet,
Die herein von den Gefilden
Rief den ungesell'gen Wilden,
Eintrat in der Menschen Hütten,
Sie gewöhnt zu sanften Sitten,
Und das teuerste der Bande
Wob, den Trieb zum Vaterlande!

Tausend fleiß'ge Hände regen,
Helfen sich in munterm Bund,
Und in feurigem Bewegen
Werden alle Kräfte kund.
Meister rührt sich und Geselle
In der Freiheit heil'gem Schutz;
Jeder freut sich seiner Stelle,
Bietet dem Verächter Trutz.
Arbeit ist des Bürgers Zierde,
Segen ist der Mühe Preis:
Ehrt den König seine Würde,
Ehret uns der Hände Fleiß.

Holder Friede,
Süße Eintracht,
Weilet, eilet
Freundlich über dieser Stadt!
Möge nie der Tag erscheinen,
Wo des rauhen Krieges Horden
Dieses stille Tal durchtoben;
Wo der Himmel,
Den des Abends sanfte Röte
Lieblich malt,
Von der Dörfer, von der Städte
Wildem Brande schrecklich strahlt!

Nun zerbrecht mir das Gebäude,
Seine Absicht hat's erfüllt,
Daß sich Herz und Auge weide
An dem wohlgelungnen Bild.
Schwingt den Hammer, schwingt,
Bis der Mantel springt!
Wenn die Glock' soll auferstehen,
Muß die Form in Stücken gehen.

Der Meister kann die Form zerbrechen
Mit weiser Hand, zur rechten Zeit;
Doch wehe, wenn in Flammenbächen
Das glüh'nde Erz sich selbst befreit!
Blindwütend mit des Donners Krachen
Zersprengt es das geborstne Haus,
Und wie aus offnem Höllenrachen
Speit es Verderben zündend aus.
Wo rohe Kräfte sinnlos walten,
Da kann sich kein Gebild gestalten;
Wenn sich die Völker selbst befrein,
Da kann die Wohlfahrt nicht gedeihn.

Weh, wenn sich in dem Schoß der Städte
Der Feuerzunder still gehäuft,
Das Volk, zerreißend seine Kette,
Zur Eigenhilfe schrecklich greift!
Da zerret an der Glocke Strängen
Der Aufruhr, daß sie heulend schallt,
Und, nur geweiht zu Friedensklängen,
Die Losung anstimmt zur Gewalt.

Freiheit und Gleichheit! hört man schallen;
Der ruh'ge Bürger greift zur Wehr,
Die Straßen füllen sich, die Hallen,
Und Würgerbanden ziehn umher.
Da werden Weiber zu Hyänen
Und treiben mit Entsetzen Scherz:
Noch zuckend, mit des Panthers Zähnen,
Zerreißen sie des Feindes Herz.
Nichts Heiliges ist mehr, es lösen
Sich alle Bande frommer scheu;
Der Gute räumt den Platz dem Bösen,
Und alle Laster walten frei.
Gefährlich ist's, den Leu zu wecken,
Verderblich ist des Tigers Zahn,
Jedoch der schrecklichste der Schrecken,
Das ist der Mensch in seinem Wahn.
Weh denen, die dem Ewigblinden
Des Lichtes Himmelsfackel leihn!
Sie strahlt ihm nicht, sie kann nur zünden,
Und äschert Städt' und Länder ein.

Freude hat mit Gott gegeben!
Sehet! wie ein gold'ner Stern
Aus der Hülse, blank und eben,
Schält sich der metallne Kern.
Von dem Helm zum Kranz
Spielt's wie Sonnenglanz.
Auch des Wappens nette Schilder
Loben den erfahrnen Bilder.

Herein! herein,
Gesellen alle, schließt den Reihen,
Daß wir die Glocke taufend weihen!
Concordia soll ihr Name sein.
Zur Eintracht, zu herzinnigem Vereine
Versammle sie die liebende Gemeine.

Und dies sei fortan ihr Beruf,
Wozu der Meister sie erschuf:
Hoch über'm niedern Erdenleben
Soll sie im blauen Himmelszelt,
Die Nachbarin des Domes, schweben
Und grenzen an die Sternenwelt,
Soll eine Stimme sein von oben,
Wie der Gestirne helle Schar,
Die ihren Schöpfer wandelnd loben
Und führen das bekränzte Jahr.
Nur ewigen und ernsten Dingen
Sei ihr metallner Mund geweiht,
Und stündlich mit den schnellen Schwingen
Berühr' im Fluge sie die Zeit.
Dem Schicksal leihe sie die Zunge;
Selbst herzlos, ohne Mitgefühl,
Begleite sie mit ihrem Schwunge
Des Lebens wechselvolles Spiel.
Und wie der Klang im Ohr vergehet,
Der mächtig tönend ihr entschallt,
So lehre sie, daß nichts bestehet,
Daß alles Irdische verhallt.

Jetzo mit der Kraft des Stranges
Wiegt die Glock' mir aus der Gruft,
Daß sie in das Reich des Klanges
Steige, in die Himmelsluft!
Ziehet, ziehet, hebt!
Sie bewegt sich, schwebt!
Freude dieser Stadt bedeute,
Friede sei ihr erst Geläute.
"""
