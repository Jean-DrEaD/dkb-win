using System.Text.RegularExpressions;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;

namespace DkbBuilder;

/// Traduz os textos fixos da janela (en, pt, es, it, ru, fr) conforme o idioma escolhido.
static class UiText
{
    static readonly string[][] Rows =
    {
        new[]{"Build your game","Crie seu jogo","Crea tu juego","Crea il tuo gioco","Соберите игру","Créez votre jeu"},
        new[]{"Pick your game files and where the game goes. DKB does the rest, once.","Escolha os arquivos do jogo e onde ele vai ficar. O DKB faz o resto, uma vez só.","Elige los archivos del juego y dónde irá. DKB hace el resto, una sola vez.","Scegli i file di gioco e dove installarlo. DKB fa il resto, una volta sola.","Выберите файлы игры и папку для неё. Остальное DKB сделает сам, один раз.","Choisissez les fichiers du jeu et son emplacement. DKB fait le reste, une seule fois."},
        new[]{"FOUND ON THIS PC","ENCONTRADOS NESTE PC","ENCONTRADOS EN ESTE PC","TROVATI SU QUESTO PC","НАЙДЕНО НА ЭТОМ ПК","TROUVÉS SUR CE PC"},
        new[]{"Not listed?","Não está na lista?","¿No aparece?","Non è in elenco?","Нет в списке?","Absent de la liste ?"},
        new[]{"Browse…","Procurar…","Examinar…","Sfoglia…","Обзор…","Parcourir…"},
        new[]{" · or drop the file on this window · "," · ou solte o arquivo nesta janela · "," · o suelta el archivo en esta ventana · "," · o trascina il file su questa finestra · "," · или перетащите файл в это окно · "," · ou déposez le fichier sur cette fenêtre · "},
        new[]{"romfs and exefs folders","pastas romfs e exefs","carpetas romfs y exefs","cartelle romfs ed exefs","папки romfs и exefs","dossiers romfs et exefs"},
        new[]{"INSTALL THE GAME TO","INSTALAR O JOGO EM","INSTALAR EL JUEGO EN","INSTALLA IL GIOCO IN","УСТАНОВИТЬ ИГРУ В","INSTALLER LE JEU DANS"},
        new[]{"Change","Alterar","Cambiar","Cambia","Изменить","Modifier"},
        new[]{"GAME LANGUAGE","IDIOMA DO JOGO","IDIOMA DEL JUEGO","LINGUA DEL GIOCO","ЯЗЫК ИГРЫ","LANGUE DU JEU"},
        new[]{"BUILD WORKERS","PROCESSOS DA BUILD","PROCESOS DE COMPILACIÓN","PROCESSI DI COMPILAZIONE","ПОТОКИ СБОРКИ","PROCESSUS DE COMPILATION"},
        new[]{"Automatic uses available memory and any existing worker override. More workers need more memory and may not be faster.","Automático usa a memória disponível e qualquer ajuste já definido. Mais processos exigem mais memória e podem não ser mais rápidos.","Automático usa la memoria disponible y cualquier ajuste existente. Más procesos necesitan más memoria y quizá no sean más rápidos.","Automatico usa la memoria disponibile e qualsiasi impostazione esistente. Più processi richiedono più memoria e potrebbero non essere più veloci.","Автоматически: по доступной памяти и уже заданной настройке. Больше потоков требуют больше памяти и не всегда быстрее.","Automatique utilise la mémoire disponible et tout réglage existant. Plus de processus demandent plus de mémoire et ne sont pas forcément plus rapides."},
        new[]{"About 45 min","Cerca de 45 min","Unos 45 min","Circa 45 min","Около 45 мин","Environ 45 min"},
        new[]{"Build the game","Criar o jogo","Crear el juego","Crea il gioco","Собрать игру","Créer le jeu"},
        new[]{"Building your game","Criando seu jogo","Creando tu juego","Creazione del gioco","Сборка игры","Création de votre jeu"},
        new[]{"Show details","Mostrar detalhes","Mostrar detalles","Mostra dettagli","Показать подробности","Afficher les détails"},
        new[]{"Hide details","Ocultar detalhes","Ocultar detalles","Nascondi dettagli","Скрыть подробности","Masquer les détails"},
        new[]{"Cancel","Cancelar","Cancelar","Annulla","Отмена","Annuler"},
        new[]{"Your game is ready","Seu jogo está pronto","Tu juego está listo","Il tuo gioco è pronto","Ваша игра готова","Votre jeu est prêt"},
        new[]{"Your game is updated","Seu jogo foi atualizado","Tu juego está actualizado","Il tuo gioco è aggiornato","Игра обновлена","Votre jeu est à jour"},
        new[]{"Play","Jogar","Jugar","Gioca","Играть","Jouer"},
        new[]{"Open folder","Abrir pasta","Abrir carpeta","Apri cartella","Открыть папку","Ouvrir le dossier"},
        new[]{"Desktop shortcut","Atalho na área de trabalho","Acceso directo en el escritorio","Collegamento sul desktop","Ярлык на рабочем столе","Raccourci sur le bureau"},
        new[]{"Start menu entry","Item no menu Iniciar","Entrada en el menú Inicio","Voce nel menu Start","Пункт в меню «Пуск»","Entrée du menu Démarrer"},
        new[]{"The build stopped","A criação parou","La creación se detuvo","La creazione si è interrotta","Сборка остановлена","La création s'est arrêtée"},
        new[]{"Nothing was changed in your game folder.","Nada foi alterado na pasta do jogo.","No se cambió nada en la carpeta del juego.","Nella cartella del gioco non è cambiato nulla.","В папке игры ничего не изменилось.","Rien n'a été modifié dans le dossier du jeu."},
        new[]{"Copy for a bug report","Copiar para relatar o erro","Copiar para informar del error","Copia per segnalare il problema","Скопировать для отчёта об ошибке","Copier pour signaler le bug"},
        new[]{"Back","Voltar","Atrás","Indietro","Назад","Retour"},
        new[]{"Repair","Reparar","Reparar","Ripara","Исправить","Réparer"},
        new[]{"Minimize","Minimizar","Minimizar","Riduci a icona","Свернуть","Réduire"},
        new[]{"Close","Fechar","Cerrar","Chiudi","Закрыть","Fermer"},
        new[]{"Starting…","Iniciando…","Iniciando…","Avvio…","Запуск…","Démarrage…"},
        new[]{"Getting the update…","Baixando a atualização…","Descargando la actualización…","Download dell'aggiornamento…","Загрузка обновления…","Téléchargement de la mise à jour…"},
        new[]{"Looking for your game files…","Procurando os arquivos do jogo…","Buscando los archivos del juego…","Ricerca dei file di gioco…","Поиск файлов игры…","Recherche des fichiers du jeu…"},
        new[]{"No game files found yet","Nenhum arquivo do jogo encontrado ainda","Aún no se encontraron archivos del juego","Nessun file di gioco trovato","Файлы игры пока не найдены","Aucun fichier de jeu trouvé"},
        new[]{"Found 1 game file","1 arquivo do jogo encontrado","Se encontró 1 archivo del juego","Trovato 1 file di gioco","Найден 1 файл игры","1 fichier de jeu trouvé"},
        new[]{"Found {0} game files","{0} arquivos do jogo encontrados","Se encontraron {0} archivos del juego","Trovati {0} file di gioco","Найдено файлов игры: {0}","{0} fichiers de jeu trouvés"},
        new[]{"No .nup files in Downloads, Desktop, Documents or the top folders of your drives. Browse to yours, or drop it on this window.","Nenhum arquivo .nup em Downloads, Área de Trabalho, Documentos ou nas pastas principais dos discos. Procure o seu ou solte-o nesta janela.","No hay archivos .nup en Descargas, Escritorio, Documentos ni en las carpetas principales de tus discos. Búscalo o suéltalo en esta ventana.","Nessun file .nup in Download, Desktop, Documenti o nelle cartelle principali dei dischi. Cercalo o trascinalo su questa finestra.","Нет файлов .nup в «Загрузках», на рабочем столе, в «Документах» и в корневых папках дисков. Укажите свой файл или перетащите его в это окно.","Aucun fichier .nup dans Téléchargements, Bureau, Documents ou les dossiers principaux de vos disques. Cherchez le vôtre ou déposez-le sur cette fenêtre."},
        new[]{"Needs 60 GB · {0} has {1} GB free","Precisa de 60 GB · {0} tem {1} GB livres","Necesita 60 GB · {0} tiene {1} GB libres","Servono 60 GB · {0} ha {1} GB liberi","Нужно 60 ГБ · на {0} свободно {1} ГБ","60 Go nécessaires · {0} a {1} Go libres"},
        new[]{"DKB's build tools are missing from its folder. Press Build and DKB offers to download them again.","As ferramentas de build do DKB não estão na pasta. Clique em Criar o jogo e o DKB oferece baixá-las de novo.","Faltan las herramientas de DKB en su carpeta. Pulsa Crear el juego y DKB ofrecerá descargarlas de nuevo.","Mancano gli strumenti di DKB nella sua cartella. Premi Crea il gioco e DKB proporrà di scaricarli di nuovo.","В папке DKB нет инструментов сборки. Нажмите «Собрать игру», и DKB предложит скачать их заново.","Les outils de DKB manquent dans son dossier. Cliquez sur Créer le jeu et DKB proposera de les retélécharger."},
        new[]{"Nothing else to install: DKB's own build tools are here, downloaded and checked by its setup.","Nada mais a instalar: as ferramentas de build do DKB já estão aqui, baixadas e verificadas pelo instalador.","Nada más que instalar: las herramientas de DKB ya están aquí, descargadas y verificadas por su instalador.","Nient'altro da installare: gli strumenti di DKB sono già qui, scaricati e verificati dall'installazione.","Больше ничего ставить не нужно: инструменты DKB уже здесь, загружены и проверены установщиком.","Rien d'autre à installer : les outils de DKB sont déjà là, téléchargés et vérifiés par son installateur."},
        new[]{"Version checked","Versão verificada","Versión comprobada","Versione verificata","Версия проверена","Version vérifiée"},
        new[]{"Read your game files","Ler os arquivos do jogo","Leer los archivos del juego","Leggere i file di gioco","Чтение файлов игры","Lire les fichiers du jeu"},
        new[]{"Translate the game to PC code","Traduzir o jogo para código de PC","Traducir el juego a código de PC","Tradurre il gioco in codice PC","Перевод игры в код ПК","Traduire le jeu en code PC"},
        new[]{"Compile","Compilar","Compilar","Compilare","Компиляция","Compiler"},
        new[]{"Put the game together","Montar o jogo","Montar el juego","Assemblare il gioco","Сборка папки игры","Assembler le jeu"},
        new[]{"About {0} minutes left","Faltam cerca de {0} minutos","Quedan unos {0} minutos","Mancano circa {0} minuti","Осталось около {0} мин","Environ {0} minutes restantes"},
        new[]{"About a minute left","Falta cerca de um minuto","Queda cerca de un minuto","Manca circa un minuto","Осталась примерно минута","Environ une minute restante"},
        new[]{"Usually about 45 minutes","Normalmente cerca de 45 minutos","Normalmente unos 45 minutos","Di solito circa 45 minuti","Обычно около 45 минут","Environ 45 minutes en général"},
        new[]{"Working…","Trabalhando…","Trabajando…","Elaborazione…","Работаем…","En cours…"},
        new[]{"The build tools stopped without saying why.","As ferramentas de build pararam sem dizer o motivo.","Las herramientas se detuvieron sin indicar el motivo.","Gli strumenti si sono fermati senza indicare il motivo.","Инструменты сборки остановились без объяснения причины.","Les outils se sont arrêtés sans donner de raison."},
        new[]{"What went wrong","O que deu errado","Qué salió mal","Cosa è andato storto","Что пошло не так","Ce qui s'est mal passé"},
        new[]{"The update stopped","A atualização parou","La actualización se detuvo","L'aggiornamento si è interrotto","Обновление остановлено","La mise à jour s'est arrêtée"},
        new[]{"Your current game is unchanged and still plays.","Seu jogo atual não mudou e continua funcionando.","Tu juego actual no cambió y sigue funcionando.","Il gioco attuale è invariato e funziona ancora.","Текущая игра не изменилась и по-прежнему работает.","Votre jeu actuel est inchangé et fonctionne toujours."},
        new[]{"The build tools need repairing","As ferramentas de build precisam de reparo","Las herramientas necesitan reparación","Gli strumenti vanno riparati","Инструменты сборки нужно восстановить","Les outils doivent être réparés"},
        new[]{"Your antivirus removed part of the build tools","Seu antivírus removeu parte das ferramentas de build","Tu antivirus eliminó parte de las herramientas","L'antivirus ha rimosso parte degli strumenti","Антивирус удалил часть инструментов сборки","Votre antivirus a supprimé une partie des outils"},
        new[]{"Updating your game","Atualizando seu jogo","Actualizando tu juego","Aggiornamento del gioco","Обновление игры","Mise à jour de votre jeu"},
        new[]{"The update could not be downloaded","Não foi possível baixar a atualização","No se pudo descargar la actualización","Impossibile scaricare l'aggiornamento","Не удалось загрузить обновление","Impossible de télécharger la mise à jour"},
        new[]{"modified yesterday","modificado ontem","modificado ayer","modificato ieri","изменён вчера","modifié hier"},
        new[]{"The build tools are not in DKB's folder.","As ferramentas de build não estão na pasta do DKB.","Las herramientas no están en la carpeta de DKB.","Gli strumenti non sono nella cartella di DKB.","Инструментов сборки нет в папке DKB.","Les outils ne sont pas dans le dossier de DKB."},
        new[]{"Using the folders {0} and {1}","Usando as pastas {0} e {1}","Usando las carpetas {0} y {1}","Uso delle cartelle {0} e {1}","Используются папки {0} и {1}","Dossiers utilisés : {0} et {1}"},
    };

