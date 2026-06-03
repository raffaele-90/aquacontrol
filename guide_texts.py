# AquaControl
# Copyright (C) 2026 Raffaele Schiavone
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from config_manager import global_config

GUIDE_TRANSLATIONS = {
"it": """
        <h2 style="color: #cdd6f4;">Guida Utente</h2>
        <br>
        <h3 style="color: #00e5ff;">Modalità PID Avanzata (Proporzionale, Integrale, Derivativo)</h3>
        <p>A differenza della modalità automatica, la modalità PID utilizza un algoritmo intelligente che adatta dinamicamente la potenza per mantenere il sensore di riferimento scelto alla temperatura impostata (<b>Obiettivo</b>), in base al carico del sistema in tempo reale.</p>
        <p>Il software offre tre profili preimpostati (<b>Lento, Normale, Veloce</b>). Per gli utenti esperti, la modalità <b>Manuale</b> permette di calibrare finemente i tre parametri matematici in modo da adattare l'algoritmo alle specifiche caratteristiche del proprio impianto:</p>

        <ul style="margin-top: 5px; margin-bottom: 15px;">
            <li style="margin-bottom: 8px;"><b style="color: #cba6f7;">Proporzionale (P):</b> Regola la sensibilità di base alle variazioni di temperatura. Agisce in risposta alla differenza istantanea tra la temperatura rilevata e l'<b>Obiettivo</b>. Un valore troppo elevato rende il controller eccessivamente reattivo, innescando continue oscillazioni nel regime di rotazione delle ventole. Incrementalo a step di <b>0.5</b>.</li>
            <li style="margin-bottom: 8px;"><b style="color: #cba6f7;">Integrale (I):</b> Gestisce la compensazione cumulativa sul lungo periodo. Analizza il tempo trascorso fuori dall'<b>Obiettivo</b> e accumula la correzione necessaria per far convergere le ventole al regime di rotazione necessario (es. 60% fisso) per mantenere stabilmente la temperatura del sensore. A causa dell'elevata inerzia termica dell'acqua, questo valore deve essere mantenuto molto basso. Modificalo a piccoli step di <b>0.01</b>.</li>
            <li style="margin-bottom: 8px;"><b style="color: #cba6f7;">Derivativo (D):</b> Applica uno smorzamento dinamico in base alla velocità con cui cambia la temperatura. <b>Nei sistemi a liquido si consiglia di mantenerlo vicino allo 0.</b> Poiché l'acqua si scalda in modo graduale, un valore eccessivamente alto porterebbe a improvvisi e ingiustificati picchi di rotazione in risposta a minime fluttuazioni di lettura del sensore.</li>
        </ul>

        <div style="background-color: #1e1e2e; padding: 10px; border-left: 4px solid #00e5ff; margin-bottom: 15px;">
            <p style="margin-top: 0;"><b>💡 Valori di Riferimento (Preset del software)</b><br>
            Se vuoi creare una curva manuale, utilizza questi valori come punto di partenza per orientarti:</p>
            <ul style="margin-bottom: 0;">
                <li><b>Lento:</b> P = 3.0 | I = 0.05 | D = 0.1</li>
                <li><b>Normale:</b> P = 5.0 | I = 0.08 | D = 0.3</li>
                <li><b>Veloce:</b> P = 8.0 | I = 0.10 | D = 0.5</li>
            </ul>
        </div>
        <hr style="border: 1px solid #313244; margin: 15px 0;">

        <h3 style="color: #00e5ff;">Sensore Virtuale (ΔT)</h3>
        <p>Attivando il <b>Sensore Virtuale (ΔT)</b>, AquaControl calcola costantemente la differenza tra il sensore principale impostato e un secondo sensore di riferimento: <br><code style="background-color: #1e1e2e; padding: 2px 5px;">[Principale] - [Riferimento] = ΔT</code></p>
        <p><b>Scenario di utilizzo tipico:</b></p>
        <p>In un sistema di raffreddamento a liquido convenzionale, la temperatura dei componenti non può mai scendere sotto la temperatura ambientale. Una curva impostata per tenere il liquido circa a 35°C funzionerà in inverno, ma in estate (con T amb > 35°C) costringerà i rotori delle ventole al 100% per raggiungere una temperatura fisicamente impossibile.</p>
        <p>Sottraendo la <i>Temperatura dell'Aria</i> (riferimento) alla <i>Temperatura del Liquido</i> (principale), è possibile impostare un <b>Obiettivo</b> PID di <b>10°C (ΔT)</b>. In questo modo, il sistema manterrà l'acqua a 30°C in inverno (20°C ambiente + 10) e a 40°C in estate (30°C ambiente + 10). Lo sforzo acustico e le prestazioni rimarranno costanti in ogni stagione, senza necessità di riprogrammare il software.</p>
        <hr style="border: 1px solid #313244; margin: 15px 0;">

        <h3 style="color: #00e5ff;">Cambio Profilo Automatico (Auto-Switch)</h3>
        <p>Questa funzione permette ad AquaControl di caricare autonomamente un profilo specifico quando avvii determinati programmi, per poi ripristinare il profilo alla chiusura.</p>
        <p><b>Come associare i programmi al profilo specifico:</b><br>
        Essendo un software nativo Linux, non è necessario cercare o inserire il percorso assoluto dell'eseguibile. È sufficiente digitare il <b>nome del processo</b> così come verrebbe letto dal terminale di sistema.</p>
        <p>Ad esempio, basterà scrivere <code>steam</code>, <code>firefox</code>, <code>blender</code>, ecc. per garantire che AquaControl rilevi immediatamente l'apertura del programma, indipendentemente dalla sua directory di installazione.</p>
        <hr style="border: 1px solid #313244; margin: 15px 0;">

        <h3 style="color: #00e5ff;">Potenza Minima e Start Boost</h3>
        <p><b>Potenza Minima (Prevenzione Stallo)</b><br>
        I motori delle ventole e delle pompe hanno un limite fisico sotto il quale non riescono a girare. Se invii un segnale del 10%, la ventola potrebbe fermarsi del tutto, pur continuando a ricevere corrente. La <i>Potenza Minima</i> imposta una soglia invalicabile di sicurezza: se decidi che questo limite è il 25%, il software ricalcolerà l'intera curva termica in modo che lo 0% logico del grafico corrisponda fisicamente al 25% reale inviato al motore. Sotto quella soglia, il canale toglierà del tutto l'alimentazione (0% fisico), spegnendo la ventola in modo netto ed evitando fastidiosi rumori elettrici o danni al motore dovuti allo stallo prolungato.</p>
        <p><b>Start Boost (Avvio Rapido)</b><br>
        L'inerzia è il nemico dei motori da fermi. Una ventola che gira perfettamente al 30% potrebbe non avere la forza magnetica sufficiente per <i>iniziare</i> a girare partendo da zero a quella stessa percentuale. Attivando lo <i>Start Boost</i>, ogni volta che il canale si accende (passando dallo 0% a un valore superiore), la scheda invierà una scarica al 100% della potenza per una frazione di secondo (la durata è configurabile, si consiglia 1 o 2 secondi al massimo) per "dare una spinta" al rotore, per poi farlo stabilizzare istantaneamente alla velocità richiesta dalla curva termica.</p>
    """,
"en": """
        <h2 style="color: #cdd6f4;">User Guide</h2>
        <br>
        <h3 style="color: #00e5ff;">Advanced PID Mode (Proportional, Integral, Derivative)</h3>
        <p>Unlike the automatic mode, the PID mode uses a smart algorithm that dynamically adapts the power to maintain the chosen reference sensor at the set temperature (<b>Target</b>), based on the system load in real-time.</p>
        <p>The software offers three preset profiles (<b>Slow, Normal, Fast</b>). For expert users, the <b>Manual</b> mode allows fine-tuning the three mathematical parameters to adapt the algorithm to the specific characteristics of their loop:</p>

        <ul style="margin-top: 5px; margin-bottom: 15px;">
            <li style="margin-bottom: 8px;"><b style="color: #cba6f7;">Proportional (P):</b> Adjusts the base sensitivity to temperature variations. It acts in response to the instantaneous difference between the detected temperature and the <b>Target</b>. A value too high makes the controller excessively reactive, triggering continuous oscillations in the fan rotation speeds. Increase it in steps of <b>0.5</b>.</li>
            <li style="margin-bottom: 8px;"><b style="color: #cba6f7;">Integral (I):</b> Manages cumulative compensation over the long term. It analyzes the time spent away from the <b>Target</b> and accumulates the necessary correction to make the fans converge to the required rotation speed (e.g., a steady 60%) to stably maintain the sensor temperature. Due to water's high thermal inertia, this value must be kept very low. Modify it in small steps of <b>0.01</b>.</li>
            <li style="margin-bottom: 8px;"><b style="color: #cba6f7;">Derivative (D):</b> Applies dynamic dampening based on the rate at which the temperature changes. <b>In liquid cooling systems, it is recommended to keep this close to 0.</b> Since water heats up gradually, an excessively high value would lead to sudden and unjustified rotation spikes in response to minimal sensor reading fluctuations.</li>
        </ul>

        <div style="background-color: #1e1e2e; padding: 10px; border-left: 4px solid #00e5ff; margin-bottom: 15px;">
            <p style="margin-top: 0;"><b>💡 Reference Values (Software presets)</b><br>
            If you want to create a manual curve, use these values as a starting point for guidance:</p>
            <ul style="margin-bottom: 0;">
                <li><b>Slow:</b> P = 3.0 | I = 0.05 | D = 0.1</li>
                <li><b>Normal:</b> P = 5.0 | I = 0.08 | D = 0.3</li>
                <li><b>Fast:</b> P = 8.0 | I = 0.10 | D = 0.5</li>
            </ul>
        </div>
        <hr style="border: 1px solid #313244; margin: 15px 0;">

        <h3 style="color: #00e5ff;">Virtual Sensor (ΔT)</h3>
        <p>By activating the <b>Virtual Sensor (ΔT)</b>, AquaControl constantly calculates the difference between the set main sensor and a second reference sensor: <br><code style="background-color: #1e1e2e; padding: 2px 5px;">[Main] - [Reference] = ΔT</code></p>
        <p><b>Typical use scenario:</b></p>
        <p>In a conventional liquid cooling system, component temperatures can never drop below the ambient temperature. A curve set to keep the liquid at around 35°C will work in winter, but in summer (with Tamb > 35°C) it will force the fan rotors to 100% to reach a physically impossible temperature.</p>
        <p>By subtracting the <i>Air Temperature</i> (reference) from the <i>Liquid Temperature</i> (main), you can set a PID <b>Target</b> of <b>10°C (ΔT)</b>. This way, the system will maintain the water at 30°C in winter (20°C ambient + 10) and 40°C in summer (30°C ambient + 10). Acoustic effort and performance will remain constant in every season, without the need to reprogram the software.</p>
        <hr style="border: 1px solid #313244; margin: 15px 0;">

        <h3 style="color: #00e5ff;">Auto Profile Switch (Auto-Switch)</h3>
        <p>This feature allows AquaControl to autonomously load a specific profile when you launch certain programs, and then restore the profile upon closing.</p>
        <p><b>How to associate programs to the specific profile:</b><br>
        Being a native Linux software, there is no need to find or enter the absolute path of the executable. Simply type the <b>process name</b> exactly as it would be read by the system terminal.</p>
        <p>For example, just typing <code>steam</code>, <code>firefox</code>, <code>blender</code>, etc., ensures that AquaControl immediately detects the opening of the program, regardless of its installation directory.</p>
        <hr style="border: 1px solid #313244; margin: 15px 0;">

        <h3 style="color: #00e5ff;">Minimum Power and Start Boost</h3>
        <p><b>Minimum Power (Stall Prevention)</b><br>
        Fan and pump motors have a physical limit below which they cannot spin. If you send a 10% signal, the fan might stop completely while still receiving power. The <i>Minimum Power</i> sets an impassable safety threshold: if you decide this limit is 25%, the software will recalculate the entire thermal curve so that the logical 0% on the graph physically corresponds to the real 25% sent to the motor. Below that threshold, the channel will completely cut the power (physical 0%), cleanly turning off the fan and preventing annoying electrical noises or motor damage due to prolonged stalling.</p>
        <p><b>Start Boost (Quick Start)</b><br>
        Inertia is the enemy of stationary motors. A fan that spins perfectly at 30% might not have enough magnetic force to <i>start</i> spinning from zero at that same percentage. By activating the <i>Start Boost</i>, every time the channel turns on (going from 0% to a higher value), the controller will send a 100% power burst for a fraction of a second (duration is configurable, 1 or 2 seconds max is recommended) to "kickstart" the rotor, and then instantly stabilize it at the speed required by the thermal curve.</p>
    """,
    "fr": """
        <h2 style="color: #cdd6f4;">Manuel de l'Utilisateur</h2>
        <br>
        <h3 style="color: #00e5ff;">Mode PID Avancé (Proportionnel, Intégral, Dérivé)</h3>
        <p>Contrairement au mode automatique, le mode PID utilise un algorithme intelligent qui adapte dynamiquement la puissance pour maintenir le capteur de référence choisi à la température définie (<b>Cible</b>), en fonction de la charge du système en temps réel.</p>
        <p>Le logiciel propose trois profils préréglés (<b>Lent, Normal, Rapide</b>). Pour les utilisateurs experts, le mode <b>Manuel</b> permet de calibrer finement les trois paramètres mathématiques afin d'adapter l'algorithme aux caractéristiques spécifiques de votre installation :</p>

        <ul style="margin-top: 5px; margin-bottom: 15px;">
            <li style="margin-bottom: 8px;"><b style="color: #cba6f7;">Proportionnel (P) :</b> Règle la sensibilité de base aux variations de température. Il agit en réponse à la différence instantanée entre la température détectée et la <b>Cible</b>. Une valeur trop élevée rend le contrôleur excessivement réactif, déclenchant des oscillations continues du régime de rotation des ventilateurs. Augmentez-le par pas de <b>0.5</b>.</li>
            <li style="margin-bottom: 8px;"><b style="color: #cba6f7;">Intégral (I) :</b> Gère la compensation cumulative sur le long terme. Il analyse le temps passé loin de la <b>Cible</b> et accumule la correction nécessaire pour faire converger les ventilateurs vers le régime de rotation requis (ex. 60% fixe) afin de maintenir la température du capteur de manière stable. En raison de la forte inertie thermique de l'eau, cette valeur doit être maintenue très basse. Modifiez-la par petits pas de <b>0.01</b>.</li>
            <li style="margin-bottom: 8px;"><b style="color: #cba6f7;">Dérivé (D) :</b> Applique un amortissement dynamique basé sur la vitesse à laquelle la température change. <b>Dans les systèmes de refroidissement liquide, il est recommandé de le maintenir proche de 0.</b> L'eau se réchauffant progressivement, une valeur excessivement élevée entraînerait des pics de rotation soudains et injustifiés en réponse aux moindres fluctuations de lecture du capteur.</li>
        </ul>

        <div style="background-color: #1e1e2e; padding: 10px; border-left: 4px solid #00e5ff; margin-bottom: 15px;">
            <p style="margin-top: 0;"><b>💡 Valeurs de Référence (Préréglages du logiciel)</b><br>
            Si vous souhaitez créer une courbe manuelle, utilisez ces valeurs comme point de départ pour vous orienter :</p>
            <ul style="margin-bottom: 0;">
                <li><b>Lent :</b> P = 3.0 | I = 0.05 | D = 0.1</li>
                <li><b>Normal :</b> P = 5.0 | I = 0.08 | D = 0.3</li>
                <li><b>Rapide :</b> P = 8.0 | I = 0.10 | D = 0.5</li>
            </ul>
        </div>
        <hr style="border: 1px solid #313244; margin: 15px 0;">

        <h3 style="color: #00e5ff;">Capteur Virtuel (ΔT)</h3>
        <p>En activant le <b>Capteur Virtuel (ΔT)</b>, AquaControl calcule constamment la différence entre le capteur principal défini et un deuxième capteur de référence : <br><code style="background-color: #1e1e2e; padding: 2px 5px;">[Principal] - [Référence] = ΔT</code></p>
        <p><b>Scénario d'utilisation typique :</b></p>
        <p>Dans un système de refroidissement liquide conventionnel, la température des composants ne peut jamais descendre en dessous de la température ambiante. Une courbe réglée pour maintenir le liquide à environ 35°C fonctionnera en hiver, mais en été (avec Tamb > 35°C), elle forcera les rotors des ventilateurs à 100% pour atteindre une température physiquement impossible.</p>
        <p>En soustrayant la <i>Température de l'Air</i> (référence) de la <i>Température du Liquide</i> (principal), il est possible de définir une <b>Cible</b> PID de <b>10°C (ΔT)</b>. De cette façon, le système maintiendra l'eau à 30°C en hiver (20°C ambiant + 10) et à 40°C en été (30°C ambiant + 10). L'effort acoustique et les performances resteront constants à chaque saison, sans qu'il soit nécessaire de reprogrammer le logiciel.</p>
        <hr style="border: 1px solid #313244; margin: 15px 0;">

        <h3 style="color: #00e5ff;">Changement de Profil Automatique (Auto-Switch)</h3>
        <p>Cette fonction permet à AquaControl de charger de manière autonome un profil spécifique lorsque vous lancez certains programmes, puis de restaurer le profil à la fermeture.</p>
        <p><b>Comment associer les programmes au profil spécifique :</b><br>
        Étant un logiciel natif Linux, il n'est pas nécessaire de chercher ou d'entrer le chemin absolu de l'exécutable. Il suffit de taper le <b>nom du processus</b> tel qu'il serait lu par le terminal du système.</p>
        <p>Par exemple, il suffira d'écrire <code>steam</code>, <code>firefox</code>, <code>blender</code>, etc. pour s'assurer qu'AquaControl détecte immédiatement l'ouverture du programme, quel que soit son répertoire d'installation.</p>
        <hr style="border: 1px solid #313244; margin: 15px 0;">

        <h3 style="color: #00e5ff;">Puissance Minimale et Start Boost</h3>
        <p><b>Puissance Minimale (Prévention du Calage)</b><br>
        Les moteurs de ventilateurs et de pompes ont une limite physique en dessous de laquelle ils ne peuvent pas tourner. Si vous envoyez un signal de 10 %, le ventilateur peut s'arrêter complètement tout en continuant à recevoir du courant. La <i>Puissance Minimale</i> fixe un seuil de sécurité infranchissable : si vous décidez que cette limite est de 25 %, le logiciel recalculera l'ensemble de la courbe thermique de sorte que le 0 % logique du graphique corresponde physiquement au 25 % réel envoyé au moteur. En dessous de ce seuil, le canal coupera complètement l'alimentation (0 % physique), éteignant proprement le ventilateur et évitant des bruits électriques gênants ou des dommages au moteur dus à un calage prolongé.</p>
        <p><b>Start Boost (Démarrage Rapide)</b><br>
        L'inertie est l'ennemi des moteurs à l'arrêt. Un ventilateur qui tourne parfaitement à 30 % peut ne pas avoir la force magnétique suffisante pour <i>commencer</i> à tourner à partir de zéro à ce même pourcentage. En activant le <i>Start Boost</i>, chaque fois que le canal s'allume (passant de 0 % à une valeur supérieure), la carte enverra une décharge de 100 % de la puissance pendant une fraction de seconde (la durée est configurable, 1 ou 2 secondes maximum sont recommandées) pour "donner une impulsion" au rotor, puis le stabiliser instantanément à la vitesse requise par la courbe thermique.</p>
    """,
    "de": """
        <h2 style="color: #cdd6f4;">Benutzerhandbuch</h2>
        <br>
        <h3 style="color: #00e5ff;">Erweiterter PID-Modus (Proportional, Integral, Derivativ)</h3>
        <p>Im Gegensatz zum automatischen Modus nutzt der PID-Modus einen intelligenten Algorithmus, der die Leistung dynamisch anpasst, um den gewählten Referenzsensor auf der eingestellten Temperatur (<b>Ziel</b>), basierend auf der Systemlast in Echtzeit.</p>
        <p>Die Software bietet drei voreingestellte Profile (<b>Langsam, Normal, Schnell</b>). Für erfahrene Benutzer ermöglicht der <b>Manuelle</b> Modus die Feinabstimmung der drei mathematischen Parameter, um den Algorithmus an die spezifischen Eigenschaften des eigenen Systems anzupassen:</p>

        <ul style="margin-top: 5px; margin-bottom: 15px;">
            <li style="margin-bottom: 8px;"><b style="color: #cba6f7;">Proportional (P):</b> Regelt die Grundempfindlichkeit gegenüber Temperaturschwankungen. Er reagiert auf die momentane Differenz zwischen der erfassten Temperatur und dem <b>Ziel</b>. Ein zu hoher Wert macht den Controller übermäßig reaktiv, was zu ständigen Schwingungen der Lüfterdrehzahlen führt. Erhöhen Sie ihn in Schritten von <b>0.5</b>.</li>
            <li style="margin-bottom: 8px;"><b style="color: #cba6f7;">Integral (I):</b> Verwaltet die kumulative Kompensation auf lange Sicht. Er analysiert die Zeit, die abseits des <b>Ziels</b> verbracht wird, und akkumuliert die notwendige Korrektur, um die Lüfter auf die erforderliche Drehzahl (z. B. konstant 60 %) zu bringen, um die Sensortemperatur stabil zu halten. Aufgrund der hohen thermischen Trägheit von Wasser muss dieser Wert sehr niedrig gehalten werden. Ändern Sie ihn in kleinen Schritten von <b>0.01</b>.</li>
            <li style="margin-bottom: 8px;"><b style="color: #cba6f7;">Derivativ (D):</b> Wendet eine dynamische Dämpfung basierend auf der Geschwindigkeit der Temperaturänderung an. <b>Bei Wasserkühlungssystemen wird empfohlen, diesen Wert nahe 0 zu halten.</b> Da sich Wasser allmählich erwärmt, würde ein übermäßig hoher Wert zu plötzlichen und ungerechtfertigten Drehzahlsprüngen als Reaktion auf minimale Sensorschwankungen führen.</li>
        </ul>

        <div style="background-color: #1e1e2e; padding: 10px; border-left: 4px solid #00e5ff; margin-bottom: 15px;">
            <p style="margin-top: 0;"><b>💡 Richtwerte (Software-Voreinstellungen)</b><br>
            Wenn Sie eine manuelle Kurve erstellen möchten, verwenden Sie diese Werte als Ausgangspunkt zur Orientierung:</p>
            <ul style="margin-bottom: 0;">
                <li><b>Langsam:</b> P = 3.0 | I = 0.05 | D = 0.1</li>
                <li><b>Normal:</b> P = 5.0 | I = 0.08 | D = 0.3</li>
                <li><b>Schnell:</b> P = 8.0 | I = 0.10 | D = 0.5</li>
            </ul>
        </div>
        <hr style="border: 1px solid #313244; margin: 15px 0;">

        <h3 style="color: #00e5ff;">Virtueller Sensor (ΔT)</h3>
        <p>Durch Aktivierung des <b>Virtuellen Sensors (ΔT)</b> berechnet AquaControl ständig die Differenz zwischen dem eingestellten Hauptsensor und einem zweiten Referenzsensor: <br><code style="background-color: #1e1e2e; padding: 2px 5px;">[Haupt] - [Referenz] = ΔT</code></p>
        <p><b>Typisches Anwendungsszenario:</b></p>
        <p>In einem herkömmlichen Wasserkühlungssystem kann die Temperatur der Komponenten niemals unter die Umgebungstemperatur fallen. Eine Kurve, die darauf eingestellt ist, die Flüssigkeit auf etwa 35°C zu halten, funktioniert im Winter, zwingt die Lüfterrotoren im Sommer (bei Tamb > 35°C) jedoch auf 100 %, um eine physiquement unmögliche Temperatur zu erreichen.</p>
        <p>Indem Sie die <i>Lufttemperatur</i> (Referenz) von der <i>Flüssigkeitstemperatur</i> (Haupt) abziehen, können Sie ein PID-<b>Ziel</b> von <b>10°C (ΔT)</b>. Auf diese Weise hält das System das Wasser im Winter auf 30°C (20°C Umgebung + 10) und im Sommer auf 40°C (30°C Umgebung + 10). Die akustische Belastung und die Leistung bleiben in jeder Jahreszeit konstant, ohne dass die Software neu programmiert werden muss.</p>
        <hr style="border: 1px solid #313244; margin: 15px 0;">

        <h3 style="color: #00e5ff;">Automatischer Profilwechsel (Auto-Switch)</h3>
        <p>Diese Funktion ermöglicht es AquaControl, beim Start bestimmter Programme automatisch ein bestimmtes Profil zu laden und das Profil beim Schließen wiederherzustellen.</p>
        <p><b>So ordnen Sie Programme dem spezifischen Profil zu:</b><br>
        Da es sich um eine native Linux-Software handelt, müssen Sie nicht nach dem absoluten Pfad der ausführbaren Datei suchen. Geben Sie einfach den <b>Prozessnamen</b> genauso ein, wie er vom Systemterminal gelesen würde.</p>
        <p>Wenn Sie beispielsweise <code>steam</code>, <code>firefox</code>, <code>blender</code> usw. eingeben, erkennt AquaControl das Öffnen des Programms sofort, unabhängig von seinem Installationsverzeichnis.</p>
        <hr style="border: 1px solid #313244; margin: 15px 0;">

        <h3 style="color: #00e5ff;">Minimale Leistung und Start Boost</h3>
        <p><b>Minimale Leistung (Verhinderung von Stillstand)</b><br>
        Lüfter- und Pumpenmotoren haben eine physikalische Grenze, unterhalb derer sie sich nicht drehen können. Wenn Sie ein 10%-Signal senden, stoppt der Lüfter möglicherweise vollständig, obwohl er weiterhin Strom erhält. Die <i>Minimale Leistung</i> legt eine unüberwindbare Sicherheitsschwelle fest: Wenn Sie dieses Limit auf 25% festlegen, berechnet die Software die gesamte thermische Kurve neu, sodass die logischen 0% im Diagramm physisch den echten 25% entsprechen, die an den Motor gesendet werden. Unterhalb dieser Schwelle schaltet der Kanal die Stromversorgung vollständig ab (physische 0%), schaltet den Lüfter sauber aus und verhindert störende elektrische Geräusche oder Motorschäden durch längeren Stillstand.</p>
        <p><b>Start Boost (Schnellstart)</b><br>
        Trägheit ist der Feind von stillstehenden Motoren. Ein Lüfter, der bei 30% perfekt läuft, hat möglicherweise nicht genug Magnetkraft, um bei demselben Prozentsatz aus dem Stillstand zu <i>starten</i>. Durch Aktivierung des <i>Start Boost</i> sendet die Karte jedes Mal, wenn sich der Kanal einschaltet (von 0% auf einen höheren Wert), für den Bruchteil einer Sekunde (die Dauer ist konfigurierbar, empfohlen werden maximal 1 oder 2 Sekunden) einen Leistungsschub von 100%, um dem Rotor "einen Schubs" zu geben, und stabilisiert ihn dann sofort auf die von der thermischen Kurve geforderte Geschwindigkeit.</p>
    """,
    "es": """
        <h2 style="color: #cdd6f4;">Manual de Usuario</h2>
        <br>
        <h3 style="color: #00e5ff;">Modo PID Avanzado (Proporcional, Integral, Derivativo)</h3>
        <p>A diferencia del modo automático, el modo PID utiliza un algoritmo inteligente que adapta dinámicamente la potencia para mantener el sensor de referencia elegido a la temperatura establecida (<b>Objetivo</b>), en función de la carga del sistema en tiempo real.</p>
        <p>El software ofrece tres perfiles preestablecidos (<b>Lento, Normal, Rápido</b>). Para los usuarios expertos, el modo <b>Manual</b> permite calibrar finamente los tres parámetros matemáticos para adaptar el algoritmo a las características específicas de su instalación:</p>

        <ul style="margin-top: 5px; margin-bottom: 15px;">
            <li style="margin-bottom: 8px;"><b style="color: #cba6f7;">Proporcional (P):</b> Regula la sensibilidad base a las variaciones de temperatura. Actúa en respuesta a la diferencia instantánea entre la temperatura detectada y el <b>Objetivo</b>. Un valor demasiado alto hace que el controlador sea excesivamente reactivo, desencadenando oscilaciones continuas en el régimen de rotación de los ventiladores. Auméntalo en pasos de <b>0.5</b>.</li>
            <li style="margin-bottom: 8px;"><b style="color: #cba6f7;">Integral (I):</b> Gestiona la compensación acumulativa a largo plazo. Analiza el tiempo transcurrido lejos del <b>Objetivo</b> y acumula la corrección necesaria para hacer converger los ventiladores al régimen de rotación necesario (ej. 60% fijo) para mantener de forma estable la temperatura del sensor. Debido a la alta inercia térmica del agua, este valor debe mantenerse muy bajo. Modifícalo en pequeños pasos de <b>0.01</b>.</li>
            <li style="margin-bottom: 8px;"><b style="color: #cba6f7;">Derivativo (D):</b> Aplica una amortiguación dinámica en función de la velocidad a la que cambia la temperatura. <b>En los sistemas de refrigeración líquida se recomienda mantenerlo cerca de 0.</b> Dado que el agua se calienta gradualmente, un valor excesivamente alto provocaría picos de rotación repentinos e injustificados en respuesta a mínimas fluctuaciones de lectura del sensor.</li>
        </ul>

        <div style="background-color: #1e1e2e; padding: 10px; border-left: 4px solid #00e5ff; margin-bottom: 15px;">
            <p style="margin-top: 0;"><b>💡 Valores de Referencia (Ajustes preestablecidos del software)</b><br>
            Si deseas crear una curva manual, utiliza estos valores como punto de partida para orientarte:</p>
            <ul style="margin-bottom: 0;">
                <li><b>Lento:</b> P = 3.0 | I = 0.05 | D = 0.1</li>
                <li><b>Normal:</b> P = 5.0 | I = 0.08 | D = 0.3</li>
                <li><b>Rápido:</b> P = 8.0 | I = 0.10 | D = 0.5</li>
            </ul>
        </div>
        <hr style="border: 1px solid #313244; margin: 15px 0;">

        <h3 style="color: #00e5ff;">Sensor Virtual (ΔT)</h3>
        <p>Al activar el <b>Sensor Virtual (ΔT)</b>, AquaControl calcula constantemente la diferencia entre el sensor principal establecido y un segundo sensor de referencia: <br><code style="background-color: #1e1e2e; padding: 2px 5px;">[Principal] - [Referencia] = ΔT</code></p>
        <p><b>Escenario de uso típico:</b></p>
        <p>En un sistema de refrigeración líquida convencional, la temperatura de los componentes nunca puede descender por debajo de la temperatura ambiente. Una curva configurada para mantener el líquido a unos 35°C funcionará en invierno, pero en verano (con Tamb > 35°C) forzará los rotores de los ventiladores al 100% para alcanzar una temperatura físicamente imposible.</p>
        <p>Restando la <i>Temperatura del Aire</i> (referencia) a la <i>Temperatura del Líquido</i> (principal), es posible establecer un <b>Objetivo</b> PID de <b>10°C (ΔT)</b>. De esta forma, el sistema mantendrá el agua a 30°C en invierno (20°C ambiente + 10) y a 40°C en verano (30°C ambiente + 10). El esfuerzo acústico y el rendimiento se mantendrán constantes en cada estación, sin necesidad de reprogramar el software.</p>
        <hr style="border: 1px solid #313244; margin: 15px 0;">

        <h3 style="color: #00e5ff;">Cambio Automático de Perfil (Auto-Switch)</h3>
        <p>Esta función permite a AquaControl cargar de forma autónoma un perfil específico cuando inicias determinados programas, para luego restaurar el perfil al cerrarlos.</p>
        <p><b>Cómo asociar los programas al perfil específico:</b><br>
        Al ser un software nativo de Linux, no es necesario buscar o introducir la ruta absoluta del ejecutable. Basta con escribir el <b>nombre del proceso</b> tal y como lo leería el terminal del sistema.</p>
        <p>Por ejemplo, bastará con escribir <code>steam</code>, <code>firefox</code>, <code>blender</code>, etc. para garantizar que AquaControl detecte inmediatamente la apertura del programa, independientemente de su directorio de instalación.</p>
        <hr style="border: 1px solid #313244; margin: 15px 0;">

        <h3 style="color: #00e5ff;">Potencia Mínima y Start Boost</h3>
        <p><b>Potencia Mínima (Prevención de Estancamiento)</b><br>
        Los motores de ventiladores y bombas tienen un límite físico por debajo del cual no pueden girar. Si envías una señal del 10%, el ventilador podría detenerse por completo, aunque siga recibiendo corriente. La <i>Potencia Mínima</i> establece un umbral de seguridad infranqueable: si decides que este límite es el 25%, el software recalculará toda la curva térmica para que el 0% lógico del gráfico corresponda físicamente al 25% real enviado al motor. Por debajo de ese umbral, el canal cortará por completo la alimentación (0% físico), apagando el ventilador de forma limpia y evitando molestos ruidos eléctricos o daños al motor debido a un estancamiento prolongado.</p>
        <p><b>Start Boost (Arranque Rápido)</b><br>
        La inercia es el enemigo de los motores parados. Un ventilador que gira perfectamente al 30% podría no tener la fuerza magnética suficiente para <i>empezar</i> a girar partiendo de cero a ese mismo porcentaje. Al activar el <i>Start Boost</i>, cada vez que el canal se encienda (pasando del 0% a un valor superior), la placa enviará una descarga al 100% de la potencia durante una fracción de segundo (la duración es configurable, se recomienda 1 o 2 segundos como máximo) para "dar un empujón" al rotor, y luego estabilizarlo instantáneamente a la velocidad requerida por la curva térmica.</p>
    """
}

def get_guide_text():
    lang = global_config.get("lang", "it")
    return GUIDE_TRANSLATIONS.get(lang, GUIDE_TRANSLATIONS["it"])
