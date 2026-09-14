package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix004 {
    static int daysIn(String month) {
        int days = 0;
        switch (month) {
            case "February":
                days = 28;
                break;
            case "April":
                days = 30;
                break;
            case "January":
                days = 31;
                break;
            default:
                days = -1;
        }
        return days;
    }
}
