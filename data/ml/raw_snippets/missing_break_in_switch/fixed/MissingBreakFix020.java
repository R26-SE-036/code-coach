package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix020 {
    static int fee(int category) {
        int total = 0;
        switch (category) {
            case 0:
                total = 0;
                break;
            case 1:
                total = 50;
                break;
            case 2:
                total = 100;
                break;
            case 3:
                total = 150;
                break;
        }
        return total;
    }
}
