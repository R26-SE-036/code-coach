package data.ml.raw_snippets.missing_break_in_switch.buggy;

public class MissingBreakBug030 {
    static int centsFor(char coin) {
        int cents = 0;
        switch (coin) {
            case 'p':
                cents = 1;
                break;
            case 'n':
                cents = 5;
            case 'd':
                cents = 10;
                break;
            case 'q':
                cents = 25;
                break;
        }
        return cents;
    }
}
