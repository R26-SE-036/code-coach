package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix022 {
    static char arrowSymbol(int keyCode) {
        char symbol = '?';
        switch (keyCode) {
            case 37:
                symbol = '<';
                break;
            case 38:
                symbol = '^';
                break;
            case 39:
                symbol = '>';
                break;
            case 40:
                symbol = 'v';
                break;
        }
        return symbol;
    }
}
