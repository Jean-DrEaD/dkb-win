using System.Diagnostics;
using System.Formats.Tar;
using System.IO;
using System.IO.Compression;
using System.Net.Http;
using System.Text.Json;

namespace DkbBuilder;

sealed class Tools
{
    public const string Tag = "v0.3.5";
    public string Version => Tag;
    public string Root = "";
    public string Dir => Path.Combine(Root, "tools");
    public string Python => Path.Combine(Dir, "python", "python.exe");
    public string Msys => Path.Combine(Dir, "msys64");
    public string Clang => Path.Combine(Msys, "clang64");
    public string Dotnet => Path.Combine(Dir, "dotnet", "dotnet.exe");
    public string Src => Path.Combine(Dir, "src");
    public static Tools? Find() => new Tools { Root = AppContext.BaseDirectory.TrimEnd('\\', '/') };
}

static class Ferramentas
{
    const string PyUrl = "https://github.com/astral-sh/python-build-standalone/releases/download/20241016/cpython-3.12.7+20241016-x86_64-pc-windows-msvc-install_only.tar.gz";
    const string MsysUrl = "https://github.com/msys2/msys2-installer/releases/latest/download/msys2-base-x86_64-latest.sfx.exe";
    const string NetUrl = "https://builds.dotnet.microsoft.com/dotnet/Sdk/8.0.427/dotnet-sdk-8.0.427-win-x64.zip";
    const string RelApi = "https://api.github.com/repos/Jean-DrEaD/dkb-win/releases/tags/" + Tools.Tag;
    static readonly string[] Pkgs = { "clang", "lld", "sdl3", "opus", "zstd", "ninja", "vulkan-headers", "vulkan-loader", "pkgconf" };

    static readonly HttpClient Http = MakeHttp();
    static HttpClient MakeHttp() { var h = new HttpClient { Timeout = Timeout.InfiniteTimeSpan }; h.DefaultRequestHeaders.UserAgent.ParseAdd("DkbBuilder"); return h; }

    public static async Task Prepare(Tools t, Action<string> log, CancellationToken ct)
    {
        Directory.CreateDirectory(t.Dir);
        var tmp = Path.Combine(t.Dir, "_downloads"); Directory.CreateDirectory(tmp);

        if (!File.Exists(t.Src + "\\.ok"))
        {
            log("== Codigo-fonte " + Tools.Tag + " ==");
            string url;
            using (var doc = JsonDocument.Parse(await Http.GetStringAsync(RelApi, ct))) url = doc.RootElement.GetProperty("zipball_url").GetString()!;
            var zip = Path.Combine(tmp, "src.zip");
            await Download(url, zip, log, ct);
            var part = t.Src + ".part"; if (Directory.Exists(part)) Directory.Delete(part, true);
            ZipFile.ExtractToDirectory(zip, part);
            var inner = Directory.GetDirectories(part).First();
            if (Directory.Exists(t.Src)) Directory.Delete(t.Src, true);
            Directory.Move(inner, t.Src); Directory.Delete(part, true);
            File.WriteAllText(t.Src + "\\.ok", Tools.Tag);
        }

        var pyDir = Path.GetDirectoryName(t.Python)!;
        if (!File.Exists(pyDir + "\\.ok"))
        {
            log("== Python 3.12 (portatil) ==");
            var gz = Path.Combine(tmp, "python.tar.gz");
            await Download(PyUrl, gz, log, ct);
            if (Directory.Exists(pyDir)) Directory.Delete(pyDir, true);
            await using (var f = File.OpenRead(gz)) await using (var z = new GZipStream(f, CompressionMode.Decompress))
                await TarFile.ExtractToDirectoryAsync(z, t.Dir, true, ct);   // cria tools\python
            if (!File.Exists(t.Python)) throw new FileNotFoundException("python.exe sumiu (antivirus?)");
            File.WriteAllText(pyDir + "\\.ok", "");
        }
        if (!File.Exists(pyDir + "\\.pip-ok"))
        {
            log("== Pacotes Python ==");
            foreach (var r in new[] { "tools\\requirements.txt", "tools\\requirements-installer.txt", "launcher\\requirements.txt" })
            {
                var f = Path.Combine(t.Src, r);
                if (File.Exists(f) && await Run(t.Python, new[] { "-m", "pip", "install", "-q", "-r", f }, t.Src, t, log, ct) != 0) throw new Exception("pip falhou em " + r);
            }
            File.WriteAllText(pyDir + "\\.pip-ok", "");
        }

        var bash = Path.Combine(t.Msys, "usr", "bin", "bash.exe");
        if (!File.Exists(bash))
        {
            log("== MSYS2 (portatil) ==");
            var sfx = Path.Combine(tmp, "msys2.sfx.exe");
            await Download(MsysUrl, sfx, log, ct);
            if (await Run(sfx, new[] { "-y", "-o" + t.Dir }, t.Dir, t, log, ct) != 0 || !File.Exists(bash)) throw new Exception("Falha ao extrair o MSYS2 (antivirus?)");
            await Bash(t, "true", log, ct);                       // 1a execucao: cria o keyring
            await Bash(t, "pacman -Syuu --noconfirm", log, ct);   // pode fechar a si mesmo
            await Bash(t, "pacman -Syuu --noconfirm", log, ct);
        }
        // Corrige o erro do print: so instala com --needed e confere arquivos (sem pacman -Q)
        log("== Pacotes MSYS2 clang64 (inclui Vulkan) ==");
        var list = string.Join(" ", Pkgs.Select(p => "mingw-w64-clang-x86_64-" + p));
        if (await Bash(t, "pacman -Sy --needed --noconfirm " + list, log, ct) != 0)
            if (await Bash(t, "pacman -Syu --needed --noconfirm " + list, log, ct) != 0) throw new Exception("pacman falhou ao instalar: " + list);
        var need = new[] { "include\\vulkan\\vulkan.h", "lib\\libvulkan-1.dll.a", "include\\SDL3\\SDL.h", "include\\opus\\opus.h", "include\\zstd.h", "bin\\clang.exe", "bin\\ld.lld.exe", "bin\\ninja.exe" };
        var miss = need.Where(n => !File.Exists(Path.Combine(t.Clang, n))).ToList();
        if (miss.Count > 0) throw new Exception("Ainda faltam (antivirus?): " + string.Join(", ", miss));

        if (!File.Exists(t.Dotnet))
        {
            log("== .NET SDK 8 (portatil) ==");
            var zip = Path.Combine(tmp, "dotnet.zip");
            await Download(NetUrl, zip, log, ct);
            ZipFile.ExtractToDirectory(zip, Path.GetDirectoryName(t.Dotnet)!, true);
        }
        try { Directory.Delete(tmp, true); } catch { }
        if (t.Root.Any(c => c > 126)) log("[AVISO] Pasta com acento/caractere especial: prefira C:\\DKB");
        log("Ferramentas prontas.");
    }

