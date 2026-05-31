# 💧 OpenAquaero 3.0

OpenAquaero è un software open-source, nativo e leggero per Linux, progettato specificamente per la gestione della scheda **Aquacomputer Aquaero 6 LT**. Offre un'interfaccia moderna e focalizzata per il controllo degli impianti a liquido custom direttamente dal tuo desktop Linux, senza dover dipendere da macchine virtuali o software proprietario.

Il programma opera in modalità **override in tempo reale**: comunica costantemente con la scheda via USB per regolarne il comportamento istante per istante, senza andare a scrivere o usurare la memoria ROM interna del dispositivo. Questo garantisce un controllo flessibile, sicuro e perfettamente integrato con il sistema operativo.

## 🚀 Funzionalità di OpenAquaero 3.0

OpenAquaero introduce una gestione avanzata e intuitiva dell'impianto, pensata per tutti gli utenti, offrendo anche una guida alle funzioni avanzate direttamente integrata all'interno del software.

- **Controllo Hardware Diretto (PWM/DC):** Il software dialoga direttamente con l'hardware tramite la porta USB. Permette di cambiare in tempo reale il tipo di segnale inviato a ogni singolo canale (PWM o DC). Questa funzione è fondamentale per gestire correttamente pompe o vecchie ventole a 3 pin sprovviste di controllo PWM, regolandone direttamente la tensione erogata.
- **Mantenimento della Temperatura (Algoritmo PID):** Invece di configurare curve rigide basate sui punti del grafico, potresti definire una temperatura obiettivo per il tuo liquido (ad esempio 40°C). Il software utilizzerà un sistema di calcolo intelligente che adatta costantemente la velocità di ventole e pompe in base al carico istantaneo del PC, impedendo al liquido di superare la soglia stabilita. Include 3 comportamenti preimpostati (*Lento, Normale, Veloce*) e una modalità manuale.
- **Sensori Virtuali (Delta T):** Questa funzione permette di creare un sensore intelligente basato sulla differenza di temperatura tra due punti dell'impianto. L'utilizzo ideale consiste nel sottrarre la temperatura di un sensore che rileva la temperatura ambientale a quella del liquido refrigerante. In questo modo si ottiene un valore di dissipazione costante in ogni stagione dell'anno: l'impianto eviterà di far girare le ventole al 100% in estate per inseguire temperature fisicamente impossibili, garantendo la stessa silenziosità acustica sia a gennaio che ad agosto.
- **Limiti Fisici e Spunto di Avvio (Start Boost):** Molte pompe e ventole non riescono a girare se ricevono una percentuale di alimentazione troppo bassa, rischiando lo stallo meccanico. Con questa funzione puoi impostare una potenza minima sotto la quale il canale si spegne completamente. Inoltre, attivando l'*Avvio rapido (Start boost)*, il software darà una spinta iniziale al 100% per una frazione di secondo ogni volta che una ventola ferma deve mettersi in moto, vincendo l'inerzia iniziale delle pale.
- **Overlay su Schermo (OSD) e Filosofia Anti-Bloatware:** Un pannello informativo fluttuante, trasparente e personalizzabile che mostra lo stato di ventole e temperature sul desktop in tempo reale. **Nota bene:** per via delle rigide regole di sicurezza dei moderni server grafici (come Wayland), l'OSD non è progettato per sovrapporsi alle schermate dei giochi in modalità fullscreen. Questo software non nasce per sostituire strumenti specifici da gioco come *MangoHud* (che rimane la scelta ideale per monitorare fps e sensori in-game), ma per tenere sotto controllo l'impianto durante sessioni di stress-test, benchmarking o durante il normale lavoro quotidiano sul desktop. OpenAquaero sposa la filosofia open-source del "fa' una sola cosa e falla bene", quindi non integra funzioni note di altri programmi che esulano dallo scopo del progetto.
- **Cambio Profilo Automatico:** OpenAquaero rileva i programmi in esecuzione sul computer. È possibile associare profili ad applicazioni specifiche, facendo in modo che il sistema possa eventualmente caricare il profilo più aggressivo all'avvio di un determinato gioco o software di rendering, per poi ripristinare il profilo precedente in automatico non appena il programma viene chiuso.

## ⚠️ AVVISO CRITICO: NON AGGIORNARE IL FIRMWARE

Il corretto funzionamento del software è stato verificato e testato su schede **Aquaero 6LT dotate di Firmware 2104**. Non viene garantita la compatibilità delle funzioni avanzate di comunicazione USB con versioni di firmware differenti.

**SI SCONSIGLIA ASSOLUTAMENTE DI AGGIORNARE IL FIRMWARE DELLA SCHEDA.**

Spesso i produttori di hardware rilasciano strumenti di gestione scritti esclusivamente per Microsoft Windows, ignorando l'esistenza di piattaforme libere e costringendo gli utenti a subire sistemi operativi commerciali che tracciano e monetizzano i dati personali. Quando programmatori indipendenti dedicano mesi di lavoro gratuito al reverse engineering per restituire agli utenti il diritto di utilizzare l'hardware acquistato su sistemi liberi come Linux, le aziende rispondono rilasciando finti "aggiornamenti di sicurezza".

Questi aggiornamenti hanno spesso il solo scopo di modificare arbitrariamente i codici interni e i protocolli di comunicazione della scheda, rompendo intenzionalmente la compatibilità con i software alternativi della community. Se hai speso oltre 150 euro per un controller hardware premium, hai il sacrosanto diritto di usarlo sul sistema operativo che preferisci. Per evitare che la tua scheda si trasformi in un costoso fermacarte su Linux, ti invitiamo a non applicare gli aggiornamenti firmware ufficiali. Se il produttore desidera contrastare questi progetti, è libero di rilasciare una versione ufficiale e nativa della propria suite per Linux; fino ad allora, la community continuerà a difendere la libertà dell'hardware.

## 🔮 Sviluppi Futuri

Il software è pienamente maturo per il controllo quotidiano dei sistemi di raffreddamento più complessi. Nelle prossime versioni pianifichiamo di integrare:
* **Sensori di Flusso:** Supporto alla lettura dei dati di portata del liquido (litri/ora) per monitorare lo stato di salute della pompa e l'efficienza dei waterblock.
* **Supporto Farbwerk 360:** Studio per la creazione di un modulo software integrato o di una dipendenza esterna leggera in grado di interfacciarsi con i controller RGB dedicati, estendendo il controllo dell'illuminazione del PC direttamente da Linux in armonia con l'ecosistema open-source (come OpenRGB).

## 🛠 Installazione (Arch Linux)

1. Clona questo repository sul tuo computer.
2. Apri il terminale nella cartella del progetto ed esegui il comando:
   
   `makepkg -si`
   
Il sistema compilerà il pacchetto, configurerà i permessi hardware della porta USB (udev) e installerà l'applicazione risolvendo automaticamente le dipendenze necessarie (come python-hidapi).

3. Se utilizzi una scheda video NVIDIA e desideri visualizzarne i dati di carico e temperatura, installa il pacchetto aggiuntivo da AUR/pacman: 

   `sudo pacman -S python-pynvml`
   
📜 Licenza
Rilasciato sotto licenza internazionale libera GNU GPLv3. Questo è un progetto indipendente sviluppato dalla community degli utenti Linux e non è in alcun modo affiliato, supportato o approvato da Aquacomputer.
