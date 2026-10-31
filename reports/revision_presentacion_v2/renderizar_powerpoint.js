// Conversión de archivo de solo lectura. No modifica presentaciones abiertas.
var input = WScript.Arguments(0);
var output = WScript.Arguments(1);
var app;
var created = false;
try {
    app = GetObject('', 'PowerPoint.Application');
} catch (e) {
    app = new ActiveXObject('PowerPoint.Application');
    created = true;
}
var deck;
try {
    deck = app.Presentations.Open(input, -1, 0, 0);
    WScript.Echo('Diapositivas abiertas: ' + deck.Slides.Count);
    var warnings = 0;
    for (var i = 1; i <= deck.Slides.Count; i++) {
        var slide = deck.Slides(i);
        for (var j = 1; j <= slide.Shapes.Count; j++) {
            var shape = slide.Shapes(j);
            if (shape.HasTextFrame && shape.TextFrame.HasText) {
                var available = shape.Height - shape.TextFrame.MarginTop - shape.TextFrame.MarginBottom;
                var required = shape.TextFrame.TextRange.BoundHeight;
                if (required > available + 2) {
                    WScript.Echo('REVISAR ' + i + ': ' + shape.TextFrame.TextRange.Text.slice(0, 90)
                        + ' altura ' + required.toFixed(1) + '/' + available.toFixed(1));
                    warnings++;
                }
            }
        }
    }
    WScript.Echo('Avisos de altura de texto: ' + warnings);
    deck.Export(output, 'PNG', 1600, 1042);
    deck.SaveAs(output + '\\vista.pdf', 32);
    WScript.Echo('Renderizado completado');
} finally {
    if (deck) deck.Close();
    if (created && app.Presentations.Count === 0) app.Quit();
}