    static async Task Download(string url, string to, Action<string> log, CancellationToken ct)
    {
        using var r = await Http.GetAsync(url, HttpCompletionOption.ResponseHeadersRead, ct);
        r.EnsureSuccessStatusCode();
        var total = r.Content.Headers.ContentLength ?? 0;
        await using var src = await r.Content.ReadAsStreamAsync(ct);
        await using var dst = File.Create(to);
        var buf = new byte[1 << 20]; long have = 0; int last = -1;
        for (int n; (n = await src.ReadAsync(buf, ct)) > 0;)
        {
            await dst.WriteAsync(buf.AsMemory(0, n), ct); have += n;
            var pc = total > 0 ? (int)(have * 10 / total) : -1;
            if (pc != last && pc >= 0) { last = pc; log($"  baixado {have >> 20} de {total >> 20} MB"); }
        }
    }

    public static Task<int> Bash(Tools t, string cmd, Action<string> log, CancellationToken ct) =>
        Run(Path.Combine(t.Msys, "usr", "bin", "bash.exe"), new[] { "-lc", cmd }, t.Dir, t, log, ct);

    public static async Task<int> Run(string exe, IEnumerable<string> args, string cwd, Tools t, Action<string> log, CancellationToken ct, Action<Process>? started = null)
    {
        var si = new ProcessStartInfo(exe) { WorkingDirectory = cwd, UseShellExecute = false, CreateNoWindow = true, RedirectStandardOutput = true, RedirectStandardError = true };
        foreach (var a in args) si.ArgumentList.Add(a);
        si.Environment["MSYSTEM"] = "CLANG64"; si.Environment["CHERE_INVOKING"] = "1"; si.Environment["PYTHONUNBUFFERED"] = "1";
        si.Environment["PATH"] = Path.Combine(t.Clang, "bin") + ";" + Path.Combine(t.Msys, "usr", "bin") + ";" + Path.GetDirectoryName(t.Dotnet) + ";" + Environment.GetEnvironmentVariable("PATH");
        using var p = Process.Start(si)!;
        started?.Invoke(p);
        p.OutputDataReceived += (_, e) => { if (e.Data != null) log(e.Data); };
        p.ErrorDataReceived += (_, e) => { if (e.Data != null) log(e.Data); };
        p.BeginOutputReadLine(); p.BeginErrorReadLine();
        try { await p.WaitForExitAsync(ct); } catch (OperationCanceledException) { try { p.Kill(true); } catch { } throw; }
        return p.ExitCode;
    }
}

sealed class Runner
{
    readonly Tools t; readonly List<string> a; readonly CancellationTokenSource cts = new(); Process? proc;
    public event Action<string>? Line;
    public event Action<string?>? Finished;
    public Runner(Tools t, List<string> a, int? workers) { this.t = t; this.a = a; }
    string? Get(string k) { var i = a.IndexOf(k); return i >= 0 && i + 1 < a.Count ? a[i + 1] : null; }
    public void Start() => _ = Task.Run(Work);
    public void Cancel() { cts.Cancel(); try { proc?.Kill(true); } catch { } }

