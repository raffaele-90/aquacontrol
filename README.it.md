# 💧 AquaControl 3.1

### Architettura e scopo del progetto

AquaControl è una suite di controllo nativa per Linux, scritta specificamente per l'ecosistema Aquacomputer, programmata per la logica dell'Aquaero 6 LT. Aquacontrol è un programma che mira ad offrire le stesse funzionalità della suite ufficiale per la gestione di impianti a liquido custom, alternativa linux al famoso CoolerControl.
CoolerControl è software eccezionale in grado di gestire innumerevoli periferiche ma, proprio per questo motivo, fallisce nell'obiettivo della specificità offerta da questo software e dai suoi controlli avanzati.

Il software si appoggia al driver ufficiale del kernel Linux (aquacomputer_d5next di Aleksa Savic) per la lettura dei sensori esposti in /sys/class/hwmon. Sopra queste letture, AquaControl introduce il suo motore di calcolo indipendente per la scrittura di valori da 0 a 255 in tempo reale.

### Reverse Engineering del Protocollo USB

Poiché il modulo del kernel non permette la modifica della tipologia di erogazione di corrente sulle quattro uscite 12v della scheda, AquaControl integra un modulo di comunicazione diretta tramite python-hidapi. Attraverso il reverse engineering del protocollo USB, il software bypassa il kernel per iniettare payload mirati (Feature Reports) in tempo reale, permettendo di commutare i canali da 12V da modalità PWM a tensione DC continua (Power Controlled). Il software comunica con la scheda in modalità ovveride in tempo reale, per scelta dell'autore.

## 🚀 Funzionalità di AquaControl 3.1

