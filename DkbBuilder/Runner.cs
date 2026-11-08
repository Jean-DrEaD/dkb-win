using System.Diagnostics;
using System.IO;

namespace DkbBuilder;

/// Where nx2/make_game.py and its Python are: a "ToolsOld" folder beside the app when packaged, or the source tree it sits in.
sealed record ToolsOld(string Root, string Python)
{
    /// Which release these ToolsOld are (ToolsOld/version.txt, written when the release is packed); null from the source tree
    public string? Version => File.Exists(Path.Combine(Root, "version.txt")) ? File.ReadAllText(Path.Combine(Root, "version.txt")).Trim() : null;

    public static ToolsOld? Find()
    {
        var envRoot = Environment.GetEnvironmentVariable("DKB_ROOT"); if (envRoot != null && File.Exists(Path.Combine(envRoot, "dkbtools", "dkb_make.py"))) { var vp = Path.Combine(envRoot, ".venv", "Scripts", "python.exe"); return new ToolsOld(envRoot, File.Exists(vp) ? vp : "python"); } var at = AppContext.BaseDirectory;
        var bundled = Path.Combine(at, "ToolsOld");
        if (File.Exists(Path.Combine(bundled, "dkbtools", "dkb_make.py")))
        {
            var py = Path.Combine(bundled, "python", "python.exe");
            return new ToolsOld(bundled, File.Exists(py) ? py : "python");
        }
        for (var d = new DirectoryInfo(at); d != null; d = d.Parent)
            if (File.Exists(Path.Combine(d.FullName, "dkbtools", "dkb_make.py")))
                return new ToolsOld(d.FullName, "python");
        return null;
    }
}

/// nx2/make_game.py as a child process: its lines as they come, and how it ended.
sealed class RunnerOld
{
    readonly ToolsOld ToolsOld;
    readonly List<string> args;
    readonly int? workers;
    Process? process;
    string? error;
    bool cancelled;

    public event Action<string>? Line;
    public event Action<string?>? Finished;

    public RunnerOld(ToolsOld ToolsOld, List<string> args, int? workers = null)
    {
        this.ToolsOld = ToolsOld;
        this.args = args;
        if (workers is <= 0) throw new ArgumentOutOfRangeException(nameof(workers), "Build workers must be positive.");
        this.workers = workers;
    }

    static ProcessStartInfo Info(ToolsOld ToolsOld, IEnumerable<string> args, int? workers = null)
    {
        var si = new ProcessStartInfo(ToolsOld.Python)
        {
            WorkingDirectory = ToolsOld.Root,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
        };
        si.Environment["PYTHONIOENCODING"] = "utf-8";
        BuildWorkers.Apply(si, workers);
        // (written into the game folder's hookshot_version.txt: the game starts this app again to update, host/hos_update.c)
        if (Environment.ProcessPath != null) si.Environment["HOOKSHOT_BUILDER_EXE"] = Environment.ProcessPath;
        // (the folder's own compiler, headers and libraries, when it has them: nothing of the PC's but Windows' own)
        var sets = new[] { ("EMSDK", "emsdk"), ("RX_CPM", "cpm"), ("WGPU_NATIVE", "wgpu-native") };
        foreach (var (name, folder) in sets)
        {
            var path = Path.Combine(ToolsOld.Root, folder);
            if (Directory.Exists(path)) si.Environment[name] = path;
        }
        si.ArgumentList.Add("-I");
        si.ArgumentList.Add(Path.Combine(ToolsOld.Root, "dkbtools", "dkb_make.py"));
        foreach (var a in args) si.ArgumentList.Add(a);
        return si;
    }

    public void Start()
    {
        Task.Run(() =>
        {
            try
            {
                using var p = Process.Start(Info(ToolsOld, args, workers))!;
                process = p;
                p.ErrorDataReceived += (_, e) => { if (e.Data != null) Line?.Invoke(e.Data); };
                p.BeginErrorReadLine();
                try { p.PriorityClass = ProcessPriorityClass.BelowNormal; } catch (Exception) { }
                while (p.StandardOutput.ReadLine() is { } line)
                {
                    if (line.StartsWith("@@error ")) error = line[8..];
                    Line?.Invoke(line);
                }
                p.WaitForExit();
                Finished?.Invoke(cancelled ? "cancelled" : p.ExitCode == 0 ? null : error ?? "The build ToolsOld stopped without saying why. See the details.");
            }
            catch (Exception e)
            {
                Finished?.Invoke("The build ToolsOld could not start: " + e.Message);
            }
        });
    }

    public void Cancel()
    {
        cancelled = true;
        try { process?.Kill(entireProcessTree: true); } catch (Exception) { }
    }

    /// Is this the supported game and version? The answer in plain words.
    public static async Task<(bool Ok, string Text)> Check(ToolsOld ToolsOld, IEnumerable<string> args)
    {
        try
        {
            using var p = Process.Start(Info(ToolsOld, args))!;
            p.ErrorDataReceived += (_, _) => { };
            p.BeginErrorReadLine();
            var result = (false, "The game files could not be read.");
            while (await p.StandardOutput.ReadLineAsync() is { } line)
            {
                if (line.StartsWith("@@check ok ")) result = (true, line[11..]);
                else if (line.StartsWith("@@check bad ")) result = (false, line[12..]);
                else if (line.StartsWith("@@error ")) result = (false, line[8..]);
            }
            await p.WaitForExitAsync();
            return result;
        }
        catch (Exception)
        {
            // (the package's own Python missing: an antivirus took it, most often, after a false alarm on the download)
            if (ToolsOld.Python == "python" && Directory.Exists(Path.Combine(ToolsOld.Root, "python")))
                return (false, "The builder's own Python (ToolsOld/python/python.exe) is missing. Your antivirus probably removed it: restore it " +
                               "from quarantine, or unpack the zip again into a folder your antivirus allows, then try again.");
            return (false, "Python was not found. Install Python 3 or use the full oot-win Builder package.");
        }
    }
}

