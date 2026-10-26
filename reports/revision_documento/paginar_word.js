var fso = new ActiveXObject('Scripting.FileSystemObject');
var root = WScript.Arguments.Item(0);
var source = WScript.Arguments.Item(1);
var app = new ActiveXObject('Word.Application');
var doc = null;
var initiallyEmpty = app.Documents.Count === 0;
try {
    app.Visible = false;
    app.DisplayAlerts = 0;
    app.AutomationSecurity = 3;
    doc = app.Documents.Open(source, false, true, false);
    doc.Repaginate();
    var out = fso.CreateTextFile(root + '\\paginacion_word.tsv', true, true);
    out.WriteLine('tipo\tpagina_fisica\tpagina_numerada\ttexto');
    out.WriteLine('TOTAL\t' + doc.ComputeStatistics(2) + '\t\t');
    for (var i = 1; i <= doc.Paragraphs.Count; i++) {
        var para = doc.Paragraphs.Item(i);
        var text = para.Range.Text.replace(/[\r\n\x07]/g, '').replace(/^\s+|\s+$/g, '');
        if (/^(Tabla\s+\d|Figura\s+\d|Anexo\s+[AB]|Integraci[oó]n del cat[aá]logo|Limpieza y transformaci[oó]n|Como comprobaci[oó]n adicional)/i.test(text)) {
            var point = para.Range.Duplicate;
            point.Collapse(1);
            out.WriteLine('TITULO\t' + point.Information(3) + '\t' + point.Information(1) + '\t' + text.replace(/\t/g,' [TAB] '));
        }
    }
    for (var j = 1; j <= doc.Tables.Count; j++) {
        var table = doc.Tables.Item(j).Range.Duplicate;
        var start = table.Duplicate;
        start.Collapse(1);
        var end = table.Duplicate;
        end.End = Math.max(end.Start, end.End - 1);
        end.Collapse(0);
        out.WriteLine('TABLA_REAL\t' + start.Information(3) + '\t' + end.Information(3) + '\t' + table.Text.substring(0, 100).replace(/[\r\n\x07\t]/g,' '));
    }
    out.Close();
    doc.ExportAsFixedFormat(root + '\\Informe_revision_paginada.pdf', 17);
    WScript.Echo('PDF y paginacion generados. Paginas: ' + doc.ComputeStatistics(2));
} finally {
    if (doc !== null) doc.Close(0);
    if (initiallyEmpty && app.Documents.Count === 0) app.Quit(0);
}