- **Interfaccia grafica e supporto multilingua**: L'interfaccia grafica è ispirata a quella di altri software che ritengo ben progettati con una ragionata organizzazione delle funzioni, concepita per essere "user friendly". Per rendere il software accessibile a chiunque, è stato tradotto in italiano, inglese, tedesco, spagnolo e francese e integra all'interno del programma stesso un manuale (anch'esso tradotto) per descrivere l'uso delle funzioni avanzate del programma.

- **Controllo Hardware PWM/DC:** Come spiegato sopra, switch a caldo baypassando le limitazioni del kernel.

- **Isteresi**: Calcola un valor medio di temperatura sulla base dei valori misurati in un determinato arco di tempo (personalizzabile) evitando la continua accelerazione/decelerazione delle ventole a causa di minime variazioni di temperatura.

- **Avvio Rapido (Start Boost):** A causa dell'inerzia meccanica delle ventole, è necessaria una maggiore potenza per avviare una ventola, rispetto alla potenza necessaria per mantenerla in rotazione. La funzione "avvio rapido" permette di applicare una potenza iniziale massima del 100% per una frazione di secondo per vincere lo stallo meccanico, per poi applicare un valore di potenza minimo che permetta alle ventole di continuare a girare, in base alla impostazioni scelte dall'utente. 

- **Mantenimento della Temperatura (Algoritmo PID):** Mantenimento di una temperatura target costante su un sensore a scelta dell'utente.
Include 3 comportamenti preimpostati (*Lento, Normale, Veloce*) e una modalità manuale.

- **Sensori Virtuali (Delta T):** Possibilità di creare un sensore virtuale calcolato sulla differenza tra due sensori. Lo scopo primario di questa funzione è di poterla utilizzare con un sensore di rilevamento di temperatura ambientale accoppiato ad un sensore per il rilevamento delle temperatura del liquido. In questo modo si può creare una curva che regola il sistema in base ad un Delta T costante, slegando il controllo dei profili dell'impianto alla temperatura assoluta del liquido, che può variare in base alle stagioni dell'anno.

- **Funzioni di sicurezza e allarmi:** Il software monitora costantemente i valori di RPM, potenza e voltaggio delle quattro uscite 12v di Aquaero, oltre a monitorare i sensori delle temperature. È possibile configurare delle soglie critiche, in cui il programma potrà intervenire in automatico mostrando un allarme (visivo e sonoro) spegnendo forzatamente il pc con permessi di root e/o lanciando un comando personalizzato a scelta dell'utente.

- **Overlay su Schermo (OSD):** Un pannello personalizzabile che è possibile spostare ovunque sul desktop. 

**Nota bene:** Per via delle regole di sicurezza di Wayland, l'OSD non è stato progettato per sovrapporsi alle schermate dei giochi in modalità fullscreen. L'OSD non mira a sostituire o sovrapporsi a strumenti dedicati come Mangohud, ma nasce come strumento di monitoring del sistema, pensato per mostrare i sensori di sistema e di aquaero, durante le normali sessioni di lavoro sul desktop, durante l'uso di benchmark o stress test in finestra. Non ho integrato e non intendo integrare funzioni che fuoriescano dallo scopo del progetto.

- **Cambio Profilo Automatico:** AquaControl permette di creare profili personalizzati e di associarli a specifici programmi (come li si avvierebbe tramite terminale); è possibile quindi associare un profilo più aggressivo all'apertura di un videogame o di un software di rendering, con ripristino automatico del profilo precedente alla chiusura del programma.


## ⚠️ AVVISO IMPORTANTE: SI SCONSIGLIA DI AGGIORNARE IL FIRMWARE

Il corretto funzionamento del software è stato verificato e testato su schede **Aquaero 6LT dotate di Firmware 2104**. Non viene garantita la compatibilità dello switch PWM/DC su altre versioni.

Spesso i produttori hardware, che non rendono disponibili i loro software su Linux, rilasciano "fix di sicurezza" al solo scopo di cambiare i protocolli di comunicazione usb e rompere la compatibilità di software opensource come questo.

## 🔮 Sviluppi Futuri

Il software è sufficientemente maturo per il controllo delle quattro uscite 12v di Aquaero 6 LT. Nelle prossime versioni pianifico di integrare:

* **Sensori di Flusso:** Supporto alla lettura dei dati relativi ai sensori di flusso, che verranno convertiti nel software in valori di portata del liquido (litri/ora) con parametri di conversione impostabili dall'utente, in base al sensore scelto. Ovviamente aggiungerò anche una voce per gestire il sistema di emergenza del programma in base alla lettura del sensore di flusso.

* **Supporto D5 Next**

* **Possibile per altro hardware Aquacomputer (Beta):** 
 Il driver aquacomputer_d5next riconosce correttamente: Aquaero 5, Aquaero 6, Octo, Quadro, Poweradjust 3, D5 Next, Aquastream XT, Aquastream Ultimate, High Flow Next, High Flow USB, MPS Flow, Leakshield, Farbwerk e Farbwerk 360. Purtroppo non possiedo nessuna di queste periferiche, ma è possibile espandere la compatibilità del software mettendo le funzionalità come "Beta" e cercando Beta tester della community che possiedono fisicamente questi dispositivi e possono provare il programma.


## 🛠 Installazione (Arch Linux)

1. Clona questo repository sul tuo computer.
2. Apri il terminale nella cartella dei sorgenti ed esegui il comando:
   
   `makepkg -si`
   
Il sistema compilerà il pacchetto, configurerà i permessi hardware della porta USB (udev) e installerà l'applicazione risolvendo automaticamente le dipendenze necessarie (come python-hidapi).

3. Se utilizzi una scheda video NVIDIA e desideri visualizzarne i dati di carico e temperatura, installa il pacchetto aggiuntivo da AUR/pacman: 

   `sudo pacman -S python-pynvml`
   
📜 Licenza
Rilasciato sotto licenza internazionale libera GNU GPLv3. Questo è un progetto indipendente è sviluppato da un utente dalla community Linux e non è in alcun modo affiliato, supportato o approvato da Aquacomputer.

## 👤 Autore / Maintainer

Sviluppato e mantenuto da **Raffaele Schiavone** ([@raffaele-90](https://github.com/raffaele-90)).

*Scrivo software libero perché credo nel diritto di poter usare l'hardware che acquisto sul sistema operativo che preferisco, senza dover installare Microsoft Windows.*