    static readonly Dictionary<string, string[]> Exact = new();
    static readonly List<(Regex Rx, string[] Row)> Pats = new();

    static UiText()
    {
        foreach (var row in Rows)
            foreach (var v in row)
                if (v.Contains("{0}"))
                    Pats.Add((new Regex("^" + Regex.Escape(v).Replace("\\{0}", "(.+?)").Replace("\\{1}", "(.+?)") + "$"), row));
                else Exact.TryAdd(v, row);
    }

    static int Idx(string c) =>
        c.StartsWith("pt") ? 1 : c.StartsWith("es") ? 2 : c.StartsWith("it") ? 3 : c.StartsWith("ru") ? 4 : c.StartsWith("fr") ? 5 : 0;

    static string Tr(string s, int i)
    {
        if (string.IsNullOrEmpty(s) || s.Length > 400) return s;
        if (Exact.TryGetValue(s, out var r)) return r[i];
        foreach (var (rx, row) in Pats)
        {
            var m = rx.Match(s);
            if (!m.Success) continue;
            var t = row[i];
            for (int g = 1; g < m.Groups.Count; g++) t = t.Replace("{" + (g - 1) + "}", m.Groups[g].Value);
            return t;
        }
        return s;
    }

    static void Walk(object o, int i)
    {
        if (o is not DependencyObject d) return;
        if (d is FrameworkElement fe && fe.ToolTip is string tt) { var t = Tr(tt, i); if (t != tt) fe.ToolTip = t; }
        if (d is TextBlock tb) { var s = tb.Text; var t = Tr(s, i); if (t != s) tb.Text = t; }
        else if (d is ContentControl cc && cc.Content is string cs) { var t = Tr(cs, i); if (t != cs) cc.Content = t; }
        if (d is ComboBox) return;
        foreach (var c in LogicalTreeHelper.GetChildren(d)) Walk(c, i);
    }

    public static void Attach(Window w, Func<string> code)
    {
        var t = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(250) };
        t.Tick += (_, _) => { try { Walk(w, Idx(code())); } catch { } };
        t.Start();
    }
}