    async Task Work()
    {
        void L(string s) => Line?.Invoke(s);
        try
        {
            L("@@stage read");
            await Ferramentas.Prepare(t, L, cts.Token);
            var dest = Get("--out") ?? Get("--update") ?? Path.Combine(t.Root, "jogo");
                var exefs = Get("--exefs"); var romfs = Get("--romfs"); var nup = Get("--nup");
                if ((exefs == null || romfs == null) && nup != null)
                {
                    var sc = Path.Combine(t.Src, "tools", "extract_nup.py");
                    var ext = Path.Combine(dest, "_nup");
                    L("== Extraindo o .nup (base + update) ==");
                    if (await Ferramentas.Run(t.Python, new[] { sc, nup, "--out", ext, "--overlay-update" }, t.Src, t, L, cts.Token, p => proc = p) != 0)
                    { Finished?.Invoke("Nao foi possivel extrair o .nup. Clique em 'Show details'."); return; }
                    exefs = Path.Combine(ext, "exefs"); romfs = Path.Combine(ext, "romfs");
                    var idx = await Nup.AddonIndex(t, nup);
                    if (idx != null)
                    {
                        L("== Extraindo a DLC ==");
                        if (await Ferramentas.Run(t.Python, new[] { sc, nup, "--package", idx, "--only", "romfs", "--out", Path.Combine(dest, "dlc") }, t.Src, t, L, cts.Token, p => proc = p) != 0)
                            L("[AVISO] DLC nao extraida; o jogo segue sem ela.");
                    }
                }
                if (exefs == null || romfs == null) { Finished?.Invoke("Escolha um .nup ou as pastas exefs e romfs."); return; }
            L("@@stage lift");
            var args = new[] { "-m", "installer", "--exefs", exefs, "--romfs", romfs, "--dest", dest,
                "--toolchain", t.Clang, "--deps", t.Clang, "--ninja", Path.Combine(t.Clang, "bin", "ninja.exe"),
                "--dll-dir", Path.Combine(t.Clang, "bin"), "--dotnet", t.Dotnet, "--lang", Get("--language") ?? "pt-BR" };
            var compiling = false;
            var code = await Ferramentas.Run(t.Python, args, t.Src, t, s =>
            {
                if (!compiling && s.Contains("compil", StringComparison.OrdinalIgnoreCase)) { compiling = true; L("@@stage compile"); }
                L(s);
            }, cts.Token, p => proc = p);
            if (code != 0) { Finished?.Invoke($"O build falhou (codigo {code}). Clique em 'Show details'."); return; }
            L("@@stage finish");
            L("@@done " + dest);
            Finished?.Invoke(null);
        }
        catch (OperationCanceledException) { Finished?.Invoke("cancelled"); }
        catch (UnauthorizedAccessException e) { Finished?.Invoke(e.Message + " (antivirus bloqueou um arquivo)"); }
        catch (Exception e) { Finished?.Invoke(e.Message); }
    }

    public static async Task<(bool Ok, string Text)> Check(Tools t, string[] a)
    {
        var i = Array.IndexOf(a, "--nup"); if (i < 0 || i + 1 >= a.Length) return (false, "Nenhum .nup.");
        var sc = Path.Combine(t.Src, "tools", "extract_nup.py");
        if (!File.Exists(t.Python) || !File.Exists(sc)) return (true, "Sera conferido no build (ferramentas ainda nao baixadas).");
        var lines = new List<string>();
        int code;
        try { code = await Ferramentas.Run(t.Python, new[] { sc, a[i + 1], "--list" }, t.Src, t, x => { lock (lines) lines.Add(x); }, CancellationToken.None); }
        catch (Exception e) { return (false, e.Message); }
        var all = string.Join("\n", lines);
        if (code != 0) return (false, lines.LastOrDefault() ?? "O .nup nao pode ser lido.");
        if (all.IndexOf("74a01bf1", StringComparison.OrdinalIgnoreCase) < 0 && all.IndexOf("bananza", StringComparison.OrdinalIgnoreCase) < 0)
            return (false, "This is build of another game (nao e o Donkey Kong Bananza).");
        var upd = all.IndexOf("update", StringComparison.OrdinalIgnoreCase) >= 0 ? " + update" : "";
        var dlc = all.IndexOf("addon", StringComparison.OrdinalIgnoreCase) >= 0 ? " + DLC" : "";
        return (true, "Donkey Kong Bananza: base" + upd + dlc);
    }
}

static class Nup
{
    public static async Task<string?> AddonIndex(Tools t, string nup)
    {
        var lines = new List<string>();
        await Ferramentas.Run(t.Python, new[] { Path.Combine(t.Src, "tools", "extract_nup.py"), nup, "--list" }, t.Src, t, x => { lock (lines) lines.Add(x); }, CancellationToken.None);
        foreach (var l in lines)
            if (l.Contains("addon", StringComparison.OrdinalIgnoreCase))
            { var m = System.Text.RegularExpressions.Regex.Match(l, @"\d+"); if (m.Success) return m.Value; }
        return null;
    }
}
